# Sampling_1 — velocidad sin tocar la proporción de clases

Experimento de DMEyF 2026, comisión lunes: Agustina Razanov, Martín López y Luis María Laguinge. Tutor: Joaquín I.
Aramendía.

## La pregunta y la respuesta corta

El tutor preguntó (Zulip 208986): **¿vale la pena el tradeoff entre velocidad y pérdida de performance?** Sobre el
baseline oficial de Bolaños (2019, LightGBM con Optuna), medimos cuánto tiempo se ahorra y cuánta ganancia se pierde en
201910 cuando se usan menos filas, sin cambiar la proporción de clases (eso lo estudia Sampling_2).

**Respuesta corta: vale la pena achicar la optimización, no el entrenamiento del modelo final.** Si Optuna busca sobre
el 10% de las filas y el modelo final se entrena con todas (`H3-0.1`), no pierde ganancia contra el control y el proceso
es 7,76 veces más rápido. Se sostiene con 8 réplicas de la optimización, que miden la suerte de Optuna: Δ con réplicas
= 1,71 M$, IC [−1,07; 4,49]. No es una mejora de ganancia: el IC contiene a 0, y una sola optimización puede mostrar
más o menos ventaja según su suerte. Entrenar el final con menos filas sí pierde: al azar desde r = 0,25 y dentro de
LightGBM con `bagging_fraction` = 0,1.

Con la segunda ronda (H4): achicar la búsqueda conservando todas las bajas pierde (`H4H-0.1`, Δ con réplicas = −11,41 M$,
IC [−15,80; −7,03]), pero achicar el final conservando las bajas y la mitad de CONTINUA con peso 2, sobre la búsqueda
del 5 % (`H4F-0.05`), no pierde, es 12,50 veces más rápido y, gastando el tiempo ahorrado en ensamblar, le gana al
control (4,63 M$, IC [0,77; 8,50]).

Todos los números son de la **ronda vigente**: el modelo final entrena con 201903–201908 (Bolaños, Zulip 211210) y se
evalúa en 201910 con 20 semillas; N\* = 3.300 queda fijo. La ronda anterior (final 201903–201906, 10 semillas) se compara
en [`comparacion_rondas.md`](experimentos/sampling_1/informe/comparacion_rondas.md): ningún veredicto cambia de lado. El
veredicto sale de la ganancia; el AUC en 201910 va al lado (ΔAUC) y en varias variantes va en otra dirección.

## Resultados

La comparación está en dos bloques en
[`experimentos/sampling_1/informe/tabla_resultados.md`](experimentos/sampling_1/informe/tabla_resultados.md), que genera
`python -m comun.reporte --experimento sampling_1` desde los ledgers, y comentada en
[`experimentos/sampling_1/informe/informe.md`](experimentos/sampling_1/informe/informe.md) § Resultados:

- **Bloque A, mismo protocolo**: una fila por variante con Δ de la réplica 0, Δ con réplicas (en `C`, las H3 y las H4,
  8 réplicas), ΔAUC, T, A, tiempo igual con intervalo (entre réplicas y por bootstrap de clientes de 201910) y el
  veredicto con su fuente. Las ocho variantes de H3 y las tres de fast-retrain de H4 (`H4F-0.05`, `H4F-0.25` y
  `H4O-0.5`, que reoptimiza sobre el set del final) no pierden con réplicas y valen la pena, y de H1 también U0.5; de
  H2 y de la búsqueda informada de H4 (`H4H-0.1`, `H4U-0.1`, que pierden) ninguna.
- **Bloque B, exploratorios**: los estudios de Martín y de Luis, replicados, con su propio protocolo; sus cifras no se
  comparan una a una con las del bloque A.

Δ es la diferencia de ganancia en 201910 contra el control `C`, al corte N\* = 3.300 envíos; A es cuántas veces más
rápida es la variante que el control (optimización más un modelo final). `U` es submuestreo uniforme del train (H1), `B`
y `GOSS` muestrean dentro de LightGBM (H2), `H3` optimiza con una muestra y entrena con todo (`H3R` y `H3L` reescalan
`min_data_in_leaf`, `H3K` muestrea clientes) y `H4` conserva todas las bajas en la búsqueda (`H4H`, `H4U`) o en el final
(`H4F`, y `H4O` también en la búsqueda). H4 y las extensiones de H3 salen de ideas que se eligieron mirando 201910 y suman más de diez contrastes sin
corrección: las conclusiones se apoyan en `H3-0.1`, `H4H-0.1` y `H4F-0.05`, fijados antes de correr. Las limitaciones,
las conclusiones y las figuras están en el informe y en [`reporte.html`](experimentos/sampling_1/informe/reporte.html).

## Experimentos

