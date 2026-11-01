# Diseño — Sampling_1

Traduce `docs/hipotesis.md` a corridas concretas. Las definiciones de G, Δ, δ, T, A, N* y los veredictos están allá y
no se repiten. Si este documento cambia después de abrir la etapa de corridas, el cambio va a `docs/bitacora.md` y las
corridas previas quedan marcadas como de la versión anterior.

## Brazos

Once brazos: el control y los diez de `hipotesis.md`. No hay otros.

| brazo | hipótesis | Optuna: datos | Optuna: espacio | final: datos | final: params fijos |
|---|---|---|---|---|---|
| `C` | control | r = 1 | 5 hp | r = 1 | — |
| `U0.5`, `U0.25`, `U0.1`, `U0.05` | H1 | muestra r, semilla 0 | 5 hp | muestra r, sorteada con la semilla final | — |
| `B0.5`, `B0.25`, `B0.1` | H2 | r = 1 | 4 hp (sin `bagging_fraction`) | r = 1 | `bagging_fraction = f`, `bagging_freq = 1` |
| `GOSS` | H2, descriptivo | r = 1 | 4 hp (sin `bagging_fraction`) | r = 1 | `data_sample_strategy = goss`, `top_rate = 0,2`, `other_rate = 0,1` |
| `H3-0.25`, `H3-0.1` | H3 | muestra r_opt, semilla 0 | 5 hp | r = 1 | — |

"5 hp" es el espacio del control (`hipotesis.md` § Control). "4 hp" son los mismos rangos sin `bagging_fraction`. En
`GOSS` sale porque LightGBM no admite bagging con GOSS; es la misma adaptación que H2 y se declara igual.

## Estudios de Optuna compartidos

Un estudio queda definido por (datos de optimización, espacio). `H3-0.25` optimiza exactamente lo mismo que `U0.25`
(muestra uniforme r = 0,25 con semilla 0, 5 hp, 40 trials, TPE con semilla 0), y `H3-0.1` lo mismo que `U0.1`. Se corre
**un** estudio y lo usan los dos brazos: H1 entrena el final con la muestra y H3 con todo. Los dos brazos se comparan
contra el control y no entre sí, así que compartir el estudio no acopla ninguna decisión. El tiempo de ese estudio entra
en T de los dos brazos.

Quedan nueve estudios: `C`, `U0.5`, `U0.25`, `U0.1`, `U0.05`, `B0.5`, `B0.25`, `B0.1` y `GOSS`.

## Grilla

- **Optimización**: 9 estudios × 40 trials = 360 entrenamientos, 100 iteraciones cada uno, sin early stopping.
- **Finales**: 11 brazos × 10 semillas = 110 corridas. Cada una predice 201908 y 201910 y guarda las dos curvas.
- **Réplica del control**: 10 corridas finales más de `C` en la VM de otra persona, con los mismos hiperparámetros. No
  entran en Δ: sirven para la compuerta de resultados (el control se repite entre personas) y para medir cuánto varía
  el tiempo entre VMs del mismo tipo.
- **Total**: 9 filas `optimizar` y 120 filas `final` en el ledger.

**Semillas finales**, iguales en todos los brazos y en este orden: 100003, 200003, 300007, 400009, 500009, 600011,
700001, 800011, 900001, 999983. La semilla 0 queda reservada para Optuna y para las muestras de optimización, y no
coincide con ninguna final.

## Parámetros fijos de LightGBM

En todos los brazos, además de los defaults:

- `objective = binary`, `num_iterations = 100`, `num_threads = 8`, `verbosity = -1`, `seed` = la semilla final en
  las corridas finales y 0 en los trials de Optuna.
- `deterministic = true` y `force_col_wise = true`. No cambian el modelo salvo por redondeo: hacen que la misma
  configuración repita el resultado (compuerta de código) y que LightGBM no cambie de estrategia de histogramas según
  r, lo que ensuciaría los tiempos. Están declarados como adaptación en `hipotesis.md` § Control.
- `feature_pre_filter = false` en el `Dataset`, porque Optuna cambia `min_data_in_leaf` entre trials. El `Dataset` se
  construye una vez por estudio y una vez por corrida final, y ese tiempo entra en T.

## Métricas que se calculan

Por corrida final, en el ledger: AUC 201908, AUC 201910, curva de ganancia acumulada en 201908 y en 201910 (archivo en
`ledger/curvas/`), ganancia máxima en 201910, filas de train, hash de la muestra, tiempos por fase y memoria máxima.
Por estudio: AUC del mejor trial, hiperparámetros elegidos (`ledger/hp/<estudio>.json`, versionado) y tiempo total.

Al consolidar, en este orden:

