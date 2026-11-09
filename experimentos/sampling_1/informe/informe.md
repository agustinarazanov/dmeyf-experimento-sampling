# Informe — Sampling_1: velocidad contra ganancia

Comisión lunes: Agustina Razanov, Martín López, Luis María Laguinge. Tutor: Joaquín I. Aramendía. Las tablas de
§ Resultados se copian de [`tabla_resultados.md`](tabla_resultados.md), que genera
`python -m comun.reporte --experimento sampling_1` desde los ledgers (`apareado.csv` y `replicas.csv` de `control`, `h1`,
`h2` y `h3`; `ledger/apareado_previo.csv` es la copia anterior a la separación, que cita por línea
`informe/decisiones.md`). Las figuras están en `informe/reporte.html` e `informe/figuras/`. El informe de cada hipótesis
está en [`h1`](../../h1/informe/informe.md), [`h2`](../../h2/informe/informe.md) y [`h3`](../../h3/informe/informe.md);
acá va la comparación y lo que es común.

## Hipótesis

Pregunta del tutor (Zulip 208986): ¿vale la pena el tradeoff entre velocidad y pérdida de performance? Sobre el baseline
de Bolaños (208135) medimos cuánto tiempo se ahorra y cuánta ganancia se pierde en 201910 con menos filas, sin cambiar la
proporción de clases (eso lo estudia Sampling_2).

- **H1**: submuestrear el train al azar (r = 0,5 a 0,05) no pierde con r ≥ 0,25 y pierde con r = 0,05.
- **H2**: muestrear dentro de LightGBM (`bagging_fraction` fijo en 0,5, 0,25 o 0,1) no pierde ni con 0,1.
- **H3**: optimizar con Optuna sobre una muestra (r_opt = 0,25 o 0,1) y entrenar el final con todo no pierde.
- **H3 con réplicas** (cambio `h3-semillas-optuna`, pre-registrado el 8-nov): con 8 réplicas de la optimización, H3
  sigue sin perder; además se prueba si la ventaja viene de que la muestra regulariza (A) o de que el control tuvo mala
  suerte (B), una tasa más chica (`H3-0.05`) y el reescalado de `min_data_in_leaf` (`H3R-0.1`). Reglas en
  [`h3/docs/hipotesis.md`](../../h3/docs/hipotesis.md) § H3 con réplicas.
- Una variante **vale la pena** si no pierde y además es al menos 2 veces más rápida (A ≥ 2).

## Diseño

Diez variantes contra el control, cada una con su Optuna (40 trials, AUC en 201908; H3 reusa los estudios de U0.25 y U0.1)
y 10 semillas finales iguales en todas. Decide la ganancia en 201910 al corte N* = 3.300 envíos, que sale del control en
201908. Δ es la diferencia contra el control apareada por semilla, con IC 95% t. Con δ = 2% de la ganancia del control
(5,52 M$): *no pierde* si la cota inferior del IC es ≥ −δ, *pierde* si la media es < −δ, *indeterminado* en el resto. T es
el tiempo de la optimización más un modelo final, medido en `n2-highmem-8`. Tres fases en VMs spot y una cuarta que
repite los finales guardando predicciones: 129 corridas válidas (9 optimizaciones y 120 finales de 12 variantes, C-rep
incluido), un solo tipo de máquina.

La fase 5 suma réplicas de la optimización: en la réplica k = 1…7 la semilla de TPE y la del sorteo de la muestra valen k
(la réplica 0 es la de las fases 1–4). `C`, `H3-0.25`, `H3-0.1`, `H3-0.05` y `H3R-0.1` quedan con 8 réplicas × 10
semillas: 28 estudios nuevos y 37 celdas de finales, en 8 VMs paralelas desde el tag `corridas-v2`. En esas variantes Δ
con réplicas es la diferencia de las medias entre réplicas con IC de Welch, y su veredicto reemplaza al de la réplica 0.
δ y N* no cambian. Detalle en `docs/hipotesis.md`, `docs/diseno.md` y
[`h3/docs/diseno.md`](../../h3/docs/diseno.md).

## Resultados

Las cifras de las tablas están en el formato del reporte (punto decimal). N* = 3,300 envíos; Ḡ_C (réplica 0) = 276.10 M$;
Ḡ_C con réplicas = 275.92 M$ (R=8); ensamble de 10 semillas del control = 275.55 M$.

### Bloque A: mismo protocolo

Ḡ, T y A salen de la réplica 0 en las variantes sin réplicas; en las marcadas (R=n), Ḡ es la media entre réplicas, T la mediana entre réplicas y A = T_C / T con T_C también mediana entre réplicas, así que se comparan con Ḡ_C con réplicas y no con Ḡ_C de la réplica 0.

