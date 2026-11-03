#!/bin/bash
# Recorre las etapas pendientes de tasks.md una tras otra, con el modelo que indica el encabezado de cada grupo,
# hasta que no quede ninguna, hasta el primer BLOQUEADO, o hasta una vuelta que no cierre ninguna tarea del grupo.
#
# uso:  scripts/etapas.sh [experimento] [cambio]
set -euo pipefail
cd "$(dirname "$0")/.."
EXP=${1:-sampling_1}
CAMBIO=${2:-separar-hipotesis}
TAREAS="openspec/changes/$CAMBIO/tasks.md"
[ -f "$TAREAS" ] || { echo "no existe $TAREAS"; exit 1; }

pendientes_de() { grep -c -E "^- \[ \] $1\." "$TAREAS" || true; }

while :; do
    GRUPO=$(grep -m1 -E '^- \[ \] [0-9]+\.' "$TAREAS" | sed -E 's/^- \[ \] ([0-9]+)\..*/\1/' || true)
    if [ -z "$GRUPO" ]; then echo "== no quedan tareas pendientes"; exit 0; fi
    ENCABEZADO=$(grep -m1 -E "^## $GRUPO\. " "$TAREAS" || echo "## $GRUPO.")
    case "$ENCABEZADO" in
        *"sesión: Opus"*)   MODELO=opus ;;
        *"sesión: Sonnet"*) MODELO=sonnet ;;
        *)        MODELO=sonnet ;;
    esac
    ANTES=$(pendientes_de "$GRUPO")
    echo "== etapa $GRUPO ($ANTES pendientes) con $MODELO · $ENCABEZADO"
    RC=0; scripts/etapa.sh "$GRUPO" "$MODELO" "$EXP" "$CAMBIO" || RC=$?
    if [ "$RC" -eq 4 ]; then
        echo "== $(date +%H:%M) esperando a que terminen las VMs (vm.sh locales) · se revisa cada 5 min"
        sleep 120
        while pgrep -f "scripts/vm.sh" >/dev/null; do sleep 300; done
        echo "== $(date +%H:%M) no queda ningún vm.sh corriendo; vuelvo al grupo $GRUPO"
        rm -f "experimentos/$EXP/ledger/sesiones/en_curso.txt"
        continue
    fi
    if [ "$RC" -ne 0 ]; then echo "== detenido en el grupo $GRUPO (código $RC)"; exit "$RC"; fi
    AHORA=$(pendientes_de "$GRUPO")
    if [ "$AHORA" -ge "$ANTES" ]; then
        echo "== la vuelta no cerró ninguna tarea del grupo $GRUPO ($AHORA pendientes); me detengo"; exit 3
    fi
done
