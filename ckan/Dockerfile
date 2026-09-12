# =====================================================================
#  CKAN Docker per l'Italia — immagine CKAN 2.12
#  Base ufficiale: python 3.14 slim, utente non-root `ckan` (uid 503).
#  Le estensioni vengono abilitate una fase alla volta (vedi CHANGELOG):
#    FASE 1  core + xloader                         (fatta)
#    FASE 2  ckanext-harvest 1.6.3 + patch                (fatta)
#    FASE 3  ckanext-dcat 2.4.4 (DCAT-AP 3) + patch + ckanext-dcatita  (fatta)
#    FASE 4  ckanext-dcatapit + multilang adeguate a 2.12   (fatta)
#    FASE 5  oai-pmh-server (OpenAIRE), dcat-ap-edp-mqa (MQA)  <- QUESTA
# =====================================================================
FROM ckan/ckan-base:2.12.0-py3.14

USER root

# Strumenti di base: `patch` serve al loop delle patch, nano/curl per il debug.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git patch nano curl \
    && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------------
#  FASE 1 — Xloader (DataStore)
# ---------------------------------------------------------------------
# NB: le estensioni vanno installate in modalita' editable sotto ${SRC_DIR}
# (PIP_SRC), altrimenti il namespace `ckanext` di /srv/app/src/ckan oscura
# quello di site-packages e il plugin non viene trovato.
RUN pip3 install --no-cache-dir -e git+https://github.com/ckan/ckanext-xloader.git@2.5.0#egg=ckanext-xloader \
    && pip3 install --no-cache-dir -r ${SRC_DIR}/ckanext-xloader/requirements.txt

