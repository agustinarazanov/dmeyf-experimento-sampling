# Resultados de sampling_1

Generado por `python -m comun.reporte --experimento sampling_1`; no editar a mano.

N* = 3,300 envíos; Ḡ_C (réplica 0) = 276.10 M$; Ḡ_C con réplicas = 275.92 M$ (R=8); ensamble de 10 semillas del control = 275.55 M$.

## Bloque A: mismo protocolo

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

### Diferencias entre variantes

| diferencia | Δ [IC entre réplicas] (M$) | réplicas | IC | veredicto |
|---|---|---|---|---|
| H3R-0.1 - H3-0.1 | -0.54 [-1.88; 0.81] | 8 | t, apareado | no cambia |
| H3R-0.25 - H3L-0.25 | 1.28 [-0.98; 3.54] | 8 | t, apareado | no cambia |
| H3R-0.1 - H3L-0.1 | 3.22 [0.63; 5.81] | 8 | t, apareado | mejora |
| H3R-0.25 - H3-0.25 | -0.29 [-2.28; 1.70] | 8 | t, apareado | no cambia |
| H3K-0.1 - H3-0.1 | -1.02 [-5.91; 3.88] | 8 | Welch, sin aparear | no cambia |
| H4H-0.1 - H4U-0.1 | -3.07 [-7.61; 1.47] | 8 | Welch, sin aparear | no cambia |

## Bloque B: exploratorios

Las cifras del bloque B no se comparan una a una con las del bloque A: otro protocolo, otra muestra o otro entorno.

| carpeta | autor | pregunta | protocolo | cifras principales | advertencia |
|---|---|---|---|---|---|
| experimentos/h3/sensibilidad_muestra | Martín López | ¿Cuánto depende de la muestra la configuración que elige H3? | 20 configuraciones al azar, 10 muestras del 25 %, una semilla final, float64, 4 hilos | 08_ganancia_por_semilla.csv, delta: mediana 0 [-9,900,000; 8,800,000], n = 10; 08_ganancia_por_semilla.csv, delta_pct: mediana 0 [-3.622; 3.219], n = 10; 07_resumen_por_semilla.csv, delta: mediana 0 [-8.051e-05; 0.002227], n = 10; 07_resumen_por_semilla.csv, spearman_seleccion: mediana 0.7752 [0.6647; 0.8165], n = 10; 07_resumen_por_semilla.csv, tiempo_busqueda_s: mediana 487 [378; 1,064], n = 10 | 10 muestras pero 4 modelos distintos; un solo 201910; no comparable 1:1 con H3-0.25 |
| experimentos/sampling_1/exploratorios/validacion_20_semillas | Luis María Laguinge | ¿Cambian los veredictos de H1 a H4 si el control y cada variante se evalúan con 20 semillas finales en lugar de 10? | 20 semillas finales por variante (lista no publicada), una búsqueda por estudio, reportes por hipótesis hechos con una versión anterior de comun/reporte.py y editados a mano; sin código ni ledger | reportado_20_semillas.csv, delta_media: mediana -0.6 [-30.75; 6.38], n = 13; reportado_20_semillas.csv, tiempo_s: mediana 175 [70; 786], n = 13; comparacion_10_semillas.csv, diferencia_delta: mediana 0.88 [-4.12; 9.68], n = 13 | solo los HTML (commits d8f04b2 y ffe5cae): no se puede reproducir; H4_HardNeg usa los hiperparámetros fijos del script de Luis (no es H4H-0.1); los tiempos de h2 no coinciden con los medidos; no cambia ningún veredicto |
| experimentos/sampling_1/exploratorios/validacion_50_semillas | Luis María Laguinge | ¿Con 50 semillas finales, qué estrategias de las hipótesis 3 y 4 ganan al control y cuántas semillas entran en un presupuesto de 900 s? | 9 estrategias con hiperparámetros fijos, 50 semillas finales (10 oficiales + 110017 + i·19937), presupuesto de 900 s; ranking y curva según K en 201908, 201910 solo informado | resumen_50_semillas_original.csv, g_201908: mediana 201,850,000 [186,450,000; 216,150,000], n = 493; resumen_50_semillas_original.csv, gmax_201908: mediana 207,350,000 [196,625,000; 218,075,000], n = 493; resumen_50_semillas_original.csv, auc_201908: mediana 0.9274 [0.9236; 0.9311], n = 493; resumen_50_semillas_original.csv, g_201910: mediana 278,850,000 [266,750,000; 296,450,000], n = 493; resumen_50_semillas_original.csv, auc_201910: mediana 0.9328 [0.9304; 0.9357], n = 493; resumen_50_semillas_original.csv, tiempo_s: mediana 19.02 [11.33; 35.72], n = 493; ranking_201908_original.csv, puesto_201908: mediana 5 [1; 9], n = 9; ranking_201908_original.csv, g_201908: mediana 201,762,698 [196,690,000; 207,856,000], n = 9; ranking_201908_original.csv, g_201908_sd: mediana 4,037,318 [3,275,288; 4,559,427], n = 9; presupuesto_original.csv, k_presupuesto: mediana 40 [4; 70], n = 9; presupuesto_original.csv, ens_k_201908: mediana 205,150,000 [198,550,000; 210,650,000], n = 9; presupuesto_original.csv, ens_k_201910: mediana 281,050,000 [278,850,000; 284,350,000], n = 9 | origen: commit 9e1889e, script de Colab con su propio panel; el resumen original elige con 201910 (ya mirado) y hay piezas reconstruidas (presupuesto, resumen CSV, H4_Hard); no es una variante ni cambia el veredicto de ninguna hipótesis |
