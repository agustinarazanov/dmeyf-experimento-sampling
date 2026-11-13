# Design

## Context

Lo que muestra el ledger de la ronda 201903–201908, revisado el 13-nov:

- **Dentro de una VM la máquina mide bien.** Las 3.619 filas de `resultados.csv` corrieron en la misma CPU (Intel Xeon @
  2.60GHz, `n2-highmem-8`), con `load_avg` de 8,7 o menos con 8 hilos, o sea un trabajo por VM. El mismo final, con los
  mismos hiperparámetros y otra semilla, tarda lo mismo con un coeficiente de variación del 2 al 6 % (variantes de una
  sola réplica, 20 semillas cada una). La tarea 1.1 recalcula ese rango del ledger antes de citarlo.
- **Entre VMs hay una sola medición.** `C-rep` repite los 20 finales de la réplica 0 del control en otra VM: 47,0 s
  contra 48,9 s de media (4 %). El ledger guarda el tipo de máquina, no la instancia.
- **Optuna es la fuente del ruido grande.** T(C) por réplica: 682, 773, 797 (réplica 0), 915, 1.089, 1.097, 1.116 y
  1.264 s; mediana 1.002 s. El final del control va de 38 a 69 s según el `num_leaves` elegido (90 a 875), y
  `tiempo_optimizacion_s` va de 644 a 1.194 s según los trials que recorre TPE.
- **A se calcula con dos referencias.** `comun/ledger.py:209-210` calcula `aceleracion` contra el T_C de la réplica 0,
  y `comun/reporte.py`, en `fila_bloque_a`, la reemplaza por `T_c` mediana solo cuando hay réplicas. Por eso A(U0.5) da
  2,25 con la réplica 0, 2,83 con la mediana y entre 1,93 y 3,57 según la réplica del control.
- **Las hipótesis no comparten grilla** (tabla de la propuesta). Hoy solo hay dos cruces entre H1 y H4:
  - tasa 0,5 en búsqueda y final: `U0.5` (Δ réplica 0 −1,38 M$ [−3,99; 1,24], T 354 s, una réplica) contra `H4O-0.5`
    (Δ con réplicas −1,33 M$ [−4,27; 1,60], T 434 s). Las bajas son 5.312 de 506.871 filas (1,05 %), así que las dos
    muestras tienen casi las mismas filas: 253.436 contra 256.092.
  - tasa 0,1 solo en la búsqueda: `H3-0.1` (+1,71 M$ [−1,07; 4,49]) contra `H4U-0.1` (−8,02 M$ [−11,52; −4,53]), que
    conserva las bajas sin peso y busca sobre una muestra con 9,6 % de bajas.
- **El texto de los informes** tiene las inconsistencias que lista la propuesta. Se confirmaron con `sed -n` sobre cada
  línea citada.
- **Dueño de las réplicas `U{r}@k`.** Hoy son de `h3` (`comun/variantes.py`, `dueno_estudio` y `dueno_variante`), y
  `h3` depende de `h1` por los estudios de la réplica 0.

Restricciones:
- 201910 se usa solo para comparar.
- Las reglas pre-registradas no se reescriben: se agregan secciones nuevas con fecha.
- Un cambio en `comun/` se anuncia en el commit.
- Las corridas las hace la VM, lanzada a pedido. El crédito no es una restricción (Agustina, 13-nov).
- La ventana del final es 201903–201908 (confirmada el 13-nov) y la ronda tiene 20 semillas finales.

## Goals / Non-Goals

**Goals:**
- Una sola definición de A en todo el bloque A, con su rango.
- Una medición que separe la aceleración que da el tamaño de los datos de la que da la elección de Optuna, y otra que
  mida el ruido entre VMs, para responder "medir tiempos de forma confiable".
- Una grilla común: las mismas cuatro tasas y 8 réplicas en cada forma de muestrear, para que cualquier par de celdas se
  pueda comparar.
