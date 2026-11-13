#!/usr/bin/env bash
# Ciclo completo de una tanda de corridas en una VM n2-highmem-8 (a pedido; spot con PROVISIONING=SPOT): crea la VM
# desde el template del curso, copia el repo en el commit actual, instala dependencias, lanza la lista de configuraciones con nohup, sube los ledgers al
# bucket, los trae de vuelta y BORRA la VM (también si algo falla).
#
#   PROYECTO=proj-uba-... BUCKET=gs://mi-bucket scripts/vm.sh configuraciones.txt [--filas 20000] [--en-seco]
#
# `configuraciones.txt`: una por línea, `metodo tasa semilla etapa [variante|-] [replica]`; `#` comenta; `-` deja la
# variante por defecto y `replica` es `--replica k` (réplicas de optimización). Ej.:
#   uniforme 0.25 0 optimizar
#   uniforme 0.25 todas final
#   opt-muestra 0.25 todas final
#   uniforme 1 todas final C-rep
#   opt-muestra 0.1 todas final - 3
# Una línea que empieza con `@` corre otro módulo en vez de `comun.correr`: `@ <módulo> <args>...` -> `python -m <módulo>
# <args>` (los exploratorios, p. ej. el paquete de Luis).
# Variables: PROYECTO (obligatoria), BUCKET (obligatoria), ZONA (northamerica-northeast2-b), NOMBRE (sampling-<usuario>),
# TEMPLATE (to-064ram-08vcpu), PERSONA (usuario de git). Cada línea es `python -m comun.correr`, desde la raíz del repo.
# `ledger/sesiones/` (costos, en_curso.txt, logs de las VMs) no viaja por el bucket en ningún sentido: es estado de esta
# máquina, y la copia vieja que llevaba cada VM pisaba al volver la versión nueva (el 9-nov se perdieron filas de costos).
# Tampoco viajan los CSV de la raíz de cada ledger (`resultados.csv`, `apareado.csv`, `replicas.csv`, `estudios.csv`,
# `reemplazadas.csv`, `tokens.csv`): los escribe `comun.consolidar` acá desde `corridas/`, y la copia vieja del bucket
# dejó el 9-nov `resultados.csv` de control y h3 con 21 y 20 filas (b736a7a); viajan `corridas/`, `hp/`, `curvas/`, etc.
# Cada corrida escribe en el ledger de quien es dueño de la variante (`comun/variantes.py`), así que se sincroniza cada
# `experimentos/<exp>/ledger/` contra `$BUCKET/experimentos/<exp>/ledger/` (el `$BUCKET/ledger/` anterior a la separación
# no se toca). Una VM nueva baja del bucket el panel, los SQLite de Optuna y los ledgers si existen, así que relanzar la
# misma lista retoma.
# Calibración por máquina (`tiempos-confiables-y-consistencia` D6): la VM corre `tiempos_hp_fijos.py --calibracion <lista> inicio`
# antes de la primera línea y `... fin` después de la última, y sube el ledger una vez más después de la del final; cada una
# deja `ledger/tiempos/calibracion_<lista>_<momento>.csv` (subcarpeta: viaja con el resto del ledger). No se calibra con
# flags extra (`--filas`, smoke) ni con SIN_CALIBRACION=1.
# `--en-seco`: imprime los comandos y los destinos y sale antes de cualquier gcloud o gsutil (no crea nada).
set -euo pipefail
cd "$(dirname "$0")/.."                # raíz del repo
[ -f .env ] && { set -a; . ./.env; set +a; }   # PROYECTO y BUCKET pueden venir de .env
LISTA=${1:?uso: vm.sh configuraciones.txt [--filas N] [--en-seco]}
shift || true
EN_SECO=""; EXTRA=""                    # EXTRA: p. ej. --filas 20000 (smoke de la propia VM)
for arg in "$@"; do
  if [ "$arg" = "--en-seco" ]; then EN_SECO=1; else EXTRA="$EXTRA $arg"; fi
done
if [ -n "$EN_SECO" ]; then : "${PROYECTO:=<PROYECTO>}"; : "${BUCKET:=<BUCKET>}"; fi
: "${PROYECTO:?falta PROYECTO}"; : "${BUCKET:?falta BUCKET}"
ZONA=${ZONA:-northamerica-northeast2-b}
REGION=${ZONA%-*}
TEMPLATE=${TEMPLATE:-to-064ram-08vcpu}
NOMBRE=${NOMBRE:-sampling-$(whoami | tr -c 'a-z0-9\n' '-')}
PERSONA=${PERSONA:-$(git config user.name)}
COMMIT=$(git rev-parse --short HEAD)
LISTA_NOMBRE=$(basename "$LISTA" .txt)   # nombre de la lista en los archivos de calibración
CALIBRAR=1; { [ -n "$EXTRA" ] || [ -n "${SIN_CALIBRACION:-}" ]; } && CALIBRAR=""
G="gcloud compute --project=$PROYECTO"
EXPERIMENTOS=$(find experimentos -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | grep -v ' ' | sort)   # carpetas de experimentos del repo (sin las de aportes, que tienen espacios y no tienen ledger)

