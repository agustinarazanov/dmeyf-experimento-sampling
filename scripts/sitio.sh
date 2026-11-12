#!/bin/bash
# Construye el sitio (Jekyll + Just the Docs) y verifica los enlaces internos con html-proofer.
# El mismo script corre local y en CI (.github/workflows/pages.yml).
#
# uso:  scripts/sitio.sh [serve] [--baseurl <ruta>]
# ej.:  scripts/sitio.sh                                   # build + verificación
#       scripts/sitio.sh --baseurl /dmeyf-experimento-sampling
#       scripts/sitio.sh serve                           # build + verificación + servidor local
set -euo pipefail
cd "$(dirname "$0")/.."

SERVE=0
BASEURL=""
while [ $# -gt 0 ]; do
  case "$1" in
    serve) SERVE=1; shift ;;
    --baseurl) BASEURL=${2:?falta el valor de --baseurl}; shift 2 ;;
    *) echo "argumento desconocido: $1" >&2; exit 2 ;;
  esac
done

BUILD=(bundle exec jekyll build)
PROOF=(bundle exec htmlproofer _site --disable-external --allow-missing-href
       --ignore-files "/originales/,/reporte_original/")
if [ -n "$BASEURL" ]; then
  BUILD+=(--baseurl "$BASEURL")
  PROOF+=(--swap-urls "^${BASEURL}:")
fi

"${BUILD[@]}"
"${PROOF[@]}"

if [ "$SERVE" = 1 ]; then
  exec bundle exec jekyll serve ${BASEURL:+--baseurl "$BASEURL"}
fi
