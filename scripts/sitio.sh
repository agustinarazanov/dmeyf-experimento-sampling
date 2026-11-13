#!/bin/bash
# Construye el sitio (MkDocs Material) y verifica enlaces internos y redacción impersonal.
# El mismo script corre local y en CI (.github/workflows/pages.yml).
#
# uso:  scripts/sitio.sh [serve]
# ej.:  scripts/sitio.sh          # búsqueda de nombres + build --strict (falla con un enlace roto o a un archivo no publicado)
#       scripts/sitio.sh serve    # lo mismo y después el servidor local en http://127.0.0.1:8000
set -euo pipefail
cd "$(dirname "$0")/.."

SERVE=0
while [ $# -gt 0 ]; do
  case "$1" in
    serve) SERVE=1; shift ;;
    *) echo "argumento desconocido: $1" >&2; exit 2 ;;
  esac
done

# Avisos de MkDocs 2 / Material que no cambian el build.
export DISABLE_MKDOCS_2_WARNING=true NO_MKDOCS_2_WARNING=1

python scripts/nombres_sitio.py
mkdocs build --strict

if [ "$SERVE" = 1 ]; then
  exec mkdocs serve --strict
fi
