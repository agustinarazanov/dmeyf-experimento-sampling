# Design

## Context

Lo que muestra el ledger de la ronda 201903–201908, revisado el 13-nov:

- **La máquina mide bien.** Las 3.619 filas de `resultados.csv` corrieron en la misma CPU (Intel Xeon @ 2.60GHz,
  `n2-highmem-8`), con `load_avg` de 8 o menos con 8 hilos, o sea un trabajo por VM. El mismo final, con los mismos
  hiperparámetros y otra semilla, tarda lo mismo con un coeficiente de variación del 1 al 5 %.
- **Optuna es la fuente del ruido.** T(C) por réplica: 682, 773, 797 (réplica 0), 915, 1.089, 1.097, 1.116 y
  1.264 s; mediana 1.002 s. El final del control va de 38 a 69 s según el `num_leaves` elegido (90 a 875), y
  `tiempo_optimizacion_s` va de 644 a 1.194 s según los trials que recorre TPE.
- **A se calcula con dos referencias.** `comun/ledger.py:209-210` calcula `aceleracion` contra el T_C de la réplica 0,
  y `comun/reporte.py`, en `fila_bloque_a`, la reemplaza por `T_c` mediana solo cuando hay réplicas. Por eso A(U0.5) da
  2,25 con la réplica 0, 2,83 con la mediana y entre 1,93 y 3,57 según la réplica del control.
- **El texto de los informes** tiene las inconsistencias que lista la propuesta. Las confirmé con `sed -n` sobre cada
  línea citada.

Restricciones:
- 201910 se usa solo para comparar.
- Las reglas pre-registradas no se reescriben: se agregan secciones nuevas con fecha.
- Un cambio en `comun/` se anuncia en el commit.
- Las corridas las hace la VM, lanzada a pedido.

## Goals / Non-Goals

**Goals:**
- Una sola definición de A en todo el bloque A, con su rango.
- Una medición que separe la aceleración que da el tamaño de los datos de la que da la elección de Optuna, para
  responder "medir tiempos de forma confiable".
- Réplicas de U0.5, para que su "vale la pena" no dependa de una sola optimización.
- Informes coherentes con las tablas generadas.
- Una respuesta al tutor sobre el undersampling (H4) y el corte N*.

**Non-Goals:**
- Volver a correr la grilla ni cambiar la definición de T.
- Réplicas de `U0.25`, `U0.1`, `U0.05`, `B*` o `GOSS`: pierden por mucho o no aceleran, y el rango de A ya muestra su
  incertidumbre de tiempo.
- `Experimentos guion.md` en la raíz.
- Tocar `ledger/apareado.csv`. Su columna `aceleracion` queda como está, con la réplica 0, porque es el par por semilla
  de la réplica 0. El reporte calcula A desde los estudios.

## Decisions

**D1. A = mediana(T_C) / T_v en el reporte, no en el ledger.** `reporte.py` calcula T_C mediana una vez, con la función
que ya usa `tiempo_igual_replicas`, y la usa en todas las filas. La alternativa era cambiar `ledger.py`, pero eso
reescribe `apareado.csv` de todas las hipótesis y mezcla la regla de tiempo con el apareamiento por semilla. Se descartó.
Como A × T_v debe dar la misma T_C en todas las filas, un test de `pytest` lo verifica.

**D2. Rango de A.**
- Sin réplicas en la variante: [min_k T_C(k) / T_v, max_k T_C(k) / T_v].
- Con réplicas: [min_k, max_k] de T_C(k) / T_v(k), apareado por k. Las réplicas comparten la semilla de TPE y del
  sorteo, igual que el IC de tiempo igual.

Se eligió el rango, y no un IC, porque con 8 réplicas un IC t de un cociente es frágil, y el rango se explica en una
línea. Va en una columna nueva al final de la tabla de `tabla_resultados.md`, para no correr las columnas que leen
los verificadores.

**D3. El tiempo igual de las filas sin réplicas no cambia.** El bootstrap de clientes y el K de tiempo igual de la
réplica 0 siguen usando T_C de la réplica 0, porque se aparean con el Δ de la réplica 0. La nota del bloque lo dice. La
alternativa, la mediana, mezclaría la referencia de tiempo de 8 réplicas con la ganancia de una.

**D4. Medición a hiperparámetros fijos.**
- **Script:** `experimentos/sampling_1/scripts/tiempos_hp_fijos.py`, que importa solo de `comun/`.
- **Celdas:** los 8 juegos de hiperparámetros del control (`C`, `C@1…7`), por r ∈ {1; 0,5; 0,25; 0,1; 0,05}, por 3
  repeticiones. Son 120 mediciones.
- **Cada medición** reproduce un trial: muestra uniforme con `comun/muestreo`, semilla 1000 + repetición, `Dataset` con
  los parámetros de dataset del control, `lgb.train` con `PARAMS_FIJOS` + hiperparámetros y predicción de 201908.
