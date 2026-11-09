# Sampling_1 — velocidad sin tocar la proporción de clases

Experimento de DMEyF 2026, comisión lunes: Agustina Razanov, Martín López y Luis María Laguinge. Tutor: Joaquín I.
Aramendía.

## La pregunta y la respuesta corta

El tutor preguntó (Zulip 208986): **¿vale la pena el tradeoff entre velocidad y pérdida de performance?** Sobre el
baseline oficial de Bolaños (2019, LightGBM con Optuna), medimos cuánto tiempo se ahorra y cuánta ganancia se pierde en
201910 cuando se usan menos filas, sin cambiar la proporción de clases (eso lo estudia Sampling_2).

**Respuesta corta: vale la pena achicar la optimización, no el entrenamiento del modelo final.** Si Optuna busca sobre
el 10% de las filas y el modelo final se entrena con todas (`H3-0.1`), no pierde ganancia contra el control y el proceso
es 8,30 veces más rápido. Se sostiene con 8 réplicas de la optimización, que miden la suerte de Optuna: Δ con réplicas
= 2,30 M$, IC [−0,88; 5,47]. No es una mejora de ganancia: el IC contiene a 0 y la ventaja que mostraba una sola
optimización (4,07 M$) era en buena parte suerte de esa optimización. Entrenar el final con menos filas sí pierde: al azar
desde r = 0,25 y dentro de LightGBM con `bagging_fraction` = 0,1.

## Resultados

La comparación está en dos bloques en
[`experimentos/sampling_1/informe/tabla_resultados.md`](experimentos/sampling_1/informe/tabla_resultados.md), que genera
`python -m comun.reporte --experimento sampling_1` desde los ledgers, y comentada en
[`experimentos/sampling_1/informe/informe.md`](experimentos/sampling_1/informe/informe.md) § Resultados:

- **Bloque A, mismo protocolo**: una fila por variante con Δ de la réplica 0, Δ con réplicas (en `C` y las H3, 8
  réplicas), T, A, tiempo igual con intervalo (entre réplicas y por bootstrap de clientes de 201910) y el veredicto con
  su fuente. Las cuatro H3 (`H3-0.05`, `H3R-0.1`, `H3-0.1`, `H3-0.25`) no pierden con réplicas y valen la pena; de H1 y
  H2 ninguna.
- **Bloque B, exploratorios**: el estudio de Martín, con su propio protocolo; sus cifras no se comparan una a una con las
  del bloque A.

Δ es la diferencia de ganancia en 201910 contra el control `C`, al corte N\* = 3.300 envíos; A es cuántas veces más
rápida es la variante que el control (optimización más un modelo final). `U` es submuestreo uniforme del train (H1), `B`
y `GOSS` muestrean dentro de LightGBM (H2) y `H3` optimiza con una muestra y entrena con todo. Las limitaciones, las
conclusiones y las figuras están en el informe y en [`reporte.html`](experimentos/sampling_1/informe/reporte.html).

## Experimentos

| experimento | qué es | pregunta | estado |
|---|---|---|---|
| [`control`](experimentos/control/) | el control `C` (y su réplica `C-rep`) y las reglas comunes (G, Δ, δ, T, A, N\*, veredictos) | ¿cuál es el punto de comparación de todas las hipótesis? | reporte |
| [`h1`](experimentos/h1/) | submuestreo uniforme del train | ¿cuánto se gana en tiempo y se pierde en ganancia con r ∈ {0,5, 0,25, 0,1, 0,05}? | [informe](experimentos/h1/informe/informe.md): ni confirmada ni refutada |
| [`h2`](experimentos/h2/) | bagging y GOSS | ¿alcanza con submuestrear dentro de LightGBM? | [informe](experimentos/h2/informe/informe.md): refutada |
| [`h3`](experimentos/h3/) | optimizar con muestra y entrenar completo | ¿se puede optimizar rápido y entrenar con todo? (la réplica 0 reusa los estudios de `h1`; las réplicas `@k` son suyas) | [informe](experimentos/h3/informe/informe.md): confirmada, también con réplicas |
| [`sampling_1`](experimentos/sampling_1/) | el experimento conjunto: compara a `h1`–`h3` contra `control`, informe y video | ¿vale la pena el tradeoff velocidad-performance? | [informe](experimentos/sampling_1/informe/informe.md) |

Cada experimento tiene `docs/` (hipótesis, diseño, bitácora), `ledger/` e `informe/`. Declara en `## Dependencias` de su
`docs/diseno.md` de quién lee (`control` como mínimo) y no toca carpetas ni ledgers ajenos. Para agregar una hipótesis
(`h4`, …): [`docs/metodo.md`](docs/metodo.md) § Agregar una hipótesis. Las rutas de `sampling_1` antes de la separación
en carpetas están en [`experimentos/sampling_1/README.md`](experimentos/sampling_1/README.md) § Correspondencia de rutas.

## Aportes de Martín y Luis

