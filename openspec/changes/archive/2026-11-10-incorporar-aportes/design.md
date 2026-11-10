# Design

## Context

Lo que hay al cerrar `h3-semillas-optuna`:
- `C`, `H3-0.25`, `H3-0.1`, `H3-0.05` y `H3R-0.1` con 8 réplicas de optimización;
- los estudios `C@k` y `U{r}@k` (k = 1…7);
- la columna `replica_opt`;
- `replicas.csv`;
- la comparación en dos bloques, con el manifiesto de Martín.

**El aporte de Luis** (`experimentos/Experimentos h3 y h4/`) son dos archivos.

`script_de_validaci_n_50_semillas.py`, de unas 390 líneas para Colab:
- **Datos:** baja el crudo, arma su propio `panel_2019.parquet` con DuckDB (lags y deltas 2) y lo pasa a float32.
- **Hiperparámetros:** de `C` y `U*`, escritos a mano. Coinciden exactamente con nuestros `hp/*.json`. Suma un
  `H4_Hard` sin el estudio que lo produjo.
- **Estrategias:** nueve, cada una con 50 semillas finales (las 10 oficiales más `110017 + i·19937`, i = 0…39):
  1. control;
  2. H3-0.25;
  3. H3-0.10;
  4. H3-0.05;
  5. "Idea A": `min_data_in_leaf` × 2 sobre U0.25;
  6. "Idea A": `min_data_in_leaf` × 3,16 sobre U0.1;
  7. "Idea B": hiperparámetros `H4_Hard`, final completo;
  8. "Idea C" fast-retrain sobre U0.05: todas las bajas + 50 % de CONTINUA con peso 2;
  9. "Idea C" fast-retrain sobre U0.25.
- **Sonda:** 40 árboles sobre el 10 % uniforme, con semilla 0. Define `pool_hard_35`, el 35 % de los negativos con
  mayor score, pero el script no lo usa: es lo que habría alimentado la búsqueda `H4_Hard`.
- **Tiempos:** se multiplican por `FACTOR_VM`, una calibración contra 16,24 s de un final de U0.1 en la VM.
- **Salidas:** un HTML con boxplot, ensambles de 10 y 50 semillas y ganancia según K. Anuncia un
  `resumen_50_semillas.csv` que nunca escribe.

`resumen_completo_de_experimentos.md`, que reporta:
- H3-0.05: +6,47 M$ y Optuna 8,89 veces más rápido.
- H4 hard: +7,19 M$.
- Fast-retrain: 12,3 s por semilla; en 900 s entran más de 60 semillas, con 283,25 M$ contra 276,65 M$ del control
  a tiempo igual.
- Descartes: reescalado lineal, H4 con negativos uniformes (−2,31 M$) y muestreo por cliente.

No hay código para la búsqueda con hard negatives, para H4 uniforme, para el muestreo por cliente, para el reescalado
lineal ni para el presupuesto de 900 s.

**El aporte de Martín** (`h3/sensibilidad_muestra/`) ya sigue las convenciones, con 13 tests sin datos y sha256 de sus
salidas. Hay que volver a correrlo en la VM.

## Goals / Non-Goals

**Goals:**
- Que ambos aportes se puedan reproducir desde el repo y que cada número reportado tenga su par reproducido.
- Que el trabajo de Luis quede con las convenciones del repo, sin perder su protocolo propio (50 semillas, 900 s).
- Que el trabajo de Luis cumpla la consigna de meses: elegir en 201908 y comparar en 201910 (D9).
- Que cada idea de Luis se pruebe como variante con el protocolo: réplicas, reglas pre-registradas, ledger.
- Cuatro hipótesis en `sampling_1`.

**Non-Goals:**
- Nuevos meses de test.
- Ideas que no estén en los aportes.
- Corregir el protocolo de Martín: se replica tal cual es.

## Decisions

### D1. Paquete de Luis

```
experimentos/sampling_1/exploratorios/validacion_50_semillas/
  __init__.py
  estrategias.py      # las 9 estrategias y sus semillas (50 + extendidas), sin datos
  validacion.py       # loop por estrategia: --estrategia, --hp {original,ledger}, --semillas
  presupuesto.py      # reconstruido: análisis de 900 s
  hp_original.json    # los hiperparámetros escritos a mano en el script, tal cual
  resultados/         # CSV por estrategia y semilla, agregados, procedencia.json
  tests/              # sin datos: semillas, estrategias, reescalados, presupuesto con datos sintéticos
  README.md           # protocolo, diferencias con el nuestro, tabla reportado/reproducido
  exploratorio.json
  resumen_original.md # el resumen de Luis, sin cambios
```

