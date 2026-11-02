# Decisiones por hipótesis

Cada decisión aplica la regla escrita en `docs/hipotesis.md` al veredicto de `ledger/apareado.csv` (línea del archivo,
contando el encabezado como 1). Comunes a todas las filas: N* = 3.300 envíos (de 201908), Ḡ_C = 276,10 M$,
δ = 5,52 M$, 10 semillas en común, T(C) = 781,6 s. Figuras en `informe/figuras/` y en `informe/reporte.html`.

## H1 — Submuestreo uniforme del train: ninguna de las dos

| brazo | línea | Δ media (M$) | IC 95% (M$) | veredicto | A |
|---|---|---|---|---|---|
| U0.5 | 11 | −1,32 | [−6,77; 4,13] | indeterminado | 2,28 |
| U0.25 | 10 | −6,38 | [−11,21; −1,55] | pierde | 4,89 |
| U0.1 | 9 | −16,94 | [−23,35; −10,53] | pierde | 9,85 |
| U0.05 | 8 | −33,77 | [−39,84; −27,70] | pierde | 11,38 |

Regla: se confirma si U0.5 y U0.25 *no pierden* y U0.05 *pierde*; se refuta si U0.5 *pierde* o U0.05 *no pierde*.
U0.5 sale *indeterminado* (línea 11) y U0.25 *pierde* (línea 10), así que no se confirma; U0.5 no pierde de forma
declarada y U0.05 pierde (línea 8), así que no se refuta. **Ninguna de las dos.** Frontera observada: ninguna tasa de la
grilla *no pierde*, así que no hay frontera dentro de la grilla. Secundarias: U0.1 *pierde*, como se predijo (línea 9);
A(U0.25) = 4,89 ≥ 2 (línea 10). Figura: `bandas_H1.png`.

## H2 — Muestrear dentro de LightGBM: refutada

| brazo | línea | Δ media (M$) | IC 95% (M$) | veredicto | A |
|---|---|---|---|---|---|
| B0.5 | 4 | −0,11 | [−4,46; 4,24] | no pierde | 0,78 |
| B0.25 | 3 | 0,66 | [−2,86; 4,18] | no pierde | 1,22 |
| B0.1 | 2 | −7,81 | [−12,27; −3,35] | pierde | 1,67 |
| GOSS (descriptivo) | 5 | 0,55 | [−2,60; 3,70] | no pierde | 0,72 |

Regla: se confirma si B0.1 *no pierde*, se refuta si *pierde*. B0.1 *pierde* (línea 2): **refutada**. Con f = 0,5 y
0,25 no pierde (líneas 4 y 3). Secundaria: A(B0.1) = 1,67 ≥ 1,5 (línea 2), pero B0.5 y GOSS son más lentos que el
control (A < 1, líneas 4 y 5). GOSS no decide. Figura: `bandas_H2.png`.

## H3 — Optimizar sobre una muestra, entrenar con todo: confirmada

| brazo | línea | Δ media (M$) | IC 95% (M$) | veredicto | A |
|---|---|---|---|---|---|
| H3-0.25 | 7 | 4,18 | [−0,60; 8,96] | no pierde | 4,50 |
| H3-0.1 | 6 | 4,07 | [−0,27; 8,41] | no pierde | 8,47 |

Regla: se confirma si H3-0.25 *no pierde*. *No pierde* (línea 7): **confirmada**. H3-0.1 también *no pierde* (línea 6).
Secundarias: A(H3-0.25) = 4,50 ≥ 2 y A(H3-0.1) = 8,47 ≥ 4 (líneas 7 y 6). Ninguno *gana*: las cotas inferiores son
negativas. Figura: `bandas_H3.png`.

## Respuesta a la pregunta del tutor

Vale la pena (no pierde y A ≥ 2): **H3-0.1** (A = 8,47, Δ = 4,07 M$, línea 6) y **H3-0.25** (A = 4,50, Δ = 4,18 M$,
línea 7). Ningún otro brazo cumple las dos condiciones: los de H1 con A ≥ 2 pierden o son indeterminados (líneas 8 a
11), y los de H2 que no pierden tienen A < 2 (líneas 3 a 5). Se predijeron H3 con ambas tasas y U0.25; U0.25 falla.
Figura: `tiempo_vs_ganancia.png`.

La comparación a tiempo igual (ensamble de K semillas) queda pendiente: el ledger guarda curvas de ganancia y no las
predicciones, así que el ensamble no se puede armar sin volver a correr los finales (`reporte.html` § Comparación a
tiempo igual muestra los K).
