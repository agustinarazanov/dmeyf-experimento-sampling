# Design

## Context

Ver `proposal.md` para la motivación. Lo que condiciona el diseño:

- **Baseline fijo (Bolaños, 28-oct, mensaje 208135)**: solo 2019; train 201903–201906 completo; positivo = BAJA+1 ∪
  BAJA+2; lags y deltas de orden 2; Optuna sobre `num_leaves`, `learning_rate`, `min_data_in_leaf`, `feature_fraction`,
  `bagging_fraction` con `bagging_freq ≥ 1`; resto en defaults de LightGBM (confirmado el 1-nov); validación 201908 por
  AUC; test 201910 solo para la comparación final.
- **Reparto con Sampling_2**: ellos hacen undersampling de CONTINUA. Este experimento no altera la proporción de clases.
- **Tutor**: Joaquín Aramendía pide hipótesis, diseño y "si vale la pena el tradeoff velocidad/performance".
- **Equipo de tres** con laptops distintas: los tiempos solo son comparables en el mismo tipo de VM.
- **Dataset**: `competencia_02_crudo.csv.gz` (201901–202108, ~160.000 clientes por mes, ~155 columnas). El panel 2019
  con lags y deltas 2 ronda 1,9 M filas × ~470 columnas; en float32 unos 3,5 GB, cómodo en 64 GB.
- **Código heredado**: `competencia-2/src/fe_panel.py` genera lags y deltas con DuckDB; `competencia.py` tiene la
  ganancia y las curvas de corte. Se copian las funciones necesarias, no se importa `competencia-2` (repos separados).
- **Presupuesto**: trial de Google Cloud de US$ 300 a 90 días; US$ 75/mes de IA; línea de base de tokens de octubre.
- **Entorno local**: LightGBM del pyenv `facultad` no carga por falta de `libomp`; solo se usa para smoke tests.

## Goals / Non-Goals

**Goals:**
- Responder H1, H2 y H3 con comparaciones apareadas por semilla y curvas tiempo-ganancia, en un video de 10 minutos.
- Que cualquiera de los tres pueda lanzar, consolidar y analizar corridas desde el repo sin ayuda.
- Bajar el contexto promedio por turno de Claude a menos de 100.000 tokens y medirlo.

**Non-Goals:**
- Buscar la mejor ganancia absoluta; el baseline es deliberadamente modesto.
- Generalizar a más meses, más features o al pipeline de la segunda entrega (se cita como trabajo futuro).
- Infraestructura: sin orquestador, sin base de datos, sin MLflow. Scripts, CSV y el bucket.

## Decisions

**D0. Un repo de experimentos, una carpeta por experimento.** Layout:

```
experimento-sampling/
├── comun/            datos.py (crudo → panel 2019 con lags y deltas), baseline.py (meses, target, espacio de
│                     hiperparámetros, defaults), ganancia.py, ledger.py (escritura de filas, consolidación, apareado),
│                     tokens.py (registro por sesión y etapa)
├── experimentos/
│   └── sampling-velocidad/   docs/ (hipotesis, diseno, bitacora, zulip/), src/ (muestreo, correr, consolidar),
│                             scripts/ (vm.sh, graficar.py), ledger/ (corridas/, curvas/, *.csv), informe/
├── plantilla/        la misma estructura vacía, con las plantillas de hipotesis.md, diseno.md y bitacora.md
├── docs/             metodo.md (las etapas y las reglas de tokens) y revision.md (las listas de compuerta)
└── openspec/
```
Cada experimento importa solo de `comun/` y de sí mismo (`python -m experimentos.sampling_velocidad.src.correr` o
un `__main__` dentro de la carpeta; el nombre del paquete usa guion bajo). Alternativa descartada: un repo por
experimento; duplica datos, baseline y ganancia, y la comparación entre experimentos del grupo se vuelve manual.
`comun/` cambia poco y cada cambio se anuncia en el commit.

**D1. Tres hipótesis, una variable cada una, mismo control.**
- H1 `uniforme`: tasa r ∈ {1, 0,5, 0,25, 0,1, 0,05} sobre todas las filas de train, sin estratificar. Optimización por
  tasa (la grilla de hiperparámetros se reoptimiza en cada variante, regla de "familia primaria" de los jueves) y 10
  semillas finales.
