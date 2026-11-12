# Validación con 50 semillas — aporte de Luis María Laguinge

**Autor:** Luis María Laguinge. **Fecha del aporte:** 2026-11-06. **Origen:** commit `9e1889e` ("Add files via upload"),
que traía `script_de_validaci_n_50_semillas.py` (un script de Colab de unas 390 líneas) y
`resumen_completo_de_experimentos.md`. El script original no se conserva como archivo: está en la historia de git. El
resumen sigue acá, sin cambios, como [`resumen_original.md`](resumen_original.md). El HTML que acompañaba el resumen (5-nov, subido
aparte en el commit `d8f04b2`) está sin cambios en [`reporte_original.html`](reporte_original.html); no confundir con
`resultados/reporte_50_semillas_original.html`, que es el reporte que genera `--agregar --hp original`.

Es **exploratorio**: no es una variante de `comun/variantes.py` y no cambia el veredicto de ninguna hipótesis. Las ideas
que prueba (reescalado de `min_data_in_leaf`, hard negatives, fast-retrain, muestreo por cliente) entran al protocolo
como variantes con réplicas en `h3` y `h4` (`openspec/changes/archive/2026-11-10-incorporar-aportes/design.md` D3 y D4). Todo se corre desde
la **raíz del repo**; el paquete importa solo de `comun/` y de esta carpeta.

## Protocolo de Luis

- Nueve estrategias, cada una con **50 semillas finales**: las 10 oficiales y `110017 + i·19937` (i = 0…39).
- Hiperparámetros fijos, escritos a mano en el script (acá en [`hp_original.json`](hp_original.json)); no repite la
  optimización.
- Mide la ganancia al corte N\* = 3.300, el máximo de la curva, el AUC, el tiempo por semilla, los ensambles de 10 y 50
  semillas y la ganancia según K.
- Analiza un **presupuesto de 900 s** (optimizar y re-entrenar semillas dentro de 15 minutos).
- Los tiempos se multiplican por `FACTOR_VM`, una calibración contra 16,24 s de un final de `U0.1` en su VM.

## Diferencias con el protocolo nuestro

| | Luis | nuestro |
|---|---|---|
| Semillas finales | 50 (+ extendidas para el presupuesto) | 10 |
| Réplicas de optimización | una por estudio (los hp se fijan) | 8 réplicas (`replica_opt`) |
| Panel de datos | arma el suyo con DuckDB en Colab | `comun.datos` (se compara una vez, D7: `panel_luis.py`, salida `ledger/luis/panel_d7.json`) |
| Ganancia | `mergesort` descendente (empates en orden inverso) | `comun.ganancia`: `argsort` estable, empates por orden de aparición |
| Tiempos | × `FACTOR_VM` | medidos en la VM, sin factor (el factor se registra aparte) |
| Mes que decide | 201910 ("campeón", máximo de la curva, K) | **201908** (consigna: 201910 solo para comparar; D9) |
| Hilos | todos los de la máquina | 8 (`bl.NUM_THREADS`) |

## Qué se portó y qué se reconstruyó

**Portado sin cambios de lógica** (`estrategias.py`, `validacion.py`, `hp_original.json`):
las nueve estrategias y sus semillas, `escalar_hp`, el entrenamiento final por semilla (modo `full` y fast-retrain con el
50 % de las CONTINUA y peso 2, que es `comun.muestreo.indices_por_clase` + `peso_inverso`; un test lo contrasta con la
receta del script), los parámetros de LightGBM, la medición del tiempo (construcción del dataset + entrenamiento +
predicción de test) y los ensambles acumulados por K. Las estrategias se numeran 1…9; en el script de Luis van de
`0_Control_C` a `8_IdeaC_FastRetrain_U0.25_H4_50pct` (la estrategia `k` de acá es la `k − 1` de allá).
`calibracion_<hp>_e<k>.json` registra además el commit, `codigo_sucio` y el tipo de máquina de la corrida.

**RECONSTRUIDO** (el script no lo tiene o no lo escribe; cada pieza está marcada así en el código; `design.md` D2):

