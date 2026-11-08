# Sampling_1 — velocidad sin tocar la proporción de clases

Experimento de DMEyF 2026, comisión lunes: Agustina Razanov, Martín López y Luis María Laguinge. Tutor: Joaquín I.
Aramendía.

## La pregunta y la respuesta corta

El tutor preguntó (Zulip 208986): **¿vale la pena el tradeoff entre velocidad y pérdida de performance?** Sobre el
baseline oficial de Bolaños (2019, LightGBM con Optuna), medimos cuánto tiempo se ahorra y cuánta ganancia se pierde en
201910 cuando se usan menos filas, sin cambiar la proporción de clases (eso lo estudia Sampling_2).

**Respuesta corta: vale la pena achicar la optimización, no el entrenamiento del modelo final.** Si Optuna busca sobre
el 10% de las filas y el modelo final se entrena con todas (`H3-0.1`), no pierde ganancia contra el control (la cota
inferior del IC queda arriba de −δ, con δ = 2%) y el proceso es 8,41 veces más rápido. Entrenar el final con menos filas sí pierde: al azar desde r = 0,25 y
dentro de LightGBM con `bagging_fraction` = 0,1.

Por ahora es una respuesta con una salvedad grande: cada variante corrió **una sola optimización de Optuna**, así que
Δ incluye la suerte de esa optimización. El cambio `h3-semillas-optuna` (§ Qué sigue) la mide.

## Resultados hasta ahora

Copiado de [`experimentos/sampling_1/informe/informe.md`](experimentos/sampling_1/informe/informe.md) § Resultados. Δ es
la diferencia de ganancia en 201910 contra el control `C`, apareada por semilla final (10 semillas), al corte N\* = 3.300
envíos. A es cuántas veces más rápido es que el control (optimización más un modelo final). Una variante *no pierde*
si la cota inferior del IC es ≥ −δ (δ = 5,52 M$) y *vale la pena* si además A ≥ 2.

| variante | Δ media (M$) | IC 95% (M$) | A | veredicto | vale la pena |
|---|---|---|---|---|---|
| H3-0.1 | 4,07 | [−0,27; 8,41] | 8,41 | no pierde | sí |
| H3-0.25 | 4,18 | [−0,60; 8,96] | 4,48 | no pierde | sí |
| U0.5 | −1,32 | [−6,77; 4,13] | 2,28 | indeterminado | no |
| U0.25 | −6,38 | [−11,21; −1,55] | 4,89 | pierde | no |
| U0.1 | −16,94 | [−23,35; −10,53] | 9,85 | pierde | no |
| U0.05 | −33,77 | [−39,84; −27,70] | 11,42 | pierde | no |
| B0.5 | −0,11 | [−4,46; 4,24] | 0,78 | no pierde | no |
| B0.25 | 0,66 | [−2,86; 4,18] | 1,21 | no pierde | no |
| B0.1 | −7,81 | [−12,27; −3,35] | 1,85 | pierde | no |
| GOSS | 0,55 | [−2,60; 3,70] | 0,72 | no pierde | no |

`U` es submuestreo uniforme del train (H1), `B` y `GOSS` muestrean dentro de LightGBM (H2) y `H3` optimiza con una
muestra y entrena con todo.

**A tiempo igual** (mismo informe, § Resultados), cada variante gasta el tiempo que le sobra en un ensamble de hasta 10
semillas: contra la ganancia media del control, Ḡ_C = 276,10 M$, quedan arriba U0.5 (+6,05), H3-0.1 (+3,85), H3-0.25
(+2,75), U0.25 y B0.25 (+0,55), y abajo U0.1 y B0.1 (−4,95) y U0.05 (−23,65); es un solo número por variante, sin
intervalo.

Las limitaciones, las conclusiones y las figuras están en el mismo informe y en
[`reporte.html`](experimentos/sampling_1/informe/reporte.html).

## Experimentos

