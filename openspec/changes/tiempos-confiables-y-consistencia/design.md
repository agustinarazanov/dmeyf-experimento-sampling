# Design

## Context

Lo que muestra el ledger de la ronda 201903–201908, revisado el 13-nov y verificado por la revisión en sesión limpia del
mismo día:

- **Dentro de una VM la máquina mide bien.** Las 3.619 filas de `resultados.csv` corrieron en la misma CPU (Intel Xeon @
  2.60GHz, `n2-highmem-8`), con `load_avg` de 8,72 o menos con 8 hilos, o sea un trabajo por VM. El mismo final, con los
  mismos hiperparámetros y otra semilla, tarda lo mismo con un coeficiente de variación del 1,8 al 6,1 % en las
  variantes sin réplicas (mediana de 2,4 % en las 121 celdas de variante y réplica).
- **Entre VMs hay una sola medición.** `C-rep` repite los 20 finales de la réplica 0 del control en otra VM: 47,0 s
  contra 48,9 s de media (4 %). El ledger guarda el tipo de máquina, no la instancia. Cada réplica corrió en su propia VM.
- **Optuna es la fuente del ruido grande.** T(C) por réplica: 682, 773, 797 (réplica 0), 915, 1.089, 1.097, 1.116 y
  1.264 s; mediana 1.002 s. El final del control va de 37 a 70 s según el `num_leaves` elegido (90 a 875), y
  `tiempo_optimizacion_s` va de 644 a 1.194 s según los trials que recorre TPE. Los trials usan 100 iteraciones fijas,
  sin early stopping.
- **A se calcula con dos referencias.** `comun/ledger.py:209-210` calcula `aceleracion` contra el T_C de la réplica 0,
  y `comun/reporte.py`, en `fila_bloque_a`, la reemplaza por `T_c` mediana solo cuando hay réplicas. Por eso A(U0.5) da
  2,25 con la réplica 0, 2,83 con la mediana y entre 1,93 y 3,57 según la réplica del control.
- **T no incluye la preparación de datos** (`tiempo_preparacion_s`): 240 s en `C` réplica 0, que arma el panel, y unos
  7,5 s en las demás.
- **Las hipótesis no comparten grilla** (tabla de la propuesta). Hoy solo hay dos cruces entre H1 y H4, y ninguno es un
  contraste directo: son dos Δ contra el control.
  - tasa 0,5 en búsqueda y final: `U0.5` (Δ réplica 0 −1,38 M$ [−3,99; 1,24], T 354 s, una réplica) y `H4O-0.5`
    (Δ con réplicas −1,33 M$ [−4,27; 1,60], T 434 s).
  - tasa 0,1 solo en la búsqueda: `H3-0.1` (+1,71 M$ [−1,07; 4,49]) y `H4U-0.1` (−8,02 M$ [−11,52; −4,53]), que
    conserva las bajas sin peso. Los IC no se tocan.
- **La receta con bajas tiene más filas que la muestra al azar de la misma tasa**, además de llevar peso. Con 506.871
  filas y 5.312 bajas (1,05 %):

  | tasa | filas al azar | filas con bajas | cociente |
  |---|---|---|---|
  | 0,5 | 253.436 | 256.092 | 1,010 |
  | 0,25 | 126.718 | 130.702 | 1,031 |
  | 0,1 | 50.687 | 55.468 | 1,094 |
  | 0,05 | 25.344 | 30.390 | 1,199 |

- **Los pares entre variantes se calculan dentro de un solo experimento.** `comun/ledger.py:replicas` arma los pares con
  los finales que `consolidar` carga para un experimento, y saltea sin avisar el par al que le falta un lado
  (`ledger.py:316-318` y `334-336`).
- **Dueño de las réplicas `U{r}@k`.** Hoy son de `h3` (`comun/variantes.py`: `dueno_estudio`, `dueno_variante` e
  `implicitas`), y `h3` depende de `h1` por los estudios de la réplica 0.
- **`scripts/vm.sh` no trae los CSV de la raíz de cada ledger** (los excluye en las tres sincronizaciones) y sincroniza
  con el bucket sin borrar: lo que está en el bucket vuelve al repo.
