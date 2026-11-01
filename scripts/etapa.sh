#!/bin/sh
# Corre una etapa (un grupo de tasks.md) en una sesión headless con el modelo indicado y después la revisa
# en otra sesión limpia. Sin orquestador con modelo: el pegamento es este script.
#
# uso:  scripts/etapa.sh <grupo> <modelo> [experimento] [cambio] [modelo_revision]
# ej.:  scripts/etapa.sh 3 sonnet
#       for g in 3 4; do scripts/etapa.sh $g sonnet || break; done
#
# Corta con código 2 si la etapa escribe BLOQUEADO (algo que necesita a un humano: VM, tutor, decisión).
# Cada sesión deja su JSON (con total_cost_usd) en ledger/sesiones/ y una fila en ledger/sesiones/costos.csv.
set -eu
cd "$(dirname "$0")/.."
GRUPO=$1
MODELO=$2
EXP=${3:-sampling-velocidad}
CAMBIO=${4:-experimento-sampling-velocidad}
MODELO_REV=${5:-opus}
PRESUPUESTO_APLICAR=${PRESUPUESTO_APLICAR:-3}
PRESUPUESTO_REVISAR=${PRESUPUESTO_REVISAR:-2}
DIR="experimentos/$EXP"
LOG="$DIR/ledger/sesiones"
BLOQUEO="$LOG/bloqueo.txt"
mkdir -p "$LOG"
rm -f "$BLOQUEO"

registrar() {
    python3 - "$1" "$2" "$3" "$LOG/costos.csv" <<'PY'
import json, sys, csv, datetime, pathlib
archivo, grupo, rol, salida = sys.argv[1:]
d = json.load(open(archivo))
fila = {
    "fecha": datetime.datetime.now().isoformat(timespec="minutes"),
    "grupo": grupo, "rol": rol,
    "modelo": next(iter(d.get("modelUsage", {})), ""),
    "turnos": d.get("num_turns", ""),
    "costo_usd": round(d.get("total_cost_usd", 0), 4),
    "sesion": d.get("session_id", ""),
    "resultado": d.get("subtype", ""),
}
p = pathlib.Path(salida); nuevo = not p.exists()
with p.open("a", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(fila))
    if nuevo: w.writeheader()
    w.writerow(fila)
print(f"{rol} g{grupo}: {fila['modelo']} {fila['turnos']} turnos US$ {fila['costo_usd']} ({fila['resultado']})")
PY
}

echo "== aplicar grupo $GRUPO con $MODELO"
claude -p --model "$MODELO" --permission-mode acceptEdits \
    --max-budget-usd "$PRESUPUESTO_APLICAR" --output-format json \
    "Aplicá solo el grupo $GRUPO de tasks.md del cambio $CAMBIO siguiendo \
.claude/skills/openspec-apply-change/SKILL.md (openspec instructions apply --change $CAMBIO --json). \
El experimento es experimentos/$EXP; leé CLAUDE.md y docs/metodo.md antes de empezar. \
Marcá cada tarea al terminarla. No crees ni borres VMs, no hagas push y no cambies el diseño. \
Si una tarea necesita algo que no podés hacer (una VM, una respuesta del tutor, una decisión de diseño), \
escribí BLOQUEADO y el motivo en $BLOQUEO y terminá." \
    > "$LOG/g${GRUPO}_aplicar.json"
registrar "$LOG/g${GRUPO}_aplicar.json" "$GRUPO" aplicar

if [ -f "$BLOQUEO" ]; then
    echo "== BLOQUEADO:"; cat "$BLOQUEO"; exit 2
fi

echo "== revisar grupo $GRUPO con $MODELO_REV"
claude -p --model "$MODELO_REV" --permission-mode acceptEdits \
    --max-budget-usd "$PRESUPUESTO_REVISAR" --output-format json \
    "Sos la revisión en sesión limpia del grupo $GRUPO de tasks.md del cambio $CAMBIO, \
experimento experimentos/$EXP. No conocés la sesión que lo implementó. \
Usá la lista correspondiente de docs/revision.md: verificá cada ítem corriendo lo que haga falta, \
corregí lo que no pase y anotalo, y cerrá la etapa en $DIR/docs/bitacora.md con el formato de cierre \
(fecha, sesión, revisor, hallazgos, correcciones, tokens). Si algo no se puede cerrar sin un humano, \
escribilo en $BLOQUEO." \
    > "$LOG/g${GRUPO}_revisar.json"
registrar "$LOG/g${GRUPO}_revisar.json" "$GRUPO" revisar

if [ -f "$BLOQUEO" ]; then
    echo "== BLOQUEADO en la revisión:"; cat "$BLOQUEO"; exit 2
fi
echo "== grupo $GRUPO cerrado"