Reglas del paquete:
- **Origen.** El script original no se conserva como archivo: queda en la historia de git (commit `9e1889e`). El
  README cita el commit y lista qué partes se portaron sin cambios de lógica y cuáles se reconstruyeron.
- **Datos.** Usa el panel de `comun.datos` y `comun.ganancia`. El panel de Luis se compara una vez contra el nuestro
  (D7). Si difiere, se documenta y se agrega `--panel-luis`, que arma el suyo con su SQL portado.
- **Hiperparámetros.**
  - `--hp original`: lee `hp_original.json`. Es la réplica fiel del aporte.
  - `--hp ledger`: lee nuestros `hp/*.json`, y el de `H4_Hard` sale del estudio `NH0.1` reconstruido.
  - Para `C` y `U*` los dos modos coinciden. El test lo verifica.
- **Tiempos.** Se miden en la VM sin `FACTOR_VM`. El factor se registra aparte para explicar la diferencia con el
  resumen.
- **Meses.** Cada semilla predice 201908 y 201910. Todo lo que ordena o decide sale de 201908 (D9).
- **Paralelismo.** `--estrategia` permite una VM por estrategia. `validacion.py --agregar` junta los CSV y arma el
  HTML y los agregados: ensambles de 10 y 50 semillas y ganancia según K.

### D2. Reconstrucciones (marcadas como tales)

| pieza | interpretación elegida | por qué |
|---|---|---|
| `resumen_50_semillas.csv` | una fila por estrategia y semilla: G al corte 3.300, ganancia máxima, AUC, tiempo | es lo que calcula el loop y el HTML anuncia |
| Presupuesto de 900 s | K = ⌊(900 − T_opt) / T_final medio⌋ semillas; ensamble de las primeras K; si K > 50, se corren semillas extra siguiendo `110017 + i·19937` | "más de 60 semillas" no entra en 50: hace falta extender |
| Búsqueda con hard negatives (`H4_Hard`) | estudio `NH0.1`: Optuna de 40 trials sobre todas las bajas + 10 % de las CONTINUA, sorteadas dentro de `pool_hard_35` de la sonda | el script define el pozo y la sonda pero no el sorteo; "10 % de la clase CONTINUA priorizando hard negatives" |
| H4 con negativos uniformes | estudio `NU0.1`: igual, con las CONTINUA sorteadas entre todas | "100 % de las bajas + 10 % de CONTINUA elegida de forma completamente aleatoria" |
| Muestreo por cliente | estudio `K0.1`: el 10 % de los clientes con todas sus filas; se usa en la búsqueda y el final es completo | lo compara con "el muestreo tradicional por filas a igual volumen" en el contexto de H3 |
| Reescalado lineal | `min_data_in_leaf` × 1/r, nada más | `escalar_hp` solo escala `min_data_in_leaf` en las ideas que corrió |

En el modo fiel, las reconstrucciones de H4 uniforme, por cliente y lineal no forman parte de las 9 estrategias, porque
Luis no las corrió en ese script. Se miden como variantes (D3) y la tabla las compara con las cifras de su resumen
donde las haya.

### D3. Variantes nuevas

Todas con 8 réplicas (k = 0…7) y 10 semillas finales.

| variante | experimento | estudio (k = 0 / k ≥ 1) | final |
|---|---|---|---|
| `H3R-0.25` | h3 | `U0.25` / `U0.25@k` | completo, `min_data_in_leaf` × 2 |
| `H3L-0.25` | h3 | `U0.25` / `U0.25@k` | completo, × 4 |
| `H3L-0.1` | h3 | `U0.1` / `U0.1@k` | completo, × 10 |
| `H3K-0.1` | h3 | `K0.1` / `K0.1@k` (h3) | completo |
| `H4H-0.1` | h4 | `NH0.1` / `NH0.1@k` (h4) | completo |
| `H4U-0.1` | h4 | `NU0.1` / `NU0.1@k` (h4) | completo |
| `H4F-0.05` | h4 | `U0.05` / `U0.05@k` | todas las bajas + 50 % de CONTINUA, peso 2 |
| `H4F-0.25` | h4 | `U0.25` / `U0.25@k` | todas las bajas + 50 % de CONTINUA, peso 2 |