| variante | hipótesis | Ḡ (M$) | Δ réplica 0 [IC] (M$) | Δ con réplicas [IC] (M$) | T mediana (s) | A | tiempo igual, réplicas [IC t] (M$) | tiempo igual, bootstrap de clientes [IC] (M$) | veredicto (fuente) |
|---|---|---|---|---|---|---|---|---|---|
| U0.05 | H1 | 242.33 | -33.77 [-39.84; -27.70] | — | 69 | 11.42 | sin réplicas | -22.10 [-37.62; -7.59] | pierde (réplica 0) |
| U0.1 | H1 | 259.16 | -16.94 [-23.35; -10.53] | — | 80 | 9.85 | sin réplicas | -4.57 [-14.74; 5.94] | pierde (réplica 0) |
| U0.25 | H1 | 269.72 | -6.38 [-11.21; -1.55] | — | 160 | 4.89 | sin réplicas | 0.63 [-9.36; 10.01] | pierde (réplica 0) |
| U0.5 | H1 | 274.78 | -1.32 [-6.77; 4.13] | — | 344 | 2.28 | sin réplicas | 5.42 [-2.97; 13.64] | indeterminado (réplica 0) |
| B0.1 | H2 | 268.29 | -7.81 [-12.27; -3.35] | — | 423 | 1.85 | sin réplicas | -3.55 [-14.30; 7.37] | pierde (réplica 0) |
| B0.25 | H2 | 276.76 | 0.66 [-2.86; 4.18] | — | 645 | 1.21 | sin réplicas | 1.16 [-7.49; 10.45] | no pierde (réplica 0) |
| B0.5 | H2 | 275.99 | -0.11 [-4.46; 4.24] | — | 1,003 | 0.78 | sin réplicas | no aplica (K<2) | no pierde (réplica 0) |
| GOSS | H2 | 276.65 | 0.55 [-2.60; 3.70] | — | 1,088 | 0.72 | sin réplicas | no aplica (K<2) | no pierde (réplica 0) |
| H3-0.05 | H3 | 277.79 (R=8) | 3.74 [1.77; 5.71] | 1.87 [-1.02; 4.76] (R=8) | 83 | 11.82 | 1.97 [-2.83; 6.76] (R=8) | 2.75 [-5.17; 12.54] | no pierde (con réplicas (8)) |
| H3R-0.1 | H3 | 277.68 (R=8) | 3.30 [0.65; 5.95] | 1.76 [-1.21; 4.73] (R=8) | 117 | 8.34 | 3.34 [-0.14; 6.82] (R=8) | 8.14 [-1.32; 18.48] | no pierde (con réplicas (8)) |
| H3-0.1 | H3 | 278.22 (R=8) | 4.07 [-0.27; 8.41] | 2.30 [-0.88; 5.47] (R=8) | 118 | 8.30 | 4.03 [0.78; 7.27] (R=8) | 4.38 [-3.96; 13.42] | no pierde (con réplicas (8)) |
| H3-0.25 | H3 | 277.74 (R=8) | 4.18 [-0.60; 8.96] | 1.81 [-1.78; 5.41] (R=8) | 216 | 4.53 | 1.83 [-1.91; 5.57] (R=8) | 3.46 [-4.29; 11.77] | no pierde (con réplicas (8)) |

Las variantes `U*`, `B*` y `GOSS` no tienen réplicas (pierden o no aceleran, y las réplicas no cambian eso).

| variante | réplicas | corridas | sd entre réplicas (M$) | sd entre semillas (M$) | varianza entre réplicas |
|---|---|---|---|---|---|
| C | 8 | 80 | 2.53 | 4.25 | 25 % |
| H3-0.05 | 8 | 80 | 2.84 | 3.96 | 33 % |
| H3-0.1 | 8 | 80 | 3.30 | 4.00 | 38 % |
| H3-0.25 | 8 | 80 | 3.93 | 4.60 | 40 % |
| H3R-0.1 | 8 | 80 | 2.99 | 3.81 | 35 % |

| diferencia | Δ [IC t entre réplicas] (M$) | réplicas | veredicto |
|---|---|---|---|
| H3R-0.1 - H3-0.1 | -0.54 [-1.88; 0.81] | 8 | no cambia |

Figuras: tiempo contra ganancia con el rango entre réplicas y descomposición de la varianza en
[`reporte.html`](reporte.html); bandas de curvas por hipótesis en `figuras/bandas_H1.png`, `bandas_H2.png` y
`bandas_H3.png`.

- **H1, ninguna de las dos** (informe de [`h1`](../../h1/informe/informe.md)): la pérdida crece a medida que baja r y
  U0.5 queda indeterminado.
