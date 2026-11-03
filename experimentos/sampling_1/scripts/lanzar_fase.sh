#!/bin/bash
# Atajo: el lanzador pasó a scripts/lanzar_fase.sh en la raíz (cambio separar-hipotesis, D7). Se deja este nombre para
# que las instrucciones y permisos que apuntan acá sigan andando.
exec "$(dirname "$0")/../../../scripts/lanzar_fase.sh" "$@"
