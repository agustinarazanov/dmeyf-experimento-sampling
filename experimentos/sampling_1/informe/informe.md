# Informe — Sampling_1: velocidad contra ganancia

Comisión lunes: Agustina Razanov, Martín López, Luis María Laguinge. Tutor: Joaquín I. Aramendía. Las tablas de
§ Resultados se copian de [`tabla_resultados.md`](tabla_resultados.md), que genera
`python -m comun.reporte --experimento sampling_1` desde los ledgers (`apareado.csv` y `replicas.csv` de `control`, `h1`,
`h2`, `h3` y `h4`; `ledger/apareado_previo.csv` es la copia anterior a la separación, que cita por línea
`informe/decisiones.md`). Las figuras están en `informe/reporte.html` e `informe/figuras/`. El informe de cada hipótesis
está en [`h1`](../../h1/informe/informe.md), [`h2`](../../h2/informe/informe.md), [`h3`](../../h3/informe/informe.md) y
[`h4`](../../h4/informe/informe.md); acá va la comparación y lo que es común.

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
- **H4** (cambio `incorporar-aportes`, pre-registrado el 9-nov): conservar **todas las bajas** en la muestra que acelera
  (en la búsqueda de Optuna o en el modelo final) mantiene la ganancia y acelera. Cuatro variantes: búsqueda con todas
  las bajas y el 10 % de CONTINUA, difícil (`H4H-0.1`) o uniforme (`H4U-0.1`), con final completo; y búsqueda como
  `H3-0.05` o `H3-0.25` con final sobre todas las bajas y la mitad de CONTINUA con peso 2 (fast-retrain, `H4F-0.05` y
  `H4F-0.25`). Reglas en [`h4/docs/hipotesis.md`](../../h4/docs/hipotesis.md).
- **Extensiones de H3** (mismo cambio): reescalado √(1/r) en r = 0,25 (`H3R-0.25`), reescalado lineal 1/r
  (`H3L-0.25`, `H3L-0.1`) y búsqueda sobre el 10 % de los clientes (`H3K-0.1`). Reglas en
  [`h3/docs/hipotesis.md`](../../h3/docs/hipotesis.md) § Extensiones del aporte de Luis.
- H4 y las extensiones vienen del aporte de Luis, que eligió y descartó estrategias **mirando 201910**: lo declaran sus
  hipótesis y va en § Limitaciones. Los **contrastes principales**, fijados antes de correr, son `H3-0.1`, `H4H-0.1` y
  `H4F-0.05` contra el control; el resto es secundario.
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

