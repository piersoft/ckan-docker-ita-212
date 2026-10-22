#!/usr/bin/env bash
# =====================================================================
#  Build e push su Docker Hub delle 4 immagini dello stack:
#    piersoft/ckan, piersoft/ckan-solr, piersoft/ckan-db, piersoft/ckan-nginx
#
#  Uso (dalla radice del repository, dopo `docker login`):
#     scripts/build-push.sh 1.0.0            # build + push
#     scripts/build-push.sh 1.0.0 --no-push  # solo build locale
#
#  Tag pubblicati per ogni immagine:
#     2.12-dcatapit-<versione>   (immutabile)
#     2.12                       (ultima 2.12)
#     latest
#  Architettura: linux/amd64 (l'immagine base ckan/ckan-base non e' multi-arch).
#  Variabili opzionali: HUB_NAMESPACE (default piersoft), CKAN_SERIES (default 2.12),
#  SOURCE_URL (repository dei sorgenti, finisce nella label OCI dell'immagine).
# =====================================================================
set -euo pipefail

VERSION="${1:-}"
PUSH=true
[ "${2:-}" = "--no-push" ] && PUSH=false

if [ -z "$VERSION" ]; then
  echo "Uso: $0 <versione> [--no-push]   es. $0 1.0.0" >&2
  exit 1
fi

NS="${HUB_NAMESPACE:-piersoft}"
SERIES="${CKAN_SERIES:-2.12}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REVISION="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
CREATED="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
SOURCE="${SOURCE_URL:-https://github.com/piersoft/ckan-docker-ita-212}"

# nome-immagine:contesto
IMAGES=(
  "ckan:ckan"
  "ckan-solr:solr"
  "ckan-db:postgresql"
  "ckan-nginx:nginx"
)

for entry in "${IMAGES[@]}"; do
  name="${entry%%:*}"
  ctx="${entry#*:}"
  repo="${NS}/${name}"
  echo ""
  echo "=== ${repo}  (contesto: ${ctx}/)"
  docker build --platform linux/amd64 \
    --build-arg TZ=Europe/Rome \
    --label org.opencontainers.image.title="${name}" \
    --label org.opencontainers.image.version="${SERIES}-dcatapit-${VERSION}" \
    --label org.opencontainers.image.revision="${REVISION}" \
    --label org.opencontainers.image.created="${CREATED}" \
    --label org.opencontainers.image.source="${SOURCE}" \
    --label org.opencontainers.image.licenses="AGPL-3.0-or-later" \
    -t "${repo}:${SERIES}-dcatapit-${VERSION}" \
    -t "${repo}:${SERIES}" \
    -t "${repo}:latest" \
    "${ROOT}/${ctx}"
done

if $PUSH; then
  for entry in "${IMAGES[@]}"; do
    repo="${NS}/${entry%%:*}"
    for tag in "${SERIES}-dcatapit-${VERSION}" "${SERIES}" latest; do
      docker push "${repo}:${tag}"
    done
  done
  echo ""
  echo "Push completato: ${NS}/{ckan,ckan-solr,ckan-db,ckan-nginx}:${SERIES}-dcatapit-${VERSION}"
else
  echo ""
  echo "Build completata (senza push)."
fi
