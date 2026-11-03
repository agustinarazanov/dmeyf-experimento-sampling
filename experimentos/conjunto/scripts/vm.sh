#!/usr/bin/env bash
# Ciclo completo de una tanda de corridas en una VM spot n2-highmem-8: crea la VM desde el template del curso, copia el
# repo en el commit actual, instala dependencias, lanza la lista de configuraciones con nohup, sube el ledger al
# bucket, lo trae de vuelta y BORRA la VM (también si algo falla).
#
#   PROYECTO=proj-uba-... BUCKET=gs://mi-bucket scripts/vm.sh configuraciones.txt [--filas 20000]
#
# `configuraciones.txt`: una por línea, `metodo tasa semilla etapa [brazo]`; `#` comenta. Ej.:
#   uniforme 0.25 0 optimizar
#   uniforme 0.25 todas final
#   opt-muestra 0.25 todas final
#   uniforme 1 todas final C-rep
# Variables: PROYECTO (obligatoria), BUCKET (obligatoria), ZONA (northamerica-northeast2-b), NOMBRE (sampling-<usuario>),
# TEMPLATE (to-064ram-08vcpu), PERSONA (usuario de git). Cada línea es `python -m src.correr` con `PYTHONPATH=../..`.
# Una VM nueva baja del bucket el panel y los SQLite de Optuna si existen, así que relanzar la misma lista retoma.
set -euo pipefail
cd "$(dirname "$0")/../../.."          # raíz del repo
[ -f .env ] && { set -a; . ./.env; set +a; }   # PROYECTO y BUCKET pueden venir de .env
LISTA=${1:?uso: vm.sh configuraciones.txt [--filas N]}
shift || true
EXTRA="$*"                              # p. ej. --filas 20000 (smoke de la propia VM)
: "${PROYECTO:?falta PROYECTO}"; : "${BUCKET:?falta BUCKET}"
ZONA=${ZONA:-northamerica-northeast2-b}
REGION=${ZONA%-*}
TEMPLATE=${TEMPLATE:-to-064ram-08vcpu}
NOMBRE=${NOMBRE:-sampling-$(whoami | tr -c 'a-z0-9\n' '-')}
PERSONA=${PERSONA:-$(git config user.name)}
EXP=experimentos/sampling-velocidad
COMMIT=$(git rev-parse --short HEAD)
G="gcloud compute --project=$PROYECTO"

[ -z "$(git status --porcelain | grep -v '/ledger/' || true)" ] || echo "AVISO: árbol sucio; a la VM va HEAD ($COMMIT), sin los cambios sin commitear" >&2

borrar() { echo "== borrando $NOMBRE"; $G instances delete "$NOMBRE" --zone="$ZONA" --delete-disks=all --quiet || true; }
trap borrar EXIT

echo "== creando $NOMBRE (n2-highmem-8, Ice Lake, spot) en $ZONA"
$G instances create "$NOMBRE" --zone="$ZONA" \
  --source-instance-template="projects/$PROYECTO/regions/$REGION/instanceTemplates/$TEMPLATE" \
  --machine-type=n2-highmem-8 --min-cpu-platform="Intel Ice Lake"
for i in $(seq 30); do $G ssh "$NOMBRE" --zone="$ZONA" --command=true >/dev/null 2>&1 && break; sleep 10; done

echo "== copiando el repo @ $COMMIT"
git archive --format=tar.gz -o /tmp/repo-$COMMIT.tgz HEAD
$G scp /tmp/repo-$COMMIT.tgz "$NOMBRE":~/ --zone="$ZONA"
$G scp "$LISTA" "$NOMBRE":~/configuraciones.txt --zone="$ZONA"