- **H2, refutada** ([`h2`](../../h2/informe/informe.md)): con f = 0,1 pierde y con 0,5 y 0,25 casi no acelera (A ≤ 1,21).
  GOSS es descriptivo.
- **H3, confirmada también con réplicas** ([`h3`](../../h3/informe/informe.md)): `H3-0.1` y `H3-0.25` no pierden con
  réplicas (cotas inferiores −0,88 y −1,78 M$, contra −δ = −5,52 M$) y aceleran 8,30 y 4,53 veces. Con réplicas Δ se
  achica: de 4,07 a 2,30 M$ en `H3-0.1` y de 4,18 a 1,81 M$ en `H3-0.25`.
- **Mecanismo: apoya (B), el control tuvo mala suerte.** El IC de Δ con réplicas de `H3-0.1` contiene a 0 y la réplica 0
  de `C` (276,10 M$) quedó debajo de la mediana de sus 8 réplicas. No hay evidencia de que la muestra regularice: H3
  no pierde, pero tampoco le gana al control.
- **`H3-0.05`, confirmada**: no pierde con réplicas y A = 11,82 (≥ 8). En la réplica 0 salía *gana*; con réplicas no.
- **`H3R-0.1`, no cambia**: reescalar `min_data_in_leaf` × √10 da −0,54 M$ [−1,88; 0,81] contra `H3-0.1`.
- U0.25 y H3-0.25 comparten el estudio de Optuna de la réplica 0, o sea los mismos hiperparámetros. U0.25 pierde y
  H3-0.25 no, así que en H1 lo que se pierde es por entrenar el final con menos filas, no por optimizar sobre una muestra.
- **Vale la pena** (no pierde y A ≥ 2): las cuatro H3 (`H3-0.05`, `H3R-0.1`, `H3-0.1` y `H3-0.25`). Ninguna de H1 ni de
  H2: las que no pierden (B0.25, B0.5, GOSS) tienen A < 2.
- **¿Alcanzan 50 semillas finales?** No, con un solo estudio de Optuna: entre el 25 % (`C`) y el 40 % (`H3-0.25`) de la
  varianza de G es suerte de la optimización, y esa parte no baja con más semillas finales. Cuentas en el informe de
  [`h3`](../../h3/informe/informe.md) § ¿Alcanzan 50 semillas finales?.
- **A tiempo igual** (`decisiones.md` § A tiempo igual): cada variante gasta el tiempo que le sobra en un ensamble de K
  semillas (K ≤ 10). Ahora tiene intervalo. Con réplicas, `H3-0.1` queda arriba del control (4,03 M$ [0,78; 7,27]); las
  otras H3 tienen IC que contienen a 0. El bootstrap de clientes de 201910, que mide el ruido del mes de test, da IC de
  unos ±8 M$ o más: solo U0.05 queda claramente abajo (−22,10 [−37,62; −7,59]), y U0.5 (5,42 [−2,97; 13,64]), que en el
  informe anterior era la que más subía, no se distingue de 0. Ensamblar el control casi no suma (275,55 M$ contra
  276,10 M$).

### Bloque B: exploratorios

Las cifras del bloque B no se comparan una a una con las del bloque A: otro protocolo, otra muestra o otro entorno.

| carpeta | autor | pregunta | protocolo | cifras principales | advertencia |
|---|---|---|---|---|---|
| experimentos/h3/sensibilidad_muestra | Martín López | ¿Cuánto depende de la muestra la configuración que elige H3? | 20 configuraciones al azar, 10 muestras del 25 %, una semilla final, float64, 4 hilos | 08_ganancia_por_semilla.csv, delta: mediana 0 [-9,900,000; 8,800,000], n = 10; 08_ganancia_por_semilla.csv, delta_pct: mediana 0 [-3.622; 3.219], n = 10; 07_resumen_por_semilla.csv, delta: mediana 0 [-8.051e-05; 0.002227], n = 10; 07_resumen_por_semilla.csv, spearman_seleccion: mediana 0.7752 [0.6647; 0.8165], n = 10; 07_resumen_por_semilla.csv, tiempo_busqueda_s: mediana 487 [378; 1,064], n = 10 | 10 muestras pero 4 modelos distintos; un solo 201910; no comparable 1:1 con H3-0.25 |

- **Martín** ([`h3/sensibilidad_muestra/`](../../h3/sensibilidad_muestra/README.md)): con 10 muestras del 25 %, la
  configuración que elige H3 cambia con la muestra, y la ganancia en 201910 se mueve de −9,9 a +8,8 M$ contra la del
  control (mediana 0; es la columna `delta` de `08_ganancia_por_semilla.csv`, en $; la `delta` de
  `07_resumen_por_semilla.csv` es diferencia de AUC, no de ganancia). Va en la misma dirección que las réplicas: la suerte de la optimización pesa tanto como la
  diferencia que se quiere medir.