| experimento | qué es | pregunta | estado |
|---|---|---|---|
| [`control`](experimentos/control/) | el control `C` (y su réplica `C-rep`) y las reglas comunes (G, Δ, δ, T, A, N\*, veredictos) | ¿cuál es el punto de comparación de todas las hipótesis? | reporte |
| [`h1`](experimentos/h1/) | submuestreo uniforme del train | ¿cuánto se gana en tiempo y se pierde en ganancia con r ∈ {0,5, 0,25, 0,1, 0,05}? | [informe](experimentos/h1/informe/informe.md): ni confirmada ni refutada |
| [`h2`](experimentos/h2/) | bagging y GOSS | ¿alcanza con submuestrear dentro de LightGBM? | [informe](experimentos/h2/informe/informe.md): refutada |
| [`h3`](experimentos/h3/) | optimizar con muestra y entrenar completo | ¿se puede optimizar rápido y entrenar con todo? (reusa los estudios de `h1`) | [informe](experimentos/h3/informe/informe.md): confirmada |
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
  variante y no cambia el veredicto de `h3`. Sigue las convenciones del repo; falta volver a correr sus pasos 07 y 08,
  que hace `incorporar-aportes`.
- **Luis** ([`experimentos/Experimentos h3 y h4/`](experimentos/Experimentos%20h3%20y%20h4/resumen_completo_de_experimentos.md))
  preguntó **si las H3 le ganan al control con 50 semillas finales** y probó muestras de búsqueda que conservan todas
  las bajas (lo que pasa a ser H4). Por ahora es un script de Colab con su resumen, fuera del método: rutas de Drive,
  hiperparámetros escritos a mano, sin ledger, y elige estrategias mirando 201910, que la consigna reserva para la
  comparación. `incorporar-aportes` lo porta a `experimentos/sampling_1/exploratorios/`, reconstruye lo que no tiene
  código y lo replica con el protocolo del repo.

## Qué sigue

Dos cambios, en este orden, con sus planes en `openspec/changes/`:

1. [`h3-semillas-optuna`](openspec/changes/h3-semillas-optuna/proposal.md): 8 réplicas de la optimización para `C`,
   `H3-0.25`, `H3-0.1` y dos variantes nuevas (`H3-0.05` y `H3R-0.1`, que reescala `min_data_in_leaf`). Separa dos
   explicaciones de la ventaja de H3: que la muestra chica lleva a hiperparámetros más regularizados, o que la única
   optimización del control cayó en una configuración mala. Suma una comparación limpia en dos bloques: lo que siguió
   el protocolo y los exploratorios.
2. [`incorporar-aportes`](openspec/changes/incorporar-aportes/proposal.md): replica los aportes de Martín y Luis y crea
   el experimento `h4` (muestras informadas por clase, que conservan todas las bajas). El grupo queda con cuatro
   hipótesis.

Cada uno actualiza las secciones de resultados, experimentos, aportes y qué sigue de este README.

## Estructura

- `comun/`: datos (panel con lags y deltas), baseline, ganancia, ledger, registro de variantes (`variantes.py`),
  muestreo, métodos, `correr.py`, `consolidar.py`, `reporte.py` y registro de tokens. Lo usan todos los experimentos;
  un cambio acá se anuncia en el commit.
- `experimentos/<nombre>/`: un experimento por carpeta. `sampling_1` además tiene `src/` y `scripts/` propios (las
  listas de las fases de las VMs).
- `plantilla/`: la estructura vacía de un experimento.
- `docs/`: [`metodo.md`](docs/metodo.md) (cómo se trabaja) y [`revision.md`](docs/revision.md) (listas de revisión).
- `scripts/`: `vm.sh`, `lanzar_fase.sh`, `etapa.sh`, `etapas.sh`, `separar_ledger.py` y los scripts del cambio
  `renombrar-brazos` (`renombrar_columna.py` y otros), para cualquier experimento o cambio.
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
se hicieron con el commit del tag `corridas-v1`:

```bash
scripts/lanzar_fase.sh <N>             # lanza experimentos/sampling_1/scripts/faseN.txt y vuelve enseguida
scripts/vm.sh <lista-de-configuraciones>
```

`vm.sh` crea la VM, copia el repo, instala dependencias, lanza las corridas con `nohup`, sube los `ledger/` de cada
experimento al bucket y borra la VM; `lanzar_fase.sh` lo deja corriendo en segundo plano. El reparto por persona está
en [`experimentos/sampling_1/docs/diseno.md`](experimentos/sampling_1/docs/diseno.md) § Reparto y fases, y la operación
paso a paso en [`experimentos/sampling_1/docs/operacion.md`](experimentos/sampling_1/docs/operacion.md).
