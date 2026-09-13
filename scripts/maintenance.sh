#!/bin/bash
# Manutenzione periodica dello stack (da cron sull'host). Uso:
#   scripts/maintenance.sh harvest-run     ogni 15 min: avvia i job harvest schedulati e chiude quelli finiti
#   scripts/maintenance.sh daily           ogni notte: log harvest, job in limbo, log xloader, immagini dangling
#   scripts/maintenance.sh weekly          ogni domenica: build cache Docker, container fermi
#   scripts/maintenance.sh xloader-all     (facoltativo) risottomette TUTTE le risorse al DataStore
# Log: /var/log/ckan212-maintenance.log (ruotato da logrotate, vedi scripts/logrotate.conf)
set -u
cd "$(dirname "$0")/.." || exit 1
LOG=/var/log/ckan212-maintenance.log
ts() { date '+%F %T'; }
run() { echo "$(ts) [$1] $*" >> "$LOG"; }
ckan() { docker compose exec -T ckan ckan "$@"; }

case "${1:-}" in
  harvest-run)
    ckan harvester run >> "$LOG" 2>&1
    ;;
  daily)
    run daily "--- inizio"
    ckan harvester abort-failed-jobs --life-span 24 >> "$LOG" 2>&1   # job harvest in limbo da >24h
    ckan harvester clean-harvest-log >> "$LOG" 2>&1                  # log harvest piu' vecchi di ckan.harvest.log_timeframe (default 10 gg)
    # log e job di xloader piu' vecchi di 30 giorni (tabelle jobs_db in ckandb)
    docker compose exec -T db psql -U postgres -d ckandb -qAtc \
      "delete from logs where job_id in (select job_id from jobs where finished < now() - interval '30 days');
       delete from metadata where job_id in (select job_id from jobs where finished < now() - interval '30 days');
       delete from jobs where finished < now() - interval '30 days';" >> "$LOG" 2>&1
    docker image prune -f >> "$LOG" 2>&1                              # immagini dangling dei rebuild
    run daily "--- fine"
    ;;
  weekly)
    run weekly "--- inizio"
    docker builder prune -af --filter "until=168h" >> "$LOG" 2>&1     # build cache piu' vecchia di 7 giorni
    docker container prune -f >> "$LOG" 2>&1                          # container fermi (non i volumi!)
    docker system df >> "$LOG" 2>&1
    run weekly "--- fine"
    ;;
  xloader-all)
    run xloader "submit di tutte le risorse al DataStore"
    ckan xloader submit all >> "$LOG" 2>&1
    ;;
  *)
    echo "uso: $0 {harvest-run|daily|weekly|xloader-all}" >&2; exit 2
    ;;
esac
