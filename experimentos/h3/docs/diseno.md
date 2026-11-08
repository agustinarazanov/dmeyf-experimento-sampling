# Diseño — h3

Traduce `docs/hipotesis.md` a corridas concretas. Máquina, parámetros fijos de LightGBM, semillas finales y métricas
que se calculan son los de [`control/docs/diseno.md`](../../control/docs/diseno.md); el reparto en fases y la
estimación, los de [`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md). Si este documento cambia después de
abrir la etapa de corridas, el cambio va a `docs/bitacora.md` y las corridas previas quedan marcadas como de la versión
anterior.

## Variantes

| variante | hipótesis | Optuna: datos | Optuna: espacio | final: datos | final: params fijos |
|---|---|---|---|---|---|
| `H3-0.25`, `H3-0.1` | H3 | muestra r_opt, semilla 0 | 5 hp | r = 1 | — |

"5 hp" es el espacio del control (`control/docs/hipotesis.md` § Control).

## Estudios de Optuna compartidos

H3 no tiene estudios propios: `H3-0.25` usa el estudio `U0.25` y `H3-0.1` el estudio `U0.1`, que son de `h1` y se leen
de su `ledger/hp/`. Por qué se comparten y qué implica está en
[`h1/docs/diseno.md`](../../h1/docs/diseno.md) § Estudios de Optuna compartidos; la falta de independencia entre
Δ(U0.25) y Δ(H3-0.25) está en `docs/hipotesis.md` § Limitaciones previstas.

## Grilla

- **Optimización**: ninguna propia (los estudios `U0.25` y `U0.1` de `h1`).
- **Finales**: 2 variantes × 10 semillas = 20 corridas, con r = 1.

## Fuera de la grilla

- **Reescalar `min_data_in_leaf` en H3**: queda como trabajo futuro, según `hipotesis.md`.

## Dependencias

- `control`: finales de `C`, N\* y δ.
- `h1`: los estudios `U0.25` y `U0.1` (`ledger/hp/U0.25.json`, `ledger/hp/U0.1.json`).
