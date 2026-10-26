#!/bin/bash
# =====================================================================
#  Impostazioni idempotenti di ckan.ini, COMUNI a web e worker.
#
#  Le esegue ckan-ita-entrypoint.sh a ogni avvio di ogni container.
#  Prima stavano in docker-entrypoint.d/02_ckan-init.sh, che gira solo nel
#  servizio web (i worker hanno un proprio `command:` e saltano
#  start_ckan.sh): i worker restavano con il ckan.ini di base, e l'harvest
#  girava senza expose_subcatalogs (nessun extra source_catalog_*), senza
#  normalize_ckan_format e clean_tags, con locale_default=en.
#  Qui un'impostazione vale per tutti: aggiungerne di nuove in questo file.
# =====================================================================
INI="${CKAN_INI:-/srv/app/ckan.ini}"
if [ ! -w "$INI" ]; then
  echo "[settings] ATTENZIONE: $INI non scrivibile, impostazioni non applicate"
  exit 0
fi

ARGS=()
if [[ "${CKAN__PLUGINS:-}" == *"dcat"* ]]; then
  # Profili RDF: euro_dcat_ap_3 e' il profilo base DCAT-AP 3; it_dcat_ap lo estende.
  # SE NON SERVE OpenAIRE/MQA togliere dcat_ap_edp_mqa da CKANEXT__DCAT__RDF__PROFILES nel .env
  ARGS+=("ckanext.dcat.rdf.profiles=${CKANEXT__DCAT__RDF__PROFILES:-euro_dcat_ap_3}"
         "ckanext.dcat.base_uri=${CKAN_SITE_URL}"
         "ckanext.dcat.expose_subcatalogs=True"
         "ckanext.dcat.normalize_ckan_format=true"
         "ckanext.dcat.clean_tags=True"
         "ckanext.dcat.resource.inherit.license=True"
         "solr_timeout=500")
fi
ARGS+=("ckan.locale_default=${CKAN_LOCALE_DEFAULT:-it}"
       "ckan.locales_offered=it en"
       "ckan.auth.create_user_via_web=false"
       "ckan.auth.public_user_details=false"
       "ckan.uploads_enabled=True"
       "geonames.username=${GEONAMES_USERNAME:-demo}")

ckan config-tool "$INI" "${ARGS[@]}" >/dev/null \
  && echo "[settings] ckan.ini allineato: ${#ARGS[@]} impostazioni" \
  || echo "[settings] ATTENZIONE: config-tool fallito"
# log delle estensioni a INFO: il livello DEBUG di default (multilang, dcatapit)
# scrive centinaia di righe per pagina di catalogo
ckan config-tool "$INI" -s logger_ckanext "level = ${CKAN_LOG_LEVEL_EXTENSIONS:-INFO}" >/dev/null \
  || echo "[settings] ATTENZIONE: livello di log non impostato"
exit 0
