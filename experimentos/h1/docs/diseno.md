# Diseño — h1

Traduce `docs/hipotesis.md` a corridas concretas. Máquina, parámetros fijos de LightGBM, semillas finales y métricas
que se calculan son los de [`control/docs/diseno.md`](../../control/docs/diseno.md); el reparto en fases y la
estimación, los de [`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md). Si este documento cambia después de
abrir la etapa de corridas, el cambio va a `docs/bitacora.md` y las corridas previas quedan marcadas como de la versión
anterior.

## Variantes

| variante | hipótesis | Optuna: datos | Optuna: espacio | final: datos | final: params fijos |
|---|---|---|---|---|---|
| `U0.5`, `U0.25`, `U0.1`, `U0.05` | H1 | muestra r, semilla 0 | 5 hp | muestra r, sorteada con la semilla final | — |

"5 hp" es el espacio del control (`control/docs/hipotesis.md` § Control).

## Estudios de Optuna compartidos

Un estudio queda definido por (datos de optimización, espacio). `H3-0.25` optimiza exactamente lo mismo que `U0.25`
(muestra uniforme r = 0,25 con semilla 0, 5 hp, 40 trials, TPE con semilla 0), y `H3-0.1` lo mismo que `U0.1`. Se corre
**un** estudio y lo usan las dos variantes: H1 entrena el final con la muestra y H3 con todo. Las dos variantes se comparan
contra el control y no entre sí, así que compartir el estudio no acopla ninguna decisión. El tiempo de ese estudio entra
en T de las dos variantes.

Los estudios `U0.25` y `U0.1` son de `h1` (su `ledger/hp/`); `h3` los lee de acá.

## Grilla

- **Optimización**: 4 estudios (`U0.5`, `U0.25`, `U0.1`, `U0.05`) × 40 trials.
- **Finales**: 4 variantes × 10 semillas = 40 corridas.

### Ronda 201903–201908 (cambio `final-con-julio-agosto`, 12-nov-2026)

Sin estudios nuevos: `U0.5`, `U0.25`, `U0.1` y `U0.05` se reusan. Los finales se repiten con train 201903–201908 (la
muestra de tasa r se sortea sobre los seis meses con la semilla final) y las 20 semillas de
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Ronda 201903–201908: 4 variantes × 20 = 80 corridas,
en la lista `fase7_r0` de la fase 7 ([`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md) § Reparto y fases).
La ronda anterior se conserva. Los apartamientos (208135, 211210) están justificados en el diseño del control.

## Dependencias

- `control`: finales de `C`, N\* y δ.