- Que lo que no se corrió quede dicho en el informe antes de que lo pregunten.
- Informes coherentes con las tablas generadas.
- Una respuesta al tutor sobre el diálogo entre H1 y H4, primero con lo que ya hay y después con la grilla completa.

**Non-Goals:**
- Volver a correr lo que ya está corrido ni cambiar la definición de T.
- Llevar a la grilla las variantes que son cruces o extensiones: `H4F-*`, `H4H-0.1`, `H4U-0.1`, `H3R-*`, `H3L-*`,
  `H3K-0.1`. Quedan como están y la tabla de cobertura las lista aparte.
- Otro mes de test. Sigue siendo 201910, ya mirado.
- Corregir por comparaciones múltiples. Se declaran los contrastes principales, como hasta ahora.
- `Experimentos guion.md` en la raíz.
- Tocar `ledger/apareado.csv`. Su columna `aceleracion` queda como está, con la réplica 0, porque es el par por semilla
  de la réplica 0. El reporte calcula A desde los estudios.

## Decisions

### Tiempos

**D1. A = mediana(T_C) / T_v en el reporte, no en el ledger.** `reporte.py` calcula T_C mediana una vez, con la función
que ya usa `tiempo_igual_replicas`, y la usa en todas las filas. La alternativa era cambiar `ledger.py`, pero eso
reescribe `apareado.csv` de todas las hipótesis y mezcla la regla de tiempo con el apareamiento por semilla. Se descartó.
Como A × T_v debe dar la misma T_C en todas las filas, un test de `pytest` lo verifica.

**D2. Rango de A.**
- Con réplicas en la variante: [min_k, max_k] de T_C(k) / T_v(k), apareado por k. Las réplicas comparten la semilla de
  TPE y del sorteo, igual que el IC de tiempo igual.
- Sin réplicas: [min_k T_C(k) / T_v, max_k T_C(k) / T_v]. Este rango solo mueve el control: la búsqueda de la variante
  es una sola, así que es un piso de su incertidumbre y el reporte lo dice. Después de D9 ninguna variante de la grilla
  queda en este caso; la regla se conserva para `C-rep` y para variantes futuras.

Se eligió el rango, y no un IC, porque con 8 réplicas un IC t de un cociente es frágil, y el rango se explica en una
línea. Va en una columna nueva al final de la tabla de `tabla_resultados.md`, para no correr las columnas que leen
los verificadores.

**D3. El tiempo igual de las filas sin réplicas no cambia.** El bootstrap de clientes y el K de tiempo igual de la
réplica 0 siguen usando T_C de la réplica 0, porque se aparean con el Δ de la réplica 0. La nota del bloque lo dice. La
alternativa, la mediana, mezclaría la referencia de tiempo de 8 réplicas con la ganancia de una.

**D4. Medición a hiperparámetros fijos.**
- **Script:** `experimentos/sampling_1/scripts/tiempos_hp_fijos.py`, que importa solo de `comun/`.
- **Celdas:** los 8 juegos de hiperparámetros del control (`C`, `C@1…7`), por 3 repeticiones, por:
  - muestra al azar, r ∈ {1; 0,5; 0,25; 0,1; 0,05} (la de H1): 120 mediciones;
  - receta de H4 (bajas + f de CONTINUA con peso 1/f), f ∈ {0,5; 0,25; 0,1; 0,05}: 96 mediciones.
- **Cada medición** reproduce un trial: muestra con `comun/muestreo`, semilla 1000 + repetición, `Dataset` con los
  parámetros de dataset del control, `lgb.train` con `PARAMS_FIJOS` + hiperparámetros y predicción de 201908.
- **Salida:** `experimentos/sampling_1/ledger/tiempos_hp_fijos.csv`, con el nombre de la instancia en cada fila.
- **Duración estimada:** según `estudios.csv`, un trial del control dura de 16 a 30 s, así que las 216 mediciones
  llevan menos de 2 h. Va en una VM propia.
