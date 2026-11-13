#!/bin/bash
# Corre una etapa (un grupo de tasks.md) en una sesión headless con el modelo indicado y después la revisa
# en otra sesión limpia. Sin orquestador con modelo: el pegamento es este script.
#
# uso:  scripts/etapa.sh <grupo> <modelo> [experimento] [cambio] [modelo_revision]
# ej.:  scripts/etapa.sh 3 sonnet
#
# Códigos de salida: 0 grupo cerrado · 1 una sesión falló · 2 BLOQUEADO (necesita una persona) · 4 EN_CURSO (VMs trabajando).
# Cada sesión deja su JSON (con total_cost_usd) en ledger/sesiones/ y una fila en ledger/sesiones/costos.csv.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -f .env ] && { set -a; . ./.env; set +a; }
GRUPO=$1
MODELO=$2
EXP=${3:-sampling_1}
CAMBIO=${4:-separar-hipotesis}
MODELO_REV=${5:-opus}
PRESUPUESTO_APLICAR=${PRESUPUESTO_APLICAR:-3}
PRESUPUESTO_REVISAR=${PRESUPUESTO_REVISAR:-2}
INDICACIONES=${INDICACIONES:-}   # texto que se agrega al final del prompt de aplicar (lo que el orquestador sabe del cambio)
DIR="experimentos/$EXP"
LOG="$DIR/ledger/sesiones"
BLOQUEO="$LOG/bloqueo.txt"
EN_CURSO="$LOG/en_curso.txt"
DATOS=${DATOS_DIR:-$HOME/datos/experimentos-dmeyf}   # fuera del repo: las sesiones escriben ahí fotos, copias del bucket y salidas
mkdir -p "$LOG"; rm -f "$EN_CURSO"          # es una señal por sesión, no un mensaje para una persona

if [ -f "$BLOQUEO" ]; then
    echo "== hay un bloqueo previo sin resolver ($BLOQUEO). Resolvelo y borrá el archivo:"; cat "$BLOQUEO"; exit 2
fi

# Lo que una sesión headless puede correr sin preguntar. Todo lo demás se deniega solo.
# Límite conocido: python puede invocar lo que sea; la baranda real es el prompt, la revisión y la alerta de presupuesto.
PERMITIDOS="Bash(openspec:*),Bash(python:*),Bash(python3:*),Bash(pytest:*),Bash(cd:*),Bash(ls:*),Bash(cat:*),\
Bash(head:*),Bash(tail:*),Bash(wc:*),Bash(grep:*),Bash(rg:*),Bash(find:*),Bash(mkdir:*),Bash(chmod:*),Bash(sh -n:*),\
Bash(git status:*),Bash(git diff:*),Bash(git log:*),Bash(git add:*),Bash(git commit:*),Bash(git tag:*),Bash(git rev-parse:*),Bash(git describe:*),Bash(git mv:*),Bash(git rm:*),\
Bash($DIR/scripts/vm.sh:*),Bash(sh $DIR/scripts/vm.sh:*),Bash(bash $DIR/scripts/vm.sh:*),\
Bash($DIR/scripts/lanzar_fase.sh:*),Bash(bash $DIR/scripts/lanzar_fase.sh:*),Bash(pgrep:*),Bash(tail:*),\
Bash(gcloud compute instances list:*),Bash(gcloud storage ls:*),Bash(gsutil ls:*),\
Bash(git grep:*),Bash(shasum:*),Bash(sha256sum:*),Bash(gsutil rsync:*),Bash(gsutil cp:*),Bash(gsutil -m rsync:*),Bash(gsutil -m cp:*),Bash(gsutil -q -m rsync:*),Bash(gsutil -q cp:*),Bash(gcloud compute regions describe:*),\
Bash(scripts/lanzar_fase.sh:*),Bash(bash scripts/lanzar_fase.sh:*),Bash(scripts/vm.sh:*),\
Bash(scripts/sitio.sh:*),Bash(bash scripts/sitio.sh:*),Bash(mkdocs build:*),Bash(git show:*),Bash(cp:*),Bash(mktemp:*),Bash(diff:*)"

correr_claude() {  # $1 modelo, $2 presupuesto, $3 archivo json, $4 prompt  -> código de salida de claude
    claude -p "$4" --model "$1" --permission-mode acceptEdits --max-budget-usd "$2" \
        --add-dir "$DATOS" --allowedTools "$PERMITIDOS" --output-format stream-json --verbose \
        | python3 scripts/_stream.py "$3"
}

registrar() {  # $1 archivo json, $2 grupo, $3 rol, $4 código de salida
    python3 - "$1" "$2" "$3" "$4" "$LOG/costos.csv" "$CAMBIO" <<'PY'
import json, sys, csv, datetime, pathlib
archivo, grupo, rol, rc, salida, cambio = sys.argv[1:]
d = json.load(open(archivo))
uso = d.get("modelUsage") or {}
modelo = max(uso, key=lambda m: (uso[m] or {}).get("outputTokens", 0)) if uso else ""
fila = {
    "fecha": datetime.datetime.now().isoformat(timespec="minutes"),
    "grupo": grupo, "rol": rol, "modelo": modelo,
    "turnos": d.get("num_turns", ""),
    "costo_usd": round(d.get("total_cost_usd") or 0, 4),
    "sesion": d.get("session_id", ""),
    "resultado": d.get("subtype", ""), "codigo": rc, "cambio": cambio,
}
p = pathlib.Path(salida); nuevo = not p.exists()
with p.open("a", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(fila))
    if nuevo: w.writeheader()
    w.writerow(fila)
print(f"{rol} g{grupo}: {modelo} {fila['turnos']} turnos US$ {fila['costo_usd']} ({fila['resultado']}, rc {rc})")
PY
}

