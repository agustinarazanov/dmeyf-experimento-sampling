# Diseño — h3

Traduce `docs/hipotesis.md` a corridas concretas. Máquina, parámetros fijos de LightGBM, semillas finales y métricas
que se calculan son los de [`control/docs/diseno.md`](../../control/docs/diseno.md); el reparto en fases y la
estimación, los de [`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md). Si este documento cambia después de
abrir la etapa de corridas, el cambio va a `docs/bitacora.md` y las corridas previas quedan marcadas como de la versión
anterior.

## Variantes

| variante | hipótesis | Optuna: datos | Optuna: espacio | final: datos | final: params fijos |
|---|---|---|---|---|---|
| `H3-0.25`, `H3-0.1` | H3 | muestra r_opt, semilla 0 (réplica k: semilla k) | 5 hp | r = 1 | — |
| `H3-0.05` | H3 con réplicas | muestra r_opt = 0,05, semilla k | 5 hp | r = 1 | — |
| `H3R-0.1` | H3 con réplicas | los estudios de `H3-0.1` | 5 hp | r = 1 | `min_data_in_leaf` × √10, recortado a [1; 8000] |

"5 hp" es el espacio del control (`control/docs/hipotesis.md` § Control). Las dos variantes nuevas (8-nov, cambio
`h3-semillas-optuna`) se registran así:

| variante | método | tasa | estudio | final |
|---|---|---|---|---|
| `H3-0.05` | `opt-muestra` | 0,05 | `U0.05` / `U0.05@k` | r = 1 |
| `H3R-0.1` | `opt-muestra-reescalado` | 0,1 | `U0.1` / `U0.1@k` | r = 1, `min_data_in_leaf` × √(1/r), recortado a [1; 8000] |

`H3R-0.1` comparte los estudios de `H3-0.1`: la diferencia entre las dos es solo el reescalado, apareada por réplica y
semilla.

## Estudios de Optuna compartidos

En la réplica 0, H3 no tiene estudios propios: `H3-0.25` usa el estudio `U0.25`, `H3-0.1` y `H3R-0.1` el estudio
`U0.1` y `H3-0.05` el estudio `U0.05`, que son de `h1` y se leen de su `ledger/hp/`. Por qué se comparten y qué implica
está en [`h1/docs/diseno.md`](../../h1/docs/diseno.md) § Estudios de Optuna compartidos; la falta de independencia entre
Δ(U0.25) y Δ(H3-0.25) está en `docs/hipotesis.md` § Limitaciones previstas.

## Réplicas de optimización

- **Réplica k**: semilla del sampler TPE = semilla del sorteo de la muestra de optimización = k. La réplica 0 es la ya
  corrida, sin cambios (mismo estudio, mismos hiperparámetros, mismas filas). Las semillas finales no cambian.
- **Nombres**: la réplica 0 usa el nombre de siempre (`C`, `U0.1`); la réplica k ≥ 1, `<estudio>@k` (`C@3`, `U0.1@3`).
  El `id` de la fila suma `@k` al nombre de la variante solo si k ≥ 1, y la columna `replica_opt` guarda k.
- **Regla de dueños de `U{r}@k`**: el estudio base `U{r}` es de `h1`; sus réplicas `U{r}@k` (k ≥ 1) son de **`h3`**. Las
  corre este cambio, sirven solo a H3 y así `h1` queda intacto: sus hiperparámetros van a
  `experimentos/h3/ledger/hp/U{r}@k.json`. `C@k` es de `control`. La regla vive en el registro
  (`comun/variantes.py`) y la cubre un test.
- **Variantes que admiten réplicas**: `C`, `H3-0.25`, `H3-0.1`, `H3-0.05` y `H3R-0.1`. Pedir una réplica k ≥ 1 de otra
  variante falla antes de cargar datos.

## Grilla con réplicas

8 réplicas (k = 0…7) × 10 semillas finales × 5 variantes (`C`, `H3-0.25`, `H3-0.1`, `H3-0.05`, `H3R-0.1`) = 40 celdas.
Ya están 3 (k = 0 de `C`, `H3-0.25` y `H3-0.1`), así que quedan **37 celdas nuevas** y **28 estudios nuevos**
(`C@k`, `U0.25@k`, `U0.1@k`, `U0.05@k` con k = 1…7).

| bloque | corridas | tiempo estimado |
|---|---|---|
| Optuna `C@1…7` | 7 × 748 s | 87 min |
| Optuna `U0.25@k`, `U0.1@k`, `U0.05@k` (k = 1…7) | 7 × (153 + 77 + 67) s | 35 min |
| Finales (37 celdas nuevas × 10 semillas) | 370 × ~35 s | 216 min |
| **Total** | | **~5,6 h de VM** |

**Por qué R = 8.** Si el desvío entre réplicas fuera de unos 4 M$ (la escala que sugiere el exploratorio de Martín),
con 8 contra 8 el IC de Welch tiene una semiamplitud cercana a ±4,3 M$: alcanza para decidir *no pierde* con
δ = 5,52 M$ si el Δ real está cerca de 0, y *gana* si pasa los 4,5 M$. Con 5 réplicas la semiamplitud sube a unos ±5,8
y *no pierde* deja de ser decidible; con 10 el costo crece un 30 % para ganar poco. R = 8 queda cerrado
(`docs/hipotesis.md` § Qué queda fijo).

La ejecución (una VM por réplica, todas desde `corridas-v2`) está en
[`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md) § Reparto y fases.

## Grilla de la réplica 0

- **Optimización**: ninguna propia (los estudios `U0.25`, `U0.1` y `U0.05` de `h1`).
- **Finales**: 2 variantes × 10 semillas = 20 corridas, con r = 1 (`H3-0.25`, `H3-0.1`, ya corridas); `H3-0.05` y
  `H3R-0.1` en k = 0 son parte de la grilla con réplicas.

## Fuera de la grilla

- **Réplicas de `U*`, `B*` y `GOSS`**: pierden o no aceleran, y las réplicas no cambian eso.
- **H4, fast-retrain y el resto de las ideas de Luis**: son del cambio `incorporar-aportes`, que reusa los estudios
  `@k` de este.
- El reescalado de `min_data_in_leaf`, que estaba acá como trabajo futuro, entró el 8-nov como `H3R-0.1`.

## Dependencias

- `control`: finales de `C` y de sus réplicas `C@1…7` (las corre `control`), N\* y δ.
- `h1`: los estudios base de la réplica 0, `U0.25`, `U0.1` y `U0.05` (`ledger/hp/U0.25.json`, `ledger/hp/U0.1.json`,
  `ledger/hp/U0.05.json`). Las réplicas `U{r}@k` con k ≥ 1 son de este experimento (§ Réplicas de optimización), así
  que no agregan dependencias.
