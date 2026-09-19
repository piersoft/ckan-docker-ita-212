"""
Plugin CKAN di ckanext-dcatita.

- DCATItaHarvestPlugin: implementa IDCATRDFHarvester (ckanext-dcat >= 2.4) e
  applica alle risorse harvestate le normalizzazioni che nel vecchio stack
  vivevano dentro patch a rdf.py / euro_dcat_ap.py.
- DCATItaURIPlugin: implementa IDCATURIGenerator e riscrive le URI di dataset e
  distribuzioni con la base del catalogo d'origine (subcatalogs.json).

Opzioni ckan.ini (tutte facoltative):
  ckanext.dcatita.subcatalogs_file        = /path/subcatalogs.json
  ckanext.dcatita.harvest_verify_ssl      = false   (default: false, come lo stack 2.10)
  ckanext.dcatita.default_applicable_legislation = true  (imposta l'ELI HVD in creazione se assente)
"""
import json
import logging

import ckan.plugins as p
import ckan.plugins.toolkit as tk

from ckanext.dcat.interfaces import IDCATRDFHarvester, IDCATURIGenerator
from ckanext.dcat.utils import catalog_uri

from ckanext.dcatita import rules

log = logging.getLogger(__name__)

# campi del dataset che dcatapit / edp-mqa valorizzano da soli in creazione
# e che l'harvester non deve far validare (comportamento storico)
_SCHEMA_KEYS_TO_DROP = ("access_rights", "applicable_legislation",
                        "applicableLegislation", "hvd_category", "package_id")


def _cfg():
    return rules.load_config(tk.config.get("ckanext.dcatita.subcatalogs_file"))


# ---------------------------------------------------------------------------
# Harvest
# ---------------------------------------------------------------------------
# "Firma" del progetto: la frase sta nel sorgente solo in base64 e viene
# decodificata a runtime dall'helper; il template base.html la scrive nel
# <head> di ogni pagina (commento HTML + meta), visibile nel sorgente della home.
_SIGNATURE_B64 = "UHJvZ2V0dG8gb3JpZ2luYXJpbyBkaSBQaWVyc29mdCAoRnJhbmNlc2NvIFBpZXJvIFBhb2xpY2VsbGkpIC0gY2thbi1kb2NrZXItaXRhLTIxMiAtIEFHUEwtMy4wLW9yLWxhdGVyIC0gaHR0cHM6Ly9naXRodWIuY29tL3BpZXJzb2Z0L2NrYW4tZG9ja2VyLWl0YS0yMTI="


def dcatita_signature():
    import base64
    try:
        return base64.b64decode(_SIGNATURE_B64).decode("utf-8")
    except Exception:  # pragma: no cover
        return ""


RESTRICTED_ACCESS_RIGHTS = "http://publications.europa.eu/resource/authority/access-right/RESTRICTED"


def dcatita_is_restricted(pkg):
    """True se il dataset ha dct:accessRights RESTRICTED (dati ad accesso limitato
    ai sensi del Data Governance Act). Funziona sia con il dict completo di
    package_show sia con quello ridotto dei risultati di ricerca."""
    if not pkg:
        return False
    value = pkg.get("access_rights") or rules._get_extra(pkg, "access_rights") or ""
    return "RESTRICTED" in str(value).upper()


def dcatita_restricted_search_url():
    """URL della ricerca filtrata sui soli dataset ad accesso limitato."""
    try:
        return tk.h.url_for("dataset.search", access_rights=RESTRICTED_ACCESS_RIGHTS)
    except Exception:
        return "/dataset/?access_rights=" + RESTRICTED_ACCESS_RIGHTS


def dcatita_mqa_badge_enabled():
    """Badge MQA di data.europa.eu nella pagina dataset (ha senso solo se il
    catalogo e' harvestato dal portale europeo)."""
    return tk.asbool(tk.config.get("ckanext.dcatita.mqa_badge", False))


