# Corridas

Cómo se corren, retoman y consolidan las corridas de todas las hipótesis, en qué máquina y en qué fases. Todos los
comandos se corren desde la raíz del repo.

## Protocolo

Cada variante tiene su Optuna (40 trials, train 201903–201906, AUC en validación, 201908) y un final que entrena con
201903–201908 y se evalúa en test (201910) con 20 semillas. Decide la ganancia al corte N\* = 3.300 clientes
contactados; el AUC va al lado. `C`, H3 y H4 tienen 8 réplicas de la optimización (otra semilla de Optuna y otra
muestra). El costo está abajo y las fases, en § Fases; los apartamientos del baseline, con su id, en
[Control y reglas](../control/README.md).

## Máquina

- Todas las corridas que cuentan van en **`n2-highmem-8`** (8 vCPU, 64 GB) con CPU **Intel Ice Lake**, que es lo que
  define T en las [reglas](../control/README.md). Cada fila del ledger registra el modelo de CPU de `/proc/cpuinfo`, y el
  análisis de tiempos descarta las filas con otra CPU.
- El curso no tiene un template `n2-highmem-8`. La VM se crea desde **`to-064ram-08vcpu`** (imagen `labo-family`, disco
  de 256 GB, script de arranque) y se sobrescriben el tipo y la plataforma:

  ```bash
  # T=projects/<proyecto>/regions/northamerica-northeast2/
  #   instanceTemplates/to-064ram-08vcpu
  gcloud compute instances create <nombre> \
    --zone=northamerica-northeast2-b \
    --source-instance-template="$T" \
    --machine-type=n2-highmem-8 \
    --min-cpu-platform="Intel Ice Lake"
  ```

  e2 queda descartada porque no deja fijar la plataforma de CPU. Región `northamerica-northeast2`, donde están los
  templates del curso; si no hay capacidad en la zona `-b`, se usa `-a` o `-c` (las tres tienen Ice Lake).

- Las fases 1 a 7 corrieron en VMs spot. Hoy `scripts/vm.sh` crea las VMs **a pedido** por defecto, porque las spot se
  reclaman a los minutos cuando falta capacidad; `PROVISIONING=SPOT` usa el template tal cual.
- La cuota del trial es de 32 vCPU por proyecto (`CPUS_ALL_REGIONS`): 4 VMs de 8 vCPU a la vez. Las fases grandes van en
  tandas.
- Una corrida por VM a la vez, en secuencia. Se registra el `load average` al iniciar cada corrida.
- Lo que tiene que sobrevivir a la VM se copia al bucket: el **SQLite de Optuna** al terminar cada trial (no se abre
  sobre gcsfuse, porque SQLite necesita locking), el **panel 2019 en Parquet** una vez después de armarlo (una VM nueva lo
  baja en vez de rehacer la media hora de preparación) y las **filas de `ledger/corridas/` y `ledger/curvas/`** al
  terminar cada corrida.
- Cada fase sale de un único commit con tag (`corridas-v1` … `corridas-v4`). Si hay que corregir código a mitad de
  camino, se crea un tag nuevo, se anota en la bitácora y se repiten las corridas afectadas.

## Una configuración

```bash
# estudio U0.25 (h1/ledger)
python -m comun.correr --metodo uniforme --tasa 0.25 \
  --semilla 0 --etapa optimizar
# variante U0.25, todas las semillas
python -m comun.correr --metodo uniforme --tasa 0.25 \
  --semilla todas --etapa final
# variante H3-0.25 (h3/ledger)
python -m comun.correr --metodo opt-muestra --tasa 0.25 \
  --semilla todas --etapa final
# réplica del control con los hiperparámetros de C
python -m comun.correr --metodo uniforme --tasa 1 \
  --semilla todas --etapa final --variante C-rep \
  --hp experimentos/control/ledger/hp/C.json
```

| método | `--tasa` | estudio | variante |
|---|---|---|---|
| `uniforme` | r | `C` (r = 1) o `U<r>` | igual al estudio |
| `bagging` | f | `B<f>` | igual al estudio |
| `goss` | 1 | `GOSS` | `GOSS` |
| `opt-muestra` | r_opt | el de `uniforme` con la misma tasa | `H3-<r_opt>` |

- `opt-muestra --etapa optimizar` corre el estudio de `uniforme` con esa tasa, que H1 y H3 comparten. El resto de los
  métodos (reescalados, por cliente, los de H4) está en `comun/metodos.py` y su nombre en `comun/variantes.py`.
- `--etapa final` usa `hp/<estudio>.json` del ledger del dueño del estudio (H3 lee el de `h1`) salvo que se pase `--hp`.
  `--semilla todas` son las semillas del diseño; una lista con comas también vale. Las que ya tienen fila válida se
  saltean. `--replica k` corre la réplica k de la optimización.
