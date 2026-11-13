# Resultados de sampling_1

Generado por `python -m comun.reporte --experimento sampling_1`; no editar a mano.

Final entrenado con 201903-201908, 20 semillas por réplica; N* = 3,300 envíos; Ḡ_C (réplica 0) = 282.48 M$; Ḡ_C con réplicas = 281.78 M$ (R=8); ensamble de 20 semillas del control = 286.55 M$.

## Bloque A: mismo protocolo

Ḡ, T y A salen de la réplica 0 en las variantes sin réplicas; en las marcadas (R=n), Ḡ es la media entre réplicas, T la mediana entre réplicas y A = T_C / T con T_C también mediana entre réplicas, así que se comparan con Ḡ_C con réplicas y no con Ḡ_C de la réplica 0.

| variante | hipótesis | Ḡ (M$) | Δ réplica 0 [IC] (M$) | Δ con réplicas [IC] (M$) | ΔAUC en 201910 [IC] | T mediana (s) | A | tiempo igual, réplicas [IC t] (M$) | tiempo igual, bootstrap de clientes [IC] (M$) | veredicto (fuente) |
|---|---|---|---|---|---|---|---|---|---|---|
| U0.05 | H1 | 252.34 | -30.14 [-34.56; -25.72] | — | -0.0176 [-0.0186; -0.0166] (réplica 0) | 70 | 11.45 | sin réplicas | -13.72 [-26.90; -0.92] | pierde (réplica 0) |
| U0.1 | H1 | 266.20 | -16.28 [-19.83; -12.73] | — | -0.0103 [-0.0111; -0.0095] (réplica 0) | 81 | 9.89 | sin réplicas | -5.82 [-15.73; 3.85] | pierde (réplica 0) |
| U0.25 | H1 | 272.91 | -9.57 [-12.65; -6.49] | — | -0.0055 [-0.0060; -0.0050] (réplica 0) | 164 | 4.87 | sin réplicas | -0.52 [-8.86; 7.54] | pierde (réplica 0) |
| U0.5 | H1 | 281.11 | -1.38 [-3.99; 1.24] | — | -0.0019 [-0.0023; -0.0015] (réplica 0) | 354 | 2.25 | sin réplicas | 5.98 [-1.71; 13.53] | no pierde (réplica 0) |
| B0.1 | H2 | 274.01 | -8.47 [-11.02; -5.92] | — | -0.0088 [-0.0094; -0.0083] (réplica 0) | 434 | 1.84 | sin réplicas | -2.34 [-11.66; 6.44] | pierde (réplica 0) |
| B0.25 | H2 | 283.36 | 0.88 [-1.95; 3.71] | — | -0.0044 [-0.0047; -0.0041] (réplica 0) | 650 | 1.23 | sin réplicas | 3.72 [-6.00; 13.31] | no pierde (réplica 0) |
| B0.5 | H2 | 281.55 | -0.94 [-3.62; 1.75] | — | -0.0012 [-0.0017; -0.0008] (réplica 0) | 1,011 | 0.79 | sin réplicas | no aplica (K<2) | no pierde (réplica 0) |
| GOSS | H2 | 278.46 | -4.01 [-7.03; -1.00] | — | +0.0005 [+0.0003; +0.0008] (réplica 0) | 1,102 | 0.72 | sin réplicas | no aplica (K<2) | indeterminado (réplica 0) |
| H3-0.05 | H3 | 283.86 (R=8) | 5.22 [2.96; 7.49] | 2.08 [-0.87; 5.02] (R=8) | -0.0020 [-0.0041; +0.0000] (R=8) | 95 | 10.56 | 4.77 [1.01; 8.53] (R=8) | 7.74 [0.06; 16.23] | no pierde (con réplicas (8)) |
| H3K-0.1 | H3 | 281.57 (R=8) | 0.44 [-1.91; 2.79] | -0.21 [-5.05; 4.63] (R=8) | -0.0033 [-0.0050; -0.0017] (R=8) | 126 | 7.98 | 3.95 [-1.58; 9.47] (R=8) | 4.24 [-6.33; 15.40] | no pierde (con réplicas (8)) |
| H3-0.1 | H3 | 283.49 (R=8) | 1.26 [-1.95; 4.48] | 1.71 [-1.07; 4.49] (R=8) | -0.0017 [-0.0030; -0.0003] (R=8) | 129 | 7.76 | 5.46 [2.93; 7.98] (R=8) | 6.04 [-2.37; 15.30] | no pierde (con réplicas (8)) |
| H3L-0.1 | H3 | 281.92 (R=8) | -1.43 [-4.02; 1.16] | 0.14 [-3.30; 3.57] (R=8) | -0.0005 [-0.0020; +0.0010] (R=8) | 130 | 7.73 | 2.98 [0.05; 5.92] (R=8) | 1.76 [-7.26; 10.72] | no pierde (con réplicas (8)) |
| H3R-0.1 | H3 | 283.37 (R=8) | 0.82 [-1.79; 3.44] | 1.59 [-1.80; 4.98] (R=8) | -0.0008 [-0.0023; +0.0006] (R=8) | 130 | 7.71 | 5.87 [4.27; 7.47] (R=8) | 5.06 [-2.15; 13.31] | no pierde (con réplicas (8)) |
| H3L-0.25 | H3 | 283.00 (R=8) | 1.32 [-1.36; 4.00] | 1.22 [-1.59; 4.03] (R=8) | +0.0004 [-0.0008; +0.0016] (R=8) | 222 | 4.51 | 5.46 [0.83; 10.08] (R=8) | 9.00 [2.14; 16.83] | no pierde (con réplicas (8)) |
| H3R-0.25 | H3 | 283.72 (R=8) | 2.04 [-0.81; 4.88] | 1.95 [-0.85; 4.74] (R=8) | +0.0000 [-0.0011; +0.0011] (R=8) | 225 | 4.46 | 5.32 [2.93; 7.71] (R=8) | 6.65 [-0.28; 14.19] | no pierde (con réplicas (8)) |
| H3-0.25 | H3 | 283.20 (R=8) | 4.73 [2.48; 6.98] | 1.42 [-2.82; 5.67] (R=8) | -0.0009 [-0.0021; +0.0004] (R=8) | 229 | 4.38 | 6.15 [3.95; 8.34] (R=8) | 8.85 [1.87; 16.83] | no pierde (con réplicas (8)) |
| H4F-0.05 | H4 | 283.19 (R=8) | 4.18 [1.11; 7.25] | 1.41 [-1.58; 4.40] (R=8) | -0.0019 [-0.0041; +0.0003] (R=8) | 80 | 12.50 | 4.63 [0.77; 8.50] (R=8) | 9.29 [1.53; 18.04] | no pierde (con réplicas (8)) |
| H4H-0.1 | H4 | 270.37 (R=8) | -9.19 [-12.06; -6.31] | -11.41 [-15.80; -7.03] (R=8) | -0.0045 [-0.0062; -0.0028] (R=8) | 126 | 7.93 | -5.68 [-10.71; -0.65] (R=8) | -8.72 [-17.99; 0.44] | pierde (con réplicas (8)) |
| H4F-0.25 | H4 | 283.04 (R=8) | 1.04 [-2.02; 4.11] | 1.26 [-1.42; 3.94] (R=8) | -0.0002 [-0.0013; +0.0009] (R=8) | 210 | 4.77 | 4.91 [2.09; 7.73] (R=8) | 2.39 [-4.62; 10.01] | no pierde (con réplicas (8)) |
| H4U-0.1 | H4 | 273.76 (R=8) | -7.70 [-10.81; -4.59] | -8.02 [-11.52; -4.53] (R=8) | -0.0037 [-0.0054; -0.0021] (R=8) | 293 | 3.41 | 3.95 [-1.40; 9.29] (R=8) | 2.91 [-7.54; 14.25] | pierde (con réplicas (8)) |
| H4O-0.5 | H4 | 280.44 (R=8) | -0.71 [-3.83; 2.40] | -1.33 [-4.27; 1.60] (R=8) | +0.0004 [-0.0007; +0.0015] (R=8) | 434 | 2.31 | 4.08 [0.49; 7.67] (R=8) | 4.34 [-3.79; 12.60] | no pierde (con réplicas (8)) |