- El exploratorio de Luis (50 semillas finales con hiperparámetros fijos) entra en este bloque cuando `incorporar-aportes`
  lo porte y escriba su manifiesto.

## Limitaciones

- Las limitaciones propias de cada hipótesis (GOSS descriptivo y adaptación de `bagging_fraction` en H2, estudios
  compartidos con `h1` y reescalado en H3) están en su informe.
- Solo `C` y las H3 tienen réplicas de Optuna. Para `U*`, `B*` y `GOSS`, Δ sigue incluyendo la suerte de una sola
  optimización; como pierden por mucho o no aceleran, no cambia la respuesta.
- 8 réplicas alcanzan para decidir *no pierde*, pero no para separar de 0 una ventaja de 1,76 a 2,30 M$. R = 8 quedó
  cerrado antes de correr.
- U0.25/H3-0.25 y U0.1/H3-0.1 comparten el estudio de la réplica 0, y H3R-0.1/H3-0.1 todos: no son evidencia
  independiente entre sí.
- La réplica del control (C-rep) se corrió en otra VM de la misma cuenta, no por otra persona.
- A N* fijo la ganancia se mueve en pasos de 1,1 M$, así que diferencias de uno o dos BAJA+2 no se distinguen del ruido.
  La comparación a tiempo igual necesitó repetir los finales guardando predicciones (fase 4): las ganancias salieron
  idénticas, pero los tiempos de las variantes sin réplicas (y por lo tanto A y K) son los de esa repetición.
- Un solo año (2019) y un solo mes de test (201910): el bootstrap de clientes muestra que el ruido de ese mes es mayor
  que el de las réplicas. Los tiempos valen para `n2-highmem-8` (VMs distintas en la fase 5; T es la mediana entre
  réplicas) y en otra máquina solo se trasladan las aceleraciones relativas.
- `num_iterations = 100` fijo y `force_col_wise`: T(C) no es el tiempo del baseline con la configuración automática.
- H4 (submuestreo informado y pesos) no se corrió en esta grilla.

## Conclusiones

El tradeoff vale la pena si lo que se achica es la **optimización**, no el entrenamiento del modelo final. Optimizar
sobre el 5 %, 10 % o 25 % de las filas y entrenar con todas no pierde contra el control, también cuando se mide la suerte
de Optuna con 8 réplicas, y es de 4,53 a 11,82 veces más rápido. Entrenar el final con menos filas sí pierde, al azar
desde r = 0,25 y dentro de LightGBM con f = 0,1. Por qué: la optimización es lo que domina T (en el control, 748 s de
Optuna contra 35 s de un final; `control/ledger/estudios.csv`), y los hiperparámetros que elige Optuna sobre la muestra
sirven para el total.

Lo que las réplicas corrigen es el tamaño de la ventaja: con una sola optimización, H3 parecía ganarle al control por
unos 4 M$; con 8 réplicas la diferencia baja a cerca de la mitad (1,76 a 2,30 M$) y su IC contiene a 0. El control había tenido mala suerte en su
única optimización (B). La respuesta práctica no cambia (H3 no pierde y acelera), pero no hay que venderla como una
mejora de ganancia. Para comparar variantes con Optuna, más semillas finales no alcanzan: hay que repetir la
optimización.

## Qué sigue

- **H4 y los aportes** (cambio [`incorporar-aportes`](../../../openspec/changes/incorporar-aportes/proposal.md)): H4
  conserva todas las bajas en la muestra de búsqueda (muestras informadas por clase y pesos), con el mismo control, las
  réplicas de este cambio y el mismo ledger; porta y replica con el protocolo del repo el script de Luis (50 semillas
  finales, fast-retrain) y vuelve a correr los pasos 07 y 08 de Martín.
- Si H4 se suma con Optuna, correrla con réplicas desde el principio: la suerte de la optimización es del mismo orden
  que las diferencias entre variantes.
- Otro mes de test, para separar el ruido de 201910 del efecto de las variantes.

## Bibliografía (para postear en Zulip)

- Ke, G. et al. (2017). *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*. NeurIPS 30. (GOSS)
- Friedman, J. H. (2002). *Stochastic Gradient Boosting*. Computational Statistics & Data Analysis 38(4). (bagging por
  iteración)
- Akiba, T. et al. (2019). *Optuna: A Next-generation Hyperparameter Optimization Framework*. KDD.
- Bergstra, J. et al. (2011). *Algorithms for Hyper-Parameter Optimization*. NeurIPS 24. (TPE)
- Bolaños, baseline oficial del experimento colaborativo, Zulip 208135 (28-oct-2026).
