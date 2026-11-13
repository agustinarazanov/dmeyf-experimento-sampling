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
- **Semillas finales**: 10 semillas fijas, las mismas en todas las variantes. Cada una fija el `seed` de LightGBM, de donde
  salen el bagging y el `feature_fraction`. En las variantes con muestreo previo, la semilla final también vuelve a sortear
  la muestra, así que el IC incluye la variabilidad de la muestra.
- **Corte**: la cantidad de envíos N* que maximiza la ganancia media del control en **201908**. Ese mismo N* se aplica
  en 201910 a todas las variantes.

## Métricas y reglas comunes

- **Métrica que decide (G)**: ganancia en 201910 al corte fijo N*, calculada contra BAJA+2 con los valores de la
  cátedra. La ganancia máxima de la curva se reporta pero no decide.
- **Δ**: G(variante) − G(control), apareada por la semilla final. Se reportan la media, el desvío, el IC 95% (t de Student,
  9 g.l., o n − 1 si una variante termina con n < 10 semillas en común) y en cuántas semillas gana la variante.
- **Margen δ**: δ = 0,02 · Ḡ_C, donde Ḡ_C es la ganancia media del control en 201910 al corte N*. Lo que se fija antes
  de correr es la regla; el valor de δ sale del control.
- **Veredicto**. Los cuatro casos cubren todo:
  - *gana*: la cota inferior del IC de Δ es mayor que 0;
  - *no pierde*: la cota inferior del IC de Δ es mayor o igual que −δ (incluye *gana*);
  - *pierde*: la media de Δ es menor que −δ;
  - *indeterminado*: el resto, cuando la cota inferior es menor que −δ y la media es mayor o igual que −δ. Faltan
    semillas para decidir y se informa así.
- **Tiempo (T)**: tiempo de pared del pipeline de la variante, medido solo en `n2-highmem-8`. Es la optimización (suma de
  la duración de los 40 trials, incluida la predicción en 201908, más un armado del `lgb.Dataset`) más la media del
  modelo final entre semillas (`Dataset`, entrenamiento y predicción en 201910). Sumar trials, y no medir el proceso
  entero, hace que T no dependa de si la VM spot se cayó y el estudio se retomó.
  No incluye leer los datos ni generar los lags, que son iguales en todas las variantes. El tiempo de `lgb.train` del
  modelo final se reporta aparte.
- **Aceleración**: A = T(control) / T(variante), con la misma definición de T en todas las variantes.

## Ronda 201903–201908 (cambio `final-con-julio-agosto`, 12-nov-2026)

Escrito antes del tag `corridas-v4` y de cualquier final de esta ronda. Lo de arriba describe la ronda anterior
(final 201903–201906, 10 semillas), que se conserva y se sigue pudiendo consolidar. En la ronda nueva cambia solo lo
siguiente; el resto (Optuna, espacio, G, Δ, regla de δ, veredictos, T, A) queda igual.

- **Ventana del final: 201903–201908.** El modelo final de cada variante entrena con los seis meses y se evalúa en test
  (201910). Lo pide el baseline: Luis Suárez preguntó si para el test en el mes 10 se reentrena incluyendo 07 y 08, y
  Bolaños respondió "Yes" (Zulip 211210). Optuna no cambia: sigue entrenando con train 201903–201906 y eligiendo por AUC
  en validación (201908); los estudios ya guardados (réplicas `@k` incluidas) se reusan. 201909 no se usa para entrenar,
  validar ni evaluar; solo aporta la clase de 201907.
- **N\* = 3.300, fijo.** Es el valor de la ronda anterior, calculado en validación (201908) con finales que no habían
  visto 201908. En la ronda nueva la predicción de 201908 sería dentro de la muestra, así que los finales no la hacen y
  N\* no se recalcula. Recalcularlo en test violaría "201910 solo para comparar".
- **δ** sigue la regla de siempre (δ = 0,02 · Ḡ_C al corte N\* = 3.300) con los `C` de la ronda nueva, así que su valor
  cambia. La tabla de rondas muestra los dos δ.