- **El orden se aleatoriza** con una semilla fija, para que una deriva de la VM no se confunda con r.
- **Por qué hiperparámetros del control y no los de cada variante:** así el tamaño y la receta son lo único que cambia.
  Los A del bloque A ya miden el otro efecto, el de la elección de Optuna.

**D5. Predicción de la medición, a pre-registrar en `control/docs/hipotesis.md` antes de lanzar la VM.** Propuesta, que
Agustina confirma o ajusta:
- **Aceleración a hiperparámetros fijos A_fijo(r):** mediana de T(1)/T(r) entre juegos de hiperparámetros. Predicción:
  A_fijo(0,5) ∈ [1,6; 2,4] y A_fijo(0,05) < 10, porque el `Dataset` de validación y la predicción de 201908 no se
  achican con r.
- **Receta de H4 contra muestra al azar a la misma tasa:** el cociente de tiempos queda en [0,9; 1,2] en las cuatro
  tasas, porque la receta agrega a lo sumo un 1 % de filas.
- **Ruido dentro de la máquina:** CV entre repeticiones de la misma celda, con mediana ≤ 5 %.
- **Se confirma** cada parte si se cumple. Es exploratoria: no cambia veredictos, solo dice cuánto del A del bloque A es
  tamaño de datos y cuánto es Optuna.

**D6. Calibración por máquina.**
- **Qué:** el mismo entrenamiento fijo (hiperparámetros de `C` réplica 0, r = 1, 2 repeticiones, como un trial) al
  empezar y al terminar la lista de cada VM de la fase 8. Lo corre `tiempos_hp_fijos.py --calibracion`, llamado por
  `scripts/vm.sh` antes y después de la lista.
- **Salida:** `experimentos/sampling_1/ledger/calibracion.csv`: lista, instancia, momento (inicio o fin), repetición,
  tiempos, CPU, carga y commit. Una lista corre en una sola VM, así que la lista identifica la máquina de cada fila del
  ledger de la fase sin agregar columnas al ledger.
- **Qué se informa:** CV entre VMs (entre las medias de cada VM) y cociente fin/inicio por VM.
- **Predicción, en `control/docs/hipotesis.md`:** CV entre VMs ≤ 5 % y cociente fin/inicio en [0,9; 1,1] en todas. Si
  alguna VM queda fuera, el informe lo dice y marca sus filas; no se descartan corridas después de ver la ganancia.
- **Alternativa descartada:** una columna `instancia` en `resultados.csv`. Cambia el esquema del ledger de todas las
  hipótesis para un dato que la lista ya da.

**D7. Búsqueda y final por separado.** La sección de tiempos del reporte muestra por variante la mediana de
`tiempo_optimizacion_s`, la mediana del tiempo del final y la fracción de T que es búsqueda. No cambia T ni la tabla
del bloque A.

### Grilla común

**D8. Las cinco filas y sus tasas.** Tasas {0,5; 0,25; 0,1; 0,05} en todas. 20 semillas finales, final 201903–201908,
N* = 3.300 y δ de la ronda (5,65 M$).

| fila | variantes | búsqueda | final | estudio | qué falta correr |
|---|---|---|---|---|---|
| al azar, búsqueda y final | `U{r}` (h1) | r al azar | r al azar | `U{r}` | réplicas 1…7 |
| al azar, solo búsqueda | `H3-{r}` (h3) | r al azar | completo | `U{r}` | `H3-0.5` entera |
| con bajas y peso, búsqueda y final | `H4O-{f}` (h4) | bajas + f de CONTINUA, peso 1/f | lo mismo | `F{f}` | f = 0,25; 0,1; 0,05 |
| con bajas y peso, solo búsqueda | `H4P-{f}` (h4) | bajas + f de CONTINUA, peso 1/f | completo, sin peso | `F{f}` | las cuatro |
| dentro de LightGBM | `B{f}` (h2) | `bagging_fraction = f` | lo mismo | `B{f}` | `B0.05` y réplicas 1…7 |

