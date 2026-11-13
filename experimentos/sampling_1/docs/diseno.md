# Diseño — Sampling_1

Reparto en fases, estimación y devolución del tutor de las corridas de todas las hipótesis. Las definiciones de G, Δ, δ,
T, A, N* y los veredictos están en [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) y no se repiten. Si
este documento cambia después de abrir la etapa de corridas, el cambio va a `docs/bitacora.md` y las corridas previas
quedan marcadas como de la versión anterior.

Desde el 2-nov el resto del diseño está en cada experimento:

- [`control/docs/diseno.md`](../../control/docs/diseno.md): variante `C`, réplica `C-rep`, semillas finales, parámetros
  fijos de LightGBM, métricas que se calculan y máquina.
- [`h1/docs/diseno.md`](../../h1/docs/diseno.md): variantes `U*`, su grilla y los estudios compartidos con H3.
- [`h2/docs/diseno.md`](../../h2/docs/diseno.md): variantes `B*` y `GOSS` y su grilla.
- [`h3/docs/diseno.md`](../../h3/docs/diseno.md): variantes `H3-*`, `H3R-*`, `H3L-*` y `H3K-0.1`, que usan los
  estudios de `h1` (réplica 0), sus réplicas `@k` y el estudio propio `K0.1`.
- [`h4/docs/diseno.md`](../../h4/docs/diseno.md): variantes `H4H-0.1`, `H4U-0.1`, `H4F-0.05` y `H4F-0.25`, con sus
  estudios `NH0.1` y `NU0.1` y los de `h1` y `h3` (agregado el 9-nov, cambio `incorporar-aportes`).

Fases 1 a 4 (lo que sigue, hasta § Reparto y fases): once variantes (el control y las diez de H1–H3) más `C-rep`; 9 estudios × 40 trials y 12 variantes × 10 semillas,
así que 9 filas `optimizar` y 120 filas `final` en los ledgers.

## Estimación de horas y costo

Unidad u: un entrenamiento de 100 iteraciones sobre el train completo (~640.000 filas × ~470 columnas) más su
predicción. Supuesto: u ≈ 1 min en `n2-highmem-8`. Factores de costo relativos a u, también supuestos:

- `uniforme` con tasa r: 0,15 + 0,85 r. La parte fija es la predicción y el armado de árboles.
- `bagging` con fracción f: 0,4 + 0,6 f. El `Dataset` completo y la búsqueda de cortes no se achican.
- `GOSS`: 0,7.

| variante | estudio (u·min) | 10 finales (u·min) | T estimado (min) | A estimado |
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
| `C-rep` | — | 10,0 | — | — |
| **total** | **191,0** | **77,8** | | |

- **Cómputo**: 268,8 u·min ≈ 4,5 h con u = 1 min. Se suma media hora por VM para bajar el crudo y armar el panel (tres
  VMs, 1,5 h), así que da **≈ 6 h de VM**. Si u resulta 3 min, son **≈ 15 h**.
- **Costo**: `n2-highmem-8` cuesta ≈ US$ 0,52/h a demanda en `us-central1`. En `northamerica-northeast2` sale algo
  más caro (≈ 10–15%), y en spot bastante menos. En el peor caso, 15 h a precio de demanda con un 15% extra dan
  **≈ US$ 9**, más disco y bucket, lejos de los US$ 300 del trial. El precio spot exacto se ve en la factura después
  de la fase 1.
- **Calibración**: el primer estudio de la fase 1 (`C`) mide u. Si el tiempo por trial supera 3 min, se recalcula esta
  tabla en la bitácora antes de seguir. Lo que cambia es el calendario; la grilla no cambia.

Las columnas de A son la estimación de costo y no una predicción del experimento; las predicciones están en el
`hipotesis.md` de cada hipótesis. Por ejemplo, la estimación de `H3-0.1` (3,9) queda apenas debajo de la predicción
secundaria A ≥ 4. En `GOSS`, el factor 0,7 depende del `learning_rate` que elija Optuna, porque GOSS no muestrea antes
de la iteración 1/`learning_rate`.

## Reparto y fases

Todas las corridas salen del mismo commit (`corridas-v1`) y de la cuenta de Agustina, en VMs `n2-highmem-8` spot del
mismo tipo. Las fases ordenan la dependencia; la cuota (`CPUS_ALL_REGIONS` 32) permite hasta tres VMs de 8 vCPU a la
vez, así que las fases 2 y 3 pueden correr en paralelo con la 1 en VMs distintas.

