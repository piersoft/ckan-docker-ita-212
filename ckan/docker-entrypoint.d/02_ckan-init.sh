#!/bin/bash
# Inizializzazione una tantum del DB delle estensioni e caricamento dei
# vocabolari DCAT-AP_IT, piu' impostazioni ckan.ini idempotenti.
# Ogni blocco e' condizionato al plugin effettivamente presente in CKAN__PLUGINS,
# cosi' lo script resta valido in tutte le fasi della migrazione.
# Il marker sta nel volume ckan_storage: ckan.ini vive nel container e si perde
# a ogni rebuild, e ricaricare i vocabolari dcatapit produce IntegrityError.
INIT_MARKER="${CKAN_STORAGE_PATH:-/var/lib/ckan}/.ckan-docker-ita.init-done"

# Controllo sul DB (indipendente da marker e rebuild): true se la tabella esiste ed ha righe
table_has_rows() {
  python3 - "$1" <<'PY'
import os, sys, psycopg2
t = sys.argv[1]
try:
    c = psycopg2.connect(os.environ["CKAN_SQLALCHEMY_URL"])
    cur = c.cursor()
    cur.execute("select to_regclass(%s)", (t,))
    if cur.fetchone()[0] is None:
        sys.exit(1)
    cur.execute(f'select 1 from "{t}" limit 1')
    sys.exit(0 if cur.fetchone() else 1)
except Exception:
    sys.exit(1)
PY
}

if [ -f "$INIT_MARKER" ]; then
  echo "[init] Init estensioni gia' eseguita, salto."
else
  # prerun.py ha gia' fatto `ckan db upgrade` (core + migrazioni dei plugin).

  if [[ $CKAN__PLUGINS == *"harvest"* ]]; then
    ckan db upgrade -p harvest
  fi

  if [[ $CKAN__PLUGINS == *"multilang"* ]] && ! table_has_rows package_multilang; then
    ckan multilang initdb || true
  fi

  if [[ $CKAN__PLUGINS == *"dcatapit_pkg"* ]] && table_has_rows dcatapit_vocabulary; then
    echo "[init] Vocabolari DCAT-AP_IT gia' presenti nel DB, salto initdb/load."
  elif [[ $CKAN__PLUGINS == *"dcatapit_pkg"* ]]; then
    VOC="${SRC_DIR}/ckanext-dcatapit/vocabularies"
    ckan dcatapit initdb
    for v in languages-filtered data-theme-filtered places-filtered frequencies-filtered filetypes-filtered; do
      ckan dcatapit load --filename="${VOC}/${v}.rdf"
    done
    ckan dcatapit load --filename "${VOC}/theme-subtheme-mapping.rdf" --eurovoc "${VOC}/eurovoc-filtered.rdf"
    ckan dcatapit load --filename "${VOC}/licences.rdf"
    ckan dcatapit load --filename "${APP_DIR}/patches/regions.rdf" --name regions
  fi

  ckan config-tool "$CKAN_INI" "ckan.build = finito"
  touch "$INIT_MARKER"
  echo -e "\n[init] Init estensioni completata"
fi

# --- impostazioni idempotenti ---
# Spostate in /srv/app/ckan-ita-settings.sh, eseguito dall'entrypoint a ogni
# avvio di OGNI container (web e worker): qui giravano solo nel web e i
# worker restavano con il ckan.ini di base.
