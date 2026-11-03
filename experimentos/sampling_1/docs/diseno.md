# Diseño — Sampling_1

Reparto en fases, estimación y devolución del tutor de las corridas de todas las hipótesis. Las definiciones de G, Δ, δ,
T, A, N* y los veredictos están en [`control/docs/hipotesis.md`](../../control/docs/hipotesis.md) y no se repiten. Si
este documento cambia después de abrir la etapa de corridas, el cambio va a `docs/bitacora.md` y las corridas previas
quedan marcadas como de la versión anterior.

Desde el 2-nov el resto del diseño está en cada experimento:

- [`control/docs/diseno.md`](../../control/docs/diseno.md): brazo `C`, réplica `C-rep`, semillas finales, parámetros
  fijos de LightGBM, métricas que se calculan y máquina.
- [`h1/docs/diseno.md`](../../h1/docs/diseno.md): brazos `U*`, su grilla y los estudios compartidos con H3.
- [`h2/docs/diseno.md`](../../h2/docs/diseno.md): brazos `B*` y `GOSS` y su grilla.
- [`h3/docs/diseno.md`](../../h3/docs/diseno.md): brazos `H3-*`, que usan los estudios de `h1`.

En total: once brazos (el control y los diez de H1–H3) más `C-rep`; 9 estudios × 40 trials y 12 brazos × 10 semillas,
así que 9 filas `optimizar` y 120 filas `final` en los ledgers.

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
| 4 | D | solo finales de los 12 brazos (11 + `C-rep`) con los JSON ya guardados, guardando predicciones (agregada el 2-nov, D12) | ≈ 60 |

Total 268,8 u·min. Cada estudio y cada corrida final aparece una sola vez. Cada brazo tiene su estudio y sus finales
en la misma VM; T(brazo) y T(C) vienen de VMs distintas, y la réplica `C-rep` en la VM B mide cuánto varía el tiempo
entre VMs. H4 queda fuera de esta tabla: la corre quien la lleva, cuando esté definida.

**Fase 4 (agregada el 2-nov).** Las fases 1 a 3 no guardaron predicciones, solo curvas, y la comparación a tiempo igual
necesita promediar probabilidades. La fase 4 repite únicamente los finales (sin estudios) de los 12 brazos en una sola
VM, con `src/correr.py` ya guardando `ledger/predicciones/<id>.parquet`. Por la clave del ledger (sin commit) esas filas
reemplazan a las anteriores: las ganancias son las mismas (determinismo, como mostró `C-rep`) y los tiempos finales
quedan todos medidos en la misma máquina. Los tiempos de optimización siguen siendo los de las fases 1 a 3.

**Orden entre fases.**

- Todo espera al cierre de la compuerta de código (`docs/revision.md` § 3) y al tag `corridas-v1`.
- La fase 1 va primero: calibra u y produce el JSON de `C`, `U0.25` y `U0.1`.
- `C-rep` necesita el JSON de `C` (por el bucket o por git); el resto de las fases 2 y 3 no espera a nada.
- N\* y δ salen del control, así que los veredictos esperan a que esté la fase 1 completa, pero las corridas no.

**Corridas perdidas.** Si una VM spot muere, se crea otra, baja el panel y el SQLite del bucket, retoma el estudio y
relanza las finales con la lista de configuraciones. El corredor saltea las que ya tienen fila en `ledger/corridas/`. Si un brazo termina con menos
de 10 semillas, el apareo usa las que tiene y se anota en la bitácora.

## Fuera de la grilla

- **Pesos o selección de instancias sobre CONTINUA** (propuestas del grupo al cierre de hipótesis): cambian la
  proporción de clases o su peso, que corresponde a H4 y corre por separado quien la propuso. Solo entran si se reabre la compuerta de hipótesis
  y se agregan a `hipotesis.md`.
- Lo que queda fuera de la grilla de una hipótesis está en su `diseno.md` (reescalar `min_data_in_leaf` en `h3`,
  respuesta del tutor sobre H2 en `h2`).

## Devolución del tutor

_Sin devolución todavía._ El post `docs/zulip/01_hipotesis.md` no se envió.

## Dependencias

Lee los ledgers de todos los experimentos para la comparación conjunta:

- `control`
- `h1`
- `h2`
- `h3`
