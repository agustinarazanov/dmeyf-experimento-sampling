# Informe — H2: muestrear dentro de LightGBM

Parte de Sampling_1: la comparación entre hipótesis, la respuesta al tutor y las limitaciones comunes están en el
[informe conjunto](../../sampling_1/informe/informe.md). Las reglas (G, Δ, δ, T, A, N*, veredictos) están en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md). Los números salen de `ledger/apareado.csv` (copiados en el
bloque A de [`tabla_resultados.md`](../../sampling_1/informe/tabla_resultados.md)) y las figuras de
[`reporte.html`](reporte.html).

## Hipótesis

H2: muestrear dentro de LightGBM (`bagging_fraction` fijo en 0,5, 0,25 o 0,1) no pierde ni con 0,1. GOSS es descriptivo y
no decide. Texto completo en `docs/hipotesis.md`, variantes en `docs/diseno.md`.

**Ronda 201903–201908.** Los números son de la ronda vigente: el final entrena con 201903–201908 (Zulip 211210) y se
evalúa en test (201910) con 20 semillas; los estudios de Optuna se reusan. El veredicto sale de la ganancia y el AUC va
al lado (Zulip 208135). Los dos apartamientos están justificados en [`docs/diseno.md`](../docs/diseno.md) § Ronda
201903–201908 y en [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Apartamientos del baseline. La ronda
anterior está en [`comparacion_rondas.md`](../../sampling_1/informe/comparacion_rondas.md).

## Resultados

N* = 3.300 envíos (fijo), Ḡ_C = 282,48 M$, δ = 5,65 M$, 20 semillas en común.

| variante | Δ media (M$) | IC 95% (M$) | ΔAUC en 201910 [IC] | A | veredicto | vale la pena |
|---|---|---|---|---|---|---|
| B0.5 | −0,94 | [−3,62; 1,75] | −0,0012 [−0,0017; −0,0008] | 0,79 | no pierde | no |
| B0.25 | 0,88 | [−1,95; 3,71] | −0,0044 [−0,0047; −0,0041] | 1,23 | no pierde | no |
| B0.1 | −8,47 | [−11,02; −5,92] | −0,0088 [−0,0094; −0,0083] | 1,84 | pierde | no |
| GOSS | −4,01 | [−7,03; −1,00] | +0,0005 [+0,0003; +0,0008] | 0,72 | indeterminado | no |

- **H2, refutada**: con f = 0,1 pierde. Con 0,5 y 0,25 no pierde, pero casi no acelera (A ≤ 1,23), porque el `Dataset`
  completo se arma igual. GOSS queda *indeterminado* (en la ronda anterior, *no pierde*) y es más lento que el control.
- **AUC y ganancia en direcciones distintas**: en B0.25, Δ de ganancia positivo (0,88 M$) con ΔAUC negativo y
  distinguible de 0 (−0,0044); en GOSS, al revés: ΔAUC positivo y distinguible de 0 (+0,0005) con Δ de ganancia
  negativo (−4,01 M$, IC debajo de 0). El AUC mide el orden de todos los clientes y G solo los 3.300 de arriba; el
  veredicto es el de ganancia.
- Figura: [`bandas_H2.png`](../../sampling_1/informe/figuras/bandas_H2.png) y [`reporte.html`](reporte.html).

## Limitaciones

Solo lo que no está justificado en el diseño:

- Los hiperparámetros elegidos con cuatro meses se usan sin cambios en un final de seis.
- **GOSS es descriptivo**: no tiene una regla que decida; su fila se lee como referencia y no como veredicto de H2.
- Adaptación de H2: en las variantes `B*` `bagging_fraction` es la variable y sale del espacio de Optuna, mientras que el
  control y `uniforme` la siguen optimizando. Por eso `bagging` y `uniforme` no tienen la misma fracción efectiva por
  iteración y la comparación entre ellos es solo descriptiva.
- Una sola semilla de Optuna por variante: Δ incluye la suerte de la optimización y el IC no la mide.
- Un solo año (2019), un solo mes de test (201910) y un solo tipo de máquina; el resto en el informe conjunto.

## Conclusión

Muestrear dentro de LightGBM no ahorra tiempo: el `Dataset` completo se arma igual, así que A queda en 1,84 o menos aun
con f = 0,1, donde además pierde. Comparación con las otras hipótesis, a tiempo igual y entre rondas: informe conjunto.
