#!/bin/bash
# Configurazione Xloader (+ OAI-PMH quando il plugin e' attivo).
# Eseguito a ogni avvio.

# ckan.ini vive nel container e si perde a ogni rebuild: il token xloader va
# (ri)creato quando manca dall'ini, indipendentemente dal marker di init.
# La configurazione OAI e' idempotente e viene riapplicata a ogni avvio.
if [[ $CKAN__PLUGINS == *"xloader"* ]] && grep -qE "^ckanext.xloader.api_token ?= ?\S" "$CKAN_INI"; then
  echo "[init] Xloader gia' configurato in ckan.ini."
elif [[ $CKAN__PLUGINS == *"xloader"* ]]; then
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
