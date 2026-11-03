# Informe — H2: muestrear dentro de LightGBM

Parte de Sampling_1: la comparación entre hipótesis, la respuesta al tutor y las limitaciones comunes están en el
[informe conjunto](../../sampling_1/informe/informe.md). Las reglas (G, Δ, δ, T, A, N*, veredictos) están en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md). Los números salen de `ledger/apareado.csv` y las figuras de
[`reporte.html`](reporte.html).

## Hipótesis

H2: muestrear dentro de LightGBM (`bagging_fraction` fijo en 0,5, 0,25 o 0,1) no pierde ni con 0,1. GOSS es descriptivo y
no decide. Texto completo en `docs/hipotesis.md`, brazos en `docs/diseno.md`.

## Resultados

N* = 3.300 envíos (de 201908), Ḡ_C = 276,10 M$, δ = 5,52 M$, 10 semillas en común.

| brazo | Δ media (M$) | IC 95% (M$) | A | veredicto | vale la pena |
|---|---|---|---|---|---|
| B0.5 | −0,11 | [−4,46; 4,24] | 0,78 | no pierde | no |
| B0.25 | 0,66 | [−2,86; 4,18] | 1,21 | no pierde | no |
| B0.1 | −7,81 | [−12,27; −3,35] | 1,85 | pierde | no |
| GOSS | 0,55 | [−2,60; 3,70] | 0,72 | no pierde | no |

- **H2, refutada**: con f = 0,1 pierde. Con 0,5 y 0,25 no pierde, pero casi no acelera (A ≤ 1,21), porque el `Dataset`
  completo se arma igual. GOSS no pierde y es más lento que el control.
- Figura: [`bandas_H2.png`](../../sampling_1/informe/figuras/bandas_H2.png) y [`reporte.html`](reporte.html).

## Limitaciones

- **GOSS es descriptivo**: no tiene una regla que decida; su fila se lee como referencia y no como veredicto de H2.
- Adaptación de H2: en los brazos `B*` `bagging_fraction` es la variable y sale del espacio de Optuna, mientras que el
  control y `uniforme` la siguen optimizando. Por eso `bagging` y `uniforme` no tienen la misma fracción efectiva por
  iteración y la comparación entre ellos es solo descriptiva.
- Una sola semilla de Optuna por brazo: Δ incluye la suerte de la optimización y el IC no la mide.
- Un solo año (2019), un solo mes de test (201910) y un solo tipo de máquina; el resto en el informe conjunto.

## Conclusión

Muestrear dentro de LightGBM no ahorra tiempo: el `Dataset` completo se arma igual, así que A queda en 1,85 o menos aun
con f = 0,1, donde además pierde. Comparación con las otras hipótesis y a tiempo igual: informe conjunto.
