# Proposal

## Why

El grupo Sampling_1 (Agustina, Martín López, Luis Laguinge; tutor Joaquín Aramendía) tiene que responder, con el baseline
de Bolaños del 28-oct, la pregunta que el tutor dejó en `Experimentos - Lunes > sampling_1` el 1-nov: **¿vale la pena el
tradeoff entre velocidad y pérdida de performance?** Como Sampling_2 toma el undersampling de la clase mayoritaria, este
experimento aísla la velocidad **sin alterar la proporción de clases**. Además, el proyecto es el banco de prueba del
método de trabajo con pocos tokens acordado el 31-oct: en octubre el contexto promedio por turno fue de ~400.000 tokens y
el consumo equivalió a ~US$ 694 de API; acá se mide si sesiones por etapa, modelos baratos para lo mecánico y salidas a
archivo bajan ese número sin perder calidad.

## What Changes

- Se crea el repo `experimento-sampling` (greenfield, compartido con el grupo) donde **cada experimento vive en su propia
  carpeta** `experimentos/<nombre>/` con la misma estructura, el código compartido va en `comun/` y una `plantilla/`
  permite que cualquier integrante u otro grupo agregue el suyo. El primero es `experimentos/sampling-velocidad/`,
  organizado por las etapas del método científico: pregunta e hipótesis, diseño, ejecución, análisis, conclusiones. Cada etapa termina con
  una revisión explícita antes de pasar a la siguiente.
- Tres hipótesis con predicción y regla de decisión escritas antes de correr nada:
  - **H1 Submuestreo uniforme**: muestrear filas al azar sin distinguir clase a tasas decrecientes baja el tiempo casi
    linealmente y la ganancia en 201910 se mantiene dentro del ruido entre semillas hasta una tasa mínima; por debajo cae.
  - **H2 Sampling interno de LightGBM**: a tiempo igual, `bagging_fraction` fijo y GOSS pierden menos que recortar el
    dataset de antemano, porque cada iteración ve filas distintas.
  - **H3 Optimizar sobre una muestra**: los hiperparámetros elegidos por Optuna sobre una muestra del 10–25% producen,
    entrenando después con todos los datos, la misma ganancia que los elegidos sobre el 100%, a una fracción del costo.
- Un **corredor reproducible**: un único punto de entrada que ejecuta una configuración (método, tasa, semilla) con el
  baseline fijo, mide tiempo de pared y memoria, y escribe una fila de ledger. El mismo código corre en la Mac (smoke
  test) y en la VM de Google Cloud (corridas reales), y las tres personas corren partes disjuntas de la grilla.
- Un **ledger de resultados** en CSV, una fila por corrida, idempotente por clave, con lo necesario para el análisis
  apareado por semilla y las curvas de ganancia.
- Un **registro de tokens** por sesión de Claude Code, calculado desde los transcripts locales, comparado contra la
  línea de base de octubre.
- Documentos del experimento en `experimentos/sampling-velocidad/docs/`: hipótesis, diseño experimental, bitácora,
  informe final y guion del video. La lista de revisión por etapa y el método son del repo (`docs/`), no del
  experimento. El post al tutor sale de `docs/hipotesis.md` del experimento.

Fuera de alcance: undersampling de la clase mayoritaria (Sampling_2), oversampling o SMOTE, selección de meses de
entrenamiento (grupo Meses), features nuevas (grupos FE) y el pipeline productivo de la segunda entrega.

## Capabilities

### New Capabilities
- `protocolo-experimental`: cómo se formula, revisa y documenta un experimento por etapas, qué queda escrito antes de
  correr, qué revisión cierra cada etapa y cómo se agrega un experimento nuevo al repo sin tocar los demás.
- `corrida-reproducible`: cómo se ejecuta una configuración del experimento de forma determinística y comparable entre
  máquinas y personas, y qué mide.
- `ledger-resultados`: qué registra cada corrida, cómo se acumula sin pisar y qué se puede derivar de él (tablas
  apareadas, curvas de ganancia).
- `registro-tokens`: cómo se mide el consumo de Claude por sesión y etapa, y contra qué se compara.

### Modified Capabilities
(ninguna: el repo es nuevo)

## Impact

- Repo nuevo `~/Documents/segundo-cuatrimestre/experimento-sampling/` con `comun/`, `experimentos/<nombre>/`
  (`docs/`, `src/`, `scripts/`, `ledger/`, `informe/`), `plantilla/`, `docs/` del método y `openspec/`. Se publica en
  GitHub para compartir con el grupo; sin dataset en el repo.
- Reutiliza de `competencia-2/src/fe_panel.py` el SQL de lags y deltas en DuckDB; no modifica `competencia-2`.
- Dependencias: Python del pyenv `facultad`, LightGBM, Optuna, DuckDB, pandas, pyarrow. En la Mac falta `libomp`
  (`brew install libomp`) para que LightGBM cargue; en la VM del template del curso ya funciona.
- Cómputo: VMs spot `n2-highmem-8` creadas desde el template del curso, una por persona, datos en el bucket, apagado al
  terminar. Estimado total: menos de 15 horas de VM, menos de US$ 5.
- Dataset: `competencia_02_crudo.csv.gz` (201901–202108) del GCS del curso; el experimento usa solo 2019.
