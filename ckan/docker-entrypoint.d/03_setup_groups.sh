#!/bin/bash
# Setup automatico dei gruppi tematici DCAT-AP_IT (una sola volta).
# Attivo solo con CKAN_SETUP_GROUPS=true nel .env (default: spento, resta
# disponibile il comando manuale `docker compose exec ckan bash /srv/app/setup_groups.sh`).
#
# I gruppi si creano via API, quindi serve il web server avviato: lo script
# parte in background, aspetta che /api/3/action/status_show risponda e poi
# lancia setup_groups.sh. Il marker sta nel volume ckan_storage, cosi' a ogni
# riavvio o rebuild non viene rieseguito.

GROUPS_MARKER="${CKAN_STORAGE_PATH:-/var/lib/ckan}/.ckan-docker-ita.groups-done"

if [[ "${CKAN_SETUP_GROUPS:-false}" == "true" ]] && [ ! -f "$GROUPS_MARKER" ]; then
  echo "[init] Gruppi tematici: setup automatico in background dopo l'avvio del web server"
  (
    for _ in $(seq 1 120); do
      if curl -fsS -o /dev/null http://localhost:5000/api/3/action/status_show; then
        if bash "${APP_DIR:-/srv/app}/setup_groups.sh"; then
          touch "$GROUPS_MARKER"
          echo "[init] Gruppi tematici creati"
        else
          echo "[init] ATTENZIONE: setup dei gruppi fallito, riprovera' al prossimo avvio"
        fi
        exit 0
      fi
      sleep 5
    done
    echo "[init] ATTENZIONE: web server non pronto dopo 10 minuti, setup dei gruppi saltato"
  ) &
fi
