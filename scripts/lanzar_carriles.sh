#!/bin/bash
# Reparte las listas de la fase 8 en carriles y lanza las de cada carril una tras otra, cada una en su VM (cambio
# `tiempos-confiables-y-consistencia`, D15). Los carriles corren en paralelo y vuelve enseguida: cada carril es un proceso en
# segundo plano (nohup + caffeinate) que llama a scripts/vm.sh por cada lista, espera a que la VM termine, trae los ledgers,
# borra la VM y sigue con la siguiente. Una corrida a la vez por VM; el paralelismo es entre VMs.
#
# uso:  scripts/lanzar_carriles.sh [--en-seco] [--carril "lista lista ..."]...
#   sin --carril: el reparto de `experimentos/sampling_1/docs/diseno.md` § Reparto y fases (4 carriles, 17 listas).
#   --en-seco: sin gcloud ni VMs; imprime los carriles, la VM y el log de cada lista y cuántas corridas lleva.
#
# Antes de lanzar se verifica que no hay ninguna VM encendida en el proyecto y que la cuota (`CPUS_ALL_REGIONS` y `N2_CPUS`)
# alcanza para un VM de 8 vCPU por carril: con 4 carriles son los 32 vCPU del límite, así que cualquier otra VM encendida
# impide el lanzamiento. Toda la fase va con un solo commit: el de HEAD al lanzar. Si HEAD cambia entre dos listas de un
# carril, ese carril se detiene (el id de cada corrida lleva el commit y no se mezclan commits dentro de una variante);
# se anota en la bitácora y las listas que faltan se relanzan con el commit nuevo. Los logs van a
# experimentos/sampling_1/ledger/sesiones/carril_<n>.log y vm_<lista>.log.
set -euo pipefail
cd "$(dirname "$0")/.."                # raíz del repo
[ -f .env ] && { set -a; . ./.env; set +a; }
EXP=${EXP:-experimentos/sampling_1}
ZONA=${ZONA:-northamerica-northeast2-b}
REGION=${ZONA%-*}
VCPU_POR_VM=8
EN_SECO=""; CARRILES=()
while [ $# -gt 0 ]; do
  case "$1" in
    --en-seco) EN_SECO=1; shift;;
    --carril) CARRILES+=("${2:?--carril necesita una lista de listas entre comillas}"); shift 2;;
    *) echo "uso: lanzar_carriles.sh [--en-seco] [--carril \"lista lista ...\"]..."; exit 1;;
  esac