Dependencias de `h4`:
- `control`;
- `h1`, por `U0.05` y `U0.25` en k = 0;
- `h3`, por `U{r}@k`.

`comun.variantes --verificar` las comprueba.

### D4. Hipótesis pre-registradas

Las reglas usan los veredictos comunes sobre Δ con réplicas (`h3-semillas-optuna` D5), con δ y N\* fijos. Van a
`h4/docs/hipotesis.md` y `h3/docs/hipotesis.md` antes de correr, revisadas en sesión limpia.

**H4 — muestras informadas por clase.** Conservar todas las bajas en la búsqueda o en el final mantiene la ganancia y
acelera.
- `H4H-0.1` y `H4U-0.1` no pierden con réplicas.
- **Difícil contra uniforme:** media de Ḡ por réplica de `H4H-0.1` − la de `H4U-0.1`, con IC de Welch.
  - *Ayuda* si la cota inferior es > 0.
  - *Empeora* si la cota superior es < 0.
  - Si no, *no cambia*.
  - Luis reporta que ayuda.
- `H4F-0.05` y `H4F-0.25`:
  - no pierden con réplicas;
  - su A es mayor que la de `H3-0.05` y `H3-0.25`;
  - a tiempo igual *ganan*: la cota inferior del IC entre réplicas es > 0.

**H3, extensiones.**
- **Raíz contra lineal:** `H3R-r` − `H3L-r` para r ∈ {0,25, 0,1}, apareada por réplica y semilla (comparten
  estudios). Gana la raíz si la cota inferior es > 0.
- **Raíz contra nada:** `H3R-0.25` − `H3-0.25`, apareada, con la misma regla de "mejora" que `H3R-0.1` en
  `h3-semillas-optuna`.
- **Por cliente:** `H3K-0.1` − `H3-0.1`, con Welch. *Empeora* si la cota superior es < 0. Luis reporta que empeora.

**Comparaciones múltiples.** Son más de diez contrastes sin corrección. El informe lo declara y la respuesta al tutor
se apoya en los contrastes principales, fijados de antemano: `H3-0.1` (de `h3-semillas-optuna`), `H4H-0.1` y
`H4F-0.05`.

### D5. Replicación de Martín

En una VM `n2-highmem-8`, con 4 hilos como en su protocolo, se corren en orden:
1. `insumos` y `insumos --solo-verificar`;
2. `sensibilidad_07`;
3. `ganancia_08 --corrida-07 <la nueva>`.

Se compara el sha256 de cada CSV nuevo con `sha256_lf` de `procedencia.json`: sus copias tienen fin de línea CRLF y
la VM escribe LF.

En la tabla del README:
- elecciones, AUC y ganancias tienen que dar "idéntico";
- los tiempos se reportan pero no se comparan, porque dependen de la máquina.

Si algún CSV difiere, se muestra la primera fila distinta y la etapa no cierra sin explicarla.

### D6. Ejecución

Todo lo lanza Agustina, en paralelo, desde el tag `corridas-v3`. Son 18 VMs × 8 vCPU = 144 vCPU, dentro de la cuota de
200. Antes se verifican la cuota y el crédito del trial.

| tanda | VMs | contenido | pared aprox. |
|---|---|---|---|
| Variantes | 8, una por réplica | las 8 variantes de D3 y los estudios `K0.1`, `NH0.1`, `NU0.1` de esa réplica | ~45 min |
| Luis | 9, una por estrategia | 50 semillas en `--hp original`; semillas extra del presupuesto donde K > 50 | ~30 min |
| Luis, agregados | local | `validacion.py --agregar`, `presupuesto.py` | minutos |
| Martín | 1 | 07 + 08 | ~2,1 h |

El modo `--hp ledger` se corre después de la tanda de variantes, porque necesita `NH0.1`, y solo para la estrategia 7.
Es una VM más, de unos 30 min.

### D7. Panel de Luis contra `comun.datos`

Una sola vez, en la VM de Martín mientras corre 07, se arma el panel con el SQL de Luis y se compara con el nuestro:
- columnas (nombres y orden);
- filas por mes;
- huella de cada columna en float32.