- **Salida:** `experimentos/sampling_1/ledger/tiempos_hp_fijos.csv`.
- **Duración estimada:** según `estudios.csv`, un trial del control dura de 16 a 30 s, así que las 120 mediciones
  llevan menos de 1 h.
- **El orden se aleatoriza** con una semilla fija, para que una deriva de la VM no se confunda con r.
- **Por qué hiperparámetros del control y no los de cada U:** así r es lo único que cambia. Los A del bloque A ya
  miden el otro efecto, el de la elección de Optuna.

**D5. Predicción de la medición, a pre-registrar en `control/docs/hipotesis.md` antes de lanzar la VM.** Propuesta, que
Agustina confirma o ajusta:
- **Aceleración a hiperparámetros fijos A_fijo(r):** mediana de T(1)/T(r) entre juegos de hiperparámetros. Predicción:
  A_fijo(0,5) ∈ [1,6; 2,4] y A_fijo(0,05) < 10, porque el `Dataset` de validación y la predicción de 201908 no se
  achican con r.
- **Ruido de la máquina:** CV entre repeticiones de la misma celda, con mediana ≤ 5 %.
- **Se confirma** cada parte si se cumple. Es exploratoria: no cambia veredictos, solo dice cuánto del A del bloque A es
  tamaño de datos y cuánto es Optuna.

**D6. Réplicas de U0.5.**
- **Registro:** `U0.5` pasa a `replicas=True` en `comun/variantes.py`, con estudios `U0.5@1…7` y semillas de TPE y de
  sorteo k, como en la fase 5.
- **Lanzamiento:** una lista de fase nueva, `experimentos/sampling_1/scripts/fase8.txt`, con 7 líneas de optimizar y
  sus finales de la ronda 201903–201908 a 20 semillas. Se lanza con `scripts/lanzar_fase.sh`.
- **Costo:** unos 7 × 330 s de optimización más 140 finales de unos 26 s, alrededor de 1,5 h.
- **Predicción, a escribir en `h1/docs/hipotesis.md` § Réplicas de U0.5 antes de correr:** U0.5 *no pierde* con
  réplicas y A ≥ 2 con la mediana. El veredicto con réplicas reemplaza al de la réplica 0, igual que en H3. Si sale
  *indeterminado* o A < 2, U0.5 deja la lista de "vale la pena" y se informa así.

**D7. Correcciones de texto.**
- **Se editan a mano solo frases.** Los números salen de `tabla_resultados.md` regenerada.
- **`decisiones.md`:** se agrega al principio un aviso de que es de las fases 1–4 (Ḡ_C = 276,10 M$, δ = 5,52 M$, 10
  semillas) y de que lo vigente está en el informe conjunto. `informe.md:206` deja de enlazarlo para los números.
  Reescribirlo duplicaría el informe.
- **Tabla de rondas:** se corrige en `scripts/comparar_rondas.py`, sacando la fila `C | pendiente` (el control no es
  una variante contra sí mismo). `H4O-0.5` sigue afuera, como decidió `final-con-julio-agosto` (tarea 4.1), y la tabla
  agrega una nota que dice que solo existe en la ronda nueva.

**D8. Respuesta al tutor.**
- **Dónde va:** `experimentos/sampling_1/docs/zulip/02_tiempos_y_undersampling.md`, que sale de los documentos.
- **Qué responde:**
  - El undersampling es H4, que conserva todas las bajas y recorta CONTINUA; H1 no toca la proporción.
  - El corte N* = 3.300 es el mismo para todas las variantes. Vale tal cual para las que entrenan el final con la
    proporción original (H1, H3, `H4H`, `H4U`). En `H4F` el peso 2 de CONTINUA restituye la proporción ponderada del
    train, así que el orden de los primeros 3.300 es comparable.
  - Los tiempos se midieron en la misma CPU con un trabajo por VM, con un ruido de máquina del 1 al 5 %, y el ruido
    que importa es el de Optuna, que ahora se reporta como rango.
- **El post a Zulip lo hace Agustina.**

## Risks / Trade-offs

- **Cambiar A después de ver los resultados** se puede leer como elegir la regla. Mitigación: la regla vieja era
  inconsistente entre filas, y no al revés. Se anota en la bitácora con el motivo, la tabla muestra A con el rango, y
  ningún veredicto de "vale la pena" cambia por D1 (U0.5 pasa de 2,25 a 2,83).
- **Las réplicas de U0.5 pueden cambiar su veredicto.** Es lo que se quiere saber. La regla queda escrita antes.
- **Las medianas de tiempo de las celdas viejas** se midieron en otras VMs y fechas que las réplicas nuevas. Es la misma
  CPU, y el CV de la máquina, que mide D4, acota ese efecto.
- **La predicción de D5** la propone una sesión que ya vio los tiempos de los finales. Por eso es exploratoria y no
  decide nada.