[ -z "$(git status --porcelain | grep -v '/ledger/' || true)" ] || echo "AVISO: árbol sucio; a la VM va HEAD ($COMMIT), sin los cambios sin commitear" >&2

# Script que corre en la VM. Sale con DONE (o FALLO) en ~/estado para que esta máquina sepa cuándo traer los ledgers.
cat > /tmp/remoto-$COMMIT.sh <<REMOTO
#!/usr/bin/env bash
set -uo pipefail
cd ~ && rm -rf repo && mkdir repo && tar xzf repo-$COMMIT.tgz -C repo && cd repo
# Historia de git aparte (~/repo_git), para quien lee commits viejos (ganancia_08 de Martín); ~/repo queda sin .git.
rm -rf ~/repo_git; [ -f ~/repo-$COMMIT.bundle ] && git clone -q ~/repo-$COMMIT.bundle ~/repo_git || true
python3 -m venv ~/venv && . ~/venv/bin/activate && pip install -q -r requirements.txt || { echo FALLO > ~/estado; exit 1; }
export PERSONA="$PERSONA" COMMIT_REPO="$COMMIT"
export DATOS_DIR=\${DATOS_DIR:-\$HOME/datos}; mkdir -p \$DATOS_DIR/optuna
gsutil -q cp "$BUCKET/panel_2019.parquet" \$DATOS_DIR/ 2>/dev/null || true
gsutil -q -m cp "$BUCKET/optuna/*.db" \$DATOS_DIR/optuna/ 2>/dev/null || true
for e in \$(ls experimentos | grep -v ' '); do
  mkdir -p experimentos/\$e/ledger
  gsutil -q -m rsync -r -x '^sesiones/|^[^/]*\.csv$' "$BUCKET/experimentos/\$e/ledger/" experimentos/\$e/ledger/ 2>/dev/null || true
done
subir() {
  for e in \$(ls experimentos | grep -v ' '); do
    gsutil -q -m rsync -r -x '^(exploracion|sesiones)/|^[^/]*\.csv$' experimentos/\$e/ledger/ "$BUCKET/experimentos/\$e/ledger/"
  done
}
calibrar() {   # momento: inicio o fin; sube lo que dejó (la calibración del final llega al bucket antes de dar la lista por terminada)
  [ -n "$CALIBRAR" ] || return 0
  python -m experimentos.sampling_1.scripts.tiempos_hp_fijos --calibracion "$LISTA_NOMBRE" "\$1" >> ~/corrida.log 2>&1 || echo "FALLO: calibración \$1" >> ~/corrida.log
  subir
}
calibrar inicio
while read -r metodo tasa semilla etapa variante replica; do
  [ -z "\$metodo" ] && continue; case "\$metodo" in \#*) continue;; esac
  if [ "\$metodo" = "@" ]; then   # línea de módulo: \`@ <módulo> <args>...\` corre \`python -m <módulo> <args>\`
    python -m \$tasa \$semilla \$etapa \$variante \$replica $EXTRA >> ~/corrida.log 2>&1 || echo "FALLO: @ \$tasa \$semilla \$etapa \$variante \$replica" >> ~/corrida.log
    subir
    continue
  fi
  B=""; [ -n "\${variante:-}" ] && [ "\$variante" != "-" ] && B="--variante \$variante"
  [ -n "\${replica:-}" ] && B="\$B --replica \$replica"
  python -m comun.correr --metodo \$metodo --tasa \$tasa --semilla \$semilla --etapa \$etapa \$B $EXTRA \
    --tras-trial 'gsutil -q cp {db} $BUCKET/optuna/' >> ~/corrida.log 2>&1 || echo "FALLO: \$metodo \$tasa \$semilla \$etapa" >> ~/corrida.log
  subir
  [ -f \$DATOS_DIR/panel_2019.parquet ] && gsutil -q cp -n \$DATOS_DIR/panel_2019.parquet "$BUCKET/" || true
done < ~/configuraciones.txt
calibrar fin
echo DONE > ~/estado
REMOTO

