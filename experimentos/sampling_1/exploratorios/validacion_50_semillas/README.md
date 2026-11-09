# Validación con 50 semillas — aporte de Luis María Laguinge

**Autor:** Luis María Laguinge. **Fecha del aporte:** 2026-11-06. **Origen:** commit `9e1889e` ("Add files via upload"),
que traía `script_de_validaci_n_50_semillas.py` (un script de Colab de unas 390 líneas) y
`resumen_completo_de_experimentos.md`. El script original no se conserva como archivo: está en la historia de git. El
resumen sigue acá, sin cambios, como [`resumen_original.md`](resumen_original.md).

Es **exploratorio**: no es una variante de `comun/variantes.py` y no cambia el veredicto de ninguna hipótesis. Las ideas
que prueba (reescalado de `min_data_in_leaf`, hard negatives, fast-retrain, muestreo por cliente) entran al protocolo
como variantes con réplicas en `h3` y `h4` (`openspec/changes/incorporar-aportes/design.md` D3 y D4). Todo se corre desde
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

## Tabla reportado / reproducido

Vacía hasta las corridas (tarea 4 del cambio). "Reconstruido" marca los números que dependen de una pieza reconstruida.

| número del resumen original | reportado | reproducido | diferencia | explicación |
|---|---|---|---|---|
| H3-0.05 sobre el control (ganancia media) | +6,47 M$ | | | |
| Optuna de H3-0.05 contra el control | 8,89 veces más rápido | | | |
| H4 hard (reconstruido: `NH0.1`) sobre el control | +7,19 M$ | | | |
| H4 con negativos uniformes (reconstruido: `NU0.1`) | −2,31 M$ | | | |
| Fast-retrain: tiempo por semilla | 12,3 s | | | |
| Fast-retrain: semillas que entran en 900 s (reconstruido) | más de 60 | | | |
| Fast-retrain: ensamble a 900 s | 283,25 M$ | | | |
| Control: ensamble a 900 s | 276,65 M$ | | | |
| Control: tiempo por semilla | 35 s | | | |
| Reescalado lineal peor que √(1/r) (reconstruido: `H3L-*`) | "cae drásticamente" | | | |
| Muestreo por cliente peor que por filas (reconstruido: `H3K-0.1`) | "peor rendimiento" | | | |

## Conclusiones

Pendientes: salen del ranking en 201908 (tarea 5.2).
