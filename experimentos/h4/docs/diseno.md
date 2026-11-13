# Diseño — h4

Traduce `docs/hipotesis.md` a corridas concretas. Las definiciones de G, Δ, δ, T, A, N* y los veredictos están en
[`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) y no se repiten. Máquina, parámetros fijos de LightGBM,
semillas finales y espacio de Optuna son los de [`control/docs/diseno.md`](../../control/docs/diseno.md); réplicas,
nombres `@k` y dueños de `U{r}@k`, los de [`h3/docs/diseno.md`](../../h3/docs/diseno.md) § Réplicas de optimización.
Si este documento cambia después de abrir la etapa de corridas, el cambio va a `docs/bitacora.md` y las corridas previas
quedan marcadas como de la versión anterior.

## Dependencias

De qué experimentos lee este (un ledger por línea). `python -m comun.variantes --verificar` lo compara con el registro de
variantes y estudios de `comun/variantes.py`.

- `control`: finales de `C` y de sus réplicas `C@1…7`, N\* y δ.
- `h1`: los estudios `U0.05` y `U0.25` y sus réplicas `U0.05@k` y `U0.25@k` (k = 1…7) (`ledger/hp/U0.05.json`,
  `ledger/hp/U0.25.json` y sus `@k`), que usan `H4F-0.05` y `H4F-0.25`.

Actualizado el 13-nov-2026 (cambio `tiempos-confiables-y-consistencia`): las réplicas `U{r}@k` pasaron de h3 a h1, así
que este experimento deja de depender de h3 (los nombres van sin comillas invertidas porque `--verificar` cuenta cada uno
como dependencia declarada). Los estudios `F{f}` y `F{f}@k` de la grilla común son propios.

## Variantes

Todas con 8 réplicas (k = 0…7) y las 10 semillas finales de siempre.

| variante | estudio (k = 0 / k ≥ 1) | dueño del estudio | final |
|---|---|---|---|
| `H4H-0.1` | `NH0.1` / `NH0.1@k` | `h4` | completo (r = 1) |
| `H4U-0.1` | `NU0.1` / `NU0.1@k` | `h4` | completo (r = 1) |
| `H4F-0.05` | `U0.05` / `U0.05@k` | `h1` / `h3` | todas las bajas + 50 % de CONTINUA, peso 2 |
| `H4F-0.25` | `U0.25` / `U0.25@k` | `h1` / `h3` | todas las bajas + 50 % de CONTINUA, peso 2 |

Las filas de las cuatro variantes van a `experimentos/h4/ledger/`; los hiperparámetros de `NH0.1`, `NU0.1` y sus `@k`, a
`experimentos/h4/ledger/hp/`. El registro (método, tasa y estudio de cada variante en `comun/variantes.py`) y los
métodos en `comun/metodos.py` son del grupo 2 del cambio.

## Muestras

Positivo = BAJA+1 ∪ BAJA+2; negativo = CONTINUA. Todo sobre el train 201903–201906.

- **Búsqueda difícil (`NH0.1`).** En la réplica k:
  1. **Sonda**: LightGBM de 40 árboles, 31 hojas y `learning_rate` 0,08 (resto como el control), entrenado sobre el
     10 % uniforme del train sorteado con semilla k; la semilla de LightGBM de la sonda también es k.
  2. **Pozo**: el 35 % de los negativos del train con mayor probabilidad según la sonda.
  3. **Muestra**: todos los positivos del train + una cantidad de negativos igual al 10 % de los negativos del train,
     sorteados sin reposición dentro del pozo con semilla k.
  4. Optuna de 40 trials sobre esa muestra, TPE con semilla k, maximiza el AUC en 201908.
- **Búsqueda uniforme (`NU0.1`).** Igual, sin sonda: los negativos se sortean entre todos los negativos del train con
  semilla k. Misma cantidad de positivos y de negativos que `NH0.1` en la misma réplica; solo cambia cómo se eligen los
  negativos.
- **Final fast-retrain (`H4F-*`).** Todos los positivos + el 50 % de los negativos, sorteados con la semilla final, con
  peso 1/0,5 = 2 en los negativos (`weight` del `lgb.Dataset`), así la proporción ponderada de clases es la del train
  completo. Se registra la cantidad de filas de entrenamiento.

El 35 % del pozo y el 10 % de CONTINUA quedan como los fijó Luis; no sabemos con qué mes los eligió
(`docs/hipotesis.md` § Origen). La sonda y el sorteo dentro del pozo son reconstrucción nuestra: el script de Luis
define la sonda y el pozo, pero no el sorteo ni el estudio que produjo sus hiperparámetros `H4_Hard`.

## Tiempo

T es el del control (optimización + media del final). En `H4H-0.1` la optimización suma el tiempo de la sonda
(entrenarla y puntuar los negativos): es parte de la variante. En `H4U-0.1` no hay sonda. En `H4F-*` la optimización es
la de su estudio `U{r}` / `U{r}@k`, medida cuando lo corrió `h1` o `h3`.

## Grilla

4 variantes × 8 réplicas × 10 semillas finales = **32 celdas, 320 finales**, y **16 estudios** propios (`NH0.1`,
`NU0.1` y sus `@k`, k = 1…7). Los estudios de `H4F-*` ya existen.

| bloque | corridas | tiempo estimado |
|---|---|---|
| Optuna `NH0.1`, `NU0.1` (k = 0…7), con sonda en `NH0.1` | 16 × ~80 s | ~22 min |
| Finales completos de `H4H-0.1` y `H4U-0.1` | 160 × ~35 s | ~93 min |
| Finales fast-retrain de `H4F-0.05` y `H4F-0.25` | 160 × ~15 s | ~40 min |
| **Total** | | **~2,6 h de VM** |

La búsqueda sobre ~11 % de las filas se estima como la de `U0.1` (77 s) más la sonda; el final fast-retrain, con la
mitad de los negativos, como algo menos de la mitad del completo (Luis midió 12,3 s calibrados).

## Parámetros fijos

Los del control (`num_iterations = 100`, `num_threads = 8`, `deterministic`, `force_col_wise`,
`feature_pre_filter = false`). Los hiperparámetros del estudio se usan tal cual en el final, sin reescalar.

## Métricas que se calculan

Las de todas las variantes con réplicas: G en 201910 al corte N\* = 3.300, Ḡ_{v,k}, Δ con réplicas con IC de Welch,
descomposición de la varianza, T como mediana entre réplicas, A y tiempo igual con IC entre réplicas. Además, D_HU
(`docs/hipotesis.md` regla 2). 201908 solo para Optuna y N\*; 201909, 201911 y 201912 no se usan.

## Máquina

`n2-highmem-8` spot, como el control.

## Estimación de horas y costo

~2,6 h de corrida para `h4`, dentro de las ~5,9 h de la tanda de variantes del cambio (que suma las de `h3`), más hasta
media hora por VM de arranque. Detalle y costo en [`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md)
§ Reparto y fases.

