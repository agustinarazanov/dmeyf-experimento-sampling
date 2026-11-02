# Decisiones por hipótesis

Cada decisión aplica la regla escrita en `docs/hipotesis.md` al veredicto de `ledger/apareado.csv` (línea del archivo,
contando el encabezado como 1). Comunes a todas las filas: N* = 3.300 envíos (de 201908), Ḡ_C = 276,10 M$,
δ = 5,52 M$, 10 semillas en común, T(C) = 783,2 s. Los tiempos son los de la fase 4 (finales repetidos con
predicciones, D12); las ganancias son idénticas a las de las fases 1 a 3 (bitácora, tarea 6.6). Figuras en
`informe/figuras/` y en `informe/reporte.html`.

## H1 — Submuestreo uniforme del train: ninguna de las dos

| brazo | línea | Δ media (M$) | IC 95% (M$) | veredicto | A |
|---|---|---|---|---|---|
| U0.5 | 11 | −1,32 | [−6,77; 4,13] | indeterminado | 2,28 |
| U0.25 | 10 | −6,38 | [−11,21; −1,55] | pierde | 4,89 |
| U0.1 | 9 | −16,94 | [−23,35; −10,53] | pierde | 9,85 |
| U0.05 | 8 | −33,77 | [−39,84; −27,70] | pierde | 11,42 |

Regla: se confirma si U0.5 y U0.25 *no pierden* y U0.05 *pierde*; se refuta si U0.5 *pierde* o U0.05 *no pierde*.
U0.5 sale *indeterminado* (línea 11) y U0.25 *pierde* (línea 10), así que no se confirma; U0.5 no pierde de forma
declarada y U0.05 pierde (línea 8), así que no se refuta. **Ninguna de las dos.** Frontera observada: ninguna tasa de la
grilla *no pierde*, así que no hay frontera dentro de la grilla. Secundarias: U0.1 *pierde*, como se predijo (línea 9);
A(U0.25) = 4,89 ≥ 2 (línea 10). Figura: `bandas_H1.png`.

## H2 — Muestrear dentro de LightGBM: refutada

| brazo | línea | Δ media (M$) | IC 95% (M$) | veredicto | A |
|---|---|---|---|---|---|
| B0.5 | 4 | −0,11 | [−4,46; 4,24] | no pierde | 0,78 |
| B0.25 | 3 | 0,66 | [−2,86; 4,18] | no pierde | 1,21 |
| B0.1 | 2 | −7,81 | [−12,27; −3,35] | pierde | 1,85 |
| GOSS (descriptivo) | 5 | 0,55 | [−2,60; 3,70] | no pierde | 0,72 |

Regla: se confirma si B0.1 *no pierde*, se refuta si *pierde*. B0.1 *pierde* (línea 2): **refutada**. Con f = 0,5 y
0,25 no pierde (líneas 4 y 3). Secundaria: A(B0.1) = 1,85 ≥ 1,5 (línea 2), pero B0.5 y GOSS son más lentos que el
control (A < 1, líneas 4 y 5). GOSS no decide. Figura: `bandas_H2.png`.

## H3 — Optimizar sobre una muestra, entrenar con todo: confirmada

| brazo | línea | Δ media (M$) | IC 95% (M$) | veredicto | A |
|---|---|---|---|---|---|
| H3-0.25 | 7 | 4,18 | [−0,60; 8,96] | no pierde | 4,48 |
| H3-0.1 | 6 | 4,07 | [−0,27; 8,41] | no pierde | 8,41 |

Regla: se confirma si H3-0.25 *no pierde*. *No pierde* (línea 7): **confirmada**. H3-0.1 también *no pierde* (línea 6).
Secundarias: A(H3-0.25) = 4,48 ≥ 2 y A(H3-0.1) = 8,41 ≥ 4 (líneas 7 y 6). Ninguno *gana*: las cotas inferiores son
negativas. Figura: `bandas_H3.png`.

## Respuesta a la pregunta del tutor

Vale la pena (no pierde y A ≥ 2): **H3-0.1** (A = 8,41, Δ = 4,07 M$, línea 6) y **H3-0.25** (A = 4,48, Δ = 4,18 M$,
línea 7). Ningún otro brazo cumple las dos condiciones: los de H1 con A ≥ 2 pierden o son indeterminados (líneas 8 a
11), y los de H2 que no pierden tienen A < 2 (líneas 3 a 5). Se predijeron H3 con ambas tasas y U0.25; U0.25 falla.
Figura: `tiempo_vs_ganancia.png`.

### A tiempo igual

Cada brazo gasta el tiempo que le sobra respecto del control en K modelos finales, K = ⌊(T(C) − T_opt) / T_final⌋
acotado a 10, y se mide la ganancia en 201910 al corte N* del promedio de sus probabilidades (`reporte.html`
§ Comparación a tiempo igual). Referencias: Ḡ_C = 276,10 M$ (un modelo del control) y el ensamble de las 10 semillas del
control, 275,55 M$.

| brazo | K | G del ensamble (M$) | G − Ḡ_C (M$) | G − ensamble de C (M$) |
|---|---|---|---|---|
| U0.5 | 29 (se usan 10) | 282,15 | 6,05 | 6,60 |
| H3-0.1 | 43 (se usan 10) | 279,95 | 3,85 | 4,40 |
| H3-0.25 | 29 (se usan 10) | 278,85 | 2,75 | 3,30 |
| U0.25 | 92 (se usan 10) | 276,65 | 0,55 | 1,10 |
| B0.25 | 5 | 276,65 | 0,55 | 1,10 |
| U0.1 | 267 (se usan 10) | 271,15 | −4,95 | −4,40 |
| B0.1 | 20 (se usan 10) | 271,15 | −4,95 | −4,40 |
| U0.05 | 425 (se usan 10) | 252,45 | −23,65 | −23,10 |
| B0.5, GOSS | 0 | no aplica (K < 2) | | |

Predicción de `hipotesis.md`: a tiempo igual la variante rápida gana y H3 es la que más rinde. **Se cumple en parte.**
Cinco de los ocho brazos con ensamble quedan por encima de Ḡ_C (U0.5, los dos H3, U0.25 y B0.25), pero los tres más
agresivos quedan por debajo (U0.1, B0.1, U0.05). H3 no es la que más rinde: U0.5 la supera por 2,2 M$. Hay que leerlo
con cuidado. Cada ensamble es un solo número sobre un solo mes, sin intervalo. A N* fijo la ganancia se mueve en pasos
de 1,1 M$ (un BAJA+2 más o menos), y solo U0.5 supera a Ḡ_C por más de δ = 5,52 M$. Además, ensamblar no le agrega
nada al control: sus 10 semillas promediadas dan 0,55 M$ menos que un modelo medio. Lo que sí es firme es la
lista de la respuesta de arriba. Los brazos que valen la pena a datos iguales (H3-0.1 y H3-0.25) siguen por encima del
control a tiempo igual. Los tres más agresivos, que pierden a datos iguales, no se rescatan ensamblando. U0.25 también
pierde a datos iguales y a tiempo igual queda a la par del control (+0,55 M$, menos de un BAJA+2). Figura:
`tiempo_igual.png`.
