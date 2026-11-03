# Hipótesis — control

Parte de Sampling_1 ([`sampling_1/docs/hipotesis.md`](../../sampling_1/docs/hipotesis.md): pregunta, respuesta al
tutor y limitaciones comunes). Este documento define el control y las reglas que usan todas las hipótesis (`h1`, `h2`,
`h3` y las que vengan); ellas no las repiten. Escrito antes de cualquier corrida real. Si algo de este documento cambia
después de abrir la etapa de corridas, el cambio se anota en `docs/bitacora.md` con su motivo y las corridas previas
quedan marcadas como de la versión anterior.

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