- El estudio de Optuna es un SQLite en `$DATOS_DIR/optuna/`. Si la corrida se corta, el mismo comando retoma los trials
  que faltan. `--tras-trial 'cmd {db}'` corre un comando después de cada trial (la VM lo usa para copiarlo al bucket).

## Qué cuenta y qué no

Una fila es **válida** (`valida = true`) si el árbol estaba limpio (los archivos de `ledger/` no cuentan), no se usó
`--filas` y los trials son 40. Lo demás es exploratorio: va a `ledger/exploracion/` (ignorado por git) y su id lleva
`exp-` y la hora, así que nunca se saltea. `consolidar` solo mira `ledger/corridas/`. Las corridas en la Mac
(`--filas 20000`) son pruebas.

Tiempos de una fila final: `tiempo_entrenamiento_s` es `Dataset` + entrenamiento + predicción en 201910;
`tiempo_lgbtrain_s`, solo `lgb.train`. En una invocación con varias semillas, la primera fila lleva además la carga de
datos y el panel (`tiempo_preparacion_s`); las otras, solo su muestreo. En una fila `optimizar`, `tiempo_optimizacion_s`
es la suma de la duración de los trials más el armado del `Dataset`.

## Consolidar y regenerar

```bash
# resultados.csv, reemplazadas.csv, estudios.csv y apareado.csv de h1
python -m comun.consolidar --experimento h1
# los de todos los dueños de variantes
python -m comun.consolidar
# bloques generados de cada página (--figuras DIR guarda también los PNG)
python -m comun.reporte --todos
# bloque rondas del Anexo
python -m scripts.comparar_rondas
```

`apareado.csv` trae N\*, δ, Δ de ganancia por variante (media, desvío, IC 95%, semillas ganadas, veredicto), Δ de AUC, T
y la aceleración. Los tiempos solo se comparan con el control si la máquina, la CPU y los hilos coinciden; si no, la
columna `nota` lo dice.

## VM

```bash
# una VM por lista; vuelve enseguida y deja la VM trabajando
scripts/lanzar_fase.sh <lista>
# muestra qué haría, sin crear nada
scripts/vm.sh configuraciones.txt --en-seco
```

`PROYECTO` y `BUCKET` salen de `.env` en la raíz del repo (ver `.env.ejemplo`). `vm.sh` crea la VM con `n2-highmem-8` e
Ice Lake, copia el repo en el commit actual, instala `requirements.txt`, corre la lista con `nohup`, sube el `ledger/` de
cada experimento y los SQLite al bucket, trae los ledgers y **borra la VM** al terminar o fallar. Antes de cada fase:

1. Commit y tag de la fase (las filas con árbol sucio no cuentan).
2. Si una VM muere, volver a correr el mismo comando: baja el panel y los SQLite del bucket, retoma el estudio y saltea
   las finales que ya tienen fila.
3. Después de traer el ledger: commit de `experimentos/*/ledger/{corridas,curvas,hp}`, push y `comun.consolidar`.

## Fases

Las siete fases que ya corrieron, con la carga de cada una, el reparto por máquina, la grilla común y la fase 8, están en [`docs/fases.md`](https://github.com/agustinarazanov/dmeyf-experimento-sampling/blob/main/experimentos/sampling_1/docs/fases.md) (no se publica en el sitio).

## Costo

- **Estimación inicial** (1-nov): unidad u = un entrenamiento de 100 iteraciones sobre el train completo (~640.000 filas
  × ~470 columnas) más su predicción, supuesta en ~1 min. Factores supuestos: `uniforme` 0,15 + 0,85 r; `bagging`
  0,4 + 0,6 f; `GOSS` 0,7. Daba 268,8 u·min para las fases 1 a 3, ≈ 6 h de VM con el arranque (≈ 15 h si u fuera 3 min).
  Esas aceleraciones estimadas eran para el costo, no predicciones del experimento.
- **Precio**: `n2-highmem-8` cuesta ≈ US$ 0,52/h a pedido en `us-central1`, algo más en `northamerica-northeast2`
  (≈ 10–15 %) y bastante menos en spot. El peor caso de cada fase (a pedido, con un 15 % extra y media hora de arranque
  por VM) quedó debajo de US$ 10 en las fases 1 a 5, de US$ 15 en la 6 y de US$ 17 en la 7, más disco y bucket, dentro
  del crédito del trial. Las horas y el costo reales de cada fase están en la
  [bitácora de sampling_1](https://github.com/agustinarazanov/dmeyf-experimento-sampling/blob/main/experimentos/sampling_1/docs/bitacora.md).
- Al terminar cada fase no queda ninguna VM encendida.