- **`H4O-{f}`** generaliza `fast-retrain-opt`: hoy la fracción está fija en 0,5 (`FRACCION_FAST_RETRAIN`) y pasa a ser la
  tasa de la variante. `H4F-*` sigue con 0,5. Los hiperparámetros no se reescalan, como en `H4O-0.5`.
- **`H4P-{f}`** es un método nuevo (`clase-peso`): optimiza con el método de `H4O-{f}` y comparte su estudio `F{f}`,
  como H3 comparte `U{r}` con H1; el final es el de `opt-muestra`. El tiempo del estudio entra en T de las dos.
- **Por qué `H4P` y no extender `H4U` a las cuatro tasas:** `H4U` no lleva peso, así que cambia dos cosas a la vez (qué
  filas y qué proporción ve Optuna). Con peso, la única diferencia con H3 es qué filas se conservan. `H4P-0.1` contra
  `H4U-0.1` aísla el peso y pone a prueba la explicación que el informe de H4 dejó sin probar.
- **`GOSS`** no tiene tasa y no entra en la grilla. Sigue siendo descriptivo, pero recibe réplicas (D9).

**D9. 8 réplicas en todo el bloque A.** Pasan a `replicas=True`: `U0.5`, `U0.25`, `U0.1`, `U0.05`, `B0.5`, `B0.25`,
`B0.1`, `B0.05` y `GOSS`. El veredicto con réplicas reemplaza al de la réplica 0, igual que en H3. `C-rep` queda con
una réplica: es la repetición del control, no una variante.

**D10. Los estudios `U{r}@k` pasan a ser de `h1`.**
- **Por qué:** con réplicas, los finales de `U{r}` en la réplica k leen `U{r}@k`. Si esos estudios siguen en `h3`, `h1`
  depende de `h3` y `h3` de `h1`: un ciclo, que `python -m comun.variantes --verificar` rechaza. La otra salida, dejar
  los finales de las réplicas de `U*` en el ledger de `h3` (lo que hace hoy `dueno_variante`), parte cada variante de H1
  en dos ledgers y `replicas.csv` de `h1` no las vería.
- **Qué cambia:** `dueno_estudio` y `dueno_variante` dejan de mandar a `h3` las réplicas de `h1`. Un script mueve de
  `h3/ledger` a `h1/ledger` los 21 estudios `U0.25@k`, `U0.1@k` y `U0.05@k` (hp, filas de corridas y de `estudios.csv`)
  sin cambiar ids ni contenido. `h3/docs/diseno.md` § Dependencias pasa a decir que todos los `U{r}` son de `h1`.
- **Invariante:** antes y después de mover, `python -m comun.consolidar` de `h3` y `h4` da las mismas tablas, salvo
  que los estudios cambian de archivo. Es el mismo criterio de "Separación sin pérdida del ledger existente".
- **Riesgo:** es el único paso que toca filas ya corridas. Va en un commit propio y antes de cualquier corrida nueva.

**D11. Tabla de cobertura.** `reporte.py` la arma del registro: una fila por (cómo, dónde), una columna por tasa, y en
cada celda la variante y sus réplicas. Una celda sin variante dice "no se corrió" y el motivo, que sale de una lista
declarada junto al registro. Debajo, las variantes fuera de la grilla, con una línea que dice qué cruzan. Para eso cada
variante del registro declara su fila de la grilla (o que está fuera). Va en el reporte de `sampling_1`, en
`tabla_resultados.md` y, copiada, en el informe conjunto.

**D12. Comparaciones directas.** Se agregan al registro (`PARES_APAREADOS` y `PARES_WELCH`) antes de correr, y cada par
declara qué decisión aísla. La tabla "Diferencias entre variantes" muestra esa columna y marca los principales.

