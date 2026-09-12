"""
Regole di normalizzazione "pure" (nessun import CKAN): caricamento di
subcatalogs.json, match dell'ente, licenze, formati, date, identificatori.

Tutto cio' che qui e' hardcoded lo era gia' nelle patch storiche di
ckan-docker-ita su ckanext-dcat 1.x; e' stato solo raccolto in un posto solo.
"""
import json
import logging
import os
import re

log = logging.getLogger(__name__)

PUBLIC_ACCESS_RIGHTS = "http://publications.europa.eu/resource/authority/access-right/PUBLIC"
HVD_LEGISLATION = "http://data.europa.eu/eli/reg_impl/2023/138/oj"
FREQ_AUTHORITY = "http://publications.europa.eu/resource/authority/frequency/"
THEME_AUTHORITY = "http://publications.europa.eu/resource/authority/data-theme/"
LANG_AUTHORITY = "http://publications.europa.eu/resource/authority/language/"
FILETYPE_AUTHORITY = "http://publications.europa.eu/resource/authority/file-type/"
IANA_MEDIA_TYPES = "https://iana.org/assignments/media-types/"
FALLBACK_LICENSE = "http://creativecommons.org/licenses/by/4.0/"
SPDX_SHA1 = "http://spdx.org/rdf/terms#checksumAlgorithm_sha1"

_CONFIG = None


# ---------------------------------------------------------------------------
# Caricamento configurazione
# ---------------------------------------------------------------------------
def load_config(path=None):
    """Carica (una volta) subcatalogs.json. `path` puo' venire da ckan.ini."""
    global _CONFIG
    if _CONFIG is not None:
        return _CONFIG
    if not path:
        path = os.path.join(os.path.dirname(__file__), "subcatalogs.json")
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    # rimuovo le chiavi di documentazione
    for k in ("publisher_type_by_ipa_prefix", "license_map", "mimetype_by_format"):
        data.setdefault(k, {}).pop("_doc", None)
    data.pop("_doc", None)
    _CONFIG = data
    log.info("dcatita: caricato %s (%d subcatalog)", path, len(data.get("subcatalogs", [])))
    return _CONFIG


def reset_config():
    global _CONFIG
    _CONFIG = None


def match_subcatalog(dataset_dict, cfg=None):
    """Ritorna la voce di subcatalogs.json che matcha il dataset, o None."""
    cfg = cfg or load_config()
    default_field = cfg.get("match_field", "holder_identifier")
    for entry in cfg.get("subcatalogs", []):
        field = entry.get("match_field", default_field)
        value = dataset_dict.get(field) or _get_extra(dataset_dict, field) or ""
        if not value:
            continue
        for needle in entry.get("match", []):
            if needle in value:
                return entry
    return None


def publisher_type_from_ipa(holder_identifier, cfg=None):
    cfg = cfg or load_config()
    if not holder_identifier:
        return None
    table = cfg.get("publisher_type_by_ipa_prefix", {})
    # prefissi (r_, m_, c_, p_) e nomi (inps, inail, ...) — la prima che matcha
    for key, uri in table.items():
        if key.endswith("_"):
            if holder_identifier.startswith(key):
                return uri
        elif key in holder_identifier:
            return uri
    return None


# ---------------------------------------------------------------------------
# Helper generici
# ---------------------------------------------------------------------------
def _get_extra(dataset_dict, key):
    for ex in dataset_dict.get("extras") or []:
        if ex.get("key") == key:
            return ex.get("value")
    return None


def set_extra(dataset_dict, key, value):
    extras = dataset_dict.setdefault("extras", [])
    for ex in extras:
        if ex.get("key") == key:
            ex["value"] = value
            return
    extras.append({"key": key, "value": value})


def dedup_extras(dataset_dict):
    seen, out = set(), []
    for ex in dataset_dict.get("extras") or []:
        k = ex.get("key")
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(ex)
    dataset_dict["extras"] = out
    return dataset_dict


def scalar_from_json_list(value):
    """'["a"]' -> 'a'; ['a','b'] -> 'a'. Le patch storiche riducevano
    hvd_category / applicable_legislation a un solo valore."""
    if value is None:
        return value
    if isinstance(value, (list, tuple)):
        return value[0] if value else ""
    if isinstance(value, str) and value.strip().startswith("["):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed[0] if parsed else ""
        except ValueError:
            pass
    return value


# ---------------------------------------------------------------------------
# Identificatori, email, url
# ---------------------------------------------------------------------------
def sanitize_identifier(value):
    if not value:
        return value
    if " " in value or "http" in value:
        value = re.sub(r"[^a-zA-Z0-9:_]", "", value)
    return value


_EMAIL_BAD = (" ", "\u00a9", ";")


def clean_email(value):
    if not value:
        return value
    if any(b in value for b in _EMAIL_BAD):
        return ""
    return value.replace("]", "")


def clean_dataset_url(value):
    """Landing page: scarta valori non-http o le doppie landing page note."""
    if not value:
        return value
    v = value.replace("http://bdap-opendata.rgs.mef.gov.it/", "https://bdap-opendata.rgs.mef.gov.it/")
    low = v.lower()
    if "onsiglio" in low or "servizieducativi" in low or "serviziocontratti" in low:
        return ""
    if not low.startswith("http"):
        return ""
    return v


def clean_resource_url(value):
    if not value:
        return value
    return value.replace("'", "%27").replace(" ", "%20")


# ---------------------------------------------------------------------------
# Licenze
# ---------------------------------------------------------------------------
def normalize_license(value, cfg=None):
    if not value or not isinstance(value, str):
        return value
    cfg = cfg or load_config()
    value = value.replace("deed.it", "")
    for src, dst in cfg.get("license_map", {}).items():
        value = value.replace(src, dst)
    return value


