# Sampling_1: velocidad sin tocar la proporción de clases

**¿Vale la pena el tradeoff entre velocidad y pérdida de performance?** Sobre el baseline del curso (2019, LightGBM con
Optuna), cuánto tiempo se ahorra y cuánta ganancia se pierde en test (201910) cuando se usan menos filas.

**Hipótesis general:** hay una forma de usar menos filas que *vale la pena*: no pierde ganancia contra el control y es
al menos 2 veces más rápida.

!!! success "Respuesta"
    Vale la pena achicar la **optimización**, al azar: correr Optuna sobre el 10 % de las filas y entrenar el final con
    todas no pierde contra el control y es casi 8 veces más rápido. Si además se quiere un final más rápido, conservar
    todas las bajas y la mitad de CONTINUA con peso 2 tampoco pierde. Ninguna de las dos es una mejora de ganancia por
    modelo: es lo mismo, más rápido, y el tiempo que sobra se puede gastar en ensamblar.

## El mapa del tradeoff

Un panel por hipótesis y un punto por variante, con su intervalo: a la derecha, más rápida que el control; abajo, pierde
ganancia. Las que valen la pena quedan arriba y a la derecha del 2×, y casi todas achican solo la optimización.

<!-- generado:hallazgo-tradeoff -->
![15 de 30 variantes no pierden y aceleran 2× o más; la más rápida entre ellas es H4F-0.05 (12.5×)](experimentos/sampling_1/figuras/tradeoff.svg)

<!-- /generado:hallazgo-tradeoff -->

!!! warning "Limitaciones principales"
    - **Test ya mirado.** H4 y las extensiones de H3 salen de un estudio que miró 201910, y no hay otro mes de test.
    - **Un mes, un año, una máquina.** Solo 2019, solo 201910 como test y tiempos medidos en `n2-highmem-8`.
    - **Ocho réplicas.** Todas las variantes repiten la búsqueda de hiperparámetros ocho veces: alcanza para decidir
      que no pierden, no para separar de cero una ventaja chica.

    El resto, en [Resultados § Limitaciones comunes](experimentos/sampling_1/README.md#limitaciones-comunes).

[Ver los resultados](experimentos/sampling_1/README.md){ .md-button .md-button--primary }

## Hipótesis

<!-- generado:tarjetas -->
<div class="grid cards" markdown>

-   **[H1 · Submuestreo uniforme del train](experimentos/h1/README.md)**

    ---

    H1 prueba si entrenar con una fracción de las filas de train, tomadas al azar sin mirar la clase, acelera sin perder ganancia.

    4 variantes: 3 pierden, 1 indeterminada.

-   **[H2 · Muestrear dentro de LightGBM](experimentos/h2/README.md)**

    ---

    H2 prueba si dejar que LightGBM muestree filas en cada árbol (`bagging_fraction` fijo y bajo), en lugar de achicar el train antes, acelera sin perder ganancia.

    5 variantes: 2 no pierden, 2 pierden, 1 indeterminada.

-   **[H3 · Optimizar sobre una muestra, entrenar con todo](experimentos/h3/README.md)**

    ---

    H3 prueba si alcanza con correr Optuna sobre una muestra chica del train y entrenar el modelo final con todas las filas.

    9 variantes: 9 no pierden. La más rápida que no pierde: H3-0.05 (10.6×).

-   **[H4 · Muestras informadas por clase](experimentos/h4/README.md)**

    ---

    H4 prueba si conviene que la muestra que acelera el pipeline conserve todas las bajas, en la búsqueda de Optuna o en el modelo final.

    12 variantes: 6 no pierden, 4 pierden, 2 indeterminadas. La más rápida que no pierde: H4F-0.05 (12.5×).

</div>

<!-- /generado:tarjetas -->
