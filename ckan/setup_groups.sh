#!/usr/bin/env bash
# =====================================================================
#  Setup iniziale dei GRUPPI tematici (DCAT-AP_IT) del catalogo.
#
#  DA ESEGUIRE UNA VOLTA, dopo il primo `docker compose up -d`, quando
#  il container CKAN risulta "healthy" (web server attivo su :5000).
#  Comando consigliato (dall'host):
#     docker compose exec ckan bash /srv/app/setup_groups.sh
#
#  E' idempotente: i gruppi gia' esistenti vengono semplicemente saltati.
#  Al termine scrive i marker "finito"/"finitigruppi" in ckan.ini cosi'
#  i riavvii successivi non rieseguono l'init pesante (vocabolari, ecc.).
# =====================================================================
set -euo pipefail

CKAN_INI="${CKAN_INI:-/srv/app/ckan.ini}"
APP_DIR="${APP_DIR:-/srv/app}"
SYSADMIN="${CKAN_SYSADMIN_NAME:-ckan_admin}"
API_BASE="http://localhost:5000/api/3/action"

echo ">> Configurazione mapping tema->gruppo e multilang"
ckan config-tool "$CKAN_INI" "ckanext.dcatapit.theme_group_mapping.file=${APP_DIR}/patches/theme_to_group.ini"
ckan config-tool "$CKAN_INI" "ckanext.dcatapit.nonconformant_themes_mapping.file=${APP_DIR}/patches/topics.json"
ckan config-tool "$CKAN_INI" "ckanext.dcatapit.theme_group_mapping.add_new_groups=true"
ckan config-tool "$CKAN_INI" "geonames.username=${GEONAMES_USERNAME:-demo}"
ckan config-tool "$CKAN_INI" "ckanext.multilang.localized_resources=true"

echo ">> Creazione token API per l'utente ${SYSADMIN}"
APITOKEN="$(ckan -c "$CKAN_INI" user token add "$SYSADMIN" gruppi | tail -n 1 | tr -d '\t')"
if [ -z "$APITOKEN" ]; then
  echo "ERRORE: impossibile creare il token API per ${SYSADMIN}." >&2
  exit 1
fi

echo ">> Creazione gruppi tematici"
for file in "${APP_DIR}/patches/groups/"*.json; do
  name="$(basename "$file" .json)"
  code="$(curl -s -o /tmp/group_resp.json -w '%{http_code}' \
            -H "Authorization: ${APITOKEN}" \
            -H "Content-Type: application/json" \
            -X POST -d @"$file" "${API_BASE}/group_create" || true)"
  case "$code" in
    200) echo "   [creato]  ${name}" ;;
    409) echo "   [esiste]  ${name} (saltato)" ;;
    *)   echo "   [WARN ${code}] ${name} -> $(cat /tmp/group_resp.json)" ;;
  esac
done

echo ">> Scrittura marker di completamento"
ckan config-tool "$CKAN_INI" 'ckan.build_groups=finitigruppi'
ckan config-tool "$CKAN_INI" 'ckan.build=finito'

echo ""
echo "Setup gruppi completato. Riavviare CKAN per applicare:"
echo "   docker compose restart ckan"
