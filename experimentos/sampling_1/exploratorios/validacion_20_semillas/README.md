# Validación con 20 semillas — aporte de Luis María Laguinge

**Autor:** Luis María Laguinge. **Fecha del aporte:** 2026-11-10. **Origen:** commit `ffe5cae` ("Add files via upload"),
que traía `experimentos/Informes 20 semillas/reporte_h1.html` … `reporte_h4.html`. Se conservan sin cambios en
[`originales/`](https://github.com/agustinarazanov/dmeyf-experimento-sampling/tree/main/experimentos/sampling_1/exploratorios/validacion_20_semillas/originales). En el mismo push llegó (commit `d8f04b2`) el HTML original de su validación de 50 semillas,
que quedó en [`../validacion_50_semillas/reporte_original.html`](../validacion_50_semillas/reporte_original.html).

Es **exploratorio**: no es una variante de `comun/variantes.py`, no escribe en ningún `ledger/` y no cambia el veredicto
de ninguna hipótesis. Todo se corre desde la **raíz del repo**.

## Qué trae

Un reporte por hipótesis con el formato de `comun/reporte.py` anterior a `renombrar-brazos` (la tabla dice "brazo"), con
el control y cada variante evaluados con **20 semillas finales** en lugar de 10, al corte N\* = 3.300 fijado en 201908 y
G en 201910. Los textos de "Predicción y regla" están reescritos a mano y no son los de `docs/hipotesis.md`.

## En qué se aparta del protocolo

| | Luis (20 semillas) | nuestro |
|---|---|---|
| Código y ledger | ninguno: solo los HTML | `comun.correr`, `ledger/` con commit y máquina por corrida |
| Semillas finales | 20 (no dice cuáles) | las 10 oficiales (`comun.baseline.SEMILLAS_FINALES`) |
| Réplicas de optimización | una | 8 (`replica_opt`) |
| H4 | `H4_HardNeg` con los hiperparámetros fijos de su script (estrategia 7 de `validacion_50_semillas`); `FastRetrain_H4_50pct` | `H4H-0.1` (búsqueda reconstruida, estudio `NH0.1`) y `H4F-0.05` |
| "Vale la pena" | A ≥ "aceleración base" | A ≥ 2 (`control/docs/hipotesis.md`) |
| Predicción y regla | reescritas después de ver los resultados ("H3-0.05 añadido tras el éxito", "se confirma que descartar bajas destruye el AUC") | las de `docs/hipotesis.md`, escritas antes de correr |
| Tiempos de `h2` | ≈ los del control (A ≈ 1,01 en las cuatro) | medidos: 423 s a 1.088 s según la variante |

Lo de la regla reescrita importa: un reporte que confirma una predicción escrita después del resultado no confirma nada
(`openspec/specs/protocolo-experimental`, "Hipótesis escritas antes de ejecutar").

## Reportado contra lo nuestro

No hay semillas por fila ni código, así que **no se puede reproducir**: la columna de la derecha es nuestra réplica 0
con las 10 semillas oficiales (`<exp>/ledger/apareado.csv`), no una reproducción de sus 20. Las cifras salen de
`extraer.py` (`--verificar` comprueba que los CSV coinciden con los HTML y los ledgers). Δ en M$; diferencia = Luis − nuestro.

| exp | variante de Luis | variante nuestra | Δ Luis (20) | veredicto Luis | Δ nuestro (10) [IC 95%] | veredicto nuestro | diferencia | T Luis (s) | T nuestro (s) |
|---|---|---|---|---|---|---|---|---|---|
| h1 | U0.5 | U0.5 | -0,60 | no pierde | -1,32 [-6,77; +4,13] | indeterminado | +0,72 | 355 | 344 |
| h1 | U0.25 | U0.25 | -5,45 | indeterminado | -6,38 [-11,21; -1,55] | pierde | +0,93 | 166 | 160 |
| h1 | U0.1 | U0.1 | -16,83 | pierde | -16,94 [-23,35; -10,53] | pierde | +0,11 | 81 | 80 |
| h1 | U0.05 | U0.05 | -30,75 | pierde | -33,77 [-39,84; -27,70] | pierde | +3,02 | 70 | 69 |
| h2 | B0.5 | B0.5 | -0,82 | no pierde | -0,11 [-4,46; +4,24] | no pierde | -0,71 | 786 | 1.003 |
| h2 | B0.25 | B0.25 | -3,46 | indeterminado | +0,66 [-2,86; +4,18] | no pierde | -4,12 | 768 | 645 |
| h2 | B0.1 | B0.1 | -10,39 | pierde | -7,81 [-12,27; -3,35] | pierde | -2,58 | 758 | 423 |
| h2 | GOSS | GOSS | +1,76 | gana | +0,55 [-2,60; +3,70] | no pierde | +1,21 | 781 | 1.088 |
| h3 | H3-0.25 | H3-0.25 | +5,39 | gana | +4,18 [-0,60; +8,96] | no pierde | +1,21 | 175 | 175 |
| h3 | H3-0.1 | H3-0.1 | +4,95 | gana | +4,07 [-0,27; +8,41] | no pierde | +0,88 | 92 | 93 |
| h3 | H3-0.05 | H3-0.05 | +4,89 | gana | +3,74 [+1,77; +5,71] | gana | +1,15 | 89 | 87 |
| h4 | H4_HardNeg | H4H-0.1 | +6,38 | gana | -3,30 [-7,38; +0,78] | indeterminado | +9,68 | 207 | 121 |
| h4 | FastRetrain_H4_50pct | H4F-0.05 | +4,73 | gana | +4,40 [-0,07; +8,87] | no pierde | +0,33 | 86 | 78 |

El control de Luis da G = 274,01 M$ con 20 semillas y T = 791 s; el nuestro, 276,10 M$ con 10 y T = 783 s.

## Qué se puede leer y qué no

1. **H1 y H3 van en la misma dirección que las nuestras.** Con el doble de semillas el IC se angosta y algunos
   veredictos se mueven un escalón (H3 pasa a "gana" en las tres tasas), pero con una sola búsqueda por estudio: el IC
   no incluye la variabilidad de Optuna, que en `h3` es entre el 33 y el 40 % de la varianza de G en las tres tasas
   (`h3/ledger/replicas.csv`, `frac_entre`). Con 8 réplicas las tres quedan en "no pierde": son los veredictos que
   cuentan.
2. **`H4_HardNeg` no es `H4H-0.1`.** El suyo usa los hiperparámetros que su script trae escritos a mano (salidos de una
   búsqueda cuyo código no está); el nuestro reconstruye esa búsqueda. La diferencia de +9,7 M$ es la misma brecha que ya
   documenta `validacion_50_semillas/README.md` (+5,48 M$ con sus hp contra −8,61 M$ con 8 réplicas): el resultado de
   Luis depende de esos hiperparámetros, no de la idea de hard negatives.
3. **Los tiempos de `h2` no son medidos**: las cuatro variantes dan A ≈ 1,01 cuando nuestro bagging y GOSS van de
   0,72 a 1,85. Sin ledger no se sabe de dónde salen. Las conclusiones de velocidad de `h2` no pueden apoyarse en ellos.
4. Para que esto pase a ser evidencia hace falta el código y la lista de semillas, o correr nuestro protocolo con 20
   semillas (`comun.correr --semilla` con una lista de 20), con la predicción escrita antes.

## Cómo se corre

```
python -m experimentos.sampling_1.exploratorios.validacion_20_semillas.extraer              # escribe resultados/*.csv
python -m experimentos.sampling_1.exploratorios.validacion_20_semillas.extraer --verificar  # sin escribir
```