1. **N\***: con las 10 curvas de `C` en 201908, el N que maximiza la ganancia media.
2. **G**: ganancia en 201910 al corte N\* para cada corrida final.
3. **Ḡ_C y δ** = 0,02 · Ḡ_C.
4. **Δ por brazo**, apareada por semilla contra `C` y solo sobre las semillas que tienen los dos. Media, desvío s,
   IC 95% = media ± 2,262 · s / √n (t de Student con n − 1 g.l.; 2,262 es el valor para n = 10) y semillas ganadas.
5. **Veredicto** con las cuatro reglas de `hipotesis.md`.
6. **T** = tiempo del estudio + media del tiempo final, como en `hipotesis.md`. El del estudio es la suma de las
   duraciones de los 40 trials (guardadas en el SQLite de Optuna) más un armado del `Dataset`, así que no depende de
   cortes de la VM spot. La predicción de 201908 de la etapa final no entra, porque solo hace falta para N\*.
   **A** = T(C) / T(brazo).

Todo sale de `ledger/apareado.csv`; nada se calcula a mano.

## Máquina

- Todas las corridas que cuentan: **`n2-highmem-8` spot** (8 vCPU, 64 GB), una VM por persona en su propia cuenta.
- El curso no tiene un template `n2-highmem-8`. Los de 8 vCPU son `to-064ram-08vcpu` (e2 custom, 64 GB) y
  `to-128ram-08vcpu` (n2 custom, 128 GB). Se crea desde **`to-064ram-08vcpu`**, que aporta la imagen `labo-family`, el
  disco de 256 GB, el startup script y la configuración spot (se borra al detenerse). La máquina se sobrescribe así:

  ```bash
  gcloud compute instances create <nombre> --zone=northamerica-northeast2-b \
    --source-instance-template=projects/<proyecto>/regions/northamerica-northeast2/instanceTemplates/to-064ram-08vcpu \
    --machine-type=n2-highmem-8 --min-cpu-platform="Intel Ice Lake"
  ```

  e2 queda descartada porque no deja fijar la plataforma de CPU.
- **Región y zona**: `northamerica-northeast2`, que es donde están los templates del curso, en la zona `-b`. Si no hay
  capacidad spot, se usa `-a` o `-c`, que también ofrecen Ice Lake.
- **Prueba (tarea 2.2, 1-nov, cuenta de Agustina)**: `prueba-sampling-n2` se creó con `n2-highmem-8`, Ice Lake y spot,
  y se borró junto con su disco en un minuto.
- **Cuotas** (proyecto de Agustina): `CPUS_ALL_REGIONS` 32; en `northamerica-northeast2`, `CPUS` 100 y `N2_CPUS` 100.
  Alcanzan para una VM de 8 vCPU sin problema. Martín y Luis tienen que verificar las suyas antes de la fase 1.
- **Trial**: según Agustina, el alta fue hace dos o tres semanas. Los templates del curso son del 13-oct, así que el
  trial vence alrededor del 11-ene-2027. La fecha exacta se confirma en Facturación → Créditos antes de la fase 1.
- Plataforma de CPU fija: las `n2` pueden caer en Cascade Lake o en Ice Lake, así que se crean con
  `--min-cpu-platform="Intel Ice Lake"`. Cada fila del ledger registra el modelo de CPU de `/proc/cpuinfo`, y el
  análisis de tiempos descarta las filas con otra CPU.
- Una corrida por VM a la vez, en secuencia. Se registra `load average` al iniciar cada corrida.
- Las corridas en la Mac (`--filas 20000`) son smoke tests con `etapa = exploracion` y no entran en `resultados.csv`.
- Un único commit con tag `corridas-v1` para todas las fases y personas. Si hay que corregir código a mitad de camino,
  se crea `corridas-v2`, se anota en la bitácora y se repiten las corridas afectadas.
- El ledger se comparte por git (`ledger/corridas/`, `ledger/curvas/`, `ledger/hp/`). El estudio SQLite de Optuna vive
  en el bucket de cada persona, para retomarlo si la VM spot muere.

## Estimación de horas y costo

Unidad u: un entrenamiento de 100 iteraciones sobre el train completo (~640.000 filas × ~470 columnas) más su
predicción. Supuesto: u ≈ 1 min en `n2-highmem-8`. Factores de costo relativos a u, también supuestos:

- `uniforme` con tasa r: 0,15 + 0,85 r. La parte fija es la predicción y el armado de árboles.
- `bagging` con fracción f: 0,4 + 0,6 f. El `Dataset` completo y la búsqueda de cortes no se achican.
- `GOSS`: 0,7.