| pieza | interpretación elegida | dónde |
|---|---|---|
| `resumen_50_semillas.csv` | una fila por estrategia y semilla: G al corte 3.300, ganancia máxima y AUC en 201908; G y AUC en 201910; tiempo | `validacion.py` (`correr_estrategia`, `agregar`) |
| Presupuesto de 900 s | K = ⌊(900 − T_opt) / T_final medio⌋; ensamble de las primeras K; si K > 50, semillas extra con `110017 + i·19937` (i ≥ 40, tope 300) | `presupuesto.py`, `--presupuesto 900` |
| Ranking y curva según K | en 201908; en 201910 solo el ensamble de K = 10, 50 y el K del presupuesto | `validacion.py --agregar` |
| `--hp ledger` | lee nuestros `hp/*.json`; `H4_Hard` sale del estudio reconstruido `NH0.1` de `h4` | `estrategias.py` |
| Búsqueda con hard negatives (`H4_Hard`), H4 uniforme, muestreo por cliente, reescalado lineal | son variantes de `h3` y `h4` (`H4H-0.1`, `H4U-0.1`, `H3K-0.1`, `H3L-*`), con sus estudios `NH0.1`, `NU0.1` y `K0.1` | `comun/variantes.py` |

**No portado:** la sonda de 40 árboles y `pool_hard_35` (el script los define pero no los usa; ahora los usa `comun`), el
armado del panel con SQL propio (`comun.datos`; solo se vuelve a armar si D7 muestra diferencias, con `--panel-luis`) y el
HTML mínimo con un boxplot (se reemplaza por el reporte de `--agregar`).

## Meses (consigna: Optuna por AUC en 201908; 201910 solo para comparar)

Cada semilla predice 201908 y 201910. **Todo lo que ordena o decide sale de 201908**: el ranking de estrategias, la
ganancia máxima de la curva (referencia) y la curva según K. De 201910 se informa G al corte fijo, el AUC y los ensambles
de K = 10, K = 50 y el K del presupuesto, para todas las estrategias y sin elegir (`tabla_201910_*.csv`). Los tests lo
comprueban con datos sintéticos donde 201908 y 201910 ordenan distinto. 201909, 201911 y 201912 no se usan. El resumen de
Luis (`resumen_original.md`) elige "campeón" y "descartes" con 201910 y dice que no sabemos con qué mes eligió los
hard negatives; sus cifras se reproducen igual, en una sección aparte, porque la tabla de abajo las necesita.

## Cómo se corre

```
# una estrategia (una VM por estrategia): escribe en experimentos/sampling_1/ledger/luis/
python -m experimentos.sampling_1.exploratorios.validacion_50_semillas.validacion --estrategia 1 --hp original --presupuesto 900
# smoke en la Mac
python -m experimentos.sampling_1.exploratorios.validacion_50_semillas.validacion --estrategia 8 --semillas 2 --filas 20000 --salida /tmp/luis_smoke
# agregados y HTML (sin datos)
python -m experimentos.sampling_1.exploratorios.validacion_50_semillas.validacion --agregar --hp original
python -m experimentos.sampling_1.exploratorios.validacion_50_semillas.presupuesto --hp original
```

Las VMs se lanzan con `scripts/lanzar_fase.sh fase6_luis_<estrategia>` (una lista por estrategia en
`experimentos/sampling_1/scripts/`; el modo `--hp ledger` es la lista `fase6_luis_7_ledger`, que va después de que `NH0.1`
esté en el ledger).

## Conclusiones

Salen solo del ranking en **201908** al corte fijo N\* = 3.300 (D9); 201910 no interviene. Corrida del 9–10-nov-2026 en
`n2-highmem-8`, hiperparámetros de Luis (`--hp original`), 50 semillas por estrategia (55, 70 y 63 donde el presupuesto
de 900 s pide más). Generado por `tabla_reproduccion.py`; no editar a mano.

