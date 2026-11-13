# Sampling_1: velocidad sin tocar la proporción de clases

**¿Vale la pena el tradeoff entre velocidad y pérdida de performance?** Sobre el baseline del curso (2019, LightGBM con
Optuna), cuánto tiempo se ahorra y cuánta ganancia se pierde en test (201910) cuando se usan menos filas.

!!! success "Respuesta"
    Vale la pena achicar la **optimización**: correr Optuna sobre una muestra al azar y entrenar el final con todas las
    filas no pierde contra el control y es varias veces más rápido. Achicar el final al azar sí pierde; conservando todas
    las bajas y la mitad de CONTINUA con peso, no.

## Resultados

### ¿Cuánto se pierde y cuánto se gana?

<!-- generado:hallazgo-tradeoff -->
Generado por `comun/reporte.py` el 2026-11-13; no editar.

![12 de 21 variantes no pierden y aceleran 2× o más; la más rápida entre ellas es H4F-0.05 (12.5×)](experimentos/sampling_1/figuras/tradeoff.svg)

<!-- /generado:hallazgo-tradeoff -->

### ¿Dónde se va el tiempo?

<!-- generado:hallazgo-tiempo -->
Generado por `comun/reporte.py` el 2026-11-13; no editar.

![En el control la optimización es el 94 % de T (748 s de 797 s); la variante con la optimización más corta, U0.05, la baja a 67 s](experimentos/sampling_1/figuras/desglose_tiempo.svg)

<!-- /generado:hallazgo-tiempo -->

### ¿Y con el tiempo ahorrado?

<!-- generado:hallazgo-ensamble -->
Generado por `comun/reporte.py` el 2026-11-13; no editar.

![](experimentos/sampling_1/figuras/tiempo_igual.svg)

<!-- /generado:hallazgo-ensamble -->

[Ver los resultados](experimentos/sampling_1/README.md){ .md-button .md-button--primary }

## Hipótesis

<!-- generado:tarjetas -->
Generado por `comun/reporte.py` el 2026-11-13; no editar.

<div class="grid cards" markdown>

-   **[H1 · Submuestreo uniforme del train](experimentos/h1/README.md)**

    ---

    H1 prueba si entrenar con una fracción de las filas de train, tomadas al azar sin mirar la clase, acelera sin perder ganancia.

    4 variantes: 1 no pierde, 3 pierden. La más rápida que no pierde: U0.5 (2.2×).

-   **[H2 · Muestrear dentro de LightGBM](experimentos/h2/README.md)**

    ---

    H2 prueba si dejar que LightGBM muestree filas en cada árbol (`bagging_fraction` fijo y bajo), en lugar de achicar el train antes, acelera sin perder ganancia.

    4 variantes: 2 no pierden, 1 pierde, 1 indeterminada.

-   **[H3 · Optimizar sobre una muestra, entrenar con todo](experimentos/h3/README.md)**

    ---

    H3 prueba si alcanza con correr Optuna sobre una muestra chica del train y entrenar el modelo final con todas las filas.

    8 variantes: 8 no pierden. La más rápida que no pierde: H3-0.05 (10.6×).

-   **[H4 · Muestras informadas por clase](experimentos/h4/README.md)**

    ---

    H4 prueba si conviene que la muestra que acelera el pipeline conserve todas las bajas, en la búsqueda de Optuna o en el modelo final.

    5 variantes: 3 no pierden, 2 pierden. La más rápida que no pierde: H4F-0.05 (12.5×).

</div>

<!-- /generado:tarjetas -->