La fase 6 (`incorporar-aportes`, desde el tag `corridas-v3`) suma las ocho variantes de H4 y de las extensiones de H3,
todas con 8 réplicas × 10 semillas desde el principio, y los estudios `K0.1`, `NH0.1` y `NU0.1` (la sonda de `NH0.1`
cuenta en T). Se comparan con el control con las mismas reglas. En las mismas VMs se replicaron los aportes de Martín y
de Luis (bloque B). Diferencias entre variantes: apareadas por réplica y semilla si comparten estudios (IC t entre
réplicas) y con IC de Welch entre réplicas si no. Detalle en [`h4/docs/diseno.md`](../../h4/docs/diseno.md).

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
| H3K-0.1 | H3 | 277.20 (R=8) | 5.17 [1.48; 8.86] | 1.28 [-3.42; 5.98] (R=8) | 118 | 8.30 | 2.38 [-4.22; 8.98] (R=8) | 10.06 [-0.44; 21.56] | no pierde (con réplicas (8)) |
| H3-0.1 | H3 | 278.22 (R=8) | 4.07 [-0.27; 8.41] | 2.30 [-0.88; 5.47] (R=8) | 118 | 8.30 | 4.03 [0.78; 7.27] (R=8) | 4.38 [-3.96; 13.42] | no pierde (con réplicas (8)) |
| H3L-0.1 | H3 | 274.46 (R=8) | -1.43 [-3.86; 1.00] | -1.46 [-4.73; 1.81] (R=8) | 120 | 8.19 | -0.65 [-3.47; 2.18] (R=8) | 3.09 [-6.05; 12.88] | no pierde (con réplicas (8)) |
| H3L-0.25 | H3 | 276.17 (R=8) | 1.21 [-2.40; 4.82] | 0.25 [-2.02; 2.51] (R=8) | 212 | 4.61 | 0.87 [-2.48; 4.22] (R=8) | -1.36 [-9.57; 6.93] | no pierde (con réplicas (8)) |
| H3R-0.25 | H3 | 277.45 (R=8) | 2.97 [-0.20; 6.14] | 1.53 [-1.92; 4.97] (R=8) | 214 | 4.58 | 3.07 [-1.88; 8.01] (R=8) | 9.18 [1.21; 17.82] | no pierde (con réplicas (8)) |
| H3-0.25 | H3 | 277.74 (R=8) | 4.18 [-0.60; 8.96] | 1.81 [-1.78; 5.41] (R=8) | 216 | 4.53 | 1.83 [-1.91; 5.57] (R=8) | 3.46 [-4.29; 11.77] | no pierde (con réplicas (8)) |
| H4F-0.05 | H4 | 277.78 (R=8) | 4.40 [-0.07; 8.87] | 1.86 [-0.83; 4.54] (R=8) | 74 | 13.17 | 3.89 [0.35; 7.43] (R=8) | 7.18 [-1.33; 17.27] | no pierde (con réplicas (8)) |
| H4H-0.1 | H4 | 267.31 (R=8) | -3.30 [-7.38; 0.78] | -8.61 [-12.78; -4.43] (R=8) | 117 | 8.35 | -4.63 [-8.07; -1.20] (R=8) | -4.12 [-13.09; 4.95] | pierde (con réplicas (8)) |
| H4F-0.25 | H4 | 277.31 (R=8) | 3.52 [-1.66; 8.70] | 1.39 [-1.87; 4.65] (R=8) | 204 | 4.81 | 3.07 [-0.09; 6.23] (R=8) | 5.73 [-2.86; 14.96] | no pierde (con réplicas (8)) |
| H4U-0.1 | H4 | 270.38 (R=8) | -2.42 [-7.11; 2.27] | -5.54 [-8.94; -2.14] (R=8) | 275 | 3.56 | 3.34 [0.77; 5.91] (R=8) | 2.72 [-7.70; 13.21] | pierde (con réplicas (8)) |

Las variantes `U*`, `B*` y `GOSS` no tienen réplicas (pierden o no aceleran, y las réplicas no cambian eso).

| variante | réplicas | corridas | sd entre réplicas (M$) | sd entre semillas (M$) | varianza entre réplicas |
|---|---|---|---|---|---|
| C | 8 | 80 | 2.53 | 4.25 | 25 % |
| H3-0.05 | 8 | 80 | 2.84 | 3.96 | 33 % |
| H3-0.1 | 8 | 80 | 3.30 | 4.00 | 38 % |
| H3-0.25 | 8 | 80 | 3.93 | 4.60 | 40 % |
| H3K-0.1 | 8 | 80 | 5.40 | 3.76 | 65 % |
| H3L-0.1 | 8 | 80 | 3.45 | 3.20 | 51 % |
| H3L-0.25 | 8 | 80 | 1.45 | 3.68 | 13 % |
| H3R-0.1 | 8 | 80 | 2.99 | 3.81 | 35 % |
| H3R-0.25 | 8 | 80 | 3.71 | 3.51 | 50 % |
| H4F-0.05 | 8 | 80 | 2.48 | 4.02 | 25 % |
| H4F-0.25 | 8 | 80 | 3.43 | 4.58 | 34 % |
| H4H-0.1 | 8 | 80 | 4.71 | 4.70 | 49 % |
| H4U-0.1 | 8 | 80 | 3.64 | 4.91 | 34 % |