## Reparto y fases

Fase 6 de `sampling_1`: una VM por réplica k (listas `fase6_r<k>`), cada una con los estudios `NH0.1`, `NU0.1` y
`K0.1` de esa réplica y los finales de las 8 variantes nuevas de `h3` y `h4`. Todo desde el tag `corridas-v3`, después
del cierre de la revisión de hipótesis y diseño.

## `H4O-0.5` (cambio `final-con-julio-agosto`, 12-nov-2026)

Predicción y reglas (4 y 5): [`docs/hipotesis.md`](hipotesis.md) § `H4O-0.5`. Solo en la ronda 201903–201908
([`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Ronda 201903–201908).

**Por qué existe (Zulip 211718).** El tutor pidió reoptimizar siempre que cambia el dataset ("siempre OP", Tschopp).
`H4F-*` no lo cumple: busca sobre una muestra uniforme (`U0.05`, `U0.25`) y entrena con todas las bajas + 50 % de
CONTINUA con peso 2. En vez de declararlo como limitación, lo convertimos en un contraste: `H4O-0.5` optimiza sobre la
misma receta con la que entrena, y el informe de `h4` da `H4O-0.5` contra `H4F-0.05` (regla 5) como resultado.

| variante | estudio (k = 0 / k ≥ 1) | dueño del estudio | método | final |
|---|---|---|---|---|
| `H4O-0.5` | `F0.5` / `F0.5@k` | `h4` | `fast-retrain-opt` | todas las bajas + 50 % de CONTINUA, peso 2, sobre 201903–201908 |

- **Estudio `F0.5@k`** (k = 0…7, 8 réplicas): muestra de búsqueda = todos los positivos + 50 % de los negativos de
  train 201903–201906, sorteados con la semilla k, con peso 2 en los negativos en el `Dataset` de cada trial. 40
  trials, TPE con semilla k, maximiza el AUC en 201908 completo y sin pesos. Hiperparámetros a
  `experimentos/h4/ledger/hp/F0.5@k.json` (`F0.5.json` en k = 0).
- **Final**: la misma receta sobre 201903–201908, sorteada con la semilla final; los hiperparámetros se usan sin
  reescalar (0,5 es la fracción de CONTINUA, no una r de búsqueda).
- **T**: suma de los 40 trials de `F0.5@k` más la media del final, como en el control; A con T como mediana entre las 8
  réplicas.
- `PARES_WELCH` suma (`H4O-0.5`, `H4F-0.05`) para D_OF.

## Ronda 201903–201908

Las cinco variantes de `h4` (`H4H-0.1`, `H4U-0.1`, `H4F-0.05`, `H4F-0.25`, `H4O-0.5`) × 8 réplicas × 20 semillas =
**40 celdas, 800 finales**, y **8 estudios** nuevos (`F0.5`, `F0.5@1…7`), que van primero en cada lista `fase7_r<k>` de
la fase 7 ([`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md) § Reparto y fases). `NH0.1`, `NU0.1` y los
`U{r}@k` se reusan; las sondas de `NH0.1` no se repiten. Las finales de `H4F-*` y `H4O-0.5` sortean la mitad de CONTINUA
sobre los seis meses. La ronda anterior (4 variantes, 10 semillas) se conserva.

