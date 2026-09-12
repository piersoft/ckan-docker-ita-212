#!/bin/bash
# Configurazione Xloader + OAI-PMH server.
# Eseguito a ogni avvio; le parti pesanti sono protette dal marker "finito".

if grep -q "finito" "$CKAN_INI"; then
  echo "Xloader/OAI gia' configurati, salto."
else
  echo "Set up ckanext.xloader.api_token nel file di configurazione CKAN"
  ckan config-tool "$CKAN_INI" "ckanext.xloader.api_token=$(ckan -c "$CKAN_INI" user token add "${CKAN_SYSADMIN_NAME:-ckan_admin}" xloader | tail -n 1 | tr -d '\t')"
  ckan config-tool "$CKAN_INI" "ckanext.xloader.jobs_db.uri=${CKAN_SQLALCHEMY_URL}"
  ckan config-tool "$CKAN_INI" "ckan.datastore.write_url=${CKAN_DATASTORE_WRITE_URL}"
  ckan config-tool "$CKAN_INI" "ckan.datastore.read_url=${CKAN_DATASTORE_READ_URL}"
  ckan config-tool "$CKAN_INI" "ckanext.xloader.site_url=http://ckan:5000"

  # URL base dell'OAI-PMH: usa CKAN_OAIPMH_BASE_URL se valorizzato,
  # altrimenti lo deriva da CKAN_SITE_URL (niente domini hardcoded).
  OAIPMH_BASE_URL="${CKAN_OAIPMH_BASE_URL:-${CKAN_SITE_URL}/oai}"
  ckan config-tool "$CKAN_INI" "ckan.oaipmh.base_url=${OAIPMH_BASE_URL}"
  ckan config-tool "$CKAN_INI" "ckan.oaipmh.sets=dataset_authority, custom_tag_set"
  ckan config-tool "$CKAN_INI" "ckan.oaipmh.metadata_formats=oai_dc"
  ckan config-tool "$CKAN_INI" "ckan.oaipmh.dc_element_map=title,description,keyword,publisher,identifier"
  ckan config-tool "$CKAN_INI" "ckanext.dcat.resource.inherit.license=True"
  ckan config-tool "$CKAN_INI" "ckanext.oai_pmh_server.resumption_token_batch_size=100"
fi