<!-- ranking:inicio -->
| puesto | estrategia | n | G 201908 (M$) | desvío (M$) | G máx. 201908 (M$) | AUC 201908 | tiempo (s) |
|---|---|---|---|---|---|---|---|
| 1 | 1 Control_C (Full 100%) | 50 | 207,86 | 3,28 | 210,24 | 0,9300 | 31,3 |
| 2 | 4 H3-0.05 (Campeon 5%) | 50 | 203,17 | 3,90 | 209,18 | 0,9269 | 20,4 |
| 3 | 8 IdeaC_FastRetrain_U0.05_H4_50pct | 70 | 202,32 | 3,44 | 207,53 | 0,9269 | 11,9 |
| 4 | 7 IdeaB_OptH4_HardNeg_Full | 50 | 201,85 | 4,41 | 208,35 | 0,9270 | 32,1 |
| 5 | 9 IdeaC_FastRetrain_U0.25_H4_50pct | 63 | 201,76 | 4,48 | 208,21 | 0,9290 | 11,8 |
| 6 | 5 IdeaA_H3-0.25_SqrtScale(x2) | 50 | 201,54 | 4,04 | 208,30 | 0,9290 | 19,8 |
| 7 | 2 H3-0.25 (Original 25%) | 50 | 199,72 | 4,50 | 208,28 | 0,9287 | 20,2 |
| 8 | 3 H3-0.10 (Original 10%) | 55 | 197,11 | 4,56 | 203,28 | 0,9252 | 14,9 |
| 9 | 6 IdeaA_H3-0.10_SqrtScale(x3.2) | 55 | 196,69 | 3,94 | 202,72 | 0,9257 | 14,9 |
<!-- ranking:fin -->

1. **El control es el primero en 201908** y ninguna estrategia lo supera: la más cercana es `H3-0.05` (estrategia 4),
   que queda por debajo. El "campeón" del resumen original no gana en el mes que decide el protocolo.
2. Las estrategias de re-entrenamiento rápido (8 y 9, ≈ 12 s por semilla contra ≈ 31 s del control) quedan en el medio
   de la tabla: pierden ganancia por semilla, pero entran más del doble de semillas en el presupuesto de 900 s.
3. Las de tasa 0,10 (3 y 6) son las últimas; el reescalado de raíz no las rescata. Con 0,25 la raíz (5) queda por encima
   del reescalado nulo (2).
4. Estos desvíos entre estrategias son del orden de la desviación entre semillas (3–5 M$): el ranking de una sola
   réplica de búsqueda por estrategia no distingue entre las del medio. Las comparaciones con réplicas de la búsqueda
   están en los informes de `h3` y `h4`.

Lo que dice el resumen original (campeón, descartes) se eligió mirando 201910 y queda solo en `resumen_original.md`.

## Reproducción del resumen original

Cada número del resumen original de Luis (todos en 201910, como él los calculó) contra lo que da este repositorio.
"RECONSTRUIDO" marca los que dependen de una pieza que el script no tenía (D2). Las diferencias son reproducido menos
reportado; los tiempos son de la VM, sin `FACTOR_VM`. No se eligió ni descartó nada con estos números. Generado por
`tabla_reproduccion.py` (`--verificar` comprueba que el README coincide con `resultados/`, `panel_d7.json`,
`hp_original.json`, `estrategias.py`, los `replicas.csv` y `estudios.csv` de `h3`, `h4`, `h1` y `control`, y
`h1/ledger/apareado.csv`).

