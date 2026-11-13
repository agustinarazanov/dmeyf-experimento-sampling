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

### Réplicas y grilla común (cambio `tiempos-confiables-y-consistencia`, 13-nov-2026)

Predicción y regla: [`docs/hipotesis.md`](hipotesis.md) § Réplicas de H1. Las cuatro `U{r}` pasan a tener 8 réplicas
(k = 0…7), como `H3-*` y `H4O-*`, y forman la fila "al azar, búsqueda y final" de la grilla común
([`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md) § Grilla común).

- **Dueño de los estudios `U{r}@k`.** Pasan a ser de `h1` (antes, de `h3`): con réplicas, los finales de `U{r}` en la
  réplica k leen `U{r}@k`, y si los estudios siguieran en `h3`, `h1` dependería de `h3` y `h3` de `h1`. Los 21 estudios
  ya corridos (`U0.25@k`, `U0.1@k`, `U0.05@k`, k = 1…7) se mueven de `h3/ledger/` a `h1/ledger/` en el repo y en el
  bucket, sin cambiar ids ni contenido.
- **Estudios nuevos**: `U0.5@1…7` (7), muestra al azar del 50 % de train 201903–201906 sorteada con la semilla k, TPE con
  semilla k, como el resto de las réplicas.
- **Finales nuevos**: `U0.5`, `U0.25`, `U0.1` y `U0.05` en k = 1…7, con las 20 semillas de la ronda 201903–201908 y la
  muestra de tasa r sorteada sobre los seis meses con la semilla final: 4 × 7 × 20 = **560 finales**. La réplica 0 ya
  está corrida.
- **T y A**: T como mediana entre réplicas y A con una sola referencia
  ([`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Medición de tiempos).
- Van en las listas `fase8_r1_a` … `fase8_r7_a` de la fase 8 ([`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md)
  § Reparto y fases).

## Dependencias

- `control`: finales de `C`, N\* y δ.
  Los estudios `U{r}` y `U{r}@k` son de este experimento (desde el 13-nov también las réplicas), así que no agregan
  dependencias.