Estudio `F0.5@k`: con algo más de la mitad de las filas del train, se estima entre la mitad y dos tercios del estudio
`C` (748 s con el train completo), unos 7 a 10 min por réplica en `n2-highmem-8`; ≤ 1,3 h los ocho.

## Grilla común (cambio `tiempos-confiables-y-consistencia`, 13-nov-2026)

Predicciones y reglas (6 a 11): [`docs/hipotesis.md`](hipotesis.md) § Grilla común. `h4` aporta dos filas de la grilla
común ([`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md) § Grilla común): "con bajas y peso, búsqueda y
final" (`H4O-{f}`) y "con bajas y peso, solo búsqueda" (`H4P-{f}`), con f ∈ {0,5; 0,25; 0,1; 0,05}.

| variante | método | tasa | estudio (k = 0 / k ≥ 1) | dueño del estudio | final |
|---|---|---|---|---|---|
| `H4O-0.25`, `H4O-0.1`, `H4O-0.05` | `fast-retrain-opt` | f | `F{f}` / `F{f}@k` | `h4` | todas las bajas + f de CONTINUA, peso 1/f, sobre 201903–201908 |
| `H4P-0.5`, `H4P-0.25`, `H4P-0.1`, `H4P-0.05` | `clase-peso` | f | `F{f}` / `F{f}@k` | `h4` | completo (r = 1), sin peso |

- **Estudio `F{f}@k`**: como `F0.5@k` (§ `H4O-0.5`) con la fracción f: todas las bajas + f de CONTINUA de train
  201903–201906, sorteado con la semilla k, peso 1/f en CONTINUA en cada trial; validación 201908 completa y sin pesos.
  `F0.5` y `F0.5@k` ya existen y conservan su `hash_muestra`.
- **`H4O-{f}`**: la fracción de CONTINUA del final pasa a ser la tasa de la variante (antes, fija en 0,5). `H4F-*` sigue
  con la mitad de CONTINUA y peso 2 en el final. Hiperparámetros sin reescalar.
- **`H4P-{f}`**: optimiza con el método de `H4O-{f}` y comparte su estudio; el final es el de `opt-muestra` (train
  201903–201908 completo, sin peso). La muestra de búsqueda de `H4P-0.1` es la misma que la de `H4U-0.1` (misma función,
  misma semilla); solo cambia el peso.
- **Estudios nuevos**: `F0.25`, `F0.1` y `F0.05` en k = 0…7: **24 estudios**.
- **Finales nuevos**, con las 20 semillas de la ronda 201903–201908: las 7 variantes nuevas en k = 0…7:
  7 × 8 × 20 = **1.120 finales**.
- **T y A**: T suma los 40 trials de `F{f}@k` y la media del final; el tiempo del estudio entra en T de `H4O-{f}` y de
  `H4P-{f}`. Mediana entre réplicas y A con una sola referencia
  ([`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Medición de tiempos).
- **Pares directos** (`PARES_APAREADOS` y `PARES_WELCH`, con lo que aísla cada uno): § Grilla común de
  [`docs/hipotesis.md`](hipotesis.md). Los que cruzan experimentos se calculan en `sampling_1`.
- **Lo que hay que tocar en `comun/`** (grupo 2 del cambio): `clase-peso` en `comun/metodos.py`, que
  `metodo_optimizacion` manda a `fast-retrain-opt`; `pesos` recibe la tasa; `fast-retrain` y `fast-retrain-opt` dejan de
  compartir la fracción fija; `validar` acepta las cuatro tasas en `fast-retrain-opt`.
- Van en las listas `fase8_r0_a` … `fase8_r7_a` de la fase 8 ([`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md)
  § Reparto y fases), cada estudio antes de sus finales.
- **Fuera de la grilla común**: `H4F-*`, `H4H-0.1` y `H4U-0.1` quedan como están (la tabla de cobertura los lista
  aparte); `H4U-0.1` entra solo en el par del peso.

## Fuera de la grilla

- Otras fracciones de CONTINUA, otros tamaños de pozo u otra sonda: no están en el aporte.
- Las dos variantes de la propuesta original de H4 en `sampling_1/docs/hipotesis.md` (20 % de CONTINUA elegido por un
  algoritmo; 10 % al azar con pesos): quedaron sin definir y no están en los aportes; H4 se prueba con las variantes de
  Luis.
- Ensambles de más de 10 semillas o el presupuesto de 900 s: son del exploratorio de Luis
  (`sampling_1/exploratorios/validacion_50_semillas/`), no de esta grilla.
