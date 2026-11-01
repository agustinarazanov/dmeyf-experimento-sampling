# Hipótesis — Sampling_1

Escrito antes de cualquier corrida real. Si algo de este documento cambia después de abrir la etapa de corridas, el
cambio se anota en `docs/bitacora.md` con su motivo y las corridas previas quedan marcadas como de la versión anterior.

## Pregunta

Pregunta del tutor (Zulip 208986, 1-nov): **¿vale la pena el tradeoff entre velocidad y pérdida de performance?**

Para el baseline de Bolaños (28-oct, Zulip 208135), ¿cuánto tiempo se ahorra y cuánta ganancia se pierde en 201910 si se
usan menos filas para entrenar u optimizar, **sin alterar la proporción de clases**? El undersampling de CONTINUA lo
estudia Sampling_2; acá la proporción de BAJA+1 ∪ BAJA+2 queda igual, en esperanza, en todos los brazos.

## Control (C)

- **Datos**: 2019; train 201903–201906 completo (r = 1); positivo BAJA+1 ∪ BAJA+2; lags y deltas de orden 2 (201901 y
  201902 solo como historia); validación 201908; test 201910, que no se usa para elegir nada.
- **Modelo**: LightGBM con defaults, salvo lo que optimiza Optuna. Son `num_iterations = 100` sin early stopping y
  `num_threads = 8`. Se fijan además tres parámetros de ejecución, que no cambian el modelo salvo por redondeo:
  `deterministic = true` y `force_col_wise = true`, para que la misma corrida se repita y la estrategia de histogramas
  no varíe con r, y `feature_pre_filter = false`, para que Optuna pueda cambiar `min_data_in_leaf`. Es una adaptación
  declarada (etapa de diseño, 1-nov). Por `force_col_wise`, T(C) no es exactamente el tiempo del baseline con la
  elección automática de LightGBM.
- **Optuna**: 40 trials, TPE con semilla de optimización 0, maximiza el AUC en 201908. El espacio de búsqueda lo fija
  cada grupo (208135); el nuestro es este:

  | hiperparámetro | rango | escala |
  |---|---|---|
  | `num_leaves` | 8 – 1024 (entero) | log |
  | `learning_rate` | 0,01 – 0,3 | log |
  | `min_data_in_leaf` | 10 – 5000 (entero) | log |
  | `feature_fraction` | 0,1 – 1,0 | lineal |
  | `bagging_fraction` | 0,1 – 1,0, con `bagging_freq = 1` | lineal |

  Los 40 trials y la semilla única de Optuna son una elección nuestra, porque 208135 no los fija.
- **Semillas finales**: 10 semillas fijas, las mismas en todos los brazos. Cada una fija el `seed` de LightGBM, de donde
  salen el bagging y el `feature_fraction`. En los brazos con muestreo previo, la semilla final también vuelve a sortear
  la muestra, así que el IC incluye la variabilidad de la muestra.
- **Corte**: la cantidad de envíos N* que maximiza la ganancia media del control en **201908**. Ese mismo N* se aplica
  en 201910 a todos los brazos.

## Métricas y reglas comunes

- **Métrica que decide (G)**: ganancia en 201910 al corte fijo N*, calculada contra BAJA+2 con los valores de la
  cátedra. La ganancia máxima de la curva se reporta pero no decide.
- **Δ**: G(brazo) − G(control), apareada por la semilla final. Se reportan la media, el desvío, el IC 95% (t de Student,
  9 g.l., o n − 1 si un brazo termina con n < 10 semillas en común) y en cuántas semillas gana el brazo.
- **Margen δ**: δ = 0,02 · Ḡ_C, donde Ḡ_C es la ganancia media del control en 201910 al corte N*. Lo que se fija antes
  de correr es la regla; el valor de δ sale del control.
- **Veredicto**. Los cuatro casos cubren todo:
  - *gana*: la cota inferior del IC de Δ es mayor que 0;
  - *no pierde*: la cota inferior del IC de Δ es mayor o igual que −δ (incluye *gana*);
  - *pierde*: la media de Δ es menor que −δ;
  - *indeterminado*: el resto, cuando la cota inferior es menor que −δ y la media es mayor o igual que −δ. Faltan
    semillas para decidir y se informa así.
- **Tiempo (T)**: tiempo de pared del pipeline del brazo, medido solo en `n2-highmem-8`. Es la optimización (suma de
  la duración de los 40 trials, incluida la predicción en 201908, más un armado del `lgb.Dataset`) más la media del
  modelo final entre semillas (`Dataset`, entrenamiento y predicción en 201910). Sumar trials, y no medir el proceso
  entero, hace que T no dependa de si la VM spot se cayó y el estudio se retomó.
  No incluye leer los datos ni generar los lags, que son iguales en todos los brazos. El tiempo de `lgb.train` del
  modelo final se reporta aparte.
- **Aceleración**: A = T(control) / T(brazo), con la misma definición de T en todos los brazos.

## H1 — Submuestreo uniforme del train

- **Variable**: tasa r de filas de 201903–201906 tomadas al azar sin distinguir clase, r ∈ {0,5, 0,25, 0,1, 0,05}.
  Optuna se corre de nuevo para cada tasa, sobre una muestra sorteada con la semilla 0 y con el mismo espacio que el
  control. El modelo final se entrena con la misma tasa, sobre una muestra que se vuelve a sortear con cada semilla
  final.
- **Métrica que decide**: el veredicto de cada tasa contra el control.
- **Predicción**: *no pierde* con r = 0,5 y 0,25; *pierde* con r = 0,05. Como predicciones secundarias, que no deciden:
  *pierde* con r = 0,1, y A ≥ 2 con r = 0,25. La predicción en 201908 tiene un costo fijo, por eso la aceleración no es
  4×.