if [ -n "$EN_SECO" ]; then
  echo "== en seco: no se ejecuta gcloud ni gsutil"
  echo "VM: $NOMBRE (n2-highmem-8, Ice Lake, ${PROVISIONING:-STANDARD}) en $ZONA, proyecto $PROYECTO, template $TEMPLATE"
  echo "repo: git archive HEAD ($COMMIT) -> /tmp/repo-$COMMIT.tgz -> ~/ en la VM; historia: git bundle -> ~/repo_git"
  echo "lista: $LISTA -> ~/configuraciones.txt (flags extra:${EXTRA:- ninguno})"
  if [ -n "$CALIBRAR" ]; then
    echo "calibración: al empezar y al terminar (experimentos/sampling_1/ledger/tiempos/calibracion_${LISTA_NOMBRE}_inicio.csv y _fin.csv)"
  else
    echo "calibración: no (flags extra o SIN_CALIBRACION)"
  fi
  echo "corridas (una por línea de la lista):"
  grep -v '^[[:space:]]*#' "$LISTA" | grep -v '^[[:space:]]*$' | while read -r metodo tasa semilla etapa variante replica; do
    if [ "$metodo" = "@" ]; then echo "  python -m $tasa $semilla $etapa ${variante:-} ${replica:-}$EXTRA"; continue; fi
    [ "${variante:-}" = "-" ] && variante=""
    echo "  python -m comun.correr --metodo $metodo --tasa $tasa --semilla $semilla --etapa $etapa${variante:+ --variante $variante}${replica:+ --replica $replica}$EXTRA"
  done
  echo "destinos de los ledgers (VM -> bucket -> acá):"
  for e in $EXPERIMENTOS; do
    echo "  experimentos/$e/ledger/  ->  $BUCKET/experimentos/$e/ledger/  ->  experimentos/$e/ledger/"
  done
  echo "otros destinos: panel $BUCKET/panel_2019.parquet, Optuna $BUCKET/optuna/ (el $BUCKET/ledger/ viejo no se toca)"
  echo "-- script remoto (/tmp/remoto-$COMMIT.sh) --"
  cat /tmp/remoto-$COMMIT.sh
  exit 0
fi

# ssh y scp con tiempo de conexión y keepalive: el 8-nov un ssh colgado contra una VM que ya no respondía dejó a vm.sh
# esperando para siempre.
SSHF=(--ssh-flag=-oConnectTimeout=20 --ssh-flag=-oServerAliveInterval=15 --ssh-flag=-oServerAliveCountMax=4)
SCPF=(--scp-flag=-oConnectTimeout=20 --scp-flag=-oServerAliveInterval=15 --scp-flag=-oServerAliveCountMax=4)
# Las copias de vuelta de varias VMs escriben en las mismas carpetas locales: van de a una (el 8-nov dos copias en
# paralelo dejaron un parquet roto). Candado con mkdir (macOS no trae flock); si quien lo tomó ya no existe, se libera.
CANDADO=${TMPDIR:-/tmp}/vm-sh-copia.lock
tomar_candado() {
  until mkdir "$CANDADO" 2>/dev/null; do
    kill -0 "$(cat "$CANDADO/pid" 2>/dev/null)" 2>/dev/null || rm -rf "$CANDADO"
    sleep 5
  done
  echo $$ > "$CANDADO/pid"
}
soltar_candado() { [ "$(cat "$CANDADO/pid" 2>/dev/null)" = "$$" ] && rm -rf "$CANDADO" || true; }
borrar() {
  soltar_candado
  echo "== borrando $NOMBRE"; $G instances delete "$NOMBRE" --zone="$ZONA" --delete-disks=all --quiet || true
}
trap borrar EXIT

# A pedido por defecto: las spot se reclaman a los minutos cuando falta capacidad y se pierde lo no traído.
# PROVISIONING=SPOT usa el template del curso tal cual. El template fija preemptible=true y gcloud no deja pisarlo, así que
# la VM a pedido repite sus propiedades (imagen labo-family, disco 256 GB, red, cuenta, etiquetas, shielded) sin el scheduling.
PROVISIONING=${PROVISIONING:-STANDARD}
echo "== creando $NOMBRE (n2-highmem-8, Ice Lake, $PROVISIONING) en $ZONA"
if [ "$PROVISIONING" = SPOT ]; then
  $G instances create "$NOMBRE" --zone="$ZONA" \
    --source-instance-template="projects/$PROYECTO/regions/$REGION/instanceTemplates/$TEMPLATE" \
    --machine-type=n2-highmem-8 --min-cpu-platform="Intel Ice Lake"