- H2 `bagging` y `goss`: `bagging_fraction` fijo en {0,5, 0,25, 0,1} con `bagging_freq = 1`, y `boosting = goss` con
  `top_rate/other_rate` por defecto. **Adaptación del baseline**: `bagging_fraction` sale del conjunto optimizado en
  esta variante porque es la variable experimental; se avisa al tutor. Cada `bagging` se decide contra el control. La
  comparación con `uniforme` es descriptiva, en la curva tiempo-ganancia. `goss` es una variante descriptiva y no decide
  H2. (Revisión de hipótesis, 1-nov.)
- H3 `opt-muestra`: Optuna sobre una muestra uniforme con r ∈ {0,1, 0,25}; con los mejores hiperparámetros se entrena
  el final con r = 1. Se compara con el control (optimizado sobre r = 1) en ganancia y en tiempo total (optimización
  más final). Es la hipótesis con más valor para el pipeline de 15 minutos.
- H4 (`docs/hipotesis.md`): submuestreo informado de CONTINUA y pesos por fila; la corre un integrante por separado con
  el mismo control, corredor y ledger. Descartado: oversampling (sin sentido en boosting tabular).

**D2. Métricas y regla de decisión.** Selección por AUC en 201908 (lo pide el baseline). Comparación en 201910 por
ganancia a envíos fijos (decide) y ganancia máxima de la curva (se reporta). El corte N* lo elige el control en
**201908**, para no usar el test al elegir. Ganancia calculada contra BAJA+2 con los valores de la cátedra. Diferencia
apareada por semilla con media, desvío e intervalo del 95% (t de Student, 10 semillas) y conteo de semillas en que gana
la variante. Regla de no inferioridad con δ = 2% de la ganancia media del control: *no pierde* si la cota inferior del IC
es ≥ −δ, *pierde* si la media es < −δ, *indeterminado* en el resto. El tiempo es el del pipeline completo
(optimización y final) en todas las variantes. Rangos de Optuna y definiciones exactas en `docs/hipotesis.md`.
(Revisión de hipótesis, 1-nov: reemplaza la regla de "un desvío" y el corte en 201910.)

**D3. Un solo punto de entrada por experimento.** Desde la carpeta del experimento, `python -m src.correr --metodo
--tasa --semilla --etapa [--hp hp.json]` (con la raíz del repo en `PYTHONPATH` para ver `comun/`). La etapa
`optimizar` corre Optuna (40 trials, una semilla, AUC en 201908) y guarda el JSON de mejores hiperparámetros; la etapa
`final` entrena con ese JSON y evalúa en 201910. Lo mismo corre en la Mac con `--filas 20000` (smoke) y en la VM.
Alternativa descartada: notebooks por persona; no son reproducibles ni comparables.

**D4. Tiempos y máquinas.** `time.perf_counter` alrededor de preparación, optimización y `lgb.train`; `num_threads = 8`
fijo; `resource.getrusage` para memoria máxima; tipo de máquina leído del metadata server de GCE (o `local`). El análisis
filtra por tipo de máquina antes de comparar tiempos. Todas las corridas reales van en `n2-highmem-8` spot desde el
template del curso; spot porque cada corrida es corta y el ledger es incremental.

**D5. Datos.** `DATOS_DIR` configurable (por defecto `~/datos/experimentos-dmeyf`). El crudo se baja del GCS del
curso una vez por máquina; el panel 2019 con lags y deltas se construye con DuckDB (SQL copiado de `fe_panel.py`) y se
guarda en Parquet. Meses 201901 y 201902 se usan solo como historia para los lags.

**D6. Ledger como archivos, dentro del experimento.** Una fila por corrida en `ledger/corridas/<id>.csv` del experimento (id = método, tasa, semilla, etapa,
commit corto). `python -m src.consolidar` arma `ledger/resultados.csv` y `ledger/apareado.csv`. Las curvas van en
`ledger/curvas/<id>.csv`. Sin base de datos: tres personas, cientos de filas, git alcanza.