# ---------------------------------------------------------------------
#  FASE 2 — Harvest: upstream 1.6.3 (supporto ufficiale CKAN 2.12) +
#  patch locali in patches/ckanext-harvest-patches/*.patch
#  (normalizzazione dei cataloghi federati, harvest source con URL duplicato)
# ---------------------------------------------------------------------
# (dalla 1.6.3 le dipendenze stanno nel pyproject.toml: niente requirements.txt)
RUN pip3 install --no-cache-dir -e git+https://github.com/ckan/ckanext-harvest.git@v1.6.3#egg=ckanext-harvest
COPY patches/ckanext-harvest-patches ${APP_DIR}/patches/ckanext-harvest-patches
RUN cd ${SRC_DIR}/ckanext-harvest && for f in ${APP_DIR}/patches/ckanext-harvest-patches/*.patch; do \
        echo "Applying $f"; patch -p1 < "$f"; done

# ---------------------------------------------------------------------
#  FASE 3 — ckanext-dcat 2.4.4 upstream + 4 patch minime
#  (patches/ckanext-dcat-patches/: subcatalog per organizzazione, fq multipli
#  sul catalog.ttl, file-type nel JSON harvester) + ckanext-dcatita (regole
#  italiane via interfacce ufficiali, vedi ckanext-dcatita/README.md)
# ---------------------------------------------------------------------
RUN pip3 install --no-cache-dir -e git+https://github.com/ckan/ckanext-dcat.git@v2.4.4#egg=ckanext-dcat \
    && pip3 install --no-cache-dir -r ${SRC_DIR}/ckanext-dcat/requirements.txt
COPY patches/ckanext-dcat-patches ${APP_DIR}/patches/ckanext-dcat-patches
RUN cd ${SRC_DIR}/ckanext-dcat && for f in ${APP_DIR}/patches/ckanext-dcat-patches/*.patch; do \
        echo "Applying $f"; patch -p1 < "$f"; done
COPY ckanext-dcatita ${SRC_DIR}/ckanext-dcatita
RUN pip3 install --no-cache-dir -e ${SRC_DIR}/ckanext-dcatita

# ---------------------------------------------------------------------
#  FASE 4 — ckanext-dcatapit (fork in ckan/ckanext-dcatapit, adeguato a 2.12:
#  extras JSONB, IGroupForm create/update/show_group_schema, CSRF, niente
#  Pylons). Fornisce form/vocabolari DCAT-AP_IT e il profilo RDF it_dcat_ap.
# ---------------------------------------------------------------------
COPY ckanext-dcatapit ${SRC_DIR}/ckanext-dcatapit
RUN pip3 install --no-cache-dir -e ${SRC_DIR}/ckanext-dcatapit \
    && pip3 install --no-cache-dir -r ${SRC_DIR}/ckanext-dcatapit/requirements.txt
# file di mapping usati da dcatapit (temi->gruppi, temi non conformi, regioni, gruppi tematici)
COPY patches/theme_to_group.ini patches/topics.json patches/regions.rdf ${APP_DIR}/patches/
COPY patches/groups ${APP_DIR}/patches/groups
RUN chmod 666 ${APP_DIR}/patches/theme_to_group.ini ${APP_DIR}/patches/topics.json
# ckanext-multilang (geosolutions-it, master 2026-05) vendorizzato in ckan/ckanext-multilang
# e portato a SQLAlchemy 2.0: dcatapit lo richiede a runtime (campi localizzati, holder).
COPY ckanext-multilang ${SRC_DIR}/ckanext-multilang
RUN pip3 install --no-cache-dir -e ${SRC_DIR}/ckanext-multilang

# ---------------------------------------------------------------------
#  FASE 5 — OAI-PMH server (OpenAIRE/DataCite) e profilo MQA data.europa.eu
#  Entrambe facoltative: attivare/disattivare via CKAN__PLUGINS e
#  CKANEXT__DCAT__RDF__PROFILES nel .env (vedi .env.example).
# ---------------------------------------------------------------------
COPY ckanext-oai-pmh-server ${SRC_DIR}/ckanext-oai-pmh-server
RUN pip3 install --no-cache-dir -e ${SRC_DIR}/ckanext-oai-pmh-server \
    && pip3 install --no-cache-dir -r ${SRC_DIR}/ckanext-oai-pmh-server/requirements.txt
COPY ckanext-dcat-ap-edp-mqa ${SRC_DIR}/ckanext-dcat-ap-edp-mqa
RUN pip3 install --no-cache-dir -e ${SRC_DIR}/ckanext-dcat-ap-edp-mqa \
    && pip3 install --no-cache-dir -r ${SRC_DIR}/ckanext-dcat-ap-edp-mqa/requirements.txt

# ---------------------------------------------------------------------
#  Patch a CKAN core (riattivare una per una dopo verifica su 2.12)
# ---------------------------------------------------------------------
# COPY patches/language_selector.html ${SRC_DIR}/ckan/ckan/templates/snippets/language_selector.html
# COPY patches/util.py                ${SRC_DIR}/ckan/ckan/views/util.py
# COPY patches/validators.py          ${SRC_DIR}/ckan/ckan/logic/validators.py
# COPY patches/__init__.py            ${SRC_DIR}/ckan/ckan/logic/__init__.py
# COPY patches/model_dictize.py       ${SRC_DIR}/ckan/ckan/lib/dictization/model_dictize.py
COPY patches/ckan_logo_col.png patches/sprite-resource-icons.png ${SRC_DIR}/ckan/ckan/public/base/images/

# Script di inizializzazione (eseguiti da start_ckan.sh a ogni avvio)
COPY docker-entrypoint.d/*.sh /docker-entrypoint.d/
RUN chmod 755 /docker-entrypoint.d/*.sh

# Script manuale per il setup iniziale dei gruppi tematici (vedi README)
COPY setup_groups.sh ${APP_DIR}/setup_groups.sh
RUN chmod +x ${APP_DIR}/setup_groups.sh

# CA bundle aggiornato (harvest verso host con catena Sectigo R46 ecc.)
RUN pip3 install --no-cache-dir -U certifi

# Permessi: tutto cio' che e' stato aggiunto deve essere leggibile da `ckan`
RUN chown -R ckan:ckan-sys ${SRC_DIR} ${APP_DIR}/setup_groups.sh

USER ckan
