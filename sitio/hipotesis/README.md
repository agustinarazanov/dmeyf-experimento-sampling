# Hipótesis

<!-- generado:tarjetas -->
Generado por `comun/reporte.py` el 2026-11-13; no editar.

<div class="grid cards" markdown>

-   **[H1 · Submuestreo uniforme del train](../../experimentos/h1/README.md)**

    ---

    H1 prueba si entrenar con una fracción de las filas de train, tomadas al azar sin mirar la clase, acelera sin perder ganancia.

    4 variantes: 1 no pierde, 3 pierden. La más rápida que no pierde: U0.5 (2.2×).

-   **[H2 · Muestrear dentro de LightGBM](../../experimentos/h2/README.md)**

    ---

    H2 prueba si dejar que LightGBM muestree filas en cada árbol (`bagging_fraction` fijo y bajo), en lugar de achicar el train antes, acelera sin perder ganancia.

    4 variantes: 2 no pierden, 1 pierde, 1 indeterminada.

-   **[H3 · Optimizar sobre una muestra, entrenar con todo](../../experimentos/h3/README.md)**

    ---

    H3 prueba si alcanza con correr Optuna sobre una muestra chica del train y entrenar el modelo final con todas las filas.

    8 variantes: 8 no pierden. La más rápida que no pierde: H3-0.05 (10.6×).

-   **[H4 · Muestras informadas por clase](../../experimentos/h4/README.md)**

    ---

    H4 prueba si conviene que la muestra que acelera el pipeline conserve todas las bajas, en la búsqueda de Optuna o en el modelo final.

    5 variantes: 3 no pierden, 2 pierden. La más rápida que no pierde: H4F-0.05 (12.5×).

</div>

<!-- /generado:tarjetas -->