Notas:

- `U0.05`: sin réplicas
- `U0.1`: sin réplicas
- `U0.25`: sin réplicas
- `U0.5`: sin réplicas
- `B0.1`: sin réplicas
- `B0.25`: sin réplicas
- `B0.5`: sin réplicas
- `GOSS`: sin réplicas

### Varianza entre réplicas y entre semillas

| variante | réplicas | corridas | sd entre réplicas (M$) | sd entre semillas (M$) | varianza entre réplicas |
|---|---|---|---|---|---|
| C | 8 | 160 | 2.78 | 4.53 | 25 % |
| H3-0.05 | 8 | 160 | 2.71 | 3.75 | 32 % |
| H3-0.1 | 8 | 160 | 2.38 | 3.94 | 24 % |
| H3-0.25 | 8 | 160 | 4.72 | 4.45 | 50 % |
| H3K-0.1 | 8 | 160 | 5.51 | 4.31 | 58 % |
| H3L-0.1 | 8 | 160 | 3.55 | 3.58 | 47 % |
| H3L-0.25 | 8 | 160 | 2.45 | 3.90 | 26 % |
| H3R-0.1 | 8 | 160 | 3.48 | 3.57 | 46 % |
| H3R-0.25 | 8 | 160 | 2.41 | 3.68 | 28 % |
| H4F-0.05 | 8 | 160 | 2.80 | 3.96 | 31 % |
| H4F-0.25 | 8 | 160 | 2.15 | 4.43 | 17 % |
| H4H-0.1 | 8 | 160 | 4.91 | 4.83 | 48 % |
| H4O-0.5 | 8 | 160 | 2.69 | 4.50 | 25 % |
| H4U-0.1 | 8 | 160 | 3.65 | 5.57 | 28 % |