- **Martín** ([`experimentos/h3/sensibilidad_muestra/`](experimentos/h3/sensibilidad_muestra/README.md)) preguntó
  **cuánto depende de la muestra la configuración que elige H3**. Repitió la búsqueda de H3 con diez muestras distintas
  y midió en 201910 la ganancia de cada modelo elegido. En 7 de 10 muestras H3 eligió la misma configuración que el
  control, y las otras tres quedan dentro del ruido de una semilla. Es exploratorio, con su propio protocolo: no es una
  variante y no cambia el veredicto de `h3`; aparece en el bloque B de la comparación. Sigue las convenciones del repo;
  falta volver a correr sus pasos 07 y 08, que hace `incorporar-aportes`.
- **Luis** ([`experimentos/sampling_1/exploratorios/validacion_50_semillas/`](experimentos/sampling_1/exploratorios/validacion_50_semillas/resumen_original.md))
  preguntó **si las H3 le ganan al control con 50 semillas finales** y probó muestras de búsqueda que conservan todas
  las bajas (lo que pasa a ser H4). Por ahora es un script de Colab con su resumen, fuera del método: rutas de Drive,
  hiperparámetros escritos a mano, sin ledger, y elige estrategias mirando 201910, que la consigna reserva para la
  comparación. `incorporar-aportes` lo porta a `experimentos/sampling_1/exploratorios/`, reconstruye lo que no tiene
  código y lo replica con el protocolo del repo.

## Qué sigue

[`h3-semillas-optuna`](openspec/changes/h3-semillas-optuna/proposal.md) ya corrió: 8 réplicas de la optimización para
`C` y las H3, dos variantes nuevas (`H3-0.05` y `H3R-0.1`, que reescala `min_data_in_leaf`) y la comparación en dos
bloques. Separó las dos explicaciones de la ventaja de H3 y la respuesta fue que la única optimización del control había
caído en una configuración peor que la mediana, no que la muestra regularice.

Sigue [`incorporar-aportes`](openspec/changes/incorporar-aportes/proposal.md): replica los aportes de Martín y Luis y crea
el experimento `h4` (muestras informadas por clase, que conservan todas las bajas), que usa las réplicas de
`h3-semillas-optuna`. El grupo queda con cuatro hipótesis. Ese cambio actualiza las secciones de resultados,
experimentos, aportes y qué sigue de este README.

## Estructura

- `comun/`: datos (panel con lags y deltas), baseline, ganancia, ledger, registro de variantes (`variantes.py`),
  muestreo, métodos, `correr.py`, `consolidar.py`, `reporte.py` y registro de tokens. Lo usan todos los experimentos;
  un cambio acá se anuncia en el commit.
- `experimentos/<nombre>/`: un experimento por carpeta. `sampling_1` además tiene `src/` y `scripts/` propios (las
  listas de las fases de las VMs).
- `plantilla/`: la estructura vacía de un experimento.
- `docs/`: [`metodo.md`](docs/metodo.md) (cómo se trabaja) y [`revision.md`](docs/revision.md) (listas de revisión).
- `scripts/`: `vm.sh`, `lanzar_fase.sh`, `etapa.sh`, `etapas.sh`, `separar_ledger.py` y los scripts del cambio
  `renombrar-brazos` (`renombrar_columna.py` y otros), para cualquier experimento o cambio; `verificar_readme.py` y
  `verificar_informe_h3.py` comprueban que los números de este README y del informe de `h3` salen de las tablas.
- `openspec/`: planes de cambio (proposal, specs, design, tasks); los cerrados en `openspec/changes/archive/` y las
  specs vigentes en `openspec/specs/`.

Los datos no están en el repo. Viven en `DATOS_DIR` (por defecto `~/datos/experimentos-dmeyf`).

## Cómo correr

### En la Mac (smoke test)

Necesita Python 3.14 (pyenv `facultad`) y `libomp` para LightGBM. Todo se corre desde la **raíz del repo**:

```bash
brew install libomp
pip install -r requirements.txt
python -m comun.datos --filas 20000
python -m comun.correr --metodo uniforme --tasa 0.25 --etapa optimizar --filas 20000
python -m comun.consolidar --experimento h1       # o sin argumento, para todos
python -m comun.reporte --experimento h1          # o --todos
python -m comun.variantes --verificar             # dependencias, ciclos y qué se rompe si falta una carpeta
python -m pytest
```

`comun.correr` escribe la fila en el ledger del dueño de la variante (`comun/variantes.py`) y lee y escribe los
hiperparámetros en el del dueño del estudio. Las corridas en la Mac son exploratorias (`etapa = exploracion`) y no
entran en los resultados.

### En la VM

Todas las corridas que cuentan van en `n2-highmem-8` spot, desde el template del curso; las de los resultados de arriba
se hicieron con el commit del tag `corridas-v1` (fases 1–4) y del tag `corridas-v2` (fase 5, las réplicas):

```bash
scripts/lanzar_fase.sh <N>             # lanza experimentos/sampling_1/scripts/faseN.txt y vuelve enseguida
scripts/vm.sh <lista-de-configuraciones>
```

`vm.sh` crea la VM, copia el repo, instala dependencias, lanza las corridas con `nohup`, sube los `ledger/` de cada
experimento al bucket y borra la VM; `lanzar_fase.sh` lo deja corriendo en segundo plano. El reparto por persona está
en [`experimentos/sampling_1/docs/diseno.md`](experimentos/sampling_1/docs/diseno.md) § Reparto y fases, y la operación
paso a paso en [`experimentos/sampling_1/docs/operacion.md`](experimentos/sampling_1/docs/operacion.md).