| fase | VM | corridas | carga (u·min) |
|---|---|---|---:|
| 1 | A | estudios `C`, `U0.25`, `U0.1` (en ese orden); finales `C`, `H3-0.25`, `H3-0.1`, `U0.25`, `U0.1` | 99,9 |
| 2 | B | estudios y finales de `U0.5` y `U0.05`; después `C-rep` (con el JSON de `C` de la fase 1) | 48,4 |
| 3 | C | estudios y finales de `B0.5`, `B0.25`, `B0.1` y `GOSS` | 120,5 |
| 4 | D | solo finales de las 12 variantes (11 + `C-rep`) con los JSON ya guardados, guardando predicciones (agregada el 2-nov, D12) | ≈ 60 |

Total 268,8 u·min. Cada estudio y cada corrida final aparece una sola vez. Cada variante tiene su estudio y sus finales
en la misma VM; T(variante) y T(C) vienen de VMs distintas, y la réplica `C-rep` en la VM B mide cuánto varía el tiempo
entre VMs. H4 queda fuera de esta tabla: la corre quien la lleva, cuando esté definida.

**Fase 4 (agregada el 2-nov).** Las fases 1 a 3 no guardaron predicciones, solo curvas, y la comparación a tiempo igual
necesita promediar probabilidades. La fase 4 repite únicamente los finales (sin estudios) de las 12 variantes en una sola
VM, con `src/correr.py` (hoy `comun/correr.py`) ya guardando `ledger/predicciones/<id>.parquet`. Por la clave del ledger (sin commit) esas filas
reemplazan a las anteriores: las ganancias son las mismas (determinismo, como mostró `C-rep`) y los tiempos finales
quedan todos medidos en la misma máquina. Los tiempos de optimización siguen siendo los de las fases 1 a 3.

**Fase 5: réplicas de optimización (agregada el 8-nov, cambio `h3-semillas-optuna`, D3).** Ocho réplicas (k = 0…7) ×
10 semillas finales × 5 variantes (`C`, `H3-0.25`, `H3-0.1`, `H3-0.05`, `H3R-0.1`); de las 40 celdas ya están las 3 de
k = 0 de las fases 1–4, así que quedan 37 celdas nuevas y 28 estudios nuevos (`C@k`, `U0.25@k`, `U0.1@k`, `U0.05@k`,
k = 1…7). Qué es una réplica, los nombres `@k` y los dueños están en
[`h3/docs/diseno.md`](../../h3/docs/diseno.md) § Réplicas de optimización; las réplicas de `C`, en
[`control/docs/diseno.md`](../../control/docs/diseno.md) § Grilla.

- **Quién**: todo lo corre Agustina, desde su cuenta; no se reparte entre integrantes.
- **Commit**: todas las VMs salen del tag `corridas-v2`.
- **Una VM `n2-highmem-8` spot por réplica**:

  | lista | VM | corridas |
  |---|---|---|
  | `fase5_r1` … `fase5_r7` | una por k = 1…7 | estudios `C@k`, `U0.25@k`, `U0.1@k`, `U0.05@k`; finales de las 5 variantes en la réplica k |
  | `fase5_r0` | una más | finales de `H3-0.05` y `H3R-0.1` en k = 0 (estudios `U0.05` y `U0.1` de `h1`, ya corridos) |

- **Carga**: Optuna `C@1…7` 7 × 748 s ≈ 87 min; Optuna `U0.25@k`, `U0.1@k`, `U0.05@k` 7 × (153 + 77 + 67) s ≈ 35 min;
  finales 370 × ~35 s ≈ 216 min; en total **~5,6 h de VM**. Cada VM de réplica tarda unos 47 min y el total de pared
  queda en ~50 min.
- **Costo**: a las ~5,6 h se suma hasta media hora por VM para preparar el entorno y bajar el panel del bucket (8 VMs,
  ≤ 4 h), así que son ≤ 10 h de VM. En el peor caso (precio a demanda, US$ 0,52/h con un 15% extra) dan **≈ US$ 6**,
  más disco y bucket, dentro del crédito del trial (§ Estimación de horas y costo).