| diferencia | Δ [IC entre réplicas] (M$) | réplicas | IC | veredicto |
|---|---|---|---|---|
| H3R-0.1 - H3-0.1 | -0.54 [-1.88; 0.81] | 8 | t, apareado | no cambia |
| H3R-0.25 - H3L-0.25 | 1.28 [-0.98; 3.54] | 8 | t, apareado | no cambia |
| H3R-0.1 - H3L-0.1 | 3.22 [0.63; 5.81] | 8 | t, apareado | mejora |
| H3R-0.25 - H3-0.25 | -0.29 [-2.28; 1.70] | 8 | t, apareado | no cambia |
| H3K-0.1 - H3-0.1 | -1.02 [-5.91; 3.88] | 8 | Welch, sin aparear | no cambia |
| H4H-0.1 - H4U-0.1 | -3.07 [-7.61; 1.47] | 8 | Welch, sin aparear | no cambia |

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
- **Mecanismo: apoya (B)** (la regla pre-registrada "el control tuvo mala suerte"). El IC de Δ con réplicas de `H3-0.1`
  contiene a 0 y la réplica 0 de `C` (276,10 M$) quedó debajo de la mediana de sus 8 réplicas. No hay evidencia de que
  la muestra regularice: H3 no pierde, pero tampoco le gana al control. La regla se cumple, pero la réplica 0 de `C`
  está arriba de la media con réplicas (275,92 M$): Δ se achica porque la réplica 0 de las H3 había salido alta, no
  porque el control haya salido bajo.
- **`H3-0.05`, confirmada**: no pierde con réplicas y A = 11,82 (≥ 8). En la réplica 0 salía *gana*; con réplicas no.
- **`H3R-0.1`, no cambia**: reescalar `min_data_in_leaf` × √10 da −0,54 M$ [−1,88; 0,81] contra `H3-0.1`.
- **Extensiones de H3** (secundarias; [`h3`](../../h3/informe/informe.md) § Extensiones): las cuatro no pierden contra
  el control. La raíz no mejora a no reescalar tampoco en r = 0,25 (−0,29 M$ [−2,28; 1,70]); le gana a la lineal en
  r = 0,1 (3,22 M$ [0,63; 5,81]) y no en r = 0,25 (1,28 M$ [−0,98; 3,54]); buscar sobre el 10 % de los clientes no
  cambia contra el 10 % de las filas (−1,02 M$ [−5,91; 3,88], Welch).
- **H4, búsqueda informada: refutada** ([`h4`](../../h4/informe/informe.md)). `H4H-0.1` y `H4U-0.1` *pierden* con
  réplicas (−8,61 y −5,54 M$, medias debajo de −5,52 M$). Elegir negativos difíciles en vez de uniformes no cambia
  (−3,07 M$ [−7,61; 1,47], Welch). Con una sola réplica no se veía: Δ réplica 0 era −3,30 y −2,42 M$.
- **H4, fast-retrain**: `H4F-0.05` *confirmada*: no pierde (1,86 M$ [−0,83; 4,54]), acelera 13,17 veces (más que
  `H3-0.05`, 11,82) y a tiempo igual *gana* (3,89 M$ [0,35; 7,43]). `H4F-0.25` no pierde y acelera 4,81 veces (más que
  `H3-0.25`, 4,53), pero a tiempo igual queda *indeterminada* ([−0,09; 6,23] M$).
- U0.25 y H3-0.25 comparten el estudio de Optuna de la réplica 0, o sea los mismos hiperparámetros. U0.25 pierde y
  H3-0.25 no, así que en H1 lo que se pierde es por entrenar el final con menos filas, no por optimizar sobre una muestra.
- **Vale la pena** (no pierde y A ≥ 2): las ocho variantes de H3 (`H3-0.05`, `H3R-0.1`, `H3K-0.1`, `H3-0.1`,
  `H3L-0.1`, `H3L-0.25`, `H3R-0.25` y `H3-0.25`) y las dos de fast-retrain (`H4F-0.05` y `H4F-0.25`). Ninguna de H1 ni
  de H2 (las que no pierden, B0.25, B0.5 y GOSS, tienen A < 2) ni de la búsqueda informada de H4, que pierde.
- **¿Alcanzan 50 semillas finales?** No, con un solo estudio de Optuna: entre el 25 % (`C`) y el 40 % (`H3-0.25`) de la
  varianza de G es suerte de la optimización, y esa parte no baja con más semillas finales. Cuentas en el informe de
  [`h3`](../../h3/informe/informe.md) § ¿Alcanzan 50 semillas finales?.