**D7. Reparto de la grilla.** Fase 1 (control y H3, barata y decisiva): una persona. Fase 2 (H1): dos personas, tasas
repartidas. Fase 3 (H2): las mismas dos personas, para equilibrar la carga. H3 comparte sus estudios de Optuna con
H1 en r = 0,25 y 0,1, porque optimizan lo mismo. Todas las fases corren un único commit con tag. El reparto queda en
`docs/diseno.md` y se marca en la bitácora. (Etapa de diseño, 1-nov.)

**D8. Método de trabajo con tokens.** Una sesión de Claude Code por etapa y por experimento, arrancando de los
artefactos de `openspec/`, de `docs/metodo.md` y de la bitácora del experimento, `/clear` al cerrar. Modelo por etapa: diseño y revisiones con Opus; código y análisis mecánico
con Sonnet; nunca pegar salidas largas en el chat, siempre a archivo y leer `head`/`tail`. Subagentes solo para
búsquedas. `comun/tokens.py` lee `~/.claude/projects/<repo>/*.jsonl` y escribe el `ledger/tokens.csv` del experimento que la
bitácora declara para cada sesión.

**D9. Revisión por etapa, no por grupo.** Cinco compuertas, cada una con su lista en `docs/revision.md` del repo
(compartida por todos los experimentos):
hipótesis (¿falsable, cuantitativa, una variable?), diseño (¿grilla completa, control apareado, tiempos comparables?),
código (smoke test pasa, determinismo verificado, ledger completo), resultados (sanity: filas de train coinciden con la
tasa, control reproduce el baseline, máquinas homogéneas; estadística apareada), informe (cada conclusión cita una tabla
del ledger). Revisa una sesión limpia con la lista, y un integrante distinto del que ejecutó la etapa cuando sea posible.
Alternativa descartada: revisar al final; los errores de diseño descubiertos tarde obligan a recorrer todo.

**D10. Las etapas que no necesitan a un humano corren headless.** `scripts/etapa.sh <grupo> <modelo>` lanza
`claude -p` con el modelo de la etapa, `--permission-mode acceptEdits`, `--max-budget-usd` y `--output-format json` para
aplicar solo ese grupo de `tasks.md`, y después una segunda sesión limpia con Opus que revisa con `docs/revision.md` y
cierra la bitácora. El costo de cada sesión sale del JSON (`total_cost_usd`) a `ledger/sesiones/costos.csv`, que es la
medida más directa para `registro-tokens`. La sesión solo puede correr los comandos de una lista explícita (`--allowedTools`): `openspec`, Python, git sin
push, lectura de archivos, y las VMs únicamente a través de `scripts/vm.sh` del experimento, que crea, corre, sube y
borra; `gcloud` solo para listar. Al terminar verifica que no quedó ninguna VM encendida. Si la etapa necesita a una
persona (respuesta del tutor, decisión de diseño, reparto entre personas), escribe `BLOQUEADO` en
`ledger/sesiones/bloqueo.txt` y el script corta. `scripts/etapas.sh` encadena las etapas pendientes hasta el primer
bloqueo, eligiendo el modelo por el encabezado del grupo. Alternativas consideradas: un Workflow de Claude Code (lo mismo con `agent()` por etapa, pero exige
la sesión abierta y gasta por la cuenta de esa sesión) y una sesión orquestadora que lanza subagentes (paga coordinación
en tokens). El script de shell es gratis de coordinar, corre desde cualquier terminal y queda versionado.

**D11. Reporte visual: un HTML estático generado desde el ledger.** `src/reporte.py` lee `resultados.csv`,
`apareado.csv`, las curvas y los documentos de hipótesis y diseño, y escribe `informe/reporte.html` con las figuras
embebidas (SVG o PNG en base64, matplotlib con la paleta de `v_estilo` de `competencia-2`, validada con la skill
`dataviz`). Secciones: introducción (pregunta, hipótesis, control, regla), tabla de todas las variantes, gráfico tiempo
contra ganancia, una sección por hipótesis con bandas de curvas y veredicto, comparación a tiempo igual, y al pie la
fecha, el commit y el estado del ledger. Las variantes sin datos se muestran como pendientes. Alternativas descartadas: un
notebook (no se abre sin entorno y mezcla código con lectura) y un dashboard con servidor (nada que operar). Se puede
publicar tal cual como artefacto para el tutor; el markdown de `docs/hipotesis.md` se convierte con una función mínima,
sin dependencia nueva.

