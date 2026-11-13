# Informe — H1: submuestreo uniforme del train

Parte de Sampling_1: la comparación entre hipótesis, la respuesta al tutor y las limitaciones comunes están en el
[informe conjunto](../../sampling_1/informe/informe.md). Las reglas (G, Δ, δ, T, A, N*, veredictos) están en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md). Los números salen de `ledger/apareado.csv` (copiados en el
bloque A de [`tabla_resultados.md`](../../sampling_1/informe/tabla_resultados.md)) y las figuras de
[`reporte.html`](reporte.html).

## Hipótesis

H1: submuestrear el train al azar (r = 0,5 a 0,05) no pierde con r ≥ 0,25 y pierde con r = 0,05. Texto completo en
`docs/hipotesis.md`, variantes y grilla en `docs/diseno.md`.

**Ronda 201903–201908.** Los números son de la ronda vigente: el final entrena con 201903–201908 (Zulip 211210) y se
evalúa en test (201910) con 20 semillas; los estudios de Optuna se reusan (train 201903–201906, validación 201908). El
veredicto sale de la ganancia y el AUC va al lado (Zulip 208135). Los dos apartamientos están justificados en
[`docs/diseno.md`](../docs/diseno.md) § Ronda 201903–201908 y en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Apartamientos del baseline. La ronda anterior (final
201903–201906, 10 semillas) está en [`comparacion_rondas.md`](../../sampling_1/informe/comparacion_rondas.md).

## Resultados

N* = 3.300 envíos (fijo), Ḡ_C = 282,48 M$, δ = 5,65 M$, 20 semillas en común.

| variante | Δ media (M$) | IC 95% (M$) | ΔAUC en 201910 [IC] | A | veredicto | vale la pena |
|---|---|---|---|---|---|---|
| U0.5 | −1,38 | [−3,99; 1,24] | −0,0019 [−0,0023; −0,0015] | 2,25 | no pierde | sí |
| U0.25 | −9,57 | [−12,65; −6,49] | −0,0055 [−0,0060; −0,0050] | 4,87 | pierde | no |
| U0.1 | −16,28 | [−19,83; −12,73] | −0,0103 [−0,0111; −0,0095] | 9,89 | pierde | no |
| U0.05 | −30,14 | [−34,56; −25,72] | −0,0176 [−0,0186; −0,0166] | 11,45 | pierde | no |

- **H1, ninguna de las dos**: U0.5 *no pierde*, pero U0.25 ya *pierde*, así que la predicción para r = 0,25 no se
  cumple. La frontera observada es r = 0,5: la menor tasa que *no pierde* con todas las mayores. La pérdida crece a
  medida que baja r. En la ronda anterior U0.5 quedaba *indeterminado* y no había frontera: con 20 semillas el IC se
  angosta lo suficiente para decidir.
- **AUC y ganancia** van en la misma dirección en las cuatro tasas: menos filas ordena peor y gana menos.
- Figura: [`bandas_H1.png`](../../sampling_1/informe/figuras/bandas_H1.png) y [`reporte.html`](reporte.html).

## Limitaciones

Solo lo que no está justificado en el diseño:

- Los hiperparámetros elegidos con cuatro meses se usan sin cambios en un final de seis.
- Una sola semilla de Optuna por variante: Δ incluye la suerte de la optimización y el IC no la mide.
- Los estudios de U0.25 y U0.1 los usa también H3 (`h3`): Δ(U0.25) y Δ(H3-0.25) no son evidencia independiente entre sí.
- Un solo año (2019), un solo mes de test (201910) y un solo tipo de máquina; el resto en el informe conjunto.

## Conclusión

Entrenar el final con menos filas al azar pierde desde r = 0,25; solo r = 0,5 *no pierde*, con A = 2,25. Comparación
con las otras hipótesis, a tiempo igual y entre rondas: informe conjunto.
