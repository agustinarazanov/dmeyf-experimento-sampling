# Diseño — control

Traduce `docs/hipotesis.md` a corridas concretas para el control, y fija la máquina, los parámetros y las métricas que
usan todas las hipótesis. Las definiciones de G, Δ, δ, T, A, N* y los veredictos están en `docs/hipotesis.md` y no se
repiten. Las variantes de cada hipótesis están en su propio `docs/diseno.md`; el reparto en fases, la estimación y la
devolución del tutor, en [`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md). Si este documento cambia
después de abrir la etapa de corridas, el cambio va a `docs/bitacora.md` y las corridas previas quedan marcadas como de
la versión anterior.

## Variantes

| variante | hipótesis | Optuna: datos | Optuna: espacio | final: datos | final: params fijos |
|---|---|---|---|---|---|
| `C` | control | r = 1 | 5 hp | r = 1 | — |

"5 hp" es el espacio del control (`hipotesis.md` § Control). `C-rep` (§ Grilla) es una réplica del control para la
compuerta de resultados, no una variante.

## Grilla

- **Optimización**: el estudio `C`, 40 trials, 100 iteraciones cada uno, sin early stopping.
- **Finales**: `C` × 10 semillas. Cada corrida predice 201908 y 201910 y guarda las dos curvas.
- **Réplica del control**: variante propia, **`C-rep`**: 10 corridas finales con el JSON de `C` y las mismas 10 semillas,
  en otra VM. El diseño original la ponía en la VM de otra persona; con la decisión del 1-nov (todas las fases en la
  cuenta de Agustina) la réplica es entre VMs de la misma persona, y eso queda como limitación declarada en el informe:
  prueba el determinismo entre máquinas, no la reproducción entre integrantes. Tiene su propio nombre de variante para que
  el id de la corrida (que incluye la variante) no choque con las de `C` y el corredor no las saltee. No entran en Δ:
  sirven para la compuerta de resultados (el control se repite) y para medir cuánto varía el tiempo entre VMs del
  mismo tipo.

- **Réplicas de optimización `C@1…7`** (8-nov-2026, cambio `h3-semillas-optuna`): siete estudios más de `C`, uno por
  réplica k = 1…7, con la semilla del sampler TPE = k (en `C` no hay muestra de optimización: r = 1), y sus 10 finales
  con las mismas semillas de abajo. Los estudios se llaman `C@k`, son de `control` y sus hiperparámetros van a
  `ledger/hp/C@k.json`; las filas llevan `replica_opt = k` y el `id` con `@k`. **Lo ya corrido no cambia**: el estudio
  `C`, sus finales y `C-rep` son la réplica 0, con el mismo `id`, y N\* = 3.300 y δ = 5,52 M$ siguen saliendo de ella
  (no se recalculan con las réplicas). Para qué sirven y cómo se usan:
  [`h3/docs/hipotesis.md`](../../h3/docs/hipotesis.md) § H3 con réplicas de optimización; ejecución:
  [`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md) § Reparto y fases.

**Semillas finales**, iguales en todas las variantes y en este orden: 100003, 200003, 300007, 400009, 500009, 600011,
700001, 800011, 900001, 999983. La semilla 0 queda reservada para Optuna y para las muestras de optimización, y no
coincide con ninguna final.

## Parámetros fijos de LightGBM

En todas las variantes, además de los defaults:

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
3. **Ḡ_C y δ**, como en `hipotesis.md` § Métricas y reglas comunes.
4. **Δ por variante**, apareada por semilla contra `C` y solo sobre las semillas que tienen los dos. Media, desvío s,
   IC 95% = media ± 2,262 · s / √n (t de Student con n − 1 g.l.; 2,262 es el valor para n = 10) y semillas ganadas.
5. **Veredicto** con las cuatro reglas de `hipotesis.md`.
6. **T**, como en `hipotesis.md`. El del estudio es la suma de las duraciones de los 40 trials (guardadas en el SQLite
   de Optuna) más un armado del `Dataset`, así que no depende de cortes de la VM spot. La predicción de 201908 de la
   etapa final no entra, porque solo hace falta para N\*. Con T sale **A**.

Todo sale del `ledger/apareado.csv` de cada experimento; nada se calcula a mano. N\* y δ salen siempre del ledger de
`control`.

## Máquina

- Todas las corridas que cuentan: **`n2-highmem-8` spot** (8 vCPU, 64 GB), una VM por persona en su propia cuenta.
- El curso no tiene un template `n2-highmem-8`. Los de 8 vCPU son `to-064ram-08vcpu` (e2 custom, 64 GB) y
  `to-128ram-08vcpu` (n2 custom, 128 GB). Se crea desde **`to-064ram-08vcpu`**, que aporta la imagen `labo-family`, el
  disco de 256 GB, el startup script y la configuración spot (se borra al detenerse). La máquina se sobrescribe así:

  ```bash
  gcloud compute instances create <nombre> --zone=northamerica-northeast2-b \
    --source-instance-template=projects/<proyecto-uba>/regions/northamerica-northeast2/instanceTemplates/to-064ram-08vcpu \
    --machine-type=n2-highmem-8 --min-cpu-platform="Intel Ice Lake"
  ```

  e2 queda descartada porque no deja fijar la plataforma de CPU.