| qué aísla | par (a − b) | tasas | IC |
|---|---|---|---|
| conservar las bajas, búsqueda y final (**principal**) | `H4O-{r}` − `U{r}` | 4 | Welch, sin aparear |
| conservar las bajas, solo búsqueda | `H4P-{r}` − `H3-{r}` | 4 | Welch, sin aparear |
| muestrear también el final, al azar | `U{r}` − `H3-{r}` | 4 | t, apareado (comparten estudio) |
| muestrear también el final, con bajas | `H4O-{r}` − `H4P-{r}` | 4 | t, apareado (comparten estudio) |
| el peso en la búsqueda | `H4P-0.1` − `H4U-0.1` | 1 | Welch, sin aparear |

H2 no entra en los pares: `bagging_fraction` sale del espacio de Optuna en `B*`, y la comparación con `U*` es
descriptiva (`h2/docs/hipotesis.md`). La tabla de cobertura la muestra al lado.

**D13. Predicciones de la grilla, a pre-registrar antes de correr.** Propuesta, que Agustina confirma o ajusta. Las
reglas de veredicto son las comunes (`control/docs/hipotesis.md`), con Δ con réplicas, δ de la ronda y N* = 3.300. Las de
diferencias son las de `h4/docs/hipotesis.md` regla 2: *ayuda* si la cota inferior del IC es > 0, *empeora* si la
superior es < 0, *no cambia* en otro caso.

- **`h1/docs/hipotesis.md` § Réplicas de H1.** Con réplicas, `U0.5` *no pierde* y A ≥ 2 con la mediana; `U0.25`, `U0.1`
  y `U0.05` *pierden*. Si `U0.5` sale *indeterminado* o con A < 2, deja la lista de "vale la pena" y se informa así.
- **`h2/docs/hipotesis.md` § Réplicas de H2 y `B0.05`.** Con réplicas, `B0.5` y `B0.25` *no pierden*, `B0.1` y `B0.05`
  *pierden*, y ninguna llega a A ≥ 2. `GOSS` se informa sin regla, como hasta ahora.
- **`h3/docs/hipotesis.md` § `H3-0.5`.** *No pierde*, con A < A(`H3-0.25`).
- **`h4/docs/hipotesis.md` § Grilla común.**
  - `H4O-{r}` − `U{r}` (principal): *no cambia* en 0,5 y *ayuda* en 0,1 y 0,05, donde la muestra al azar se queda con
    unas 531 y 266 de las 5.312 bajas. En 0,25 no hay predicción firme y se informa.
  - `H4O-{r}` contra `C`: *no pierde* en 0,5 (ya medido) y en 0,25; *pierde* en 0,05. En 0,1 se informa.
  - `H4P-{r}` contra `C`: *no pierde* en las cuatro tasas, y `H4P-{r}` − `H3-{r}`: *no cambia* en las cuatro.
  - `H4P-0.1` − `H4U-0.1`: *ayuda*. Si *no cambia*, la explicación del informe de H4 (la proporción distorsionada en la
    búsqueda) queda sin sostén y se dice.
- **Origen de estas variantes.** Se agregan después de ver 201910 en todas las celdas vecinas. Cada `docs/hipotesis.md`
  lo declara y los informes lo listan entre las limitaciones ("Ideas que vienen de mirar el test"). Entran todas juntas
  y ninguna se elige ni se descarta por su resultado.
- **Comparaciones múltiples.** D12 suma 17 contrastes sin corrección. Los principales de este cambio son los cuatro
  `H4O-{r}` − `U{r}`; el resto es secundario.

**D14. Regla para variantes nuevas.** `docs/metodo.md` § Agregar una hipótesis suma un paso: la variante declara su fila
de la grilla, corre las cuatro tasas con 8 réplicas y declara sus pares directos, o declara el hueco con su motivo en la
lista de D11 antes de correr. `docs/revision.md` § 2 suma el ítem que lo verifica.