### Diferencias entre variantes

| diferencia | Δ [IC entre réplicas] (M$) | réplicas | IC | veredicto |
|---|---|---|---|---|
| H3R-0.1 - H3-0.1 | -0.12 [-1.95; 1.71] | 8 | t, apareado | no cambia |
| H3R-0.25 - H3L-0.25 | 0.72 [-0.90; 2.35] | 8 | t, apareado | no cambia |
| H3R-0.1 - H3L-0.1 | 1.45 [0.65; 2.25] | 8 | t, apareado | mejora |
| H3R-0.25 - H3-0.25 | 0.52 [-1.59; 2.64] | 8 | t, apareado | no cambia |
| H3K-0.1 - H3-0.1 | -1.93 [-6.68; 2.83] | 8 | Welch, sin aparear | no cambia |
| H4H-0.1 - H4U-0.1 | -3.39 [-8.06; 1.28] | 8 | Welch, sin aparear | no cambia |
| H4O-0.5 - H4F-0.05 | -2.74 [-5.69; 0.21] | 8 | Welch, sin aparear | no cambia |

## Bloque B: exploratorios

Las cifras del bloque B no se comparan una a una con las del bloque A: otro protocolo, otra muestra o otro entorno.

### experimentos/h3/sensibilidad_muestra