**D12. El ledger guarda las predicciones de cada corrida final; la comparación a tiempo igual sale de una fase 4.**
La hipótesis decía que el ensamble de K semillas salía "del mismo ledger, sin corridas nuevas", pero el ledger guardaba
curvas de ganancia y no predicciones, y una curva no se promedia con otra. Decisión (2-nov): `src/correr.py` escribe por
cada final `ledger/predicciones/<id>.parquet` (`numero_de_cliente`, `prob` float32, `es_baja2` int8, en el orden del mes
de test) y la fila lo referencia en `predicciones_201910`; los parquet no van a git (ya los excluye `.gitignore`), viven
en el bucket y `vm.sh` los trae con el resto del ledger. Una fase 4 vuelve a correr solo los finales de las 12 variantes
(11 + `C-rep`) con los JSON de hiperparámetros ya guardados, en una sola VM; por la clave sin commit (spec
`ledger-resultados`) esas filas reemplazan a las de las fases 1 a 3, así que además todos los tiempos finales quedan
medidos en la misma máquina. Las ganancias no cambian (LightGBM es determinista con la misma semilla, hilos y tipo de
máquina: `C-rep` lo mostró con Δ = 0), así que los veredictos a datos iguales no se recalculan por otra razón que la
trazabilidad. Alternativas descartadas: aceptar la comparación como pendiente (deja sin responder la pregunta del
tutor sobre qué se hace con el tiempo ahorrado) y usar el máximo de G entre K semillas (sesgo de selección, cambia la
definición). Costo: ≈ 1 h de VM spot.

## Risks / Trade-offs

- [Spot muere a mitad de una optimización] → cada trial de Optuna se persiste en SQLite en el bucket; la corrida se
  reanuda con el mismo estudio.
- [Tiempos ruidosos por otras cargas en la VM] → una corrida por VM a la vez; se registra `load average` al inicio.
- [El control no reproduce "el baseline" de otro grupo] → no hay número oficial; se documenta el nuestro con 10 semillas
  y se compara solo contra él.
- [H2 cambia el conjunto optimizado del baseline] → se avisa al tutor antes de correr; es una adaptación explícita.
- [Ganancia con 10 semillas no separa diferencias chicas] → se reporta el intervalo y se aceptan empates como resultado
  válido ("no pierde" es una conclusión).
- [Fuga de 201910 a la selección] → el corredor solo evalúa 201910 en la etapa `final` y la etapa `optimizar` no lo carga.
- [El trial de Google Cloud vence o la cuota es de 8 vCPU] → verificar fecha de alta y cuota antes de la fase 1; si hace
  falta, pasar a cuenta paga con alerta de presupuesto.
- [Una sesión headless se desboca o hace algo irreversible] → tope en dólares por sesión, lista cerrada de comandos
  permitidos (sin push, sin `gcloud create/delete` directo), VMs solo por `vm.sh` con verificación final de que no quedó
  ninguna, y la revisión limpia después de cada grupo.
- [Una VM queda encendida tras un fallo de `vm.sh`] → la verificación final con `gcloud compute instances list` y la
  alerta de presupuesto del trial; una VM spot de 64 GB olvidada cuesta ~US$ 4,5 por día.
- [Método de tokens que no se mide] → `tokens.py` corre al cerrar cada etapa y el número va a la bitácora.

## Migration Plan

Repo nuevo: no hay migración. Publicación en GitHub al cerrar la compuerta de diseño, con `.gitignore` para datos y
`ledger/curvas/` grandes si hiciera falta.

## Open Questions

- Si el tutor prefiere que H2 mantenga `bagging_fraction` optimizado y compare solo GOSS, se reduce esa variante sin
  tocar H1 ni H3.
- Valores exactos de ganancia por acierto y por error para 2019: se toman los de la cátedra del año; si cambian, el
  análisis se recalcula desde las curvas guardadas.