- **Región y zona**: `northamerica-northeast2`, que es donde están los templates del curso, en la zona `-b`. Si no hay
  capacidad spot, se usa `-a` o `-c`: las tres zonas listan Ice Lake entre sus plataformas (`gcloud compute zones
  list`, 1-nov).
- `<proyecto-uba>` es el proyecto del curso de cada persona (en el caso de Agustina, `proj-uba-261012163242176`, "UBA
  DMEyF"). Los templates son del proyecto y no globales, así que cada uno los verifica con `gcloud compute
  instance-templates list` en su proyecto.
- **Prueba (tarea 2.2, 1-nov, cuenta de Agustina)**: `prueba-sampling-n2` se creó con `n2-highmem-8`, Ice Lake y spot,
  y se borró junto con su disco en un minuto.
- **Cuotas** (proyecto `proj-uba-261012163242176` de Agustina): `CPUS_ALL_REGIONS` 32; en `northamerica-northeast2`, `CPUS` 100 y `N2_CPUS` 100.
  Alcanzan para una VM de 8 vCPU sin problema. Martín y Luis tienen que verificar las suyas antes de la fase 1.
- **Trial**: alta el 11-oct-2026, confirmada por Agustina el 1-nov. Son 90 días, así que vence el **9-ene-2027**; al
  1-nov quedaban 69 días. Las corridas van en el proyecto `UBA DMEyF` (`proj-uba-261012163242176`).
- **Decisión del 1-nov (Agustina)**: todas las corridas van en su cuenta y su proyecto. Un integrante lleva la H4 por
  separado ([`sampling_1/docs/hipotesis.md`](../../sampling_1/docs/hipotesis.md)), con el mismo corredor y ledger,
  cuando la defina. No hay verificaciones pendientes de otras cuentas.
- Plataforma de CPU fija: las `n2` pueden caer en Cascade Lake o en Ice Lake, así que se crean con
  `--min-cpu-platform="Intel Ice Lake"`. Cada fila del ledger registra el modelo de CPU de `/proc/cpuinfo`, y el
  análisis de tiempos descarta las filas con otra CPU.
- Una corrida por VM a la vez, en secuencia. Se registra `load average` al iniciar cada corrida.
- Las corridas en la Mac (`--filas 20000`) son smoke tests con `etapa = exploracion` y no entran en `resultados.csv`.
- Un único commit con tag `corridas-v1` para todas las fases y personas. Si hay que corregir código a mitad de camino,
  se crea `corridas-v2`, se anota en la bitácora y se repiten las corridas afectadas.
- El ledger se comparte por git (`ledger/corridas/`, `ledger/curvas/`, `ledger/hp/` de cada experimento).
- El template borra la VM cuando spot la detiene, disco incluido. Por eso, lo que tiene que sobrevivir se copia al
  bucket de cada persona:
  - el **SQLite de Optuna** es un archivo local en la VM y se copia al bucket (`gsutil cp`) al terminar cada trial. No
    se abre sobre gcsfuse, porque SQLite necesita locking;
  - el **panel 2019 en Parquet** se sube una vez después de armarlo. Una VM nueva lo baja del bucket en vez de
    rehacer la media hora de preparación;
  - las **filas de `ledger/corridas/` y `ledger/curvas/`** se suben al terminar cada corrida.

## Ronda 201903–201908 (cambio `final-con-julio-agosto`, 12-nov-2026)

Definición, apartamientos con su id y predicción: [`docs/hipotesis.md`](hipotesis.md) § Ronda 201903–201908. Lo de
arriba sigue valiendo para la ronda anterior, que no se borra ni se pisa.

- **Optimización**: ninguna nueva. Los estudios `C` y `C@1…7` se reusan; siguen entrenando con 201903–201906 y eligiendo
  por AUC en 201908.
- **Finales**: `C` y `C@1…7` × 20 semillas = 160 corridas, y `C-rep` × 20 = 20 corridas, todas con train 201903–201908 y
  la lista de 20 semillas de `hipotesis.md` (las 10 de arriba primero, en el mismo orden). Predicen solo 201910:
  `auc_val` y la curva de 201908 quedan vacíos, porque esa predicción sería dentro de la muestra.
- **Panel**: suma 201907 con su clase (sale de 201908 y 201909 del crudo). 201909 no se usa para entrenar, validar ni
  evaluar.
- **Consolidado**: N\* = 3.300 fijo (no se recalcula); δ = 0,02 · Ḡ_C con los `C` de esta ronda; Δ con IC t de 19 g.l.
  Cada fila final lleva `meses_final = 201903-201908` y el id la ventana; el consolidado no mezcla rondas.
- **Apartamientos de los que se hace cargo este diseño** (detalle en `hipotesis.md`): ganancia como métrica que decide,
  con ΔAUC al lado (Zulip 208135); ventana del final de seis meses (Zulip 211210). Solo el uso sin cambios de los
  hiperparámetros de cuatro meses en un final de seis y la duda abierta sobre la ventana (si el tutor quería
  201905–201908) quedan como limitaciones.
- **Ejecución**: fase 7 de `sampling_1`, tag `corridas-v4` (listas, horas y costo en
  [`sampling_1/docs/diseno.md`](../../sampling_1/docs/diseno.md) § Reparto y fases).

## Dependencias

Ninguna: el control no lee de otro experimento.
