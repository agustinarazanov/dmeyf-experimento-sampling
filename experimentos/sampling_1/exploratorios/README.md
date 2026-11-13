# Exploratorios

Tres estudios con su propio protocolo, hechos fuera de la grilla y replicados en las VMs del experimento (fase 6 de
[Corridas](../corridas.md)). Motivaron las réplicas de Optuna, H4 y las extensiones de H3, pero no deciden ningún
veredicto: sus cifras salen de otro protocolo, otra muestra u otro entorno, y no se comparan una a una con las de
[Resultados](../README.md).

## `sensibilidad_muestra`

¿Cuánto depende de la muestra la configuración que elige H3? Con 10 muestras del 25 %, la configuración elegida cambia
con la muestra, y la ganancia en 201910 se mueve de −9,9 a +8,8 M$ contra la del control (mediana 0). Es la columna
`delta` de `08_ganancia_por_semilla.csv`, en $; la `delta` de `07_resumen_por_semilla.csv` es diferencia de AUC, no de
ganancia.

Sus pasos 07 y 08 se volvieron a correr en `n2-highmem-8` con otras versiones de Python, LightGBM y numpy, y las
elecciones, los AUC y las ganancias salieron idénticos; solo cambian los tiempos. Va en la misma dirección que las
réplicas de [H3](../../h3/README.md): la suerte de la optimización pesa tanto como la diferencia que se quiere medir. De
acá sale la escala de desvío con la que se eligió R = 8.

Código, reproducción y detalle:
[`experimentos/h3/sensibilidad_muestra/`](https://github.com/agustinarazanov/dmeyf-experimento-sampling/blob/main/experimentos/h3/sensibilidad_muestra/README.md).

## `validacion_50_semillas`

¿Con 50 semillas finales, qué estrategias de H3 y H4 le ganan al control, y cuántas semillas entran en un presupuesto de
900 s? El script se portó al repo, con las piezas sin código reconstruidas y marcadas, y se corrió en `n2-highmem-8`
con sus hiperparámetros. Ordenadas por la ganancia en 201908 (como pide la consigna), el control queda primero y ninguna
estrategia lo supera; el «campeón» de su resumen, elegido mirando 201910, no gana en el mes que decide.

De acá salen H4 y las extensiones de H3, que entraron con reglas escritas antes de correr y declaran que vienen de mirar
201910. Al repetir la búsqueda con réplicas, la búsqueda con negativos difíciles pierde y H3 queda en *no pierde*; la
idea de producción del estudio, el fast-retrain, es la que se sostiene (`H4F-0.05`, en [H4](../../h4/README.md)).

Código, reproducción y detalle:
[`experimentos/sampling_1/exploratorios/validacion_50_semillas/`](https://github.com/agustinarazanov/dmeyf-experimento-sampling/blob/main/experimentos/sampling_1/exploratorios/validacion_50_semillas/README.md).

## `validacion_20_semillas`

¿Cambian los veredictos de H1 a H4 si el control y cada variante se evalúan con 20 semillas finales en lugar de 10? Solo
quedan los HTML de los reportes, sin código ni ledger, así que no se puede reproducir. La pregunta la contesta ahora la
ronda vigente con el protocolo del experimento: 20 semillas publicadas, con réplicas y desde los ledgers. Ningún
veredicto cambia de lado (§ Rondas de [Resultados](../README.md)).

Detalle:
[`experimentos/sampling_1/exploratorios/validacion_20_semillas/`](https://github.com/agustinarazanov/dmeyf-experimento-sampling/blob/main/experimentos/sampling_1/exploratorios/validacion_20_semillas/README.md).

## Cifras

Pregunta, protocolo, cifras principales y advertencia de cada estudio, leídos de su `exploratorio.json` y de sus CSV.

<!-- generado:bloque-b -->
Generado por `comun/reporte.py` el 2026-11-13; no editar.

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
- **Advertencia:** solo los HTML (commits d8f04b2 y ffe5cae): no se puede reproducir; H4_HardNeg usa los hiperparámetros fijos del script de validacion_50_semillas (no es H4H-0.1); los tiempos de h2 no coinciden con los medidos; no cambia ningún veredicto

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

<!-- /generado:bloque-b -->
