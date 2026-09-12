"""
Profilo RDF `dcat_ita` — va messo IN CODA alla catena dei profili:

    ckanext.dcat.rdf.profiles = euro_dcat_ap_3 it_dcat_ap dcat_ita

Non produce triple "sue": rifinisce il grafo gia' costruito dai profili
precedenti applicando le regole che nello stack 2.10 erano patch dentro
ckanext-dcat (processors.py / euro_dcat_ap.py / base.py). Lato parse non fa
nulla: le normalizzazioni dei dati harvestati stanno in plugins.DCATItaHarvestPlugin.
"""
import logging

from rdflib import BNode, Literal, URIRef
from rdflib.namespace import RDF, XSD

import ckan.plugins.toolkit as tk

from ckanext.dcat.profiles.base import (
    RDFProfile, CleanedURIRef, DCAT, DCT, RDFS, SPDX, FOAF,
)
from ckanext.dcat.utils import resource_uri

from ckanext.dcatita import rules
from ckanext.dcatita.plugins import rewrite_uri, _cfg

log = logging.getLogger(__name__)

DCATAPIT = URIRef("http://dati.gov.it/onto/dcatapit#")


def _ns(local):
    return URIRef(str(DCATAPIT) + local)


class DCATItaProfile(RDFProfile):

    # ------------------------------------------------------------------ parse
    def parse_dataset(self, dataset_dict, dataset_ref):
        return dataset_dict

    # ------------------------------------------------------------------ graph
    def graph_from_dataset(self, dataset_dict, dataset_ref):
        g = self.g
        cfg = _cfg()
        entry = rules.match_subcatalog(dataset_dict, cfg) or {}
        site_url = tk.config.get("ckan.site_url", "").rstrip("/")

        # --- identificatore --------------------------------------------------
        for obj in list(g.objects(dataset_ref, DCT.identifier)):
            if isinstance(obj, Literal):
                clean = rules.sanitize_identifier(str(obj))
                if clean != str(obj):
                    g.remove((dataset_ref, DCT.identifier, obj))
                    g.add((dataset_ref, DCT.identifier, Literal(clean)))

        # --- landing page ------------------------------------------------------
        for obj in list(g.objects(dataset_ref, DCAT.landingPage)):
            if not rules.clean_dataset_url(str(obj)):
                g.remove((dataset_ref, DCAT.landingPage, obj))

        # --- dct:accessRights come RightsStatement (default PUBLIC) -------------
        if not any(g.objects(dataset_ref, DCT.accessRights)):
            ar = dataset_dict.get("access_rights") or rules._get_extra(dataset_dict, "access_rights") \
                or rules.PUBLIC_ACCESS_RIGHTS
            self._add_statement(dataset_ref, DCT.accessRights, ar, DCT.RightsStatement)
        else:
            for obj in g.objects(dataset_ref, DCT.accessRights):
                if isinstance(obj, URIRef) and (obj, RDF.type, DCT.RightsStatement) not in g:
                    g.add((obj, RDF.type, DCT.RightsStatement))

        prov = dataset_dict.get("provenance") or rules._get_extra(dataset_dict, "provenance")
        if prov and not any(g.objects(dataset_ref, DCT.provenance)):
            self._add_statement(dataset_ref, DCT.provenance, prov, DCT.ProvenanceStatement)

        # --- vocabolari EU: frequenza, temi, lingue --------------------------------
        self._to_vocab(dataset_ref, DCT.accrualPeriodicity, rules.frequency_uri)
        self._to_vocab(dataset_ref, DCAT.theme, rules.theme_uri)
        self._to_vocab(dataset_ref, DCT.language, rules.language_uri,
                       keep_if=lambda v: "authority" in v)

        # --- publisher: dct:type dal codice IPA, identificatore, classe dcatapit ---
        holder = dataset_dict.get("holder_identifier") or rules._get_extra(dataset_dict, "holder_identifier") or ""
        pub_type = rules.publisher_type_from_ipa(holder, cfg)
        for pub in g.objects(dataset_ref, DCT.publisher):
            if pub_type:
                for old in list(g.objects(pub, DCT.type)):
                    g.remove((pub, DCT.type, old))
                g.add((pub, DCT.type, URIRef(pub_type)))
            if holder and not any(g.objects(pub, DCT.identifier)):
                g.add((pub, DCT.identifier, Literal(holder)))

        # --- distribuzioni ---------------------------------------------------------
        resources = {}
        for r in dataset_dict.get("resources") or []:
            resources[str(CleanedURIRef(resource_uri(r)))] = r

        for dist in list(g.objects(dataset_ref, DCAT.distribution)):
            r = resources.get(str(dist), {})
            self._fix_distribution(dataset_dict, dataset_ref, dist, r, entry, site_url, cfg)

    # ------------------------------------------------------------------ helpers
    def _fix_distribution(self, dataset_dict, dataset_ref, dist, r, entry, site_url, cfg):
        g = self.g

        # accessURL = pagina risorsa CKAN (fix "delicato" del 22.12.25), downloadURL = url
        url = r.get("url")
        if r.get("id") and dataset_dict.get("id") and site_url:
            access_url = f"{site_url}/dataset/{dataset_dict['id']}/resource/{r['id']}"
            if entry.get("access_url_from_download"):
                access_url = r.get("download_url") or url or access_url
            self._replace_all(dist, DCAT.accessURL, CleanedURIRef(access_url))
        if url and not any(g.objects(dist, DCAT.downloadURL)):
            g.add((dist, DCAT.downloadURL, CleanedURIRef(url)))

        # dct:rights PUBLIC se assente
        if not any(g.objects(dist, DCT.rights)):
            self._add_statement(dist, DCT.rights, r.get("rights") or rules.PUBLIC_ACCESS_RIGHTS,
                                DCT.RightsStatement)

        # licenza: mapping URI italiane -> URI canoniche (solo le voci lato grafo)
        for obj in list(g.objects(dist, DCT.license)):
            new = rules.normalize_license(str(obj), cfg, side="graph")
            if new != str(obj):
                g.remove((dist, DCT.license, obj))
                g.add((dist, DCT.license, URIRef(new)))

        # formato normalizzato + media type IANA
        fmt = rules.normalize_format(r.get("format"), url)
        if fmt:
            for obj in list(g.objects(dist, DCT["format"])):
                if isinstance(obj, Literal):
                    g.remove((dist, DCT["format"], obj))
            if not any(g.objects(dist, DCT["format"])):
                g.add((dist, DCT["format"], Literal(fmt)))
            if not any(g.objects(dist, DCAT.mediaType)):
                mt = rules.mimetype_for_format(fmt, cfg)
                if mt:
                    g.add((dist, DCAT.mediaType, URIRef(mt)))
                    g.add((URIRef(mt), RDF.type, DCT.MediaType))

        # byteSize: MQA vuole un valore; storico = 1024 se sconosciuto
        if not any(g.objects(dist, DCAT.byteSize)):
            g.add((dist, DCAT.byteSize, Literal(1024.0, datatype=XSD.decimal)))

        # checksum: Emilia-Romagna espone hash non validi -> si toglie; altrimenti algoritmo default sha1
        for cs in list(g.objects(dist, SPDX.checksum)):
            if entry.get("skip_checksum"):
                g.remove((cs, None, None))
                g.remove((dist, SPDX.checksum, cs))
            elif not any(g.objects(cs, SPDX.algorithm)):
                g.add((cs, SPDX.algorithm, URIRef(rules.SPDX_SHA1)))

        # dcat:accessService: licenza e diritti di default
        for svc in g.objects(dist, DCAT.accessService):
            if not any(g.objects(svc, DCT.license)):
                g.add((svc, DCT.license, URIRef(rules.FALLBACK_LICENSE)))
            if not any(g.objects(svc, DCT.accessRights)):
                g.add((svc, DCT.accessRights, URIRef(rules.PUBLIC_ACCESS_RIGHTS)))

        # URI della distribuzione con la base del catalogo d'origine (per ultima:
        # da qui in poi `dist` non e' piu' il nodo giusto)
        if entry.get("base_uri") and not entry.get("dataset_only"):
            new = rewrite_uri(str(dist), entry)
            if new != str(dist):
                self._rename_node(dist, CleanedURIRef(new))

    def _add_statement(self, subject, predicate, value, _class):
        if str(value).startswith("http"):
            obj = URIRef(value)
            self.g.add((subject, predicate, obj))
            self.g.add((obj, RDF.type, _class))
        else:
            node = BNode()
            self.g.add((subject, predicate, node))
            self.g.add((node, RDF.type, _class))
            self.g.add((node, RDFS.label, Literal(value)))

    def _to_vocab(self, subject, predicate, to_uri, keep_if=None):
        for obj in list(self.g.objects(subject, predicate)):
            v = str(obj)
            if isinstance(obj, URIRef) and (keep_if(v) if keep_if else v.startswith("http")):
                continue
            new = to_uri(v)
            if new != v or not isinstance(obj, URIRef):
                self.g.remove((subject, predicate, obj))
                self.g.add((subject, predicate, URIRef(new)))

    def _replace_all(self, subject, predicate, obj):
        for old in list(self.g.objects(subject, predicate)):
            self.g.remove((subject, predicate, old))
        self.g.add((subject, predicate, obj))

    # predicati il cui oggetto e' un URL "vero" e non va riscritto quando si
    # rinomina il nodo della distribuzione
    _KEEP_OBJECT = (DCAT.accessURL, DCAT.downloadURL, DCAT.landingPage, FOAF.homepage)

    def _rename_node(self, old, new):
        g = self.g
        for s, p, o in list(g.triples((old, None, None))):
            g.remove((s, p, o))
            g.add((new, p, o))
        for s, p, o in list(g.triples((None, None, old))):
            if p in self._KEEP_OBJECT:
                continue
            g.remove((s, p, o))
            g.add((s, p, new))

    # ------------------------------------------------------------------ catalog
    def graph_from_catalog(self, catalog_dict, catalog_ref):
        g = self.g
        taxonomy = URIRef("http://publications.europa.eu/resource/authority/data-theme")
        if (catalog_ref, DCAT.themeTaxonomy, taxonomy) not in g:
            g.add((catalog_ref, DCAT.themeTaxonomy, taxonomy))