- **A tiempo igual** (`decisiones.md` § A tiempo igual): cada variante gasta el tiempo que le sobra en un ensamble de K
  semillas (K ≤ 10). Ahora tiene intervalo. Con réplicas, `H3-0.1` (4,03 M$ [0,78; 7,27]) y `H4F-0.05` (3,89 M$
  [0,35; 7,43]) quedan arriba del control; `H4U-0.1` también (3,34 M$ [0,77; 5,91]) aunque pierda con réplicas, porque
  el ensamble suma ganancia por sí solo. Las otras H3 y `H4F-0.25` tienen IC que contienen a 0, y `H4H-0.1` queda abajo
  (−4,63 M$ [−8,07; −1,20]). El bootstrap de clientes de 201910, que mide el ruido del mes de test, da IC de
  unos ±8 M$ o más: solo U0.05 queda claramente abajo (−22,10 [−37,62; −7,59]), y U0.5 (5,42 [−2,97; 13,64]), que en el
  informe anterior era la que más subía, no se distingue de 0. Ensamblar el control casi no suma (275,55 M$ contra
  276,10 M$).

### Bloque B: exploratorios

Las cifras del bloque B no se comparan una a una con las del bloque A: otro protocolo, otra muestra o otro entorno.

| carpeta | autor | pregunta | protocolo | cifras principales | advertencia |
|---|---|---|---|---|---|
| experimentos/h3/sensibilidad_muestra | Martín López | ¿Cuánto depende de la muestra la configuración que elige H3? | 20 configuraciones al azar, 10 muestras del 25 %, una semilla final, float64, 4 hilos | 08_ganancia_por_semilla.csv, delta: mediana 0 [-9,900,000; 8,800,000], n = 10; 08_ganancia_por_semilla.csv, delta_pct: mediana 0 [-3.622; 3.219], n = 10; 07_resumen_por_semilla.csv, delta: mediana 0 [-8.051e-05; 0.002227], n = 10; 07_resumen_por_semilla.csv, spearman_seleccion: mediana 0.7752 [0.6647; 0.8165], n = 10; 07_resumen_por_semilla.csv, tiempo_busqueda_s: mediana 487 [378; 1,064], n = 10 | 10 muestras pero 4 modelos distintos; un solo 201910; no comparable 1:1 con H3-0.25 |
| experimentos/sampling_1/exploratorios/validacion_50_semillas | Luis María Laguinge | ¿Con 50 semillas finales, qué estrategias de las hipótesis 3 y 4 ganan al control y cuántas semillas entran en un presupuesto de 900 s? | 9 estrategias con hiperparámetros fijos, 50 semillas finales (10 oficiales + 110017 + i·19937), presupuesto de 900 s; ranking y curva según K en 201908, 201910 solo informado | resumen_50_semillas_original.csv, g_201908: mediana 201,850,000 [186,450,000; 216,150,000], n = 493; resumen_50_semillas_original.csv, gmax_201908: mediana 207,350,000 [196,625,000; 218,075,000], n = 493; resumen_50_semillas_original.csv, auc_201908: mediana 0.9274 [0.9236; 0.9311], n = 493; resumen_50_semillas_original.csv, g_201910: mediana 278,850,000 [266,750,000; 296,450,000], n = 493; resumen_50_semillas_original.csv, auc_201910: mediana 0.9328 [0.9304; 0.9357], n = 493; resumen_50_semillas_original.csv, tiempo_s: mediana 19.02 [11.33; 35.72], n = 493; ranking_201908_original.csv, puesto_201908: mediana 5 [1; 9], n = 9; ranking_201908_original.csv, g_201908: mediana 201,762,698 [196,690,000; 207,856,000], n = 9; ranking_201908_original.csv, g_201908_sd: mediana 4,037,318 [3,275,288; 4,559,427], n = 9; presupuesto_original.csv, k_presupuesto: mediana 40 [4; 70], n = 9; presupuesto_original.csv, ens_k_201908: mediana 205,150,000 [198,550,000; 210,650,000], n = 9; presupuesto_original.csv, ens_k_201910: mediana 281,050,000 [278,850,000; 284,350,000], n = 9 | origen: commit 9e1889e, script de Colab con su propio panel; el resumen original elige con 201910 (ya mirado) y hay piezas reconstruidas (presupuesto, resumen CSV, H4_Hard); no es una variante ni cambia el veredicto de ninguna hipótesis |