### Corridas

**D15. Fase 8, en paralelo.** Una corrida a la vez por VM, como siempre: el paralelismo es entre VMs y no cambia la
medición de tiempos.

- **Dos listas por réplica**, cada una en su VM: `fase8_rk_a` (h1, h3 y h4) y `fase8_rk_b` (h2), para k = 0…7. Dentro
  de cada lista, cada estudio va antes que sus finales. Más `fase8_medicion` (D4) en otra VM: 17 VMs, 136 vCPU
  (decisión de Agustina, 13-nov).
- **Qué llevan entre las dos listas de la réplica k ≥ 1** (`_a`: lo de `U`, `H3`, `F`, `H4O` y `H4P`; `_b`: lo de `B` y
  `GOSS`):
  - estudios: `U0.5@k`, `F0.25@k`, `F0.1@k`, `F0.05@k`, `B0.5@k`, `B0.25@k`, `B0.1@k`, `B0.05@k`, `GOSS@k`;
  - finales (20 semillas): `U0.5`, `U0.25`, `U0.1`, `U0.05`, `H3-0.5`, `H4O-0.25`, `H4O-0.1`, `H4O-0.05`, `H4P-0.5`,
    `H4P-0.25`, `H4P-0.1`, `H4P-0.05`, `B0.5`, `B0.25`, `B0.1`, `B0.05`, `GOSS`.
- **Réplica 0:** estudios `F0.25`, `F0.1`, `F0.05` y `B0.05`; finales de `H3-0.5`, `H4O-0.25`, `H4O-0.1`, `H4O-0.05`,
  las cuatro `H4P` y `B0.05`. El resto de la réplica 0 ya existe.
- **Totales:** 67 estudios y 2.560 finales.
- **Estimación**, con los tiempos de `estudios.csv` y `resultados.csv` de la ronda: una lista `_a` lleva unos 12 min
  de estudios y 1,4 h de finales; una `_b`, unos 57 min de estudios y 1 h de finales. Con media hora de arranque, cada VM
  termina en unas 2 a 2,5 h; las de la réplica 0 y la de la medición, antes. En total unas 36 h de VM y unas 2,5 h de
  reloj. A US$ 0,52/h más un 15 % de disco (`sampling_1/docs/diseno.md` § Estimación de horas y costo), unos US$ 22.
- **Si la cuota de vCPU no alcanza para 17 VMs**, `lanzar_fase.sh` no lanza ninguna: se lanzan en dos tandas (primero
  las `_a` y la medición, después las `_b`) o se pide más cuota. El resultado no cambia, solo el reloj.
- **Los estudios ya corridos** (`U0.25@k`, `U0.1@k`, `U0.05@k`, `F0.5@k`) no se repiten: la VM los lee del repo.

### Texto y respuesta

**D16. Correcciones de texto.**
- **Se editan a mano solo frases.** Los números salen de `tabla_resultados.md` regenerada.
- **`decisiones.md`:** se agrega al principio un aviso de que es de las fases 1–4 (Ḡ_C = 276,10 M$, δ = 5,52 M$, 10
  semillas) y de que lo vigente está en el informe conjunto. `informe.md:206` deja de enlazarlo para los números.
  Reescribirlo duplicaría el informe.
- **Tabla de rondas:** se corrige en `scripts/comparar_rondas.py`, sacando la fila `C | pendiente` (el control no es
  una variante contra sí mismo). `H4O-0.5` sigue afuera, como decidió `final-con-julio-agosto` (tarea 4.1), y la tabla
  agrega una nota que dice que solo existe en la ronda nueva. Las variantes de este cambio tampoco entran: no existen en
  la ronda anterior.
- **Las correcciones que no dependen de números nuevos** se hacen en paralelo con el código (tarea 3.1); las que citan
  A o veredictos, después de regenerar.

