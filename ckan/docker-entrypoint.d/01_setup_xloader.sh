#!/bin/bash
# Configurazione Xloader (+ OAI-PMH quando il plugin e' attivo).
# Eseguito a ogni avvio; le parti "una tantum" sono protette dal marker
# $INIT_MARKER (file nel volume ckan_storage, sopravvive alla ricreazione del container).
INIT_MARKER="${CKAN_STORAGE_PATH:-/var/lib/ckan}/.ckan-docker-ita.init-done"

if [ -f "$INIT_MARKER" ]; then
  echo "[init] Xloader/OAI gia' configurati, salto."
  exit 0
fi

if [[ $CKAN__PLUGINS == *"xloader"* ]]; then
  echo "[init] Configuro ckanext.xloader"
  ckan config-tool "$CKAN_INI" "ckanext.xloader.api_token=$(ckan -c "$CKAN_INI" user token add "${CKAN_SYSADMIN_NAME:-ckan_admin}" xloader | tail -n 1 | tr -d '\t')"
  ckan config-tool "$CKAN_INI" "ckanext.xloader.jobs_db.uri=${CKAN_SQLALCHEMY_URL}"
  ckan config-tool "$CKAN_INI" "ckan.datastore.write_url=${CKAN_DATASTORE_WRITE_URL}"
  ckan config-tool "$CKAN_INI" "ckan.datastore.read_url=${CKAN_DATASTORE_READ_URL}"
  ckan config-tool "$CKAN_INI" "ckanext.xloader.site_url=http://ckan:5000"
fi

if [[ $CKAN__PLUGINS == *"oai_pmh_server"* ]]; then
  echo "[init] Configuro ckanext-oai-pmh-server"
  # URL base dell'OAI-PMH: CKAN_OAIPMH_BASE_URL se valorizzato, altrimenti ${CKAN_SITE_URL}/oai
  OAIPMH_BASE_URL="${CKAN_OAIPMH_BASE_URL:-${CKAN_SITE_URL}/oai}"
  ckan config-tool "$CKAN_INI" "ckan.oaipmh.base_url=${OAIPMH_BASE_URL}"
  ckan config-tool "$CKAN_INI" "ckan.oaipmh.sets=dataset_authority, custom_tag_set"
  ckan config-tool "$CKAN_INI" "ckan.oaipmh.metadata_formats=oai_dc"
  ckan config-tool "$CKAN_INI" "ckan.oaipmh.dc_element_map=title,description,keyword,publisher,identifier"
  ckan config-tool "$CKAN_INI" "ckanext.oai_pmh_server.resumption_token_batch_size=100"
fi
