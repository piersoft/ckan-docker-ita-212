# The format vocabulary can be found in the data.europa.eu [GitLab repository](https://gitlab.com/european-data-portal/edp-vocabularies).

import os
from urllib.parse import urljoin
from typing import Union
from rdflib import Graph, URIRef, Literal

import traceback

import logging


# ckan-docker-ita: la cache dei vocabolari scaricati va in una cartella
# scrivibile (volume ckan_storage); se il download fallisce si usa la copia
# bundled in /srv/app/patches (es. rete assente in build/avvio).
def _cache_path(name):
    base = os.environ.get("CKAN_STORAGE_PATH") or "/var/lib/ckan"
    d = os.path.join(base, "edp-vocabularies")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def _bundled_path(name):
    return os.path.join(os.environ.get("APP_DIR", "/srv/app"), "patches", name)

log = logging.getLogger(__name__)


class DataEuropaLicenseVocabulary:
    __prefix: str = None
    __file_types = []

    def __init__(
        self,
        file_types,
        prefix,
    ):
        self.__file_types = file_types
        self.__prefix = prefix

    def getUri(self, media_type) -> Union[URIRef, Literal]:

        if isinstance(media_type, URIRef):
            return media_type

        if str(media_type) in self.__file_types:
            return URIRef(urljoin(self.__prefix, str(media_type)))

        log.warn("Unable to properly format value to be complaing with MQA")
        return media_type


class DataEuropaVocabularyBuilder:
    def __init__(self):
        self.__instance = None

    def __call__(
        self,
        urls=[
            "https://gitlab.com/european-data-portal/edp-vocabularies/-/raw/master/edp-non-proprietary-format.rdf",
            "https://gitlab.com/european-data-portal/edp-vocabularies/-/raw/master/edp-machine-readable-format.rdf",
        ],
        prefix="http://publications.europa.eu/resource/authority/file-type/",
        filename=None,
    ):
        if not self.__instance:
            filename = filename or _cache_path("edp-licences-skos.rdf")
            # Create local file
            try:
                self._create_local_file(urls, filename)
            except Exception as err:
                traceback.print_exc()
                log.warn("Using local file")

            if not os.path.exists(filename):
                log.warning("Vocabolario EDP non scaricato, uso la copia bundled")
                filename = _bundled_path("edp-licences-skos.rdf")
            file_types = self._read_local_file(filename)
            self.__instance = DataEuropaVocabulary(file_types, prefix)

        return self.__instance

    def _create_local_file(self, urls, filename):
        g = Graph()
        for url in urls:
            log.info(f"Downloading information from {url}")
            g.parse(format="xml", location=url)

        g.serialize(format="pretty-xml", destination=filename)

    def _read_local_file(self, filename):
        g = Graph()
        g.parse(filename)

        # for s, p, o in g:
        file_types = []
        for s in g.subjects():
            file_types.append(os.path.split(s)[1])

        return list(set(file_types))