@tk.blanket.config_declarations
class DCATItaHarvestPlugin(p.SingletonPlugin):
    p.implements(IDCATRDFHarvester, inherit=True)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)

    def update_config(self, config_):
        tk.add_template_directory(config_, "templates")

    def get_helpers(self):
        return {"dcatita_signature": dcatita_signature,
                "dcatita_mqa_badge_enabled": dcatita_mqa_badge_enabled,
                "dcatita_is_restricted": dcatita_is_restricted,
                "dcatita_restricted_search_url": dcatita_restricted_search_url}

    # --- sessione HTTP: i cataloghi PA con catene TLS rotte ------------------
    def update_session(self, session):
        if not tk.asbool(tk.config.get("ckanext.dcatita.harvest_verify_ssl", False)):
            session.verify = False
            try:
                import urllib3
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            except Exception:  # pragma: no cover
                pass
        return session

    # --- schema ---------------------------------------------------------------
    def update_package_schema_for_create(self, package_schema):
        for k in _SCHEMA_KEYS_TO_DROP:
            package_schema.pop(k, None)
        return package_schema

    def update_package_schema_for_update(self, package_schema):
        for k in _SCHEMA_KEYS_TO_DROP:
            package_schema.pop(k, None)
        return package_schema

    # --- dataset ---------------------------------------------------------------
    def before_create(self, harvest_object, dataset_dict, temp_dict):
        self._normalize(dataset_dict, creating=True)

    def before_update(self, harvest_object, dataset_dict, temp_dict):
        self._normalize(dataset_dict, creating=False)

    def _normalize(self, d, creating):
        cfg = _cfg()
        entry = rules.match_subcatalog(d, cfg) or {}

        d.pop("package_id", None)

        # identificatore, descrizione, tag, frequenza
        if not d.get("identifier"):
            d["identifier"] = d.get("id")
        d["identifier"] = rules.sanitize_identifier(d.get("identifier"))
        if not d.get("notes"):
            d["notes"] = "N_A"
        tags = d.get("tags") or []
        if not tags:
            d["tags"] = [{"name": "N_A"}]
        else:
            d["tags"] = self._clean_tags(tags)
        if entry.get("frequency_unknown"):
            d["frequency"] = "UNKNOWN"
        else:
            d["frequency"] = rules.normalize_frequency_value(d.get("frequency"))

        # landing page
        d["url"] = rules.clean_dataset_url(d.get("url"))
        landing = rules._get_extra(d, "landingpage")
        if landing and not d.get("url"):
            d["url"] = landing
        if d.get("url") and not landing:
            rules.set_extra(d, "landingpage", d["url"])

        # email
        for k in ("author_email", "maintainer_email"):
            if d.get(k) is not None:
                d[k] = rules.clean_email(d[k])

        # diritti di accesso / HVD (solo se assenti: non si sovrascrive un
        # eventuale RESTRICTED dichiarato dalla sorgente, serve al DGA)
        if not d.get("access_rights"):
            d["access_rights"] = rules._get_extra(d, "access_rights") or rules.PUBLIC_ACCESS_RIGHTS
        for k in ("hvd_category", "applicable_legislation"):
            if d.get(k) is not None:
                d[k] = rules.scalar_from_json_list(d[k])
            ex = rules._get_extra(d, k)
            if ex is not None:
                rules.set_extra(d, k, rules.scalar_from_json_list(ex))
        if d.get("applicableLegislation") and not d.get("applicable_legislation"):
            d["applicable_legislation"] = rules.scalar_from_json_list(d.pop("applicableLegislation"))
        if creating and not d.get("applicable_legislation") and \
                tk.asbool(tk.config.get("ckanext.dcatita.default_applicable_legislation", True)):
            d["applicable_legislation"] = rules.HVD_LEGISLATION

        # date
        rules.normalize_temporal(d)

        # risorse
        for r in d.get("resources") or []:
            self._normalize_resource(r, d, cfg)

        # subcatalog (dct:hasPart) — metadati del catalogo d'origine
        self._apply_source_catalog(d, entry, cfg)

        rules.dedup_extras(d)

    def _normalize_resource(self, r, d, cfg):
        if r.get("url"):
            r["url"] = rules.clean_resource_url(r["url"])
        r["format"] = rules.normalize_format(r.get("format"), r.get("url"))
        if not r.get("distribution_format"):
            r["distribution_format"] = r["format"]
        if not r.get("rights"):
            r["rights"] = rules.PUBLIC_ACCESS_RIGHTS
        for k in ("license", "license_type"):
            if r.get(k):
                r[k] = rules.normalize_license(r[k], cfg)
        if not r.get("name") or len(r["name"]) < 2:
            r["name"] = "N/A"

    def _apply_source_catalog(self, d, entry, cfg):
        """Completa gli extras source_catalog_* letti da processors._add_source_catalog."""
        homepage = entry.get("homepage") or entry.get("base_uri")
        if homepage:
            rules.set_extra(d, "source_catalog_homepage", homepage)
        if entry.get("language"):
            rules.set_extra(d, "source_catalog_language", entry["language"])
        if entry.get("modified_from_extra"):
            v = rules._get_extra(d, entry["modified_from_extra"])
            if v:
                rules.set_extra(d, "source_catalog_modified", v)
        if entry.get("publisher") and not rules._get_extra(d, "source_catalog_publisher"):
            pub = dict(entry["publisher"])
            pub.setdefault("uri", "")
            pub.setdefault("email", "")
            rules.set_extra(d, "source_catalog_publisher", json.dumps(pub))
        # default storici quando l'harvest ha lasciato la chiave vuota
        for key, default in (("source_catalog_title", "Portale Dati Aperti"),
                             ("source_catalog_description", "Portale Dati Aperti")):
            for ex in d.get("extras") or []:
                if ex.get("key") == key and not ex.get("value"):
                    ex["value"] = default

    @staticmethod
    def _clean_tags(tags):
        from ckan.lib.munge import munge_tag
        out = []
        for t in tags:
            if isinstance(t, dict):
                name = munge_tag(t.get("name") or "")
                if name:
                    t["name"] = name
                    out.append(t)
            else:
                name = munge_tag(t)
                if name and name not in out:
                    out.append(name)
        return out