**D17. Respuesta al tutor, en dos tiempos.** Las dos salen de los documentos y las postea Agustina.
- **Primera**, `experimentos/sampling_1/docs/zulip/02_dialogo_h1_h4.md`, apenas cierra la revisión de hipótesis (1.5):
  - "Mismos cortes" se contesta en sus dos lecturas. Como tasas de muestreo: H4 no repite la grilla de H1, y hoy se
    cruzan en dos puntos (los del Context), con sus números. Como corte de envíos: N* = 3.300 es el mismo para todas las
    variantes.
  - "¿Se verá alguna diferencia?": en 0,5 no se distinguen; en 0,1 solo en la búsqueda, conservar las bajas sin peso
    sale peor. Lo demás no está corrido, y se dice qué se va a correr (D8) y con qué predicción (D13).
  - Tiempos: cómo se midieron, qué se sabe del ruido y qué se va a medir (D4, D6).
- **Segunda**, `03_grilla_y_tiempos.md`, al cerrar el informe: la tabla de cobertura, los cuatro contrastes principales y
  la sección de tiempos.
- **En el informe conjunto:**
  - el undersampling es H4, que conserva todas las bajas y recorta CONTINUA; H1 no toca la proporción;
  - el corte N* vale tal cual para las variantes que entrenan el final con la proporción original (`U*`, `B*`, H3,
    `H4H`, `H4U`, `H4P`); en `H4F` y `H4O` el peso 1/f de CONTINUA restituye la proporción ponderada del train, así que
    el orden de los primeros 3.300 es comparable.

## Risks / Trade-offs

- **Cambiar A después de ver los resultados** se puede leer como elegir la regla. Mitigación: la regla vieja era
  inconsistente entre filas, y no al revés. Se anota en la bitácora con el motivo, la tabla muestra A con el rango, y
  ningún veredicto de "vale la pena" cambia por D1 (U0.5 pasa de 2,25 a 2,83).
- **Las réplicas pueden cambiar veredictos de H1 y H2.** Es lo que se quiere saber. Las reglas quedan escritas antes.
- **Variantes nuevas con el test ya mirado.** No hay otro mes. Mitigación: entran todas las celdas de la grilla, con
  predicción y regla antes de correr, y cuatro contrastes principales fijados (D13).
- **Más contrastes sin corrección.** Con 17 más, alguno puede salir significativo por azar. Se declara y las
  conclusiones se apoyan en los principales.
- **Mover estudios de `h3` a `h1`** toca filas ya corridas. Mitigación: commit propio, invariante de consolidado
  idéntico (D10) y revisión de código antes de correr.
- **El alcance creció**: el cambio pasó de una VM de 2–3 h a 17 VMs y 9 variantes nuevas. Mitigación: la primera
  respuesta al tutor no espera a las corridas (D17), y las correcciones de texto van en paralelo (D16).
- **Peso 1/f grande en `H4O-0.05` y `H4P-0.05`** (20 en CONTINUA), con `min_data_in_leaf` sin reescalar. Es parte de la
  receta y se declara como limitación, igual que en `H4O-0.5`.
- **Las medianas de tiempo de las celdas viejas** se midieron en otras VMs y fechas que las réplicas nuevas. Es la misma
  CPU, y la calibración (D6) mide el ruido entre las VMs de esta fase; para las fases anteriores sigue habiendo solo
  `C-rep`, y el informe lo dice.
- **Las predicciones de D5, D6 y D13** las propone una sesión que ya vio los resultados de la ronda. Las de tiempos son
  exploratorias y no deciden nada; las de la grilla se declaran como "ideas que vienen de mirar el test".
- **Cuota de vCPU.** 17 VMs piden 136 vCPU N2 en la región y en el proyecto; las fases anteriores usaron 64. Se
  verifica antes de lanzar (tarea 5.1).