exitoso() { grep -q '"subtype": "success"' "$1"; }

SELLO=$(date +%Y%m%dT%H%M%S)
J_APLICAR="$LOG/g${GRUPO}_aplicar_$SELLO.json"
J_REVISAR="$LOG/g${GRUPO}_revisar_$SELLO.json"

TAREAS="openspec/changes/$CAMBIO/tasks.md"
SIN_REVISAR=$(grep -E "^- \[ \] $GRUPO\." "$TAREAS" | grep -v -i -c "revis" || true)
if [ "$SIN_REVISAR" -eq 0 ]; then
    echo "== grupo $GRUPO: solo queda la revisión; salteo la sesión de aplicar"
else
echo "== aplicar grupo $GRUPO con $MODELO"
RC=0
correr_claude "$MODELO" "$PRESUPUESTO_APLICAR" "$J_APLICAR" \
    "Aplicá solo el grupo $GRUPO de tasks.md del cambio $CAMBIO siguiendo \
.claude/skills/openspec-apply-change/SKILL.md (openspec instructions apply --change $CAMBIO --json). \
El experimento es experimentos/$EXP; leé CLAUDE.md y docs/metodo.md antes de empezar. \
PROYECTO y BUCKET ya están definidos: los carga .env (en la raíz del repo, ignorado por git) y los lee vm.sh; \
no los busques en los documentos ni pidas que los definan. \
Corré python y pytest a secas desde la raíz del repo (python -m comun.X, o python -m experimentos.$EXP.src.X para lo que todavía no pasó a comun/): el entorno ya está resuelto; \
no antepongas variables de entorno (PYENV_VERSION=..., PYTHONPATH=...) ni export, porque esa forma no está en la lista de comandos permitidos y te la van a negar. \
Marcá cada tarea al terminarla, solo con la evidencia que pide su texto. Las tareas del grupo que dicen 'Revisar' o 'revisión en sesión limpia' no las hagas, \
no las marques y no las bloquees: las hace la sesión de revisión que corre después de esta. Las corridas en VM se lanzan solo con el lanzador y las listas que definen las tareas del cambio \
(scripts/lanzar_fase.sh <lista>), que vuelve enseguida y deja las VMs trabajando; nunca gcloud, ni vm.sh sin --en-seco. Si lanzaste fases y las \
tareas dependen de sus resultados, no bloquees ni marques: escribí EN_CURSO y qué esperás en $EN_CURSO y terminá; \
el loop espera a que las VMs terminen y vuelve a correr este grupo, y entonces consolidás, verificás y marcás. \
Si los resultados ya están (ledger/corridas con filas, sin vm.sh corriendo: pgrep -f vm.sh), consolidá y marcá. Commiteá al cerrar cada tarea (sin Co-Authored-By). No hagas push y no cambies el diseño. \
No publiques en Zulip ni mandes mensajes fuera del repo. \
Si una tarea necesita algo que no podés hacer (una decisión de diseño), escribí BLOQUEADO y el motivo en $BLOQUEO y terminá. $INDICACIONES" || RC=$?
registrar "$J_APLICAR" "$GRUPO" aplicar "$RC"
if [ -f "$BLOQUEO" ]; then echo "== BLOQUEADO:"; cat "$BLOQUEO"; exit 2; fi
if [ "$RC" -ne 0 ] || ! exitoso "$J_APLICAR"; then echo "== la sesión de aplicar no terminó bien (rc $RC)"; exit 1; fi
if [ -f "$EN_CURSO" ]; then echo "== EN_CURSO (VMs trabajando):"; cat "$EN_CURSO"; exit 4; fi
fi

echo "== revisar grupo $GRUPO con $MODELO_REV"
RC=0
correr_claude "$MODELO_REV" "$PRESUPUESTO_REVISAR" "$J_REVISAR" \
    "Sos la revisión en sesión limpia del grupo $GRUPO de tasks.md del cambio $CAMBIO, \
experimento experimentos/$EXP. No conocés la sesión que lo implementó. \
Usá la lista correspondiente de docs/revision.md: verificá cada ítem corriendo lo que haga falta, \
corregí lo que no pase y anotalo, cerrá la etapa en $DIR/docs/bitacora.md con el formato de cierre \
(fecha, sesión, revisor, hallazgos, correcciones, tokens), marcá como hecha la tarea de revisión del grupo en tasks.md \
y commiteá (sin Co-Authored-By). No publiques en Zulip ni mandes mensajes fuera del repo. \
Si algo no se puede cerrar sin un humano, \
escribilo en $BLOQUEO." || RC=$?
registrar "$J_REVISAR" "$GRUPO" revisar "$RC"
if [ -f "$BLOQUEO" ]; then echo "== BLOQUEADO en la revisión:"; cat "$BLOQUEO"; exit 2; fi
if [ "$RC" -ne 0 ] || ! exitoso "$J_REVISAR"; then echo "== la sesión de revisión no terminó bien (rc $RC)"; exit 1; fi
echo "== grupo $GRUPO cerrado"