# ---------------------------------------------------------------------------
# URI
# ---------------------------------------------------------------------------
# cache package_id -> voce di subcatalogs.json, riempita da dataset_uri() (che
# ckanext-dcat chiama sempre prima delle risorse dello stesso dataset) e letta
# da resource_uri(), dove il dict della risorsa non porta holder_identifier.
_ENTRY_BY_DATASET = {}
_ENTRY_CACHE_MAX = 5000


class DCATItaURIPlugin(p.SingletonPlugin):
    """URI di dataset e distribuzioni con la base del catalogo d'origine
    (es. https://dati.regione.marche.it/dataset/<id>) anziche' quella di
    dati.gov.it, per i cataloghi elencati in subcatalogs.json. Passando da
    IDCATURIGenerator la stessa URI viene vista da TUTTI i profili
    (euro_dcat_ap_3, it_dcat_ap, dcat_ita): nessun nodo sdoppiato."""
    p.implements(IDCATURIGenerator, inherit=True)

    def dataset_uri(self, dataset_dict, default_uri):
        entry = rules.match_subcatalog(dataset_dict, _cfg())
        if len(_ENTRY_BY_DATASET) > _ENTRY_CACHE_MAX:
            _ENTRY_BY_DATASET.clear()
        if dataset_dict.get("id"):
            _ENTRY_BY_DATASET[dataset_dict["id"]] = entry
        if not entry or entry.get("distribution_only"):
            return None
        return rewrite_uri(default_uri, entry)

    def resource_uri(self, resource_dict, default_uri):
        entry = _ENTRY_BY_DATASET.get(resource_dict.get("package_id"))
        if not entry or entry.get("dataset_only"):
            return None
        return rewrite_uri(default_uri, entry)


def rewrite_uri(uri, entry):
    base = catalog_uri().rstrip("/")
    new_base = entry.get("base_uri")
    out = str(uri)
    if new_base:
        out = out.replace(base + "/", new_base.rstrip("/") + "/")
        out = out.replace(base, new_base.rstrip("/"))
    for src, dst in entry.get("replace", []):
        out = out.replace(src, dst)
    return out
