#!/bin/bash
# =====================================================================
#  ENTRYPOINT dell'immagine CKAN (servizio web e worker).
#
#  Segreti applicativi: se nel .env SECRET_KEY, WTF_CSRF_SECRET_KEY e i
#  segreti JWT sono assenti, vuoti o lasciati a CHANGE_ME, vengono generati
#  una sola volta e salvati nel volume ckan_storage
#  (${CKAN_STORAGE_PATH}/.ckan-docker-ita.secrets), condiviso con i worker.
#  Cosi' restano stabili tra un riavvio e l'altro e i token API non si
#  invalidano a ogni ricreazione del container.
#  Se nel .env ci sono valori reali, questo script non tocca nulla.
#
#  I segreti vengono esportati per il processo avviato e scritti anche in
#  ckan.ini, cosi' funzionano pure i comandi lanciati con `docker compose exec`.
# =====================================================================
set -e

is_placeholder() {
  case "$1" in
    ""|CHANGE_ME|string:CHANGE_ME) return 0 ;;
    *) return 1 ;;
  esac
}

if is_placeholder "${CKAN___SECRET_KEY:-}" \
   || is_placeholder "${CKAN___WTF_CSRF_SECRET_KEY:-}" \
   || is_placeholder "${CKAN___API_TOKEN__JWT__ENCODE__SECRET:-}" \
   || is_placeholder "${CKAN___API_TOKEN__JWT__DECODE__SECRET:-}"; then

  SECRETS_FILE="${CKAN_STORAGE_PATH:-/var/lib/ckan}/.ckan-docker-ita.secrets"

  if [ ! -s "$SECRETS_FILE" ]; then
    echo "[entrypoint] Segreti non impostati nel .env: li genero in $SECRETS_FILE"
    umask 077
    JWT="string:$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
    {
      echo "GEN_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
      echo "GEN_WTF_CSRF_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')"
      echo "GEN_JWT_SECRET=${JWT}"
    } > "${SECRETS_FILE}.tmp"
    mv "${SECRETS_FILE}.tmp" "$SECRETS_FILE"
  fi

  # shellcheck disable=SC1090
  . "$SECRETS_FILE"

  is_placeholder "${CKAN___SECRET_KEY:-}" && export CKAN___SECRET_KEY="$GEN_SECRET_KEY"
  is_placeholder "${CKAN___WTF_CSRF_SECRET_KEY:-}" && export CKAN___WTF_CSRF_SECRET_KEY="$GEN_WTF_CSRF_SECRET_KEY"
  is_placeholder "${CKAN___API_TOKEN__JWT__ENCODE__SECRET:-}" && export CKAN___API_TOKEN__JWT__ENCODE__SECRET="$GEN_JWT_SECRET"
  is_placeholder "${CKAN___API_TOKEN__JWT__DECODE__SECRET:-}" && export CKAN___API_TOKEN__JWT__DECODE__SECRET="$GEN_JWT_SECRET"

  if [ -w "${CKAN_INI:-/srv/app/ckan.ini}" ]; then
    ckan config-tool "${CKAN_INI:-/srv/app/ckan.ini}" \
      "SECRET_KEY=${CKAN___SECRET_KEY}" \
      "WTF_CSRF_SECRET_KEY=${CKAN___WTF_CSRF_SECRET_KEY}" \
      "api_token.jwt.encode.secret=${CKAN___API_TOKEN__JWT__ENCODE__SECRET}" \
      "api_token.jwt.decode.secret=${CKAN___API_TOKEN__JWT__DECODE__SECRET}" >/dev/null \
      || echo "[entrypoint] ATTENZIONE: impossibile scrivere i segreti in ckan.ini"
  fi
fi

exec "$@"
