# Informe — H1: submuestreo uniforme del train

Parte de Sampling_1: la comparación entre hipótesis, la respuesta al tutor y las limitaciones comunes están en el
[informe conjunto](../../sampling_1/informe/informe.md). Las reglas (G, Δ, δ, T, A, N*, veredictos) están en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md). Los números salen de `ledger/apareado.csv` y las figuras de
[`reporte.html`](reporte.html).

## Hipótesis

H1: submuestrear el train al azar (r = 0,5 a 0,05) no pierde con r ≥ 0,25 y pierde con r = 0,05. Texto completo en
`docs/hipotesis.md`, variantes y grilla en `docs/diseno.md`.

## Resultados

N* = 3.300 envíos (de 201908), Ḡ_C = 276,10 M$, δ = 5,52 M$, 10 semillas en común.

| variante | Δ media (M$) | IC 95% (M$) | A | veredicto | vale la pena |
|---|---|---|---|---|---|
| U0.5 | −1,32 | [−6,77; 4,13] | 2,28 | indeterminado | no |
| U0.25 | −6,38 | [−11,21; −1,55] | 4,89 | pierde | no |
| U0.1 | −16,94 | [−23,35; −10,53] | 9,85 | pierde | no |
| U0.05 | −33,77 | [−39,84; −27,70] | 11,42 | pierde | no |

- **H1, ninguna de las dos**: la pérdida crece a medida que baja r (todas las tasas debajo de 0,5 pierden) y U0.5 queda
  indeterminado. No hay frontera dentro de la grilla.
- Figura: [`bandas_H1.png`](../../sampling_1/informe/figuras/bandas_H1.png) y [`reporte.html`](reporte.html).

## Limitaciones

- Una sola semilla de Optuna por variante: Δ incluye la suerte de la optimización y el IC no la mide.
- Los estudios de U0.25 y U0.1 los usa también H3 (`h3`): Δ(U0.25) y Δ(H3-0.25) no son evidencia independiente entre sí.
- Un solo año (2019), un solo mes de test (201910) y un solo tipo de máquina; el resto en el informe conjunto.

## Conclusión

Entrenar el final con menos filas al azar pierde desde r = 0,25; ninguna tasa de la grilla *no pierde* contra el control con
Optuna propio en cada una. Comparación con las otras hipótesis y a tiempo igual: informe conjunto.