- **Martín, replicado** ([`h3/sensibilidad_muestra/`](../../h3/sensibilidad_muestra/README.md) § Reproducción en la
  VM): sus pasos 07 y 08 se volvieron a correr en `n2-highmem-8` con otras versiones de Python, LightGBM y numpy, y las
  elecciones, los AUC y las ganancias salieron idénticos; solo cambian los tiempos. Con 10 muestras del 25 %, la
  configuración que elige H3 cambia con la muestra, y la ganancia en 201910 se mueve de −9,9 a +8,8 M$ contra la del
  control (mediana 0; es la columna `delta` de `08_ganancia_por_semilla.csv`, en $; la `delta` de
  `07_resumen_por_semilla.csv` es diferencia de AUC, no de ganancia). Va en la misma dirección que las réplicas: la
  suerte de la optimización pesa tanto como la diferencia que se quiere medir.
- **Luis, replicado** ([`validacion_50_semillas/`](../exploratorios/validacion_50_semillas/README.md)): el script se
  portó al repo, con las piezas sin código reconstruidas y marcadas, y se corrió en `n2-highmem-8` con sus
  hiperparámetros. Ordenadas por G en 201908 (como pide la consigna), el control queda primero y ninguna estrategia lo
  supera; el "campeón" de su resumen, elegido en 201910, no gana en el mes que decide. Su README tiene la tabla
  reportado/reproducido de cada número del resumen original: las ventajas que reportaba sobre el control van en el
  mismo sentido con sus hiperparámetros, pero con una sola búsqueda por estrategia; al repetir la búsqueda (bloque A) la
  búsqueda difícil pierde y H3 queda en *no pierde*. Su idea de producción, el fast-retrain, es la que se sostiene con
  réplicas (`H4F-0.05`).

## Limitaciones

- **Test ya mirado.** H4 y las extensiones de H3 salen del aporte de Luis, que eligió y descartó estrategias mirando su
  ganancia en 201910, y no hay otro mes de test (la consigna lo reserva para la comparación). Entraron todas juntas, con
  reglas escritas antes de correr, y ninguna se eligió ni se descartó acá por 201910; aun así, esos resultados no
  cuentan con un mes de test que no se haya mirado.
- **Comparaciones múltiples.** Entre H4 y las extensiones de H3 hay más de diez contrastes sin corrección: con un 5 % de
  error por contraste, alguno puede salir significativo por azar. Las conclusiones se apoyan en los contrastes
  principales fijados antes de correr (`H3-0.1`, `H4H-0.1` y `H4F-0.05` contra el control); el resto es secundario.
- Las limitaciones propias de cada hipótesis (GOSS descriptivo y adaptación de `bagging_fraction` en H2, estudios
  compartidos con `h1` y reescalado en H3, sonda y proporción de clases en H4) están en su informe.
- Solo `C`, las H3 y las H4 tienen réplicas de Optuna. Para `U*`, `B*` y `GOSS`, Δ sigue incluyendo la suerte de una
  sola optimización; como pierden por mucho o no aceleran, no cambia la respuesta.
- 8 réplicas alcanzan para decidir *no pierde*, pero no para separar de 0 una ventaja de 1,76 a 2,30 M$. R = 8 quedó
  cerrado antes de correr.
- U0.25/H3-0.25 y U0.1/H3-0.1 comparten el estudio de la réplica 0; H3R, H3L y H3 de la misma tasa comparten todos, y
  `H4F-0.05`/`H4F-0.25` comparten los de `H3-0.05`/`H3-0.25`: no son evidencia independiente entre sí.
- H4 cambia la proporción de clases en la búsqueda (o en el final, con peso 2 para restituirla), el terreno de
  Sampling_2; es la excepción declarada en `h4/docs/hipotesis.md`.
- La réplica del control (C-rep) se corrió en otra VM de la misma cuenta, no por otra persona.
- A N* fijo la ganancia se mueve en pasos de 1,1 M$, así que diferencias de uno o dos BAJA+2 no se distinguen del ruido.
  La comparación a tiempo igual necesitó repetir los finales guardando predicciones (fase 4): las ganancias salieron
  idénticas, pero los tiempos de las variantes sin réplicas (y por lo tanto A y K) son los de esa repetición.