| experimento | qué es | pregunta | estado |
|---|---|---|---|
| [`control`](experimentos/control/) | el control `C` (y su réplica `C-rep`) y las reglas comunes (G, Δ, δ, T, A, N\*, veredictos) | ¿cuál es el punto de comparación de todas las hipótesis? | reporte |
| [`h1`](experimentos/h1/) | submuestreo uniforme del train | ¿cuánto se gana en tiempo y se pierde en ganancia con r ∈ {0,5, 0,25, 0,1, 0,05}? | [informe](experimentos/h1/informe/informe.md): ni confirmada ni refutada |
| [`h2`](experimentos/h2/) | bagging y GOSS | ¿alcanza con submuestrear dentro de LightGBM? | [informe](experimentos/h2/informe/informe.md): refutada |
| [`h3`](experimentos/h3/) | optimizar con muestra y entrenar completo | ¿se puede optimizar rápido y entrenar con todo? (la réplica 0 reusa los estudios de `h1`; las réplicas `@k` son suyas) | [informe](experimentos/h3/informe/informe.md): confirmada, también con réplicas; mecanismo sin resolver; extensiones sin cambios contra no reescalar |
| [`h4`](experimentos/h4/) | muestras informadas por clase: todas las bajas en la búsqueda o en el final | ¿conviene que la muestra que acelera conserve todas las bajas? (usa estudios de `h1` y `h3`) | [informe](experimentos/h4/informe/informe.md): búsqueda informada refutada; fast-retrain confirmado con 5 % y 25 %; reoptimizar sobre el set del final no cambia |
| [`sampling_1`](experimentos/sampling_1/) | el experimento conjunto: compara a `h1`–`h4` contra `control`, informe y video | ¿vale la pena el tradeoff velocidad-performance? | [informe](experimentos/sampling_1/informe/informe.md) |

Cada experimento tiene `docs/` (hipótesis, diseño, bitácora), `ledger/` e `informe/`. Declara en `## Dependencias` de su
`docs/diseno.md` de quién lee (`control` como mínimo) y no toca carpetas ni ledgers ajenos. Para agregar una hipótesis
(`h4`, …): [`docs/metodo.md`](docs/metodo.md) § Agregar una hipótesis. Las rutas de `sampling_1` antes de la separación
en carpetas están en [`experimentos/sampling_1/README.md`](experimentos/sampling_1/README.md) § Correspondencia de rutas.

## Aportes de Martín y Luis

- **Martín** ([`experimentos/h3/sensibilidad_muestra/`](experimentos/h3/sensibilidad_muestra/README.md)) preguntó
  **cuánto depende de la muestra la configuración que elige H3**. Repitió la búsqueda de H3 con diez muestras distintas
  y midió en 201910 la ganancia de cada modelo elegido. En 7 de 10 muestras H3 eligió la misma configuración que el
  control, y las otras tres quedan dentro del ruido de una semilla. Es exploratorio, con su propio protocolo: no es una
  variante y no cambia el veredicto de `h3`; aparece en el bloque B de la comparación. **Replicado**: sus pasos 07 y 08
  se volvieron a correr en la VM y las elecciones, los AUC y las ganancias salieron idénticos (README § Reproducción en
  la VM).
- **Luis** ([`experimentos/sampling_1/exploratorios/validacion_50_semillas/`](experimentos/sampling_1/exploratorios/validacion_50_semillas/README.md))
  preguntó **si las H3 le ganan al control con 50 semillas finales** y probó muestras que conservan todas las bajas (lo
  que pasó a ser H4). **Replicado**: su script de Colab se portó al repo, con las piezas sin código reconstruidas y
  marcadas, y se corrió en la VM; su README compara cada número del resumen original con el reproducido. Ordenadas en
  201908, como pide la consigna, ninguna estrategia supera al control. Sus ideas entraron como variantes con réplicas
  (`h4` y las extensiones de `h3`): la búsqueda con negativos difíciles pierde y el fast-retrain se sostiene.

## Qué sigue

[`h3-semillas-optuna`](openspec/changes/archive/2026-11-09-h3-semillas-optuna/proposal.md) sumó 8 réplicas de la optimización y la
comparación en dos bloques; [`incorporar-aportes`](openspec/changes/archive/2026-11-10-incorporar-aportes/proposal.md) replicó los aportes
de Martín y Luis y sumó `h4` y las extensiones de `h3`: el grupo queda con cuatro hipótesis.
[`final-con-julio-agosto`](openspec/changes/final-con-julio-agosto/proposal.md) volvió a correr todos los finales con
201903–201908 y 20 semillas, sumó `H4O-0.5` y el AUC al lado de la ganancia. Lo que falta es otro mes de test, que
separe el ruido de 201910 del efecto de las variantes y que no se haya mirado al elegir H4.

## Ver el sitio localmente

Los informes, reportes, hipótesis, método y bitácoras se leen como sitio en
<https://agustinarazanov.github.io/dmeyf-experimento-sampling/>. Para verlo antes de pushear (hace falta Ruby y
Bundler):

```bash
bundle install
scripts/sitio.sh serve    # construye, verifica los enlaces internos y sirve en http://localhost:4000
```

Sin `serve`, `scripts/sitio.sh` solo construye y verifica. Los `reporte.html` son páginas del sitio: abiertos como
archivo suelto se ven sin estilo.

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
  `verificar_informe_h3.py` comprueban que los números de este README y de los informes de `h3` y `h4` (`--informe`)
  salen de las tablas.
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