- **Se confirma** si con r = 0,5 y 0,25 el brazo *no pierde* y con r = 0,05 *pierde*: hay margen y después hay caída.
- **Se refuta** si con r = 0,5 el brazo *pierde* (no hay margen) o si con r = 0,05 *no pierde* (no hay caída dentro de
  la grilla).
- **Ninguna de las dos** en cualquier otro caso, por ejemplo con r = 0,25 *indeterminado* o con r = 0,25 perdiendo
  mientras r = 0,5 no pierde. Se informa como frontera observada la menor r tal que esa tasa y todas las mayores *no
  pierden*.

## H2 — Muestrear dentro de LightGBM

- **Variable**: `bagging_fraction` fijo en f ∈ {0,5, 0,25, 0,1}, con `bagging_freq = 1`. Cada árbol ve una fracción f
  distinta de las filas, pero el modelo usa todas.
- **Adaptación declarada del baseline**: en estos brazos `bagging_fraction` es la variable experimental, así que sale
  del espacio de Optuna; los otros cuatro hiperparámetros se siguen optimizando con los mismos rangos.
- **Métrica que decide**: el veredicto de cada f contra el control.
- **Predicción**: *no pierde* con las tres fracciones, también con f = 0,1, donde H1 predice que el muestreo previo
  pierde. Como predicción secundaria, que no decide: A ≥ 1,5 con f = 0,1, porque el `Dataset` completo se construye
  igual.
- **Se confirma** si con f = 0,1 *no pierde*.
- **Se refuta** si con f = 0,1 *pierde*.
- **Ninguna de las dos** si con f = 0,1 sale *indeterminado*.
- **Lectura conjunta con H1, descriptiva**: en la curva tiempo-ganancia de todos los brazos se mira si los puntos de
  `bagging` quedan por encima de los de `uniforme` al mismo tiempo. No es una prueba, porque `uniforme` sigue
  optimizando `bagging_fraction` y no tiene la misma fracción efectiva por iteración.
- **Brazo descriptivo `goss`** (`top_rate = 0,2`, `other_rate = 0,1`, sin bagging porque LightGBM no lo admite): se
  reporta su veredicto contra el control, pero no decide H2. A partir de la iteración 1/`learning_rate` usa un 30% de
  filas por iteración; antes no muestrea. También cambia la mezcla de clases de cada árbol, porque se queda con los
  casos de gradiente alto.

## H3 — Optimizar sobre una muestra, entrenar con todo

- **Variable**: tasa de la muestra uniforme sobre la que corre Optuna, r_opt ∈ {0,1, 0,25}. La muestra de optimización
  se sortea con la semilla 0. El modelo final se entrena con r = 1 y con los hiperparámetros tal como salen de la
  muestra, sin reescalar `min_data_in_leaf`.
- **Métrica que decide**: el veredicto de cada r_opt contra el control.
- **Predicción**: *no pierde* con ambas tasas. Como predicción secundaria, que no decide: A ≥ 2 con r_opt = 0,25 y
  A ≥ 4 con r_opt = 0,1.
- **Se confirma** si con r_opt = 0,25 *no pierde*.
- **Se refuta** si con r_opt = 0,25 *pierde*.
- **Ninguna de las dos** si con r_opt = 0,25 sale *indeterminado*.
- **Riesgo conocido**: el `min_data_in_leaf` que se elige sobre la muestra queda chico para el train completo. Si eso
  hace perder a r_opt = 0,1, el reescalado se propone como trabajo futuro y no como un brazo nuevo.

## Respuesta a la pregunta del tutor

Un brazo **vale la pena** si *no pierde* contra el control y además A ≥ 2, con la definición común de T. La respuesta
del video es la lista de brazos que valen la pena, con su A y su Δ, más la curva tiempo-ganancia de todos los brazos.
Predicción: valen la pena H3 con ambas tasas y H1 con r = 0,25. Para un pipeline acotado en tiempo, como el de 15
minutos de la segunda entrega, lo que más sirve es H3 con r_opt = 0,1, porque la optimización domina el tiempo total.

## Limitaciones previstas

- Con 10 semillas no se separan diferencias menores que δ; esos casos salen como *indeterminado* y se informan.
- Aparear por semilla ayuda poco entre brazos con datos e hiperparámetros distintos, porque la misma semilla no produce
  modelos correlacionados. El IC apareado es honesto, pero no es mucho más angosto que uno no apareado.
- Optuna corre con una sola semilla por brazo, así que Δ incluye la suerte de la optimización, que el IC no mide.
- El corte N* sale de 201908, así que si la tasa de bajas de 201910 es distinta, todos los brazos pagan igual.
- `goss` cambia la mezcla de clases por iteración y queda fuera de la evidencia. Además, si Optuna elige
  `learning_rate` cerca de 0,01, las 100 iteraciones caen antes de 1/`learning_rate` y GOSS nunca muestrea; se
  informa el `learning_rate` elegido.
- H1 y H3 comparten el estudio de Optuna en r = 0,25 y 0,1 (`docs/diseno.md`), así que Δ(U0.25) y Δ(H3-0.25) tienen la
  misma suerte de optimización y no son evidencia independiente entre sí.
- Hay un solo mes de test (201910) y un solo año (2019), así que la conclusión vale para este baseline.
- Los tiempos se miden en `n2-highmem-8`. Si el pipeline de la segunda entrega corre en otra máquina, por ejemplo con
  la predicción en la laptop, las aceleraciones relativas se pueden trasladar, pero los segundos absolutos no.
