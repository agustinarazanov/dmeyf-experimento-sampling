#!/bin/bash
# Lanza una o varias listas de configuraciones, cada una en su VM, en segundo plano, y vuelve enseguida. vm.sh bloquea
# hasta que la VM termina (horas) y recién entonces trae los ledgers y borra la VM, por eso acá va con nohup y caffeinate
# (la Mac no debe dormirse).
#
# uso:  scripts/lanzar_fase.sh [--en-seco] <lista>...
#   <lista>  un número N (`faseN.txt`), un nombre (`fase5_r3`) o una ruta a un .txt
# ej.:  scripts/lanzar_fase.sh 1
#       scripts/lanzar_fase.sh fase5_r1 fase5_r2 fase5_r3 fase5_r4 fase5_r5 fase5_r6 fase5_r7 fase5_r0
#
# Las listas están en experimentos/sampling_1/scripts/ (o en la carpeta de EXP, si se define); el log de cada VM va a
# <EXP>/ledger/sesiones/vm_<lista>.log. Antes de lanzar más de una VM se verifica la cuota de vCPU N2 de la región:
# hacen falta 8 vCPU libres por VM; si no alcanzan no se lanza ninguna (se lanzan en tandas). `--en-seco` no llama a
# gcloud ni lanza nada: por cada lista imprime la VM, las corridas y los destinos de los ledgers.
set -euo pipefail
cd "$(dirname "$0")/.."                # raíz del repo
[ -f .env ] && { set -a; . ./.env; set +a; }
EN_SECO=""; LISTAS=()
for arg in "$@"; do
  if [ "$arg" = "--en-seco" ]; then EN_SECO=1; else LISTAS+=("$arg"); fi
done
[ ${#LISTAS[@]} -gt 0 ] || { echo "uso: lanzar_fase.sh [--en-seco] <lista>..."; exit 1; }
EXP=${EXP:-experimentos/sampling_1}
ZONA=${ZONA:-northamerica-northeast2-b}
REGION=${ZONA%-*}
VCPU_POR_VM=8

# Resuelve cada argumento a (ruta, nombre corto).
RUTAS=(); NOMBRES=()
for l in "${LISTAS[@]}"; do
  if [[ "$l" =~ ^[0-9]+$ ]]; then ruta="$EXP/scripts/fase$l.txt"; corto="f$l"
  elif [ -f "$l" ]; then ruta="$l"; corto=$(basename "$l" .txt)
  else ruta="$EXP/scripts/$l.txt"; corto="$l"; fi
  [ -f "$ruta" ] || { echo "no existe $ruta"; exit 1; }
  corto=${corto#fase}; [[ "$corto" =~ ^[0-9] ]] && corto="f$corto"
  RUTAS+=("$ruta"); NOMBRES+=("$corto")
done
nombre_vm() { echo "sampling-$1" | tr '_A-Z' '-a-z'; }   # nombres de GCE: minúsculas, dígitos y guiones

if [ -n "$EN_SECO" ]; then
  echo "== en seco: sin gcloud ni VMs. Cuota N2 que se verificaría: ${#RUTAS[@]} VMs x $VCPU_POR_VM = $(( ${#RUTAS[@]} * VCPU_POR_VM )) vCPU en $REGION"
  for i in "${!RUTAS[@]}"; do
    echo "== lista ${RUTAS[$i]} -> VM $(nombre_vm "${NOMBRES[$i]}"), log $EXP/ledger/sesiones/vm_${NOMBRES[$i]}.log"
    NOMBRE=$(nombre_vm "${NOMBRES[$i]}") scripts/vm.sh "${RUTAS[$i]}" --en-seco | sed -n '/^corridas/,/^otros destinos/p'
  done
  exit 0
fi

# Cuota de vCPU N2 de la región: límite menos uso, contra lo que piden las VMs que se van a lanzar.
: "${PROYECTO:?falta PROYECTO}"
NECESARIAS=$(( ${#RUTAS[@]} * VCPU_POR_VM ))
LIBRES=$(gcloud compute regions describe "$REGION" --project "$PROYECTO" --format=json | python3 -c '
import json, sys
q = {c["metric"]: c for c in json.load(sys.stdin)["quotas"]}["N2_CPUS"]
print(int(q["limit"] - q["usage"]))')
echo "cuota N2_CPUS en $REGION: $LIBRES vCPU libres, hacen falta $NECESARIAS (${#RUTAS[@]} VMs)"
[ "$LIBRES" -ge "$NECESARIAS" ] || { echo "cuota insuficiente: lanzar en tandas"; exit 1; }

for i in "${!RUTAS[@]}"; do
  ruta=${RUTAS[$i]}; corto=${NOMBRES[$i]}
  LOG="$EXP/ledger/sesiones/vm_$corto.log"
  mkdir -p "$EXP/ledger/sesiones"
  if pgrep -f "vm.sh $ruta" >/dev/null; then echo "$ruta ya está corriendo (ver $LOG)"; continue; fi
  NOMBRE=$(nombre_vm "$corto") nohup caffeinate -i scripts/vm.sh "$ruta" > "$LOG" 2>&1 &
  echo "$ruta lanzada en la VM $(nombre_vm "$corto") (pid $!); log: $LOG"
done