- **Pregunta:** ¿Cuánto depende de la muestra la configuración que elige H3?
- **Protocolo:** 20 configuraciones al azar, 10 muestras del 25 %, una semilla final, float64, 4 hilos
- **Cifras principales:**
  - 08_ganancia_por_semilla.csv, delta: mediana 0 [-9,900,000; 8,800,000], n = 10
  - 08_ganancia_por_semilla.csv, delta_pct: mediana 0 [-3.622; 3.219], n = 10
  - 07_resumen_por_semilla.csv, delta: mediana 0 [-8.051e-05; 0.002227], n = 10
  - 07_resumen_por_semilla.csv, spearman_seleccion: mediana 0.7752 [0.6647; 0.8165], n = 10
  - 07_resumen_por_semilla.csv, tiempo_busqueda_s: mediana 487 [378; 1,064], n = 10
- **Advertencia:** 10 muestras pero 4 modelos distintos; un solo 201910; no comparable 1:1 con H3-0.25

### experimentos/sampling_1/exploratorios/validacion_20_semillas

- **Pregunta:** ¿Cambian los veredictos de H1 a H4 si el control y cada variante se evalúan con 20 semillas finales en lugar de 10?
- **Protocolo:** 20 semillas finales por variante (lista no publicada), una búsqueda por estudio, reportes por hipótesis hechos con una versión anterior de comun/reporte.py y editados a mano; sin código ni ledger
- **Cifras principales:**
  - reportado_20_semillas.csv, delta_media: mediana -0.6 [-30.75; 6.38], n = 13
  - reportado_20_semillas.csv, tiempo_s: mediana 175 [70; 786], n = 13
  - comparacion_10_semillas.csv, diferencia_delta: mediana 0.88 [-4.12; 9.68], n = 13
- **Advertencia:** solo los HTML (commits d8f04b2 y ffe5cae): no se puede reproducir; H4_HardNeg usa los hiperparámetros fijos del script de Luis (no es H4H-0.1); los tiempos de h2 no coinciden con los medidos; no cambia ningún veredicto

### experimentos/sampling_1/exploratorios/validacion_50_semillas

- **Pregunta:** ¿Con 50 semillas finales, qué estrategias de las hipótesis 3 y 4 ganan al control y cuántas semillas entran en un presupuesto de 900 s?
- **Protocolo:** 9 estrategias con hiperparámetros fijos, 50 semillas finales (10 oficiales + 110017 + i·19937), presupuesto de 900 s; ranking y curva según K en 201908, 201910 solo informado
- **Cifras principales:**
  - resumen_50_semillas_original.csv, g_201908: mediana 201,850,000 [186,450,000; 216,150,000], n = 493
  - resumen_50_semillas_original.csv, gmax_201908: mediana 207,350,000 [196,625,000; 218,075,000], n = 493
  - resumen_50_semillas_original.csv, auc_201908: mediana 0.9274 [0.9236; 0.9311], n = 493
  - resumen_50_semillas_original.csv, g_201910: mediana 278,850,000 [266,750,000; 296,450,000], n = 493
  - resumen_50_semillas_original.csv, auc_201910: mediana 0.9328 [0.9304; 0.9357], n = 493
  - resumen_50_semillas_original.csv, tiempo_s: mediana 19.02 [11.33; 35.72], n = 493
  - ranking_201908_original.csv, puesto_201908: mediana 5 [1; 9], n = 9
  - ranking_201908_original.csv, g_201908: mediana 201,762,698 [196,690,000; 207,856,000], n = 9
  - ranking_201908_original.csv, g_201908_sd: mediana 4,037,318 [3,275,288; 4,559,427], n = 9
  - presupuesto_original.csv, k_presupuesto: mediana 40 [4; 70], n = 9
  - presupuesto_original.csv, ens_k_201908: mediana 205,150,000 [198,550,000; 210,650,000], n = 9
  - presupuesto_original.csv, ens_k_201910: mediana 281,050,000 [278,850,000; 284,350,000], n = 9
- **Advertencia:** origen: commit 9e1889e, script de Colab con su propio panel; el resumen original elige con 201910 (ya mirado) y hay piezas reconstruidas (presupuesto, resumen CSV, H4_Hard); no es una variante ni cambia el veredicto de ninguna hipótesis
