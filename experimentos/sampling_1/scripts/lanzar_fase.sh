#!/bin/bash
# Lanza una fase en su VM, en segundo plano, y vuelve enseguida. vm.sh bloquea hasta que la VM termina (horas) y
# recién entonces trae el ledger y borra la VM, por eso acá va con nohup y caffeinate (la Mac no debe dormirse).
#
# uso:  experimentos/conjunto/scripts/lanzar_fase.sh <1|2|3|4>
set -euo pipefail
cd "$(dirname "$0")/../../.."          # raíz del repo
[ -f .env ] && { set -a; . ./.env; set +a; }
N=${1:?uso: lanzar_fase.sh <1|2|3|4>}
EXP=experimentos/conjunto
LISTA="$EXP/scripts/fase$N.txt"
[ -f "$LISTA" ] || { echo "no existe $LISTA"; exit 1; }
LOG="$EXP/ledger/sesiones/vm_f$N.log"
mkdir -p "$EXP/ledger/sesiones"
if pgrep -f "vm.sh $LISTA" >/dev/null; then echo "la fase $N ya está corriendo (ver $LOG)"; exit 0; fi
export NOMBRE="sampling-f$N"
nohup caffeinate -i "$EXP/scripts/vm.sh" "$LISTA" > "$LOG" 2>&1 &
echo "fase $N lanzada en la VM $NOMBRE (pid $!); log: $LOG"
