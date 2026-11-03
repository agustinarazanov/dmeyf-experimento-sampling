# Informe — Sampling_1: velocidad contra ganancia

Comisión lunes: Agustina Razanov, Martín López, Luis María Laguinge. Tutor: Joaquín I. Aramendía. Los números salen de
`apareado.csv` de `h1`, `h2` y `h3` (`ledger/apareado_previo.csv` es la copia anterior a la separación,
que cita por línea `informe/decisiones.md`) y las figuras de `informe/reporte.html` y `informe/figuras/`. El informe de
cada hipótesis está en [`h1`](../../h1/informe/informe.md), [`h2`](../../h2/informe/informe.md) y
[`h3`](../../h3/informe/informe.md); acá va la comparación y lo que es común.

## Hipótesis

Pregunta del tutor (Zulip 208986): ¿vale la pena el tradeoff entre velocidad y pérdida de performance? Sobre el baseline
de Bolaños (208135) medimos cuánto tiempo se ahorra y cuánta ganancia se pierde en 201910 con menos filas, sin cambiar la
proporción de clases (eso lo estudia Sampling_2).

- **H1**: submuestrear el train al azar (r = 0,5 a 0,05) no pierde con r ≥ 0,25 y pierde con r = 0,05.
- **H2**: muestrear dentro de LightGBM (`bagging_fraction` fijo en 0,5, 0,25 o 0,1) no pierde ni con 0,1.
- **H3**: optimizar con Optuna sobre una muestra (r_opt = 0,25 o 0,1) y entrenar el final con todo no pierde.
- Un brazo **vale la pena** si no pierde y además es al menos 2 veces más rápido (A ≥ 2).

## Diseño

Diez brazos contra el control, cada uno con su Optuna (40 trials, AUC en 201908; H3 reusa los estudios de U0.25 y U0.1)
y 10 semillas finales iguales en todos. Decide la ganancia en 201910 al corte N* = 3.300 envíos, que sale del control en 201908. Δ es la diferencia contra
el control apareada por semilla, con IC 95% t. Con δ = 2% de la ganancia del control (5,52 M$): *no pierde* si la cota
inferior del IC es ≥ −δ, *pierde* si la media es < −δ, *indeterminado* en el resto. T es el tiempo de la optimización más
un modelo final, medido en `n2-highmem-8`. Tres fases en VMs spot y una cuarta que repite los finales guardando
predicciones: 129 corridas válidas en `resultados.csv` (9 optimizaciones y 120 finales de 12 brazos, C-rep incluido), un
solo tipo de máquina. Detalle en `docs/hipotesis.md` y `docs/diseno.md`.

## Resultados

| brazo | Δ media (M$) | IC 95% (M$) | A | veredicto | vale la pena |
|---|---|---|---|---|---|
| H3-0.1 | 4,07 | [−0,27; 8,41] | 8,41 | no pierde | sí |
| H3-0.25 | 4,18 | [−0,60; 8,96] | 4,48 | no pierde | sí |
| U0.5 | −1,32 | [−6,77; 4,13] | 2,28 | indeterminado | no |
| U0.25 | −6,38 | [−11,21; −1,55] | 4,89 | pierde | no |
| U0.1 | −16,94 | [−23,35; −10,53] | 9,85 | pierde | no |
| U0.05 | −33,77 | [−39,84; −27,70] | 11,42 | pierde | no |
| B0.5 | −0,11 | [−4,46; 4,24] | 0,78 | no pierde | no |
| B0.25 | 0,66 | [−2,86; 4,18] | 1,21 | no pierde | no |
| B0.1 | −7,81 | [−12,27; −3,35] | 1,85 | pierde | no |
| GOSS | 0,55 | [−2,60; 3,70] | 0,72 | no pierde | no |

Figura principal: `figuras/tiempo_vs_ganancia.png`. Bandas de curvas por hipótesis: `figuras/bandas_H1.png`,
`bandas_H2.png`, `bandas_H3.png`.

- **H1, ninguna de las dos** (informe de [`h1`](../../h1/informe/informe.md)): la pérdida crece a medida que baja r y
  U0.5 queda indeterminado.
