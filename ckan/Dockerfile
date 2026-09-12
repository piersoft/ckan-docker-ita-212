# =====================================================================
#  CKAN Docker per l'Italia — immagine CKAN 2.12
#  Base ufficiale: python 3.14 slim, utente non-root `ckan` (uid 503).
#  Le estensioni vengono abilitate una fase alla volta (vedi CHANGELOG):
#    FASE 1  core + xloader                         <- QUESTA
#    FASE 2  ckanext-harvest (senza pylons)
#    FASE 3  ckanext-dcat 2.4.x (DCAT-AP 3) + patch
#    FASE 4  ckanext-dcatapit su 2.12 / DCAT-AP 3
#    FASE 5  ckanext-multilang, oai-pmh-server, dcat-ap-edp-mqa
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
RUN pip3 install --no-cache-dir ckanext-xloader==2.5.0

# ---------------------------------------------------------------------
#  FASE 2 — Harvest  (disattivato: da portare su 2.12 senza pylons)
# ---------------------------------------------------------------------
# COPY patches/ckanext-harvest ${SRC_DIR}/ckanext-harvest
# RUN pip3 install --no-cache-dir -e ${SRC_DIR}/ckanext-harvest \
#     && pip3 install --no-cache-dir -r ${SRC_DIR}/ckanext-harvest/requirements.txt

# ---------------------------------------------------------------------
#  FASE 3 — ckanext-dcat 2.4.x  (disattivato)
# ---------------------------------------------------------------------
# RUN pip3 install --no-cache-dir ckanext-dcat==2.4.4

# ---------------------------------------------------------------------
#  FASE 4 — ckanext-dcatapit  (disattivato)
# ---------------------------------------------------------------------
# COPY patches/ckanext-dcatapit ${SRC_DIR}/ckanext-dcatapit
# RUN pip3 install --no-cache-dir -e ${SRC_DIR}/ckanext-dcatapit
# COPY patches/theme_to_group.ini patches/topics.json patches/regions.rdf ${APP_DIR}/patches/
# COPY patches/groups ${APP_DIR}/patches/groups

# ---------------------------------------------------------------------
#  FASE 5 — multilang, oai-pmh-server, dcat-ap-edp-mqa  (disattivato)
# ---------------------------------------------------------------------

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