- **Cuota**: 8 VMs (64 vCPU), dentro de la cuota de 200 vCPU N2 de `us-central1`. Antes de lanzar se verifican la cuota
  y el crédito del trial (`CLAUDE.md` § Cómputo); si la cuota no alcanzara, se lanzan en tandas. El lanzador
  (`scripts/lanzar_fase.sh`) hace la verificación de la cuota.
- **Orden**: espera al cierre de la revisión de hipótesis y diseño del cambio y al tag `corridas-v2`; las 8 listas no
  dependen entre sí. Una VM que se cae se retoma con el mecanismo de § Corridas perdidas.

**Fase 6: aportes de Luis y Martín (agregada el 9-nov, cambio `incorporar-aportes`, D6).** Las 8 variantes nuevas
(`H3R-0.25`, `H3L-0.25`, `H3L-0.1`, `H3K-0.1` de `h3` y `H4H-0.1`, `H4U-0.1`, `H4F-0.05`, `H4F-0.25` de `h4`) con 8
réplicas × 10 semillas, los 24 estudios nuevos (`K0.1`, `NH0.1`, `NU0.1`, k = 0…7) y la replicación de los dos
exploratorios.

- **Quién**: todo lo lanza Agustina, desde su cuenta, en paralelo.
- **Commit**: todas las VMs salen del tag `corridas-v3`, después del cierre de la revisión de hipótesis y diseño y del
  de código.
- **VMs `n2-highmem-8` spot**:

  | tanda | listas | VMs | contenido | pared aprox. |
  |---|---|---|---|---|
  | Variantes | `fase6_r0` … `fase6_r7` | 8, una por réplica k | estudios `K0.1`, `NH0.1`, `NU0.1` de la réplica k; finales de las 8 variantes en k | ~45 min |
  | Luis | `fase6_luis_<estrategia>` | 9, una por estrategia | 50 semillas con `--hp original`; semillas extra del presupuesto donde K > 50 | ~30 min |
  | Luis, agregados | — | local | `validacion.py --agregar`, `presupuesto.py` | minutos |
  | Martín | una | 1 | `sensibilidad_07` + `ganancia_08` (4 hilos) y la comparación del panel de Luis con `comun.datos` | ~2,1 h |
  | Luis, `--hp ledger` | una | 1 | estrategia 7 con los hiperparámetros de `NH0.1`, después de la tanda de variantes | ~30 min |

- **Carga**: variantes ~5,9 h de VM (~3,3 h de `h3` y ~2,6 h de `h4`, detalle en el `diseno.md` de cada una); Luis
  ~3,7 h; Martín ~2,1 h. En total unas 12 h de VM y ~2 h de pared.
- **Cuota**: 18 VMs × 8 vCPU = 144 vCPU simultáneas, dentro de la cuota de 200 vCPU N2. Antes de lanzar se verifican la
  cuota y el crédito del trial; si no alcanzan, se lanzan en tandas (ninguna decisión depende del orden).
- **Costo**: unas 12 h de VM más el arranque de cada una; con el peor caso de § Estimación de horas y costo (US$ 0,52/h
  a demanda con un 15 % extra) quedan debajo de US$ 15, dentro del crédito del trial.
- El detalle de los exploratorios (paquete de Luis, replicación de Martín, panel) está en `openspec/changes/
  incorporar-aportes/design.md` D1, D5 y D7 hasta que se archive el cambio.

**Fase 7: ronda 201903–201908 (agregada el 12-nov, cambio `final-con-julio-agosto`, D8).** Repite todos los finales
con train 201903–201908 (Zulip 211210) y 20 semillas, y suma `H4O-0.5` con sus 8 estudios `F0.5@k` (Zulip 211718).
Definición de la ronda, semillas y predicción: [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) § Ronda
201903–201908; por hipótesis, la sección de la ronda en el `diseno.md` de [`control`](../../control/docs/diseno.md),
[`h1`](../../h1/docs/diseno.md), [`h2`](../../h2/docs/diseno.md), [`h3`](../../h3/docs/diseno.md) y
[`h4`](../../h4/docs/diseno.md). No se repite ningún estudio existente; la ronda anterior queda en el ledger, marcada con
`meses_final = 201903-201906`.

- **Quién**: todo lo lanza Agustina, desde su cuenta, con `scripts/lanzar_fase.sh`. Las sesiones solo usan `--en-seco`.
- **Commit**: todas las VMs salen del tag `corridas-v4`, después del cierre de la revisión de hipótesis y diseño y del de
  código.
