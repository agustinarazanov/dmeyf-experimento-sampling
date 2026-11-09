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
- `h1`: los estudios `U0.05` y `U0.25` de la réplica 0 (`ledger/hp/U0.05.json`, `ledger/hp/U0.25.json`), que usan
  `H4F-0.05` y `H4F-0.25`.
- `h3`: las réplicas `U0.05@k` y `U0.25@k` (k = 1…7), de `h3` por la regla de dueños de `h3-semillas-optuna`.

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

~2,6 h de corrida para `h4`, dentro de las ~5,8 h de la tanda de variantes del cambio (que suma las de `h3`), más hasta
media hora por VM de arranque. Detalle y costo en [`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md)
§ Reparto y fases.

## Reparto y fases

Fase 6 de `sampling_1`: una VM por réplica k (listas `fase6_r<k>`), cada una con los estudios `NH0.1`, `NU0.1` y
`K0.1` de esa réplica y los finales de las 8 variantes nuevas de `h3` y `h4`. Todo desde el tag `corridas-v3`, después
del cierre de la revisión de hipótesis y diseño.

## Fuera de la grilla

- Otras fracciones de CONTINUA, otros tamaños de pozo u otra sonda: no están en el aporte.
- Las dos variantes de la propuesta original de H4 en `sampling_1/docs/hipotesis.md` (20 % de CONTINUA elegido por un
  algoritmo; 10 % al azar con pesos): quedaron sin definir y no están en los aportes; H4 se prueba con las variantes de
  Luis.
- Ensambles de más de 10 semillas o el presupuesto de 900 s: son del exploratorio de Luis
  (`sampling_1/exploratorios/validacion_50_semillas/`), no de esta grilla.