done
if [ ${#CARRILES[@]} -eq 0 ]; then   # el reparto propuesto: primero la medición y las `_a`, al final las `_b`
  CARRILES=(
    "fase8_medicion fase8_r0_a fase8_r1_a fase8_r0_b fase8_r1_b"
    "fase8_r2_a fase8_r3_a fase8_r2_b fase8_r3_b"
    "fase8_r4_a fase8_r5_a fase8_r4_b fase8_r5_b"
    "fase8_r6_a fase8_r7_a fase8_r6_b fase8_r7_b"
  )
fi
nombre_corto() { local c=${1#fase}; [[ "$c" =~ ^[0-9] ]] && c="f$c"; echo "$c"; }   # fase8_r0_a -> f8_r0_a (como lanzar_fase.sh)
nombre_vm() { echo "sampling-$(nombre_corto "$1")" | tr '_A-Z' '-a-z'; }
ruta_lista() { local l=$1; [ -f "$l" ] && { echo "$l"; return; }; echo "$EXP/scripts/$l.txt"; }

# Todas las listas existen y ninguna está repetida entre carriles.
TODAS=()
for c in "${CARRILES[@]}"; do
  for l in $c; do
    [ -f "$(ruta_lista "$l")" ] || { echo "no existe $(ruta_lista "$l")"; exit 1; }
    for otra in ${TODAS[@]+"${TODAS[@]}"}; do [ "$otra" = "$l" ] && { echo "la lista $l está en dos carriles"; exit 1; }; done
    TODAS+=("$l")
  done
done
COMMIT=$(git rev-parse --short HEAD)
NECESARIAS=$(( ${#CARRILES[@]} * VCPU_POR_VM ))

if [ -n "$EN_SECO" ]; then
  echo "== en seco: sin gcloud ni VMs. ${#CARRILES[@]} carriles, ${#TODAS[@]} listas, commit $COMMIT"
  echo "== cuota que se verificaría: $NECESARIAS vCPU libres (CPUS_ALL_REGIONS y N2_CPUS en $REGION) y ninguna VM encendida"
  n=0
  for c in "${CARRILES[@]}"; do
    n=$((n + 1)); echo "== carril $n (log $EXP/ledger/sesiones/carril_$n.log), una lista tras otra:"
    for l in $c; do
      r=$(ruta_lista "$l")
      est=$(grep -vc '^[[:space:]]*\(#\|$\)' "$r" || true)
      opt=$(grep -v '^#' "$r" | grep -c ' optimizar ' || true); fin=$(grep -v '^#' "$r" | grep -c ' final ' || true)
      mod=$(grep -c '^@ ' "$r" || true)
      echo "   $l -> VM $(nombre_vm "$l"), log $EXP/ledger/sesiones/vm_$(nombre_corto "$l").log: $est líneas ($opt estudios, $fin finales, $mod módulos)"
    done
  done
  echo "== el comando de cada lista es: scripts/vm.sh <lista> (con NOMBRE=<VM>); el commit de la fase es $COMMIT"
  exit 0
fi

: "${PROYECTO:?falta PROYECTO}"
VIVAS=$(gcloud compute instances list --project "$PROYECTO" --format='value(name,status)')
[ -z "$VIVAS" ] || { echo "hay VMs encendidas en el proyecto, no se lanza nada:"; echo "$VIVAS"; exit 1; }
libres() { python3 -c '
import json, sys
q = {c["metric"]: c for c in json.load(sys.stdin)["quotas"]}.get(sys.argv[1])
print(int(q["limit"] - q["usage"]) if q else 999999)' "$1"; }
LIBRES=$(gcloud compute regions describe "$REGION" --project "$PROYECTO" --format=json | libres N2_CPUS)
LIBRES_GLOBAL=$(gcloud compute project-info describe --project "$PROYECTO" --format=json | libres CPUS_ALL_REGIONS)
echo "cuota N2_CPUS en $REGION: $LIBRES vCPU libres; CPUS_ALL_REGIONS: $LIBRES_GLOBAL libres; hacen falta $NECESARIAS (${#CARRILES[@]} carriles)"
[ "$LIBRES" -ge "$NECESARIAS" ] && [ "$LIBRES_GLOBAL" -ge "$NECESARIAS" ] || { echo "cuota insuficiente: menos carriles"; exit 1; }

PRIORIDAD=""; command -v taskpolicy >/dev/null && PRIORIDAD="taskpolicy -t 0 -l 0"
mkdir -p "$EXP/ledger/sesiones"
# Un carril: las listas una tras otra, con el mismo commit. Corre en segundo plano.
correr_carril() {
  local n=$1; shift
  for l in "$@"; do
    if [ "$(git rev-parse --short HEAD)" != "$COMMIT" ]; then
      echo "$(date '+%F %T') carril $n: HEAD cambió ($COMMIT -> $(git rev-parse --short HEAD)); se detiene antes de $l"; return 1
    fi
    echo "$(date '+%F %T') carril $n: empieza $l en la VM $(nombre_vm "$l")"
    if NOMBRE=$(nombre_vm "$l") scripts/vm.sh "$(ruta_lista "$l")" > "$EXP/ledger/sesiones/vm_$(nombre_corto "$l").log" 2>&1; then
      echo "$(date '+%F %T') carril $n: terminó $l"
    else
      echo "$(date '+%F %T') carril $n: FALLÓ $l (ver vm_$(nombre_corto "$l").log); sigue con la siguiente"
    fi
  done
  echo "$(date '+%F %T') carril $n: terminado"
}
n=0
for c in "${CARRILES[@]}"; do
  n=$((n + 1))
  # shellcheck disable=SC2086
  nohup $PRIORIDAD caffeinate -i bash -c "$(declare -f nombre_corto nombre_vm ruta_lista correr_carril); EXP='$EXP'; COMMIT='$COMMIT'; correr_carril $n $c" \
    > "$EXP/ledger/sesiones/carril_$n.log" 2>&1 &
  echo "carril $n lanzado (pid $!): $c; log $EXP/ledger/sesiones/carril_$n.log"
done