- **Cuota.** El proyecto del curso (`proj-uba-261012163242176`) tiene `CPUS_ALL_REGIONS` = 32, o sea 4 VMs a la vez, y
  `N2_CPUS` = 100 en la región (consulta con `gcloud` del 13-nov). Las fases 6 y 7 se lanzaron de a 4. En el período de
  prueba no se puede pedir aumento ([cuotas de Compute Engine](https://docs.cloud.google.com/compute/resource-usage),
  [período de prueba](https://docs.cloud.google.com/free/docs/free-cloud-features)). La cuenta tiene otro proyecto con la
  misma cuota, pero los scripts no lo pueden usar tal como están: `.env` pisa el `PROYECTO` del entorno, `vm.sh` tiene
  fija la cuenta de servicio del proyecto del curso y la imagen es de la cátedra (`machinae`).
- **Versiones sin fijar.** `requirements.txt` no fija versiones y cada VM instala al arrancar; ni el ledger ni nada
  guarda la versión de LightGBM con que corrió cada fase.
- **Qué mide la duración de un trial** (`duracion_s`, `correr.py:216-229`): el entrenamiento y la predicción de 201908,
  con el `Dataset` armado una vez antes de los trials. El mejor trial de `C` (el 31 de 40) tardó 27,15 s. Los `.db` de
  `C@1…7` están solo en el bucket.
- **El reporte de `h4` no encuentra hoy los estudios `U0.05@k` y `U0.25@k`**, que están en el ledger de `h3`: para
  `H4F-0.05` y `H4F-0.25` muestra T y A de la réplica 0 (`reporte.py:172-189`, `505-509` y `616`). El reporte de
  `sampling_1` lee todos los ledgers y no tiene el problema.
- **El texto de los informes** tiene las inconsistencias que lista la propuesta.

Restricciones:
- 201910 se usa solo para comparar.
- Las reglas pre-registradas no se reescriben: se agregan secciones nuevas con fecha.
- Un cambio en `comun/` se anuncia en el commit.
- Las corridas las hace la VM, lanzada a pedido. El crédito no es una restricción (Agustina, 13-nov); la cuota sí.
- La ventana del final es 201903–201908 (confirmada el 13-nov) y la ronda tiene 20 semillas finales.
- **"Siempre OP" (Zulip 211718)**: buscar sobre una muestra y entrenar el final con otra receta es la hipótesis de H3, de
  `H4F` y de las nuevas `H3-0.5` y `H4P`. Agustina decidió el 13-nov que ese apartamiento vale porque es parte del
  experimento: se declara con su id en los informes, como hasta ahora, y no se le pregunta al tutor.
- **En paralelo con `sitio-legible`, en una rama** (decisión de Agustina, 13-nov). `sitio-legible` se aplica en `main`;
  este cambio, en la rama `tiempos-confiables`, en un worktree aparte, para que las dos sesiones no compartan carpeta.
  - **En la rama van los grupos 1, 2 y 5** (predicciones, código de corridas y corridas). Tocan sobre todo archivos que
    `sitio-legible` no toca: `comun/metodos.py`, `comun/correr.py`, `comun/ledger.py`, `comun/consolidar.py`, `scripts/`
    y los ledgers. Las VMs reciben el código de la carpeta desde la que se lanzan (`git archive HEAD`), así que corren
    el de la rama sin que haga falta unirla antes.
  - **Los grupos 3, 4 y 6 esperan** (reporte e informes): `sitio-legible` reorganiza `comun/reporte.py` y funde los
    documentos en un README por experimento. Empiezan cuando `sitio-legible` esté archivado y la rama unida a `main`.
  - **Conflictos esperados al unir:** `comun/variantes.py` y `tests/test_variantes.py` (los dos cambios los tocan),
    `cargar_replicas` en `comun/reporte.py`, y las secciones nuevas de `docs/hipotesis.md` y `docs/diseno.md`, que pasan
    al README de cada experimento. Las rutas que nombra este cambio (`informe.md`, `tabla_resultados.md`, `guion.md`,
    `docs/hipotesis.md`, las figuras) son las de hoy y se actualizan al unir. Desde 2b.3 este documento las conserva
    como estaban; la equivalencia con las rutas nuevas está en `proposal.md` (último párrafo) y en
    `sampling_1/docs/rutas.md`, y las tareas de los grupos 3, 4 y 6 ya usan las nuevas.
  - **El bucket es uno solo.** La mudanza de D10 lo cambia para las dos ramas; `sitio-legible` no lanza VMs ni
    sincroniza ledgers, así que no la deshace. Si alguien lanza una VM desde `main` antes de unir, los estudios vuelven
    a `h3`: no se lanza nada desde `main` hasta la unión.
- **Las páginas que se publican van en voz impersonal**: `sitio-legible` hace fallar la construcción del sitio si una
  página publicada nombra al tutor. En el informe, la pregunta se cita por su id de Zulip.

## Goals / Non-Goals

**Goals:**
- Una sola definición de A en todo el bloque A, con su intervalo.
- Una medición que separe la aceleración que da el tamaño de los datos de la que da la elección de Optuna, y otra que
  mida el ruido entre VMs, para responder "medir tiempos de forma confiable".
- Una grilla común: las mismas cuatro tasas y 8 réplicas en cada forma de muestrear, para que cualquier par de celdas se
  pueda comparar.
- Que lo que no se corrió quede dicho en el informe antes de que lo pregunten.
- Informes coherentes con las tablas generadas.
- Que el informe conjunto responda la pregunta del tutor sobre el diálogo entre H1 y H4, primero con lo que ya hay y
  después con la grilla completa.

**Non-Goals:**
- Volver a correr lo que ya está corrido ni cambiar la definición de T.
- Llevar a la grilla las variantes que son cruces o extensiones: `H4F-*`, `H4H-0.1`, `H4U-0.1`, `H3R-*`, `H3L-*`,
  `H3K-0.1`. Quedan como están y la tabla de cobertura las lista aparte.
- Una comparación a igual cantidad de filas entre la muestra al azar y la receta con bajas. Se comparan a igual tasa de
  CONTINUA y se informa la cantidad de filas de cada lado (D12).
- Otro mes de test. Sigue siendo 201910, ya mirado.
- Corregir por comparaciones múltiples. Se declaran los contrastes principales, como hasta ahora.
- Pedir más cuota, crear proyectos nuevos o usar el segundo proyecto de la cuenta.
- `Experimentos guion.md` en la raíz.
- Borradores o mensajes de Zulip: no se guardan en el repo y ninguna sesión los escribe ni los manda.
- Tocar `ledger/apareado.csv`. Su columna `aceleracion` queda como está, con la réplica 0, porque es el par por semilla
  de la réplica 0. El reporte calcula A desde los estudios.

## Decisions

### Tiempos

**D1. A = mediana(T_C) / T_v en el reporte, no en el ledger.** `reporte.py` calcula la mediana de T_C una sola vez, sobre
todas las réplicas del control, y la usa en todas las filas. Hoy `tiempo_igual_replicas` la calcula por variante, sobre
las réplicas que tiene en común con el control (`reporte.py:518`): con réplicas incompletas la referencia cambiaría de
una fila a otra, y eso se corrige. La alternativa era cambiar `ledger.py`, pero eso reescribe `apareado.csv` de todas las
hipótesis y mezcla la regla de tiempo con el apareamiento por semilla. Se descartó. Como A × T_v debe dar la misma T_C
en todas las filas, un test de `pytest` lo verifica.

**D2. Intervalo de A.** Bootstrap por percentiles (2,5 y 97,5) del cociente de medianas: se remuestrean con reposición
las réplicas del control y, por separado, las de la variante, 10.000 veces y con semilla fija.
- **Por qué no el mínimo y el máximo de T_C(k) / T_v(k):** aparear por k es arbitrario. Que la semilla k de TPE sea la
  misma no relaciona las trayectorias de dos estudios con datos distintos, y con otro emparejamiento el rango cambia.
- **Qué mide:** la variación entre réplicas, que junta la de Optuna y la de la VM, porque cada réplica corrió en su
  propia VM. El reporte lo dice así; la calibración (D6) dice cuánto es de la VM.
- **Límites, que el reporte declara en la nota:** con 8 réplicas la mediana remuestreada toma pocos valores y el
  intervalo queda cerca del segundo y el séptimo valor de cada lado, así que una réplica rara lo mueve. La revisión lo
  simuló con tiempos como los del control y cubrió el 96 %. Remuestrear por separado supone que los dos lados son
  independientes; en las fases 5 a 7 la réplica k del control y la de la variante compartían VM, y eso lo hace
  conservador.
- **La fila del control** no lleva intervalo: su A es 1 por definición.
- **Sin réplicas en la variante** solo se remuestrea el control: es un piso de la incertidumbre de A y el reporte lo
  dice. Después de D9 ninguna variante de la grilla queda en este caso; la regla se conserva para `C-rep` y para
  variantes futuras.
- **El tiempo igual con réplicas sigue apareado por k**, y no es una inconsistencia: ahí el ensamble de la réplica k se
  compara contra la ganancia del control de esa misma réplica, así que el par tiene sentido. La nota lo dice.
- Va en una columna nueva al final de la tabla del bloque A, para no correr las columnas que leen los verificadores.

**D3. El tiempo igual de las filas sin réplicas no cambia.** El bootstrap de clientes y el K de tiempo igual de la
réplica 0 siguen usando T_C de la réplica 0, porque se aparean con el Δ de la réplica 0. La nota del bloque lo dice. La
alternativa, la mediana, mezclaría la referencia de tiempo de 8 réplicas con la ganancia de una.

**D4. Medición a hiperparámetros fijos.**
- **Script:** `experimentos/sampling_1/scripts/tiempos_hp_fijos.py`, que importa solo de `comun/`. En la VM se lanza con
  una línea `@ experimentos.sampling_1.scripts.tiempos_hp_fijos` en su lista: `vm.sh` ya acepta líneas `@ módulo`.
- **Celdas:** los 8 juegos de hiperparámetros del control (`C`, `C@1…7`), por 3 repeticiones, por:
  - muestra al azar, r ∈ {1; 0,5; 0,25; 0,1; 0,05} (la de H1): 120 mediciones;
  - receta de H4 (bajas + f de CONTINUA con peso 1/f), f ∈ {0,5; 0,25; 0,1; 0,05}: 96 mediciones.
- **Cada medición** reproduce un trial: muestra con `comun/muestreo`, semilla 1000 + repetición, `Dataset` con los
  parámetros de dataset del control, `lgb.train` con `PARAMS_FIJOS` + hiperparámetros y predicción de 201908.
- **Qué se cronometra:** tres tiempos por separado, el armado del `Dataset`, el entrenamiento y la predicción de 201908.
  El tiempo de la medición es entrenamiento más predicción, que es lo mismo que guarda Optuna como duración de un trial
  (el `Dataset` queda fuera del reloj). Así la medición se puede comparar con los trials ya corridos.
- **Salida:** un archivo por medición en `experimentos/sampling_1/ledger/tiempos/hp_fijos/` (216 archivos), con la
  cantidad de filas, el nombre de la instancia y las versiones de LightGBM, numpy y Optuna. Si la VM se relanza, el
  script saltea las mediciones que ya tienen archivo. Una subcarpeta viaja con `vm.sh` como `corridas/`; un CSV en la
  raíz del ledger no vuelve de la VM. Un consolidador local arma `experimentos/sampling_1/ledger/tiempos_hp_fijos.csv`.
- **La VM de la medición también extrae las anclas** (D6): lee de los `.db` de `C` y `C@1…7`, que `vm.sh` baja del
  bucket, la duración del mejor trial de cada uno y la deja en `tiempos/anclas_trials.csv`. Así el consolidador local no
  necesita los `.db`.
- **Duración estimada:** un trial del control dura de 16 a 30 s, así que las 216 mediciones llevan menos de 2 h. Va en
  una VM propia.
- **El orden se aleatoriza** con una semilla fija, para que una deriva de la VM no se confunda con r.
- **Por qué hiperparámetros del control y no los de cada variante:** así el tamaño y la receta son lo único que cambia.
  Los A del bloque A ya miden el otro efecto, el de la elección de Optuna.

**D5. Predicción de la medición, a pre-registrar antes de lanzar la VM.** Propuesta, que Agustina confirma o ajusta:
- **Aceleración a hiperparámetros fijos A_fijo(r):** mediana de T(1)/T(r) entre juegos de hiperparámetros. Predicción:
  A_fijo(0,5) ∈ [1,6; 2,4] y A_fijo(0,05) < 10, porque la predicción de 201908 no se achica con r.
- **Receta de H4 contra muestra al azar a la misma tasa:** el cociente de tiempos queda entre 0,9 y 1,1 veces el
  cociente de filas de la tabla del Context (o sea, hasta 1,32 en 0,05): el tiempo sigue a las filas y el peso no lo
  cambia.
- **Ruido dentro de la máquina:** CV entre repeticiones de la misma celda, con mediana ≤ 5 %.
- **Se confirma** cada parte si se cumple. Es exploratoria: no cambia veredictos, solo dice cuánto del A del bloque A es
  tamaño de datos y cuánto es Optuna.

**D6. Calibración por máquina.**
- **Qué:** al empezar y al terminar la lista de cada VM de la fase 8, `tiempos_hp_fijos.py --calibracion` corre:
  - el trial de calibración: hiperparámetros de `C` réplica 0, r = 1, la misma semilla que el trial original, 2
    repeticiones, cronometrado como en D4;
  - un final viejo: `C` réplica 0 con la primera semilla final, cronometrado como lo hace el corredor para un final
    (`Dataset`, entrenamiento y predicción de 201910, sin la carga de datos) y sin escribir en el ledger de `control`.

  Lo llama `scripts/vm.sh` antes y después de la lista. Después de la calibración del final hace falta una subida más al
  bucket antes de dar la lista por terminada: si no, ese archivo se pierde con la VM.
- **Salida:** un archivo por lista y momento, `experimentos/sampling_1/ledger/tiempos/calibracion_<lista>_<momento>.csv`,
  con instancia, repetición, tiempos, CPU, carga, commit y versiones de LightGBM, numpy y Optuna. Así varias VMs no se
  pisan al subir. El consolidador arma `experimentos/sampling_1/ledger/calibracion.csv`.
- **Versiones fijas en la fase 8:** `requirements.txt` pasa a fijar las versiones exactas (las que instala una VM de
  prueba), para que todas las VMs de la fase corran lo mismo. Las versiones de las fases 1 a 7 no se conocen, y el
  informe lo dice.
- **La lista identifica la máquina** de cada fila del ledger de la fase, sin agregar columnas al ledger, porque una lista
  corre en una sola VM. Si una lista se relanza en otra VM, la calibración del relanzamiento lleva otro nombre de
  instancia y las filas se separan por fecha; la bitácora anota el relanzamiento.
- **Ancla con las fases anteriores, sin corridas extra:**
  - el trial de calibración es el mejor trial del estudio `C` (27,15 s en la VM de la fase 1); lo mismo los mejores
    trials de `C@1…7`, que la medición de D4 repite. Las duraciones salen de `tiempos/anclas_trials.csv` (D4);
  - el final viejo se compara con el tiempo de esa misma corrida en el ledger de la fase 7 y con `C-rep`.

  Cada ancla es una sola medición vieja, sin repeticiones; el informe lo dice.
- **Qué se informa:** CV entre VMs (entre las medias de cada VM), cociente fin/inicio por VM y cociente de cada VM
  contra las dos anclas.
- **Las VMs corren en horarios distintos** (D15), así que el CV entre VMs junta la VM y la hora. El informe lo dice.
- **Predicción:** CV entre VMs ≤ 5 %, cociente fin/inicio en [0,9; 1,1] y cociente contra las anclas en [0,9; 1,1], en
  todas. Si alguna VM queda fuera, el informe lo dice y marca sus filas; no se descartan corridas después de ver la
  ganancia.
- **Alternativa descartada:** una columna `instancia` en `resultados.csv`. Cambia el esquema del ledger de todas las
  hipótesis para un dato que la lista ya da.

**D7. Búsqueda, final y preparación por separado.** La sección de tiempos del reporte muestra por variante la mediana de
`tiempo_optimizacion_s`, la mediana del tiempo del final y la fracción de T que es búsqueda. Muestra también la mediana
de `tiempo_preparacion_s`, con la nota de que no entra en T porque es igual para todas las variantes. No cambia T ni la
tabla del bloque A.

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
- **Lo que hay que tocar en `comun/metodos.py` y `comun/correr.py`:**
  - `metodo_optimizacion` manda a `uniforme` todo método de H3 o H4 sin estudio propio: `clase-peso` tiene que ir a
    `fast-retrain-opt`, con un test;
  - `pesos(metodo, datos)` no recibe la tasa: cambia su firma y sus dos llamadas (`correr.py:217` y `293`);
  - `fast-retrain` y `fast-retrain-opt` comparten la función `fast_retrain`, con la fracción fija: se separan, para que
    `H4F-*` siga en 0,5 aunque su tasa sea 0,05 o 0,25;
  - `validar` rechaza `fast-retrain-opt` con tasa distinta de 0,5: pasa a aceptar las cuatro.
- **Lo que no cambia** (verificado en la revisión): los nombres nuevos no chocan con el registro, y `F0.5` conserva su
  `hash_muestra`.
- **Por qué `H4P` y no extender `H4U` a las cuatro tasas:** `H4U` no lleva peso, así que cambia dos cosas a la vez (qué
  filas y qué proporción ve Optuna). La muestra de búsqueda de `H4P-0.1` es la misma que la de `H4U-0.1` (misma función
  y misma semilla), así que ese par aísla el peso y pone a prueba la explicación que el informe de H4 dejó sin probar.
- **`GOSS`** no tiene tasa y no entra en la grilla. Sigue siendo descriptivo, pero recibe réplicas (D9).

**D9. 8 réplicas en todo el bloque A.** Pasan a `replicas=True`: `U0.5`, `U0.25`, `U0.1`, `U0.05`, `B0.5`, `B0.25`,
`B0.1`, `B0.05` y `GOSS`. El veredicto con réplicas reemplaza al de la réplica 0, igual que en H3. `C-rep` queda con
una réplica: es la repetición del control, no una variante.

**D10. Los estudios `U{r}@k` pasan a ser de `h1`.**
- **Por qué:** con réplicas, los finales de `U{r}` en la réplica k leen `U{r}@k`. Si esos estudios siguen en `h3`, `h1`
  depende de `h3` y `h3` de `h1`: un ciclo, que `python -m comun.variantes --verificar` rechaza. La otra salida, dejar
  los finales de las réplicas de `U*` en el ledger de `h3` (lo que hace hoy `dueno_variante`), parte cada variante de H1
  en dos ledgers y `replicas.csv` de `h1` no las vería. La revisión confirmó el ciclo y no encontró una salida más simple.
- **Qué cambia en el código:**
  - `comun/variantes.py`: `dueno_estudio`, `dueno_variante` e `implicitas` dejan de mandar a `h3` las réplicas de `h1`;
  - `comun/reporte.py`: `cargar_replicas` lee los estudios del dueño de cada estudio, no solo de `control` y del
    experimento del reporte. Sin eso, el reporte de `h3` pierde los tiempos de las réplicas y vuelve a la réplica 0;
  - tests que afirman el dueño viejo: `tests/test_variantes.py:108` y `tests/test_replicas.py:14-15`.
- **Qué cambia en los documentos:** `## Dependencias` de `h3/docs/diseno.md` (todos los `U{r}` son de `h1`) y de
  `h4/docs/diseno.md` (deja de depender de `h3`; si no, `--verificar` falla por declarar de más).
- **Qué se mueve:** los 21 estudios `U0.25@k`, `U0.1@k` y `U0.05@k`, de `h3/ledger` a `h1/ledger`: sus hp, sus filas
  de `corridas/` y las de `estudios.csv`, sin cambiar ids ni contenido. **También en el bucket**: `vm.sh` sincroniza sin
  borrar, así que si quedan en el bucket vuelven a `h3` con la primera VM y los estudios quedan duplicados.
- **Cómo se mueve en el bucket**, que es parte de este cambio y lo corre la sesión de código (tarea 2.1), no una persona
  a mano:
  1. verificar que no hay ninguna VM viva en el proyecto: una VM que sincroniza a mitad de la mudanza devuelve los
     archivos a `h3`;
  2. copia de respaldo de `experimentos/h1/ledger/` y `experimentos/h3/ledger/` del bucket a
     `$BUCKET/respaldo/2026-11-mover-U/`, que `vm.sh` no sincroniza, y listado de los archivos a mover en la bitácora;
  3. copiar cada archivo a su carpeta nueva de `h1` y verificar que el tamaño y el hash (crc32c) coinciden con el
     original;
  4. recién entonces borrar el original de `h3`;
  5. verificar el resultado: ningún `U*@k` en `h3/` del bucket, los 21 estudios en `h1/` con el mismo crc32c que el
     respaldo, y el resto del bucket igual al árbol de trabajo del repo comparado con los mismos filtros que usa `vm.sh`
     (sin `exploracion/`, `sesiones/` ni los CSV de la raíz).

  El script tiene `--en-seco`, que imprime los pasos sin tocar nada, y se puede volver a correr si se corta. El commit
  del repo y la mudanza del bucket van juntos, sin lanzar ninguna VM en el medio.
- **Vuelta atrás:** `--deshacer` restaura `h1` y `h3` del bucket desde el respaldo, y el commit propio se revierte con
  `git revert`. El respaldo se borra al archivar el cambio.
- **Invariante:** antes y después de mover, dan las mismas tablas `python -m comun.consolidar` de `h3` y `h4` y
  `python -m comun.reporte` de `h3` y `sampling_1`, salvo que los estudios cambian de archivo. Hay dos diferencias
  esperadas y ninguna más:
  - `h1` gana exactamente las 21 filas de optimización en `resultados.csv` y `estudios.csv`;
  - el reporte de `h4` pasa a mostrar T y A con réplicas en `H4F-0.05` y `H4F-0.25` (hoy muestra los de la réplica 0,
    como dice el Context). Se anota en la bitácora con los valores de antes y de después.
- **Riesgo:** es el único paso que toca filas ya corridas. Va en un commit propio y antes de cualquier corrida nueva.

**D11. Tabla de cobertura.** `reporte.py` la arma del registro: una fila por (cómo, dónde), una columna por tasa, y en
cada celda la variante y sus réplicas. Una celda sin variante dice "no se corrió" y el motivo, que sale de una lista
declarada junto al registro. Debajo, las variantes fuera de la grilla, con una línea que dice qué cruzan. Para eso cada
variante del registro declara su fila de la grilla (o que está fuera). Va en el reporte de `sampling_1`, en
`tabla_resultados.md` y, copiada, en el informe conjunto.

**D12. Comparaciones directas.** Se agregan al registro (`PARES_APAREADOS` y `PARES_WELCH`) antes de correr, y cada par
declara qué decisión aísla. La tabla "Diferencias entre variantes" muestra esa columna, las filas de entrenamiento de
cada lado y marca los principales.

| qué aísla | par (a − b) | tasas | IC | experimentos |
|---|---|---|---|---|
| conservar las bajas, búsqueda y final (**principal**) | `H4O-{r}` − `U{r}` | 4 | Welch, sin aparear | h4 y h1 |
| conservar las bajas, solo búsqueda | `H4P-{r}` − `H3-{r}` | 4 | Welch, sin aparear | h4 y h3 |
| muestrear también el final, al azar | `U{r}` − `H3-{r}` | 4 | t, apareado (comparten estudio) | h1 y h3 |
| muestrear también el final, con bajas | `H4O-{r}` − `H4P-{r}` | 4 | t, apareado (comparten estudio) | h4 |
| el peso en la búsqueda | `H4P-0.1` − `H4U-0.1` | 1 | Welch, sin aparear | h4 |

- **Los pares entre experimentos se calculan en `sampling_1`.** `replicas.csv` es de cada experimento y solo con sus
  variantes; calcular `U − H3` en `h1` volvería a crear el ciclo de D10. El agregador arma
  `experimentos/sampling_1/ledger/pares.csv` desde los `resultados.csv` de todos los dueños, con la misma cuenta que usa
  `ledger.replicas`. Los pares de un solo experimento siguen en su `replicas.csv`.
- **Quién lo arma:** `python -m comun.consolidar` sin `--experimento` lo escribe al final, después de consolidar a todos
  los dueños, y `--experimento sampling_1` lo arma solo. Hoy `consolidar` y `reporte` nunca pasan por `sampling_1` como
  dueño de un ledger.
- **Un par declarado al que le falta un lado sale como pendiente**, con el nombre de la variante que falta.
  `ledger.replicas` hoy lo saltea en silencio: el "pendiente" lo pone la función nueva, y un test falla si un par
  declarado no aparece.
- **Réplicas incompletas:** una réplica entra en un par solo si tiene las 20 semillas en los dos lados. El par se calcula
  con las réplicas completas y dice cuántas son.
- **Los pares "conservar las bajas" no aíslan una sola cosa.** La receta con bajas cambia qué filas quedan, suma entre
  un 1 % y un 20 % de filas (tabla del Context) y lleva peso. Se comparan a igual tasa de CONTINUA, que es lo que
  pregunta el tutor, y la tabla muestra las filas de cada lado. El informe lo declara.
- **El par del peso sí aísla una cosa:** `H4P-0.1` y `H4U-0.1` buscan sobre la misma muestra.
- **Etiquetas:** las de `ledger._veredicto_par`: *mejora* si la cota inferior del IC es > 0, *empeora* si la superior es
  < 0, *no cambia* en otro caso.
- H2 no entra en los pares: `bagging_fraction` sale del espacio de Optuna en `B*`, y la comparación con `U*` es
  descriptiva (`h2/docs/hipotesis.md`). La tabla de cobertura la muestra al lado y el informe dice por qué.

**D13. Predicciones de la grilla, a pre-registrar antes de correr.** Propuesta, que Agustina confirma o ajusta. Las
reglas de veredicto son las comunes (`control/docs/hipotesis.md`), con Δ con réplicas, δ de la ronda y N* = 3.300; A es
la de D1. Las de diferencias usan las etiquetas de D12.

- **`h1/docs/hipotesis.md` § Réplicas de H1.** Con réplicas, `U0.5` *no pierde* y A ≥ 2; `U0.25`, `U0.1` y `U0.05`
  *pierden*. Si `U0.5` sale *indeterminado* o con A < 2, deja la lista de "vale la pena" y se informa así.
- **`h2/docs/hipotesis.md` § Réplicas de H2 y `B0.05`.** Con réplicas, `B0.5` y `B0.25` *no pierden* con A < 2; `B0.1` y
  `B0.05` *pierden*. O sea, ninguna `B` "vale la pena". Con la regla de D1, `B0.1` ya tiene A = 2,31 en la réplica 0 y
  `B0.25`, 1,54. `GOSS` se informa sin regla, como hasta ahora.
- **`h3/docs/hipotesis.md` § `H3-0.5`.** *No pierde* y A ≥ 2.
- **`h4/docs/hipotesis.md` § Grilla común.**
  - `H4O-{r}` − `U{r}` (principal): *no cambia* en 0,5 y *mejora* en 0,1 y 0,05, donde la muestra al azar se queda con
    unas 531 y 266 de las 5.312 bajas. En 0,25 no hay predicción firme y se informa.
  - `H4O-{r}` contra `C`: *no pierde* en 0,5 (ya medido) y en 0,25; *pierde* en 0,05. En 0,1 se informa.
  - `H4P-{r}` contra `C`: *no pierde* en las cuatro tasas, y `H4P-{r}` − `H3-{r}`: *no cambia* en las cuatro.
  - `H4P-0.1` − `H4U-0.1`: *mejora*. Si *no cambia*, la explicación del informe de H4 (la proporción distorsionada en la
    búsqueda) queda sin sostén y se dice.
- **Origen de estas variantes.** Se agregan después de ver 201910 en todas las celdas vecinas. Cada `docs/hipotesis.md`
  lo declara y los informes lo listan entre las limitaciones ("Ideas que vienen de mirar el test"). Entran todas juntas
  y ninguna se elige ni se descarta por su resultado.
- **Comparaciones múltiples.** Este cambio suma, sin corrección, los 17 contrastes de D12, 9 veredictos nuevos contra
  `C` (las variantes nuevas) y 8 veredictos que se vuelven a decidir con réplicas (`U*`, `B*` menos `B0.05`, y `GOSS`).
  Los principales son los cuatro `H4O-{r}` − `U{r}`; el resto es secundario.

**D14. Regla para variantes nuevas.** `docs/metodo.md` § Agregar una hipótesis suma un paso: la variante declara su fila
de la grilla, corre las cuatro tasas con 8 réplicas y declara sus pares directos, o declara el hueco con su motivo en la
lista de D11 antes de correr. `docs/revision.md` § 2 suma el ítem que lo verifica.

### Corridas

**D15. Fase 8, en cuatro carriles.** Una corrida a la vez por VM, como siempre: el paralelismo es entre VMs y no cambia
la medición de tiempos.

- **17 listas, cada una en su VM:** `fase8_rk_a` (h1, h3 y h4) y `fase8_rk_b` (h2), para k = 0…7, más
  `fase8_medicion` (D4). Dentro de cada lista, cada estudio va antes que sus finales. Ninguna lista `_a` lee nada de una
  `_b`: `U0.5@k` y `F*@k` van en `_a`, y `B*@k` y `GOSS@k` en `_b`.
- **Qué llevan entre las dos listas de la réplica k ≥ 1:**
  - estudios: `U0.5@k`, `F0.25@k`, `F0.1@k`, `F0.05@k`, `B0.5@k`, `B0.25@k`, `B0.1@k`, `B0.05@k`, `GOSS@k`;
  - finales (20 semillas): `U0.5`, `U0.25`, `U0.1`, `U0.05`, `H3-0.5`, `H4O-0.25`, `H4O-0.1`, `H4O-0.05`, `H4P-0.5`,
    `H4P-0.25`, `H4P-0.1`, `H4P-0.05`, `B0.5`, `B0.25`, `B0.1`, `B0.05`, `GOSS`.
- **Réplica 0:** estudios `F0.25`, `F0.1`, `F0.05` y `B0.05`; finales de `H3-0.5`, `H4O-0.25`, `H4O-0.1`, `H4O-0.05`,
  las cuatro `H4P` y `B0.05`. El resto de la réplica 0 ya existe.
- **Totales:** 67 estudios y 2.560 finales.
- **Cuatro carriles en el proyecto del curso.** La cuota da para 4 VMs a la vez. Las 17 listas se reparten en cuatro
  carriles; cada carril lanza sus listas una tras otra, cada una en su VM, sin intervención. Un script
  (`scripts/lanzar_carriles.sh`) lo hace, con `--en-seco`. En cada carril van primero `fase8_medicion` y las `_a`, y al
  final las `_b`.
- **No se usa el segundo proyecto de la cuenta.** Sumaría otras 4 VMs, pero pide cambiar cómo los scripts leen el
  proyecto, la cuenta de servicio y los permisos sobre el bucket y la imagen (Context).
- **La cuota queda justa:** 4 VMs de 8 vCPU son los 32 del límite. Cualquier otra VM encendida en el proyecto hace que
  `lanzar_fase.sh` no lance. Se verifica antes de empezar.
- **Un solo commit para toda la fase.** El id de cada corrida lleva el commit, así que si se corrige algo entre listas
  un relanzamiento vuelve a correr todo. Un arreglo a mitad de la fase se anota en la bitácora y las listas que faltan
  se relanzan con el commit nuevo, sin mezclar commits dentro de una misma variante.
- **Estimación**, con los tiempos de `estudios.csv` y `resultados.csv` de la ronda, verificada por la revisión: una
  lista `_a` lleva unos 12 min de estudios y 1,4 h de finales; una `_b`, unos 57 min de estudios y 1 h de finales, más
  media hora de arranque por VM. En total unas 36 h de VM, que en cuatro carriles son unas 12 h de reloj. A US$ 0,52/h
  más un 15 % de disco (`sampling_1/docs/diseno.md` § Estimación de horas y costo), unos US$ 22.
- **Los estudios ya corridos** (`U0.25@k`, `U0.1@k`, `U0.05@k`, `F0.5@k`) no se repiten: la VM los lee del bucket, ya
  movidos a `h1` (D10).

### Texto y respuesta

**D16. Correcciones de texto.**
- **Se editan a mano solo frases.** Los números salen de `tabla_resultados.md` regenerada.
- **Las frases se buscan por su texto.** Los números de línea de las tareas son orientativos: algunos están corridos.
- **`decisiones.md`:** se agrega al principio un aviso de que es de las fases 1–4 (Ḡ_C = 276,10 M$, δ = 5,52 M$, 10
  semillas) y de que lo vigente está en el informe conjunto. El informe conjunto deja de enlazarlo para los números.
  Reescribirlo duplicaría el informe.
- **Tabla de rondas:** se corrige en `scripts/comparar_rondas.py`, sacando la fila `C | pendiente` (el control no es
  una variante contra sí mismo). `H4O-0.5` sigue afuera, como decidió `final-con-julio-agosto` (tarea 4.1), y la tabla
  agrega una nota que dice que solo existe en la ronda nueva. Las variantes de este cambio tampoco entran: no existen en
  la ronda anterior.
- **Las correcciones que no dependen de números nuevos** se hacen en paralelo con el código (tarea 4.1); las que citan
  A o veredictos, después de regenerar.

**D17. La respuesta a la pregunta del tutor queda en el informe conjunto.** El repo no guarda borradores de mensajes
de Zulip y ninguna sesión escribe ni manda mensajes: los escribe y los manda Agustina, leyendo el informe (decisión del
13-nov). Lo que hace este cambio es que el informe tenga la respuesta, en dos tiempos. La sección va en voz
impersonal y cita la pregunta por su id (Zulip 212124), sin nombrar al tutor.
- **Primero**, apenas cierra la revisión de hipótesis (1.5): una sección «Diálogo entre H1 y H4» en el informe conjunto,
  con lo que ya se sabe.
  - "Mismos cortes" se contesta en sus dos lecturas. Como tasas de muestreo: H4 no repite la grilla de H1, y hoy se
    cruzan en dos puntos (los del Context). Como corte de envíos: N* = 3.300 es el mismo para todas las variantes.
  - "¿Se verá alguna diferencia?": todavía no hay un contraste directo entre H1 y H4. En 0,5, los Δ contra el control
    de `U0.5` y `H4O-0.5` son casi iguales, con IC que se superponen y una sola réplica de `U0.5`. En 0,1 solo en la
    búsqueda, `H4U-0.1` pierde y `H3-0.1` no, con IC que no se tocan; ahí `H4U-0.1` tiene además un 9 % más de filas y
    no lleva peso. El contraste directo es parte de lo que se corre (D8, D12), con su predicción (D13).
  - Tiempos: cómo se midieron, qué se sabe del ruido y qué se va a medir (D4, D6).
- **Después**, al cerrar el informe: la misma sección con la tabla de cobertura, los cuatro contrastes principales con
  las filas de cada lado y la sección de tiempos.
- **Además, en el informe conjunto:**
  - el undersampling es H4, que conserva todas las bajas y recorta CONTINUA; H1 no toca la proporción;
  - el corte N* vale tal cual para las variantes que entrenan el final con la proporción original (`U*`, `B*`, H3,
    `H4H`, `H4U`, `H4P`); en `H4F` y `H4O` el peso 1/f de CONTINUA restituye la proporción ponderada del train, así que
    el orden de los primeros 3.300 es comparable;
  - por qué H2 no entra en los pares directos.

## Risks / Trade-offs

- **Cambiar A después de ver los resultados** se puede leer como elegir la regla. Mitigación: la regla vieja era
  inconsistente entre filas, y no al revés. Se anota en la bitácora con el motivo, la tabla muestra A con su intervalo,
  y ningún veredicto de "vale la pena" cambia por D1 (`U0.5` pasa de 2,25 a 2,83; `B0.25` queda en 1,54 y `B0.5` en
  0,99).
- **Las réplicas pueden cambiar veredictos de H1 y H2.** Es lo que se quiere saber. Las reglas quedan escritas antes.
- **Variantes nuevas con el test ya mirado.** No hay otro mes. Mitigación: entran todas las celdas de la grilla, con
  predicción y regla antes de correr, y cuatro contrastes principales fijados (D13).
- **Más contrastes sin corrección** (D13). Alguno puede salir significativo por azar. Se declara y las conclusiones se
  apoyan en los principales.
- **Los pares principales mezclan filas, cantidad y peso** (D12). Es la comparación que pide el tutor, a igual tasa. Se
  declara, y la medición a hiperparámetros fijos da el efecto en tiempo de las filas de más.
- **Mover estudios de `h3` a `h1`** toca filas ya corridas, en el repo y en el bucket. Mitigación: commit propio,
  invariante de consolidado y de reportes idénticos (D10), chequeo de que no vuelven a `h3` después de la fase (5.3) y
  revisión de código antes de correr.
- **El alcance creció**: el cambio pasó de una VM de 2–3 h a 17 VMs y 9 variantes nuevas. Mitigación: la sección del
  informe que responde la pregunta no espera a las corridas (D17), y las correcciones de texto van en paralelo (D16).
- **Cuota.** 17 VMs no entran a la vez: van en cuatro carriles, de noche.
- **VMs en horarios distintos.** Es el mismo tipo de máquina, la misma región, la misma imagen y las mismas versiones;
  la calibración mide si las VMs difieren, con la hora mezclada (D6).
- **Dos cambios en paralelo.** Al unir la rama hay conflictos (Restricciones). Mitigación: en la rama solo van los
  grupos que casi no comparten archivos con `sitio-legible`; el invariante de D10 se verifica dentro de la rama, antes
  de unir, y los tests y `--verificar` se vuelven a correr después de unir.
- **Peso 1/f grande en `H4O-0.05` y `H4P-0.05`** (20 en CONTINUA), con `min_data_in_leaf` sin reescalar. Es parte de la
  receta y se declara como limitación, igual que en `H4O-0.5`.
- **Las medianas de tiempo de las celdas viejas** se midieron en otras VMs y fechas que las réplicas nuevas, y la A de
  `U*`, `B*` y `GOSS` va a mezclar las dos épocas. Las anclas de D6 lo miden.
- **Las predicciones de D5, D6 y D13** las propone una sesión que ya vio los resultados de la ronda. Las de tiempos son
  exploratorias y no deciden nada; las de la grilla se declaran como "ideas que vienen de mirar el test".