- **Listas**, una por réplica k, todas con `--semilla todas` (las 20). Cada una empieza por el estudio `F0.5@k` (`F0.5`
  en k = 0) y sigue con los finales de la réplica k:

  | lista | celdas (variante × réplica) |
  |---|---|
  | `fase7_r0` | `C`, las 8 de `h3`, las 5 de `h4` en k = 0; más `U0.5`, `U0.25`, `U0.1`, `U0.05` (`h1`), `B0.5`, `B0.25`, `B0.1`, `GOSS` (`h2`) y `C-rep`: 23 |
  | `fase7_r1` … `fase7_r7` | `C@k`, las 8 de `h3` y las 5 de `h4` en la réplica k: 14 cada una |

  Son 23 + 7 × 14 = **121 celdas × 20 semillas = 2.420 finales** y **8 estudios** `F0.5@k`.
- **Carga**: unas **24 h de cómputo** (los finales de la ronda anterior en `n2-highmem-8` promediaron ~24 s con cuatro
  meses; con seis, × 1,5 ≈ 36 s, y 2.420 × 36 s ≈ 24 h). `fase7_r0` lleva 460 finales y las otras 280, así que `r0` tarda ~4,5 h y cada
  una de las otras ~2,8 h.
- **Cuota y tandas**: `CPUS_ALL_REGIONS` 32 permite 4 VMs de 8 vCPU a la vez. Dos tandas: `r0`–`r3` y después
  `r4`–`r7`; unas **7 h de pared**. Antes de lanzar se verifican la cuota y el crédito del trial (vence el 9-ene-2027).
- **Costo**: ≈ **US$ 5** en spot. En el peor caso de § Estimación de horas y costo (a demanda, US$ 0,52/h con un 15 %
  extra), 24 h más media hora de arranque por VM (8 VMs) dan ≈ US$ 17, más disco y bucket, dentro del crédito.
- **Antes de lanzar**: el ledger del bucket migrado con `scripts/agregar_meses_final.py` y verificado bajándolo de
  nuevo. Una VM que se cae se retoma como en § Corridas perdidas (`existe_fila` retoma por semilla).
- **Al terminar**: ninguna VM encendida; horas y costo reales a la bitácora.

**Orden entre fases.**

- Todo espera al cierre de la compuerta de código (`docs/revision.md` § 3) y al tag `corridas-v1`.
- La fase 1 va primero: calibra u y produce el JSON de `C`, `U0.25` y `U0.1`.
- `C-rep` necesita el JSON de `C` (por el bucket o por git); el resto de las fases 2 y 3 no espera a nada.
- N\* y δ salen del control, así que los veredictos esperan a que esté la fase 1 completa, pero las corridas no.

**Corridas perdidas.** Si una VM spot muere, se crea otra, baja el panel y el SQLite del bucket, retoma el estudio y
relanza las finales con la lista de configuraciones. El corredor saltea las que ya tienen fila en `ledger/corridas/`. Si una variante termina con menos
de 10 semillas, el apareo usa las que tiene y se anota en la bitácora.

## Fuera de la grilla

- **Pesos o selección de instancias sobre CONTINUA** (propuestas del grupo al cierre de hipótesis): cambian la
  proporción de clases o su peso, que corresponde a H4 y corre por separado quien la propuso. Solo entran si se reabre la compuerta de hipótesis
  y se agregan a `hipotesis.md`. *Entraron el 9-nov* como `h4` (cambio `incorporar-aportes`), con las variantes del
  aporte de Luis; fase 6.
- Lo que queda fuera de la grilla de una hipótesis está en su `diseno.md` (réplicas de `U*`, `B*` y `GOSS` en `h3`,
  respuesta del tutor sobre H2 en `h2`). Reescalar `min_data_in_leaf` en `h3`, que estaba acá, entró el 8-nov como
  `H3R-0.1` (fase 5).

## Devolución del tutor

Las devoluciones del curso se anotan en la bitácora con su id de Zulip. El repo no guarda borradores de mensajes
(decisión de Agustina, 13-nov).

## Dependencias

Lee los ledgers de todos los experimentos para la comparación conjunta:

- `control`
- `h1`
- `h2`
- `h3`
- `h4`

h4 se suma a esta lista en el mismo commit que registra sus variantes en `comun/variantes.py` (grupo 2 de
`incorporar-aportes`): `--verificar` exige que la lista coincida con el registro, y hasta entonces h4 no tiene
variantes registradas.