else
  $G instances create "$NOMBRE" --zone="$ZONA" --machine-type=n2-highmem-8 --min-cpu-platform="Intel Ice Lake" \
    --provisioning-model=STANDARD --maintenance-policy=MIGRATE \
    --image-family=labo-family --image-project=machinae --boot-disk-size=256GB --boot-disk-type=pd-standard \
    --network=default --service-account=411419693023-compute@developer.gserviceaccount.com --scopes=cloud-platform \
    --tags=https-server,http-server,jupyter-server,rdp-server \
    --shielded-secure-boot --shielded-vtpm --shielded-integrity-monitoring \
    --metadata=startup-script="#!/bin/bash
sudo -u ds gcloud config set project $PROYECTO"
fi
for i in $(seq 30); do $G ssh "$NOMBRE" --zone="$ZONA" "${SSHF[@]}" --command=true >/dev/null 2>&1 && break; sleep 10; done

echo "== copiando el repo @ $COMMIT"
git archive --format=tar.gz -o /tmp/repo-$COMMIT.tgz HEAD
git bundle create /tmp/repo-$COMMIT.bundle HEAD 2>/dev/null
$G scp /tmp/repo-$COMMIT.tgz /tmp/repo-$COMMIT.bundle "$NOMBRE":~/ --zone="$ZONA" "${SCPF[@]}"
$G scp "$LISTA" "$NOMBRE":~/configuraciones.txt --zone="$ZONA" "${SCPF[@]}"
$G scp /tmp/remoto-$COMMIT.sh "$NOMBRE":~/remoto.sh --zone="$ZONA" "${SCPF[@]}"
# La corrida va en una unidad transitoria de systemd, no en la sesión ssh: el 1-nov una actualización automática
# (unattended-upgrades reinició el agente de Google) mató el nohup de la fase 3 sin dejar traza. Por eso además se
# apagan los timers de apt mientras dura la VM.
$G ssh "$NOMBRE" --zone="$ZONA" "${SSHF[@]}" --command="rm -f ~/estado; sudo systemctl disable --now apt-daily.timer apt-daily-upgrade.timer unattended-upgrades >/dev/null 2>&1; sudo systemd-run --quiet --unit=corrida --uid=\$USER --gid=\$USER --setenv=HOME=\$HOME --setenv=PATH=/usr/local/bin:/usr/bin:/bin -p WorkingDirectory=\$HOME -p StandardOutput=append:\$HOME/remoto.log -p StandardError=append:\$HOME/remoto.log bash \$HOME/remoto.sh"

echo "== corriendo; seguimiento: $G ssh $NOMBRE --zone=$ZONA --command='tail -f ~/corrida.log'"
# Hasta que la VM escriba ~/estado o deje de existir (una spot desalojada se borra sola: el template dice DELETE).
ESTADO=""
while :; do
  ESTADO=$($G ssh "$NOMBRE" --zone="$ZONA" "${SSHF[@]}" --command='cat ~/estado 2>/dev/null' 2>/dev/null || true)
  [ -n "$ESTADO" ] && break
  VIVA=$($G instances describe "$NOMBRE" --zone="$ZONA" --format='value(status)' 2>/dev/null || true)
  case "$VIVA" in RUNNING|PROVISIONING|STAGING) ;; *) ESTADO="PERDIDA (${VIVA:-la VM ya no existe})"; break;; esac
  sleep 60
done
echo "== estado: $ESTADO"

echo "== trayendo los ledgers"
tomar_candado
for e in $EXPERIMENTOS; do
  mkdir -p "experimentos/$e/ledger"
  gsutil -q -m rsync -r -x '^sesiones/|^[^/]*\.csv$' "$BUCKET/experimentos/$e/ledger/" "experimentos/$e/ledger/" || true
done
# Lo que el bucket no alcanzó a recibir: los ledgers de la VM, sin exploración. Con DONE la VM ya subió todo y una VM
# perdida no responde, así que solo se intenta con FALLO; no pisa nada de lo que vino del bucket.
if [ "$ESTADO" = FALLO ]; then
  T=$(mktemp -d)
  $G ssh "$NOMBRE" --zone="$ZONA" "${SSHF[@]}" --command='cd ~/repo/experimentos && tar czf ~/ledgers.tgz --exclude=exploracion --exclude=sesiones */ledger' 2>/dev/null \
    && $G scp "$NOMBRE":~/ledgers.tgz "$T/ledgers.tgz" --zone="$ZONA" "${SCPF[@]}" 2>/dev/null \
    && tar xzf "$T/ledgers.tgz" -C "$T" && rm "$T/ledgers.tgz" \
    && rsync -a --ignore-existing "$T/" experimentos/ || true
  rm -rf "$T"
fi
soltar_candado
[ "$ESTADO" = DONE ]   # el trap borra la VM; el código de salida dice si la tanda terminó