# Script que corre en la VM. Sale con DONE (o FALLO) en ~/estado para que esta máquina sepa cuándo traer el ledger.
cat > /tmp/remoto-$COMMIT.sh <<REMOTO
#!/usr/bin/env bash
set -uo pipefail
cd ~ && rm -rf repo && mkdir repo && tar xzf repo-$COMMIT.tgz -C repo && cd repo
python3 -m venv ~/venv && . ~/venv/bin/activate && pip install -q -r requirements.txt || { echo FALLO > ~/estado; exit 1; }
export PYTHONPATH=../.. PERSONA="$PERSONA" COMMIT_REPO="$COMMIT"
export DATOS_DIR=\${DATOS_DIR:-\$HOME/datos}; mkdir -p \$DATOS_DIR/optuna
gsutil -q cp "$BUCKET/panel_2019.parquet" \$DATOS_DIR/ 2>/dev/null || true
gsutil -q -m cp "$BUCKET/optuna/*.db" \$DATOS_DIR/optuna/ 2>/dev/null || true
cd $EXP
subir() { gsutil -q -m rsync -r ledger/ "$BUCKET/ledger/"; }
while read -r metodo tasa semilla etapa brazo; do
  [ -z "\$metodo" ] && continue; case "\$metodo" in \#*) continue;; esac
  B=""; [ -n "\${brazo:-}" ] && B="--brazo \$brazo"
  python -m src.correr --metodo \$metodo --tasa \$tasa --semilla \$semilla --etapa \$etapa \$B $EXTRA \
    --tras-trial 'gsutil -q cp {db} $BUCKET/optuna/' >> ~/corrida.log 2>&1 || echo "FALLO: \$metodo \$tasa \$semilla \$etapa" >> ~/corrida.log
  subir
  [ -f \$DATOS_DIR/panel_2019.parquet ] && gsutil -q cp -n \$DATOS_DIR/panel_2019.parquet "$BUCKET/" || true
done < ~/configuraciones.txt
echo DONE > ~/estado
REMOTO
$G scp /tmp/remoto-$COMMIT.sh "$NOMBRE":~/remoto.sh --zone="$ZONA"
# La corrida va en una unidad transitoria de systemd, no en la sesión ssh: el 1-nov una actualización automática
# (unattended-upgrades reinició el agente de Google) mató el nohup de la fase 3 sin dejar traza. Por eso además se
# apagan los timers de apt mientras dura la VM.
$G ssh "$NOMBRE" --zone="$ZONA" --command="rm -f ~/estado; sudo systemctl disable --now apt-daily.timer apt-daily-upgrade.timer unattended-upgrades >/dev/null 2>&1; sudo systemd-run --quiet --unit=corrida --uid=\$USER --gid=\$USER --setenv=HOME=\$HOME --setenv=PATH=/usr/local/bin:/usr/bin:/bin -p WorkingDirectory=\$HOME -p StandardOutput=append:\$HOME/remoto.log -p StandardError=append:\$HOME/remoto.log bash \$HOME/remoto.sh"

echo "== corriendo; seguimiento: $G ssh $NOMBRE --zone=$ZONA --command='tail -f ~/corrida.log'"
until [ "$($G ssh "$NOMBRE" --zone="$ZONA" --command='cat ~/estado 2>/dev/null' 2>/dev/null || true)" != "" ]; do sleep 60; done
ESTADO=$($G ssh "$NOMBRE" --zone="$ZONA" --command='cat ~/estado')
echo "== estado: $ESTADO"

echo "== trayendo el ledger"
mkdir -p "$EXP/ledger"
gsutil -q -m rsync -r "$BUCKET/ledger/" "$EXP/ledger/" || true
$G scp --recurse "$NOMBRE":~/repo/$EXP/ledger/corridas "$NOMBRE":~/repo/$EXP/ledger/curvas "$NOMBRE":~/repo/$EXP/ledger/hp "$NOMBRE":~/repo/$EXP/ledger/predicciones "$EXP/ledger/" --zone="$ZONA" 2>/dev/null || true
[ "$ESTADO" = DONE ]   # el trap borra la VM; el código de salida dice si la tanda terminó