- **20 semillas finales**, en este orden: las 10 oficiales (100003, 200003, 300007, 400009, 500009, 600011, 700001,
  800011, 900001, 999983) y las 10 de la fórmula de Luis, 110017 + i · 19937 con i = 0…9: 110017, 129954, 149891,
  169828, 189765, 209702, 229639, 249576, 269513, 289450. Ninguna choca con las oficiales ni con la semilla 0. Las
  primeras 10 son las de la ronda anterior, así que se puede reconsolidar la ronda nueva con 10 y separar el efecto de la
  ventana del de las semillas. El IC por semilla pasa a t de Student con 19 g.l. (n − 1 si faltan semillas).

### Apartamientos del baseline

Cada uno con su id y su motivo. Los tres están justificados; va a § Limitaciones del informe solo una cosa que la
tabla nombra: el uso sin cambios de los hiperparámetros de cuatro meses en un final de seis.

| apartamiento | id | justificación |
|---|---|---|
| El veredicto sale de la ganancia G y no del AUC, aunque el baseline dice "métrica auc". El AUC en 201910 se reporta al lado: ΔAUC con su IC por semilla y con réplicas en todas las tablas. | Zulip 208135 | La regla de veredicto se escribió en pesos antes de la primera corrida y δ está definido en pesos. Un umbral de AUC sería una regla nueva escrita después de haber visto los AUC de la ronda anterior. Optuna sí elige por AUC en validación, como pide 208135. |
| Ventana del final 201903–201908 (seis meses). | Zulip 211210 | La respuesta dice que se reentrena incluyendo 07 y 08, no que se saquen 03 y 04. Agustina confirmó los seis meses el 13-nov-2026. |
| Los hiperparámetros elegidos con cuatro meses se usan sin cambios en un final de seis, incluido `min_data_in_leaf`, que es absoluto. | Zulip 211210 | Es lo que pide la consigna (reentrenar con los hiperparámetros ya elegidos), no una variante. Reescalar sería una variante nueva y la idea ya está en `H3R` y `H3L`. Se declara como limitación porque cambia el régimen del final. |

### Predicción y regla de la ronda

- **Veredictos estables.** Para cada variante, con Δ por semilla (sin réplicas) y con Δ con réplicas donde existen, se
  compara el veredicto de la ronda anterior con el de la nueva. Un *cambio de lado* es pasar de *gana* o *no pierde* a
  *pierde*, o al revés; los pasos desde o hacia *indeterminado* no cuentan.
  - **Predicción**: 0 cambios de lado.
  - **Se confirma** si hay 0 cambios de lado; **se refuta** si hay 1 o más.
- **IC más angosto.** Para cada variante, la razón ancho del IC 95% de Δ por semilla en la ronda anterior / ancho en la
  nueva. Con el mismo desvío sería 1,53 (2,262/√10 contra 2,093/√20), del orden de √2.
  - **Predicción**: la mediana de la razón entre variantes está entre 1,2 y 1,9.
  - **Se confirma** si está en [1,2; 1,9]; **se refuta** si es menor que 1,2 o mayor que 1,9.
- **Con réplicas el ancho baja menos**, porque entre el 33 y el 40 % de la varianza de `H3` es entre réplicas y las
  réplicas siguen siendo 8.
  - **Predicción**: la mediana de la razón de anchos del IC de Welch de Δ con réplicas es menor que la mediana de la
    razón por semilla, y menor que 1,3.
  - **Se confirma** si se cumplen las dos desigualdades; **se refuta** si no se cumple alguna.
- `H4O-0.5`, que solo existe en la ronda nueva, tiene su predicción y su regla en
  [`h4/docs/hipotesis.md`](../../h4/docs/hipotesis.md) § `H4O-0.5`.

Un veredicto que cambie no se descarta ni se reemplaza: la tabla de rondas
(`sampling_1/informe/comparacion_rondas.md`) muestra, por variante, Δ y veredicto en las dos rondas, con los dos δ.
