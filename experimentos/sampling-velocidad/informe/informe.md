# Informe — Sampling_1: velocidad contra ganancia

Comisión lunes: Agustina Razanov, Martín López, Luis María Laguinge. Tutor: Joaquín I. Aramendía. Los números salen de
`ledger/apareado.csv` (por línea en `informe/decisiones.md`) y las figuras de `informe/reporte.html` y
`informe/figuras/`.

## Hipótesis

Pregunta del tutor (Zulip 208986): ¿vale la pena el tradeoff entre velocidad y pérdida de performance? Sobre el baseline
de Bolaños (208135) medimos cuánto tiempo se ahorra y cuánta ganancia se pierde en 201910 con menos filas, sin cambiar la
proporción de clases (eso lo estudia Sampling_2).

- **H1**: submuestrear el train al azar (r = 0,5 a 0,05) no pierde con r ≥ 0,25 y pierde con r = 0,05.
- **H2**: muestrear dentro de LightGBM (`bagging_fraction` fijo en 0,5, 0,25 o 0,1) no pierde ni con 0,1.
- **H3**: optimizar con Optuna sobre una muestra (r_opt = 0,25 o 0,1) y entrenar el final con todo no pierde.
- Un brazo **vale la pena** si no pierde y además es al menos 2 veces más rápido (A ≥ 2).

## Diseño

Diez brazos contra el control, cada uno con su propio Optuna (40 trials, AUC en 201908) y 10 semillas finales iguales en
todos. Decide la ganancia en 201910 al corte N* = 3.300 envíos, que sale del control en 201908. Δ es la diferencia contra
el control apareada por semilla, con IC 95% t. Con δ = 2% de la ganancia del control (5,52 M$): *no pierde* si la cota
inferior del IC es ≥ −δ, *pierde* si la media es < −δ, *indeterminado* en el resto. T es el tiempo de la optimización más
un modelo final, medido en `n2-highmem-8`. Tres fases en VMs spot, 119 corridas válidas, un solo tipo de máquina. Detalle
en `docs/hipotesis.md` y `docs/diseno.md`.

## Resultados

| brazo | Δ media (M$) | IC 95% (M$) | A | veredicto | vale la pena |
|---|---|---|---|---|---|
| H3-0.1 | 4,07 | [−0,27; 8,41] | 8,47 | no pierde | sí |
| H3-0.25 | 4,18 | [−0,60; 8,96] | 4,50 | no pierde | sí |
| U0.5 | −1,32 | [−6,77; 4,13] | 2,28 | indeterminado | no |
| U0.25 | −6,38 | [−11,21; −1,55] | 4,89 | pierde | no |
| U0.1 | −16,94 | [−23,35; −10,53] | 9,85 | pierde | no |
| U0.05 | −33,77 | [−39,84; −27,70] | 11,38 | pierde | no |
| B0.5 | −0,11 | [−4,46; 4,24] | 0,78 | no pierde | no |
| B0.25 | 0,66 | [−2,86; 4,18] | 1,22 | no pierde | no |
| B0.1 | −7,81 | [−12,27; −3,35] | 1,67 | pierde | no |
| GOSS | 0,55 | [−2,60; 3,70] | 0,72 | no pierde | no |

Figura principal: `figuras/tiempo_vs_ganancia.png`. Bandas de curvas por hipótesis: `figuras/bandas_H1.png`,
`bandas_H2.png`, `bandas_H3.png`.

- **H1, ninguna de las dos**: la pérdida crece a medida que baja r (todas las tasas debajo de 0,5 pierden) y U0.5 queda
  indeterminado. No hay frontera dentro de la grilla.
- **H2, refutada**: con f = 0,1 pierde. Con 0,5 y 0,25 no pierde, pero casi no acelera (A ≤ 1,22), porque el `Dataset`
  completo se arma igual. GOSS no pierde y es más lento que el control.
- **H3, confirmada**: las dos tasas no pierden y aceleran 4,5 y 8,5 veces. Ninguna *gana*: las cotas inferiores son
  negativas, aunque la media de Δ es positiva.
- U0.25 y H3-0.25 comparten el estudio de Optuna, o sea los mismos hiperparámetros. U0.25 pierde y H3-0.25 no, así que en
  H1 lo que se pierde es por entrenar el final con menos filas, no por optimizar sobre una muestra.

## Limitaciones

- Una sola semilla de Optuna por brazo: Δ incluye la suerte de la optimización y el IC no la mide.
- U0.25/H3-0.25 y U0.1/H3-0.1 comparten estudio: no son evidencia independiente entre sí.
- La réplica del control (C-rep) se corrió en otra VM de la misma cuenta, no por otra persona.
- La comparación a tiempo igual (ensamble de K semillas del brazo rápido) quedó pendiente: el ledger guarda las curvas
  de ganancia y no las predicciones, y el ensamble no se puede armar sin volver a correr los finales. El reporte muestra
  los K.
- Un solo año (2019) y un solo mes de test (201910). Los tiempos valen para `n2-highmem-8` y en otra máquina solo se
  trasladan las aceleraciones relativas.
- `num_iterations = 100` fijo y `force_col_wise`: T(C) no es el tiempo del baseline con la configuración automática.
- H4 (submuestreo informado y pesos) no se corrió en esta grilla.

## Conclusiones

El tradeoff vale la pena si lo que se achica es la **optimización**, no el entrenamiento del modelo final. Optimizar
sobre el 10% de las filas y entrenar con todas da la misma ganancia que el control (dentro de δ) en un octavo del tiempo.
Entrenar el final con menos filas sí pierde, al azar desde r = 0,25 y dentro de LightGBM con f = 0,1. Por qué: la
optimización es lo que domina T (40 trials contra un solo final), y los hiperparámetros que elige Optuna se trasladan
bien de la muestra al total.

## Qué seguiría

- Guardar las predicciones de los finales y armar la comparación a tiempo igual.
- Reescalar `min_data_in_leaf` al pasar de la muestra al total en H3, y bajar r_opt debajo de 0,1.
- Más semillas de Optuna para medir la suerte de la optimización.
- Correr H4 con el mismo control y el mismo ledger.

## Bibliografía (para postear en Zulip)

- Ke, G. et al. (2017). *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*. NeurIPS 30. (GOSS)
- Friedman, J. H. (2002). *Stochastic Gradient Boosting*. Computational Statistics & Data Analysis 38(4). (bagging por
  iteración)
- Akiba, T. et al. (2019). *Optuna: A Next-generation Hyperparameter Optimization Framework*. KDD.
- Bergstra, J. et al. (2011). *Algorithms for Hyper-Parameter Optimization*. NeurIPS 24. (TPE)
- Bolaños, baseline oficial del experimento colaborativo, Zulip 208135 (28-oct-2026).