| número del resumen original | reportado | reproducido | diferencia | explicación |
|---|---|---|---|---|
<!-- tabla:inicio -->
| Optuna del control | ~13 minutos | 12,5 min (`t_opt` de `hp_original.json`, el de Luis); 15,8 min (mediana de 8 réplicas en la VM) | -0,5 min (el de Luis) | el de Luis coincide; el de la VM es otra máquina, sin `FACTOR_VM` |
| Error estándar de 10 a 50 semillas | cayó a la mitad | 1,20 M$ con las primeras 10 semillas y 0,55 M$ con 50 (estrategia 1, G en 201910): cociente 0,46 | -0,04 | consistente: con el mismo desvío el cociente es √(10/50) ≈ 0,45 |
| Todas las variantes de H3 le ganan al control (50 semillas) | "todas GANAN" | estrategia 2: +4,55 M$ [+2,97; +6,14]; estrategia 3: +3,89 M$ [+2,18; +5,61]; estrategia 4: +5,61 M$ [+4,10; +7,12]; estrategia 5: +4,05 M$ [+2,69; +5,41]; estrategia 6: +3,87 M$ [+2,42; +5,32] (Δ apareado por semilla en 201910, IC 95%) | 5 de 5 con IC sobre cero | una sola búsqueda por estrategia: el IC no incluye la variabilidad de Optuna; veredictos con 8 réplicas (`h3`): `H3-0.05` no pierde, `H3-0.1` no pierde, `H3-0.25` no pierde, `H3R-0.1` no pierde, `H3R-0.25` no pierde |
| Hiperparámetros de H3-0.05 | `feature_fraction = 0.34`, `min_data_in_leaf = 985` | `feature_fraction = 0,34`, `min_data_in_leaf = 985` (`hp_original.json`) | idéntico | son los hiperparámetros fijados en su script, portados sin cambios |
| `feature_fraction` del control | 0.985 | 0,985 (`hp_original.json`) | idéntico | ídem |
| H3-0.05 sobre el control (ganancia media) | +6,47 M$ | +5,61 M$ (50 semillas, estrategia 4 contra 1, hiperparámetros de Luis); +1,87 M$ (8 réplicas × 10 semillas, `h3`) | -0,86 M$ (50 semillas) | mismo sentido, menor magnitud; con réplicas el IC de Δ incluye el cero (veredicto "no pierde", no "gana") |
| Optuna de H3-0.05 contra el control | 8,89 veces más rápido | 15,88 veces (mediana de 948 s contra 60 s, 8 réplicas, solo la optimización) | 6,99 | tiempos medidos en la VM, sin `FACTOR_VM`; no es una diferencia de ganancia, depende de la máquina |
| H4 hard (reconstruido: `NH0.1`) sobre el control | +7,19 M$ | +5,48 M$ (50 semillas, estrategia 7 con los hiperparámetros de Luis); -2,13 M$ (`--hp ledger`, `NH0.1`); -8,61 M$ (8 réplicas, `H4H-0.1`) | -1,71 M$ (50 semillas, `original`) | RECONSTRUIDO: con los hiperparámetros de Luis da positivo; con la búsqueda reconstruida (`NH0.1`) da negativo, en 50 semillas y con réplicas; la ventaja no se sostiene al repetir la búsqueda |
| H4 con negativos uniformes (reconstruido: `NU0.1`) sobre el control | −2,31 M$ | -5,54 M$ (8 réplicas, `H4U-0.1`) | -3,23 M$ | RECONSTRUIDO: mismo signo, mayor magnitud; con réplicas el IC queda por debajo del cero |
| Hiperparámetros de H4 uniforme (reconstruido: `NU0.1`) | `num_leaves = 226`, `feature_fraction > 0.70` | `num_leaves = 236`, `feature_fraction = 0,65` (medianas de 8 réplicas); `NH0.1`: `num_leaves = 14`, `feature_fraction = 0,31` | — | RECONSTRUIDO: la búsqueda no es la suya; se informa para ver si la uniforme elige árboles más complejos que la difícil |
| Fast-retrain: tiempo por semilla | 12,3 s | 11,9 s y 11,8 s (estrategias 8 y 9, medidos en la VM); 11,3 s (mediana de `H4F-0.05`, solo entrenamiento) | -0,4 s (estrategia 8) | tiempo de máquina, sin `FACTOR_VM`; del mismo orden |
| Fast-retrain: semillas que entran en 900 s (reconstruido) | más de 60 | 70 (estrategia 8) y 63 (estrategia 9) | consistente | RECONSTRUIDO: K = ⌊(900 − T_opt) / T_final medio⌋ |
| Fast-retrain: ensamble a 900 s | 283,25 M$ | 278,85 M$ y 282,15 M$ (201910, ensamble de las primeras K semillas) | -4,40 M$ y -1,10 M$ | RECONSTRUIDO: el ensamble depende de las semillas elegidas y de K; un solo ensamble por estrategia, sin IC |
| Control: ensamble a 900 s | 276,65 M$ | 278,85 M$ (K = 4) | +2,20 M$ | RECONSTRUIDO: ídem; el ensamble de pocas semillas es muy variable |
| Control: tiempo por semilla | 35 s | 31,3 s (estrategia 1); 31,2 s (mediana de `C` en `control`, solo entrenamiento) | -3,7 s | tiempo de máquina, sin `FACTOR_VM` |
| Control: semillas que entran en 15 minutos | 4 | 4 (estrategia 1) | idéntico | RECONSTRUIDO: misma fórmula que el fast-retrain |
| Fast-retrain: fracción de CONTINUA y peso | 50 %, `w = 2` | 50 %, `w = 2` (`estrategias.py`) | idéntico | parámetro portado sin cambios |
| Reescalado √(1/r): menos varianza entre semillas y mejor ensamble | sin número | desvío de G en 201910: 4,12 contra 4,59 M$ (0,25: estrategia 5 contra 2) y 3,84 contra 4,02 M$ (0,10: 6 contra 3); ensamble a 900 s: 284,35 contra 281,05 M$ y 283,25 contra 279,95 M$ | — | un solo ensamble y una sola búsqueda por estrategia; con réplicas, los contrastes `H3R` contra `H3` están en `h3` |
| H1: muestreo uniforme también en el final (descarte) | "se desploma" por debajo del 50 % | `U0.25`: -6,38 M$, pierde; `U0.1`: -16,94 M$, pierde; `U0.05`: -33,77 M$, pierde (`h1/ledger/apareado.csv`, 10 semillas) | — | mismo sentido; es la H1 de la primera ronda, sin réplicas de la búsqueda |
| Reescalado lineal peor que √(1/r) (reconstruido: `H3L-*`) | "cae drásticamente" | `H3L-0.1` contra `H3R-0.1`: -3,22 M$; `H3L-0.25` contra `H3R-0.25`: -1,28 M$ (diferencia de medias de réplicas) | — | RECONSTRUIDO: el lineal queda por debajo del de raíz en ambas tasas; son diferencias de medias, no un contraste con IC |
| Muestreo por cliente peor que por filas (reconstruido: `H3K-0.1`) | "peor rendimiento" | `H3K-0.1` contra `H3-0.1`: -1,02 M$ (diferencia de medias de réplicas) | — | RECONSTRUIDO: mismo sentido, diferencia chica; no es un contraste con IC |
| Panel de Luis contra `comun.datos` (D7) | — | 765 columnas contra 755 (nuestro panel suma 10: `tmobile_app` y `cmobile_app_trx` con sus lags y deltas); filas por mes iguales; huellas de las 755 columnas comunes: 0 distintas; estrategia 1 con `--panel-luis`: 273,99 M$ contra 274,63 M$ en 201910 | -0,64 M$ | veredicto "distintos" por las columnas extra; el efecto sobre la ganancia es chico frente a la desviación entre semillas |
<!-- tabla:fin -->

**Comparación de paneles (D7).** El panel que arma el SQL de Luis y `comun.datos` tienen las mismas filas por mes y la
misma huella en las columnas que comparten, pero el nuestro suma las columnas de `mobile_app` con sus lags y deltas. El
veredicto es "distintos" y se corrió la estrategia 1 con `--panel-luis` (`ledger/luis/panel_luis`, `panel_d7.json`):
la diferencia de ganancia es la última fila de la tabla. Por eso las diferencias con el resumen se atribuyen sobre todo
a que Luis usó un solo ensamble o una sola búsqueda por estrategia, a los tiempos, al entorno y, en las filas
RECONSTRUIDAS, a que la pieza no es la suya; el panel pesa poco.