- Un solo año (2019) y un solo mes de test (201910): el bootstrap de clientes muestra que el ruido de ese mes es mayor
  que el de las réplicas. Los tiempos valen para `n2-highmem-8` (VMs distintas en la fase 5; T es la mediana entre
  réplicas) y en otra máquina solo se trasladan las aceleraciones relativas.
- `num_iterations = 100` fijo y `force_col_wise`: T(C) no es el tiempo del baseline con la configuración automática.

## Conclusiones

El tradeoff vale la pena si lo que se achica es la **optimización**, no el entrenamiento del modelo final. Optimizar
sobre el 5 %, 10 % o 25 % de las filas y entrenar con todas no pierde contra el control, también cuando se mide la suerte
de Optuna con 8 réplicas, y es de 4,53 a 11,82 veces más rápido. Entrenar el final con menos filas sí pierde, al azar
desde r = 0,25 y dentro de LightGBM con f = 0,1. Por qué: la optimización es lo que domina T (en el control, 748 s de
Optuna contra 35 s de un final; `control/ledger/estudios.csv`), y los hiperparámetros que elige Optuna sobre la muestra
sirven para el total.

Lo que las réplicas corrigen es el tamaño de la ventaja: con una sola optimización, H3 parecía ganarle al control por
unos 4 M$; con 8 réplicas la diferencia baja a cerca de la mitad (1,76 a 2,30 M$) y su IC contiene a 0. La regla de mecanismo da (B), pero la suerte de
la réplica 0 estaba más en las H3 que en el control. La respuesta práctica no cambia (H3 no pierde y acelera), pero no hay que venderla como una
mejora de ganancia. Para comparar variantes con Optuna, más semillas finales no alcanzan: hay que repetir la
optimización.

Con los tres contrastes principales, fijados antes de correr H4:
- **`H3-0.1` contra el control: no pierde** (2,30 M$ [−0,88; 5,47] con réplicas) y acelera 8,30 veces. Es la respuesta
  de arriba.
- **`H4H-0.1` contra el control: pierde** (−8,61 M$ [−12,78; −4,43]). Achicar la búsqueda conservando todas las bajas
  y recortando CONTINUA rinde peor que achicarla al azar, elijan como se elijan los negativos. La ventaja que reportaba
  el aporte de Luis no se sostiene al repetir la búsqueda.
- **`H4F-0.05` contra el control: no pierde** (1,86 M$ [−0,83; 4,54]), acelera 13,17 veces y **a tiempo igual gana**
  (3,89 M$ [0,35; 7,43]). Achicar también el final, conservando todas las bajas y la mitad de CONTINUA con peso 2,
  agrega velocidad sin perder; con el tiempo que sobra se ensamblan más semillas. La cota inferior está cerca de 0, y
  esta variante viene de una idea vista en 201910.

La respuesta al tutor se amplía: vale la pena achicar la optimización (al azar, no informada por clase) y, si además se
quiere el final más rápido, achicar CONTINUA conservando las bajas con peso. Ninguna de las dos es una mejora de ganancia
por modelo; la ganancia extra, si la hay, viene de ensamblar con el tiempo ahorrado.

## Qué sigue

- Otro mes de test, para separar el ruido de 201910 del efecto de las variantes y para tener uno que no se haya mirado
  al elegir H4 y las extensiones de H3.
- Fast-retrain sobre otras búsquedas (por ejemplo, `H3-0.1`) y con otras fracciones de CONTINUA, con réplicas desde el
  principio: la suerte de la optimización es del mismo orden que las diferencias entre variantes.

## Bibliografía (para postear en Zulip)

- Ke, G. et al. (2017). *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*. NeurIPS 30. (GOSS)
- Friedman, J. H. (2002). *Stochastic Gradient Boosting*. Computational Statistics & Data Analysis 38(4). (bagging por
  iteración)
- Akiba, T. et al. (2019). *Optuna: A Next-generation Hyperparameter Optimization Framework*. KDD.
- Bergstra, J. et al. (2011). *Algorithms for Hyper-Parameter Optimization*. NeurIPS 24. (TPE)
- Bolaños, baseline oficial del experimento colaborativo, Zulip 208135 (28-oct-2026).