| brazo | estudio (u·min) | 10 finales (u·min) | T estimado (min) | A estimado |
|---|---:|---:|---:|---:|
| `C` | 40,0 | 10,0 | 41,0 | 1,0 |
| `U0.5` | 23,0 | 5,8 | 23,6 | 1,7 |
| `U0.25` | 14,5 | 3,6 | 14,9 | 2,8 |
| `U0.1` | 9,4 | 2,4 | 9,6 | 4,3 |
| `U0.05` | 7,7 | 1,9 | 7,9 | 5,2 |
| `B0.5` | 28,0 | 7,0 | 28,7 | 1,4 |
| `B0.25` | 22,0 | 5,5 | 22,6 | 1,8 |
| `B0.1` | 18,4 | 4,6 | 18,9 | 2,2 |
| `GOSS` | 28,0 | 7,0 | 28,7 | 1,4 |
| `H3-0.25` | (de `U0.25`) | 10,0 | 15,5 | 2,6 |
| `H3-0.1` | (de `U0.1`) | 10,0 | 10,4 | 3,9 |
| réplica `C` | — | 10,0 | — | — |
| **total** | **191,0** | **77,8** | | |

- **Cómputo**: 268,8 u·min ≈ 4,5 h con u = 1 min. Se suma media hora por VM para bajar el crudo y armar el panel (tres
  VMs, 1,5 h), así que da **≈ 6 h de VM**. Si u resulta 3 min, son **≈ 15 h**.
- **Costo**: `n2-highmem-8` cuesta ≈ US$ 0,52/h a demanda en `us-central1`. En `northamerica-northeast2` sale algo
  más caro (≈ 10–15%), y en spot bastante menos. En el peor caso, 15 h a precio de demanda con un 15% extra dan
  **≈ US$ 9**, más disco y bucket, lejos de los US$ 300 del trial. El precio spot exacto se ve en la factura después
  de la fase 1.
- **Calibración**: el primer estudio de la fase 1 (`C`) mide u. Si el tiempo por trial supera 3 min, se recalcula esta
  tabla en la bitácora antes de seguir. Lo que cambia es el calendario; la grilla no cambia.

Las columnas de A son la estimación de costo y no una predicción del experimento; las predicciones están en
`hipotesis.md`. Por ejemplo, la estimación de `H3-0.1` (3,9) queda apenas debajo de la predicción secundaria A ≥ 4.
En `GOSS`, el factor 0,7 depende del `learning_rate` que elija Optuna, porque GOSS no muestrea antes de la iteración
1/`learning_rate`.

## Reparto y fases

Las tres personas corren el mismo commit, en VMs del mismo tipo, cada una en su cuenta. Las fases ordenan la
dependencia y el reparto equilibra la carga.

| fase | persona | corridas | carga (u·min) |
|---|---|---|---:|
| 1 | Agustina | estudios `C`, `U0.25`, `U0.1` (en ese orden); finales `C`, `H3-0.25`, `H3-0.1`, `U0.25`, `U0.1` | 99,9 |
| 2 | Martín | estudios y finales de `U0.5` y `U0.05` | 38,4 |
| 2 | Luis | réplica de `C` (con el JSON de la fase 1) | 10,0 |
| 3 | Martín | estudios y finales de `B0.5` y `B0.25` | 62,5 |
| 3 | Luis | estudios y finales de `B0.1` y `GOSS` | 58,0 |

Por persona: Agustina 99,9, Martín 100,9, Luis 68,0; total 268,8. Cada estudio y cada corrida final aparece una sola
vez. Cada brazo tiene su estudio y sus finales en la misma VM; T(brazo) y T(C) sí vienen de VMs distintas, y la
réplica de `C` mide cuánto varía el tiempo entre ellas.

**Dependencias.**

- Todo espera al cierre de la compuerta de código (`docs/revision.md` § 3) y al tag `corridas-v1`.
- La fase 1 va primero: calibra u y produce el JSON de `C`, `U0.25` y `U0.1`.
- Luis necesita el JSON de `C` (por git) para la réplica; sus corridas de fase 3 no esperan.
- Martín arranca las fases 2 y 3 en paralelo con la fase 1, porque sus estudios no dependen de nada. La calibración de
  u solo cambia el calendario, así que no la espera.
- N\* y δ salen del control, así que los veredictos esperan a que esté la fase 1 completa, pero las corridas no.

**Corridas perdidas.** Si una VM spot muere, el estudio se retoma desde su SQLite y las finales se relanzan con la
lista de configuraciones. El corredor saltea las que ya tienen fila en `ledger/corridas/`. Si un brazo termina con menos
de 10 semillas, el apareo usa las que tiene y se anota en la bitácora.

## Fuera de la grilla

- **Pesos o selección de instancias sobre CONTINUA** (propuestas del grupo al cierre de hipótesis): cambian la
  proporción de clases o su peso, que es territorio de Sampling_2. Solo entran si se reabre la compuerta de hipótesis
  y se agregan a `hipotesis.md`.
- **Reescalar `min_data_in_leaf` en H3**: queda como trabajo futuro, según `hipotesis.md`.
- **Respuesta del tutor sobre H2**: si pide mantener `bagging_fraction` optimizado, salen `B0.5`, `B0.25` y `B0.1`, y
  la fase 3 queda solo con `GOSS`. H1 y H3 no cambian.

## Devolución del tutor

_Sin devolución todavía._ El post `docs/zulip/01_hipotesis.md` no se envió.