| resultado | qué se hace |
|---|---|
| Iguales | el paquete usa `comun.datos` y la tabla atribuye las diferencias con el resumen a tiempos y entorno |
| Distintos | se documenta qué difiere y se corre la estrategia 1 con `--panel-luis` para medir cuánto pesa |

### D8. Comparación y textos

- **`sampling_1`.** Suma `h4` sin cambiar el generador; la spec ya lo pide.
- **Bloque B:** muestra a Martín y a Luis con sus cifras reproducidas y la columna de diferencia con lo reportado.
- **`informe.md` de `sampling_1`:**
  - Resultados con cuatro hipótesis.
  - Conclusiones que respondan al tutor con los contrastes principales.
  - Limitaciones: ideas que salen de mirar 201910 y comparaciones múltiples.
- **`guion.md`:** cuatro hipótesis; los aportes de Martín y Luis como "lo que motivó la segunda ronda".
- **README:** resultados, mapa con `h4` y estado de los aportes como "replicado".

### D9. Consigna de meses en el trabajo de Luis

La consigna dice: Optuna se ordena por AUC en 201908, y 201910 se usa para la comparación "y no debe ser usado para más
que eso". 201911 y 201912 no se usan, y 201909 tampoco: no tiene rol en la consigna y no le damos uno.

| uso en el script de Luis | en el paquete portado |
|---|---|
| "Campeón" y "descartes" por ganancia media en 201910 | ranking por G en **201908** al corte N\* = 3.300; el README clasifica las estrategias con ese ranking y 201910 aparece en una tabla final con todas, sin elegir |
| `gan_max`: máximo de la curva de 201910, que es elegir el corte en test | se calcula en 201908 y se informa como referencia; en 201910 solo G al corte fijo |
| Ganancia según K (1…50) en 201910 | la curva según K se calcula en 201908; en 201910 se informa el ensamble del K que fija el presupuesto (D2) o el K = 10 y 50 del script, sin elegir K mirando el test |
| Presupuesto de 900 s | K sale de los tiempos y la ganancia del ensamble se reporta en 201908 y en 201910; no hay elección en test |
| Raíz contra lineal y H4 difícil contra uniforme | no se eligen: son variantes de D3, todas comparadas en 201910 con las reglas comunes |
| Hard negatives, 35 % del pozo y 10 % de CONTINUA | se mantienen como los fijó Luis; el README dice que no sabemos con qué mes los eligió |

Sus números originales en 201910 se reproducen igual, porque la tabla reportado/reproducido los necesita, pero en una
sección aparte: "Reproducción del resumen original". Las conclusiones del paquete salen solo del ranking en 201908.

En el bloque A no cambia nada: las variantes se comparan con el control en 201910 y no hay selección entre ellas. La
declaración de origen se mantiene: las variantes salen de un análisis que miró 201910. Lo que cambia es que en el repo
ninguna se elige ni se descarta con 201910.

## Risks / Trade-offs

- **[La reconstrucción no es lo que hizo Luis]** Cada interpretación queda escrita (D2). Si una cifra reconstruida no
  se parece a la de su resumen, la tabla lo muestra; no se ajusta la reconstrucción para que coincida.
- **[Test ya mirado]** H4 y los reescalados vienen de resultados de Luis en 201910. No usamos otro mes: seguimos la
  consigna → todas las variantes entran sin selección, los contrastes principales se fijan de antemano y la limitación
  queda declarada (spec).
- **[El ranking en 201908 contradice a Luis]** Puede que en 201908 su "campeón" no sea el primero → el README lo
  muestra tal cual. Las conclusiones del exploratorio son las de 201908, y las suyas quedan en `resumen_original.md`.
- **[Martín no reproduce byte a byte]** Si LightGBM o numpy difieren de su versión, sus CSV pueden cambiar en
  decimales → se registran las versiones; la tabla separa "idéntico", "igual salvo redondeo" y "distinto".
- **[Costo y cuota]** Unas 12 h de VM y 144 vCPU simultáneas. Si el trial no alcanza o la cuota baja, se lanzan en
  tandas; ninguna decisión depende del orden.
- **[`pool_hard_35` depende de la sonda]** La sonda es parte de la variante. Su tiempo cuenta en T y su semilla es la
  de la réplica, así que su suerte también entra en el IC.
