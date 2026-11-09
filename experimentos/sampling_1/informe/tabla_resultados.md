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
| H3-0.1 | H3 | 278.22 (R=8) | 4.07 [-0.27; 8.41] | 2.30 [-0.88; 5.47] (R=8) | 118 | 8.30 | 4.03 [0.78; 7.27] (R=8) | 4.38 [-3.96; 13.42] | no pierde (con réplicas (8)) |
| H3-0.25 | H3 | 277.74 (R=8) | 4.18 [-0.60; 8.96] | 1.81 [-1.78; 5.41] (R=8) | 216 | 4.53 | 1.83 [-1.91; 5.57] (R=8) | 3.46 [-4.29; 11.77] | no pierde (con réplicas (8)) |

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
| H3R-0.1 | 8 | 80 | 2.99 | 3.81 | 35 % |

### Diferencia apareada por réplica y semilla

| diferencia | Δ [IC t entre réplicas] (M$) | réplicas | veredicto |
|---|---|---|---|
| H3R-0.1 - H3-0.1 | -0.54 [-1.88; 0.81] | 8 | no cambia |

## Bloque B: exploratorios

Las cifras del bloque B no se comparan una a una con las del bloque A: otro protocolo, otra muestra o otro entorno.

| carpeta | autor | pregunta | protocolo | cifras principales | advertencia |
|---|---|---|---|---|---|
| experimentos/h3/sensibilidad_muestra | Martín López | ¿Cuánto depende de la muestra la configuración que elige H3? | 20 configuraciones al azar, 10 muestras del 25 %, una semilla final, float64, 4 hilos | 08_ganancia_por_semilla.csv, delta: mediana 0 [-9,900,000; 8,800,000], n = 10; 08_ganancia_por_semilla.csv, delta_pct: mediana 0 [-3.622; 3.219], n = 10; 07_resumen_por_semilla.csv, delta: mediana 0 [-8.051e-05; 0.002227], n = 10; 07_resumen_por_semilla.csv, spearman_seleccion: mediana 0.7752 [0.6647; 0.8165], n = 10; 07_resumen_por_semilla.csv, tiempo_busqueda_s: mediana 487 [378; 1,064], n = 10 | 10 muestras pero 4 modelos distintos; un solo 201910; no comparable 1:1 con H3-0.25 |