# ---------------------------------------------------------------------------
# Date
# ---------------------------------------------------------------------------
_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}")


def to_date_only(value):
    """'2025-06-04T18:17:21Z' -> '2025-06-04'. Ricorsiva su liste/dict."""
    if value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [to_date_only(v) for v in value]
    if isinstance(value, dict):
        return {k: to_date_only(v) for k, v in value.items()}
    v = str(value).strip()
    if _ISO_DATE.match(v):
        return v[:10]
    return v


def normalize_temporal(dataset_dict):
    """Ogni chiave (dataset ed extras) contenente 'temporal' -> solo data.
    temporal_coverage puo' essere una stringa JSON di dict: si normalizza
    dentro e si riserializza (il validator dcatapit la vuole cosi')."""
    for k in list(dataset_dict.keys()):
        if "temporal" not in str(k).lower():
            continue
        v = dataset_dict.get(k)
        if isinstance(v, str) and v.strip().startswith("["):
            try:
                parsed = json.loads(v)
                dataset_dict[k] = json.dumps(to_date_only(parsed))
                continue
            except ValueError:
                pass
        dataset_dict[k] = to_date_only(v)
    for ex in dataset_dict.get("extras") or []:
        if "temporal" in str(ex.get("key", "")).lower():
            ex["value"] = to_date_only(ex.get("value"))
    return dataset_dict


# ---------------------------------------------------------------------------
# Frequenza, temi, lingue
# ---------------------------------------------------------------------------
def normalize_frequency_value(value):
    if not value:
        return "UNKNOWN"
    return str(value).replace("Dato non disponibile", "UNKNOWN")


def frequency_uri(value):
    """Valore CKAN (es. 'ANNUAL', 'Sconosciuta') -> URI del vocabolario EU."""
    v = str(value)
    if "Sconosciuta" in v:
        return FREQ_AUTHORITY + "UNKNOWN"
    if v.startswith("http"):
        return v
    return FREQ_AUTHORITY + v


def theme_uri(value):
    v = str(value).replace('["', "").replace('"]', "")
    return v if v.startswith("http") else THEME_AUTHORITY + v


def language_uri(value):
    v = str(value).replace('["', "").replace('"]', "")
    return v if "authority" in v else LANG_AUTHORITY + v


# ---------------------------------------------------------------------------
# Formati e media type
# ---------------------------------------------------------------------------
# (sottostringa nel formato, formato normalizzato) — in ordine di priorita'
_FORMAT_BY_FORMAT = (
    ("geo json", "GEOJSON"), ("GEOJSON", "GEOJSON"), ("csv-semicolon", "CSV"),
    ("csv-", "CSV"), ("CSV-", "CSV"), ("csv", "CSV"), ("CSV", "CSV"),
    ("-link", "HTML"), ("link", "HTML_SIMPL"), ("zip", "ZIP"), ("ZIP", "ZIP"),
    ("pdf", "PDF"), ("PDF", "PDF"), ("doc", "DOC"), ("xls", "XLS"),
    ("esri", "SHP"), ("kml", "KML"), ("ov2", "BIN"), ("OV2", "BIN"),
    ("wms", "WMS"), ("wfs", "WFS"), ("gml", "GML"), ("OData", "XML"),
)
# (sottostringa nell'url, formato) — usata quando il formato e' assente/placeholder
_FORMAT_BY_URL = (
    ("turtle", "RDF_TURTLE"), (".ttl", "RDF_TURTLE"), ("geojson", "GEOJSON"),
    ("gml", "GML"), ("sparql", "SPARQLQ"), ("rdf", "RDF"), ("xlsx", "XLSX"),
    ("xls", "XLSX"), ("download-metadata", "ZIP"), ("zip(", "ZIP"), ("zip", "ZIP"),
    (".csv", "CSV"), ("json", "JSON"), ("xsd", "XML"), ("xml", "XML"),
    ("pdf", "PDF"), ("ov2", "BIN"), ("fgb", "SHP"), ("shp", "SHP"), ("kml", "KML"),
    ("umap.openstreetmap", "HTML_SIMPL"), ("infogram.com", "HTML_SIMPL"),
    ("pubhtml", "HTML_SIMPL"),
)
_PLACEHOLDER_FORMATS = ("OP_DATPRO", "ARC", "")


def normalize_format(fmt, url=None):
    """Formato leggibile e stabile a partire dal formato dichiarato e/o dall'URL."""
    fmt = (fmt or "").replace(FILETYPE_AUTHORITY, "")
    if fmt and not fmt.startswith("http"):
        for needle, out in _FORMAT_BY_FORMAT:
            if needle in fmt:
                fmt = out
                break
    low_url = (url or "").lower()
    if (fmt in _PLACEHOLDER_FORMATS or fmt.startswith("http")) and low_url:
        for needle, out in _FORMAT_BY_URL:
            if needle in low_url:
                return out
    if "N/N" in (url or ""):
        return fmt
    return fmt


def mimetype_for_format(fmt, cfg=None):
    """Ritorna l'URI IANA del media type per il formato, o None."""
    if not fmt:
        return None
    cfg = cfg or load_config()
    f = fmt.upper()
    for key, mt in cfg.get("mimetype_by_format", {}).items():
        if key in f:
            return mt if mt.startswith("http") else IANA_MEDIA_TYPES + mt
    return None


def clean_tag(name):
    """Versione minimale di ckan.lib.munge.munge_tag (per usi senza CKAN)."""
    name = re.sub(r"[^\w\-. ]", "", name or "").strip().lower()
    name = re.sub(r"\s+", " ", name)
    return name[:100]
