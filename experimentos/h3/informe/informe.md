# Informe — H3: optimizar sobre una muestra, entrenar con todo

Parte de Sampling_1: la comparación entre hipótesis, la respuesta al tutor y las limitaciones comunes están en el
[informe conjunto](../../sampling_1/informe/informe.md). Las reglas (G, Δ, δ, T, A, N*, veredictos) están en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md). Los números salen de `ledger/apareado.csv` y las figuras de
[`reporte.html`](reporte.html).

## Hipótesis

H3: optimizar con Optuna sobre una muestra uniforme (r_opt = 0,25 o 0,1) y entrenar el final con todo no pierde. Texto
completo en `docs/hipotesis.md`, variantes y dependencias en `docs/diseno.md`.

## Resultados

N* = 3.300 envíos (de 201908), Ḡ_C = 276,10 M$, δ = 5,52 M$, 10 semillas en común.

| variante | Δ media (M$) | IC 95% (M$) | A | veredicto | vale la pena |
|---|---|---|---|---|---|
| H3-0.1 | 4,07 | [−0,27; 8,41] | 8,41 | no pierde | sí |
| H3-0.25 | 4,18 | [−0,60; 8,96] | 4,48 | no pierde | sí |

- **H3, confirmada**: las dos tasas no pierden y aceleran 4,5 y 8,4 veces. Ninguna *gana*: las cotas inferiores son
  negativas, aunque la media de Δ es positiva.
- Figura: [`bandas_H3.png`](../../sampling_1/informe/figuras/bandas_H3.png) y [`reporte.html`](reporte.html).

## Limitaciones

- **Estudios de `h1`**: H3 no corre su propio Optuna; usa los estudios de U0.25 y U0.1 de `h1` (`h1/ledger/hp/`). Δ(H3-0.25)
  y Δ(U0.25) tienen la misma suerte de optimización y no son evidencia independiente entre sí; además, su tiempo de
  optimización sale del ledger de `h1`. Sin esa carpeta, H3 no se puede correr ni consolidar.
- Una sola semilla de Optuna por estudio: Δ incluye la suerte de la optimización y el IC no la mide.
- `min_data_in_leaf` se usa tal como sale de la muestra, sin reescalar.
- Un solo año (2019), un solo mes de test (201910) y un solo tipo de máquina; el resto en el informe conjunto.

## Conclusión

Optimizar sobre el 10% de las filas y entrenar con todas da la misma ganancia que el control (dentro de δ) en un octavo
del tiempo. Como U0.25 usa los mismos hiperparámetros y pierde, lo que se pierde en H1 es por entrenar el final con menos
filas y no por optimizar sobre una muestra. Comparación con las otras hipótesis y a tiempo igual: informe conjunto.