- **H2, refutada** ([`h2`](../../h2/informe/informe.md)): con f = 0,1 pierde y con 0,5 y 0,25 casi no acelera (A ≤ 1,21).
  GOSS es descriptivo.
- **H3, confirmada** ([`h3`](../../h3/informe/informe.md)): las dos tasas no pierden y aceleran 4,5 y 8,4 veces.
- U0.25 y H3-0.25 comparten el estudio de Optuna, o sea los mismos hiperparámetros. U0.25 pierde y H3-0.25 no, así que en
  H1 lo que se pierde es por entrenar el final con menos filas, no por optimizar sobre una muestra.
- **A tiempo igual** (`figuras/tiempo_igual.png`, `decisiones.md` § A tiempo igual): cada brazo gasta el tiempo que le
  sobra en un ensamble de K semillas (K ≤ 10). Contra Ḡ_C = 276,10 M$ quedan arriba U0.5 (+6,05), H3-0.1 (+3,85),
  H3-0.25 (+2,75), U0.25 y B0.25 (+0,55), y abajo U0.1 y B0.1 (−4,95) y U0.05 (−23,65). El ensamble de las 10 semillas
  del control da 275,55 M$, o sea que ensamblar casi no suma. La predicción (la variante rápida gana y H3 es la que más
  rinde) se cumple en parte: cinco de los ocho brazos con ensamble quedan arriba de Ḡ_C, pero los tres más agresivos
  quedan abajo y es U0.5, no H3, la que más rinde. Como referencia, solo U0.5 supera a Ḡ_C por más de δ.

## Limitaciones

- Las limitaciones propias de cada hipótesis (GOSS descriptivo y adaptación de `bagging_fraction` en H2, estudios
  compartidos con `h1` en H3) están en su informe.
- Una sola semilla de Optuna por brazo: Δ incluye la suerte de la optimización y el IC no la mide.
- U0.25/H3-0.25 y U0.1/H3-0.1 comparten estudio: no son evidencia independiente entre sí.
- La réplica del control (C-rep) se corrió en otra VM de la misma cuenta, no por otra persona.
- La comparación a tiempo igual da un solo número por brazo (un ensamble, un mes), sin intervalo. A N* fijo la
  ganancia se mueve en pasos de 1,1 M$, así que diferencias de uno o dos BAJA+2 no se distinguen del ruido. Para
  armarla hubo que repetir los finales guardando predicciones (fase 4). Las ganancias salieron idénticas, pero los
  tiempos (y por lo tanto A y K) son los de esa repetición.
- Un solo año (2019) y un solo mes de test (201910). Los tiempos valen para `n2-highmem-8` y en otra máquina solo se
  trasladan las aceleraciones relativas.
- `num_iterations = 100` fijo y `force_col_wise`: T(C) no es el tiempo del baseline con la configuración automática.
- H4 (submuestreo informado y pesos) no se corrió en esta grilla.

## Conclusiones

El tradeoff vale la pena si lo que se achica es la **optimización**, no el entrenamiento del modelo final. Optimizar
sobre el 10% de las filas y entrenar con todas da la misma ganancia que el control (dentro de δ) en un octavo del tiempo.
Entrenar el final con menos filas sí pierde, al azar desde r = 0,25 y dentro de LightGBM con f = 0,1. Por qué: la
optimización es lo que domina T (en el control, 748 s de Optuna contra 35 s de un final; tabla de `reporte.html`
§ A tiempo igual y `control/ledger/estudios.csv`), y los hiperparámetros que elige Optuna se trasladan
bien de la muestra al total. Gastar el tiempo ahorrado en más semillas no cambia la respuesta. Los dos H3 siguen
arriba del control y los brazos agresivos siguen abajo. El único que mejora de forma notable es U0.5, que a datos
iguales era indeterminado. Como es un solo número sin intervalo, no alcanza para declararlo ganador.

## Qué seguiría

- Repetir la comparación a tiempo igual en otro mes de test (o con bootstrap de clientes) para darle un intervalo.
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
