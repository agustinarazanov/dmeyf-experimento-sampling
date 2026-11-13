# H3 — sensibilidad a la muestra de búsqueda (07) y ganancia en 201910 (08)

Aporte de Martín López a `h3`. Responde una pregunta que el diseño de `h3` deja abierta: **¿cuánto depende de la
muestra la configuración que elige H3?** Se repite la búsqueda de H3 con diez muestras distintas del 25 % del train y
las mismas 20 configuraciones. Después se mide en 201910 la ganancia del modelo que eligió cada muestra.

Es **exploratorio y complementario**: no es una variante de `comun/variantes.py`, no escribe en `h3/ledger/` y no cambia
el veredicto de `h3/README.md`. Usa su propio protocolo (búsqueda aleatoria emparejada, float64, 4 hilos),
que se describe abajo, y no se puede comparar uno a uno con las variantes `H3-0.25` y `H3-0.1`.

Todo se corre desde la **raíz del repo**. El paquete importa solo de `comun/` y de esta carpeta.

## Resultados

Corridas reportadas: 07 `20261103T191818_13788` (220 ajustes: 20 de Control y 200 de H3, una sola sesión de
7.230 s) y 08 `20261103T213646_2332`. Los CSV agregados están en [`resultados/`](https://github.com/agustinarazanov/dmeyf-experimento-sampling/tree/main/experimentos/h3/sensibilidad_muestra/resultados): copias byte a byte de
las salidas, con sha256 en `procedencia.json`. Los agregados que no figuran en los CSV, como el tiempo de los 20
ajustes de Control, están en `resumen.json`.

### 07 — elección y tiempo de búsqueda (`resultados/07_resumen_por_semilla.csv`)

- **Control** (20 configuraciones con todo el train): gana la configuración 6, con AUC 0,92960 en la mitad de
  selección de 201908 y **0,92738** en la mitad de evaluación.
- **H3 elige la misma configuración que Control en 7 de 10 muestras.** Las otras tres eligen la 3 (semilla
  20261103), la 16 (20261102) y la 13 (20261111), que en el ranking de Control ocupan los puestos 4, 7 y 2.
- **Delta de AUC** (H3 − Control, en la mitad de evaluación): mediana 0, rango [−0,00008; +0,00223].
- **Spearman** entre los rankings de H3 y de Control en selección: mediana 0,775, rango [0,665; 0,817].
- **Ahorro en la búsqueda: 69 % mediano.** Los 20 ajustes de Control tardan 1.580 s y la búsqueda de H3, una mediana
  de 487 s por muestra (31 % de Control), con un rango de 378 a 1.064 s. El máximo se debe a un solo ajuste lento
  por carga de la máquina: la configuración 1 de la semilla 20261111 tardó 616 s, contra unos 16 s de las otras.
  Medido por muestra, el ahorro va de 33 % a 76 %.

### 08 — ganancia en 201910 con 3.300 envíos (`resultados/08_ganancia_por_*.csv`)

| Config. | Rol | Ganancia | BAJA+2 | BAJA+1 | CONTINUA |
|---|---|---|---|---|---|
| 6 | Control (y H3 en 7 muestras) | 273.350.000 | 331 | 380 | 2.589 |
| 3 | H3, semilla 20261103 | 282.150.000 | 339 | 379 | 2.582 |
| 16 | H3, semilla 20261102 | 268.950.000 | 327 | 386 | 2.587 |
| 13 | H3, semilla 20261111 | 263.450.000 | 322 | 377 | 2.601 |

- **Empate en 7 de 10 muestras.** Eligen la configuración 6, el mismo modelo que Control, así que la diferencia es 0.
- **Rango de −3,62 % a +3,22 %:** +8,80 M$ (+3,22 %) con la 3, −4,40 M$ (−1,61 %) con la 16 y −9,90 M$ (−3,62 %)
  con la 13. La mediana es 0.
- La implementación propia, el módulo del grupo en 4a42bc6 y su curva de corte dan la misma ganancia en las 4
  configuraciones. Las etiquetas del grupo coinciden con el target del paquete en todos los clientes de
  201903–201906, 201908 y 201910, con 0 discrepancias. 201910 tiene 632 BAJA+2, 621 BAJA+1 y 134.380 CONTINUA.
- **Validación con el código del paquete** (2026-11-04). Se corrió `ganancia_08` completo con `--corrida-07`
  apuntando a la corrida original de 07, sin reentrenar, con los insumos verificados por `insumos --solo-verificar`.
  Terminó con código 0 en 192 s y verificó elecciones, modelos y predicciones de agosto.
  - En las 4 configuraciones coinciden exactamente envíos, BAJA+2, BAJA+1, CONTINUA, ganancias y corte con la
    corrida 08 `20261103T213646_2332`. `ganancia_por_semilla.csv` es idéntico byte a byte, y también lo son las
    predicciones de 201910.
  - En `ganancia_por_configuracion.csv` solo difiere `segundos_prediccion`, que es tiempo de ejecución.

### Cómo leer estos números

- **Las 10 muestras comparten el mes de evaluación y representan solo 4 modelos.** Las 7 que eligen la 6 son el
  mismo modelo que Control. Hay una sola mitad de evaluación de 201908 y un solo 201910 para todas. No son 10
  tests independientes: el rango mide la sensibilidad de la elección a la muestra, no la incertidumbre del
  desempeño.
- **Cada fila es un solo modelo, con una sola semilla de LightGBM.** En el grupo, el Control varía entre 271 y
  282 M$ solo por la semilla final, así que diferencias de ±10 M$ quedan dentro de ese ruido.
- **Los deltas de AUC positivos no indican que H3 sea mejor.** Las configuraciones 13 y 16 superan a la 6 en la
  mitad de evaluación, pero no en la de selección. Es ruido entre dos mitades del mismo mes.
- **201908 completo ya se había usado en 06** para elegir y evaluar, así que la mitad de evaluación no es un holdout
  virgen. La elección para 201910 también se hizo con 201908.
- **No se puede comparar uno a uno con `h3/README.md`.** Allí G es la media de 10 semillas finales, con 40
  pruebas de Optuna, otro espacio de búsqueda, float32, 8 hilos y una sola muestra compartida con `h1`.

## Requisitos

- Python 3.12. Las corridas reportadas usaron 3.12.0 en Windows 11, con 8 núcleos lógicos y 15,7 GB de RAM.
- Los paquetes de `requirements.txt` de la raíz y los de [`requirements.txt`](https://github.com/agustinarazanov/dmeyf-experimento-sampling/blob/main/experimentos/h3/sensibilidad_muestra/requirements.txt) de esta carpeta. Esta
  carpeta fija las versiones de las corridas (LightGBM 4.7.0, numpy 2.5.2, pandas 3.0.5, duckdb 1.5.5,
  scikit-learn 1.9.0, scipy 1.18.1) y agrega `psutil`. El protocolo compara huellas sha256 de matrices float64,
  probabilidades y parámetros efectivos, así que con otras versiones esas comparaciones pueden fallar.
- `git`, con el commit 4a42bc6 en la historia del clon.
- Datos en `DATOS_DIR`, como en el resto del repo (por defecto `~/datos/experimentos-dmeyf`):
  - `insumos.py` necesita unos 1,2 GB de disco;
  - cada corrida completa de 07 ocupa unos 165 MB de salida;
  - la carga pide unos 3 GB de memoria y memmaps temporales de 4 GB en disco.

```bash
python -m venv .venv            # en Windows: .venv\Scripts\activate
pip install -r requirements.txt -r experimentos/h3/sensibilidad_muestra/requirements.txt
export DATOS_DIR=~/datos/experimentos-dmeyf     # opcional
```

## Orden de ejecución

| Paso | Comando | Lee | Escribe | Tiempo de referencia |
|---|---|---|---|---|
| 0 | `python -m pytest experimentos/h3/sensibilidad_muestra` | lo versionado | nada | 5 s |
| 1 | `python -m experimentos.h3.sensibilidad_muestra.insumos` | el crudo (lo baja `comun.datos` si falta) | `DATOS_DIR/competencia_02_2019*.parquet`, `…_features/` | ~6,5 min |
| 2 | `python -m experimentos.h3.sensibilidad_muestra.ganancia_08 --solo-pruebas` | `git show 4a42bc6:…` | `…/08_evaluar_ganancia_h3_prueba/<marca>/` | 1 s |
| 3 | `python -m experimentos.h3.sensibilidad_muestra.sensibilidad_07` | insumos y `referencia/` | `…/07_sensibilidad_muestra_h3/<marca>/` | ~2 h (220 ajustes) |
| 4 | `python -m experimentos.h3.sensibilidad_muestra.ganancia_08 --corrida-07 <carpeta del paso 3>` | crudo, insumos, salida de 07 | `…/08_evaluar_ganancia_h3/<marca>/` | ~4 min |

- `…` es `DATOS_DIR/h3_sensibilidad_muestra/ejecuciones`, o la carpeta que se pase con `--salida`. Las salidas
  tienen modelos, predicciones por cliente y memmaps, así que quedan fuera del repo.
- Cada corrida crea una carpeta `<AAAAMMDDTHHMMSS>_<pid>` nueva y nunca sobrescribe.
- `insumos.py` tampoco sobrescribe. Si un insumo existe, lo saltea; para regenerarlo hay que borrarlo a mano.
  `--crudo RUTA` usa un crudo ya descargado y `--solo-verificar` compara los insumos existentes con la referencia sin
  escribir nada.
- Si 07 se corta, `--reanudar <carpeta>` verifica el diseño y saltea los ajustes hechos. `--detener-tras N` corta a
  propósito, para probar la reanudación.
- Los tiempos son los de las corridas reportadas o del recorrido corto en la laptop de Martín.

### Cómo recibe 08 la salida de 07

Al terminar, 07 imprime `Salida para ganancia_08: --corrida-07 <carpeta>`, y 08 recibe esa carpeta. De ella lee:

- `diseno.json`: modo, ids de configuración, semillas y sha256 de los predictores;
- `ajustes.jsonl`: AUC de selección, parámetros efectivos y sha256 de las predicciones de agosto de cada ajuste;
- `control_seleccion.json` y `resumen_por_semilla.csv`;
- `control/modelo_XX.txt` y `control/pred_XX.npy`.

Antes de leer 201910, 08 hace tres comprobaciones y se detiene si alguna falla:

1. Recalcula desde `ajustes.jsonl` la ganadora de Control y la elegida de cada semilla, y comprueba que coinciden con
   lo que guardó 07. En modo completo, la ganadora tiene que ser la 6.
2. Carga cada modelo distinto y comprueba que reproduce exactamente su predicción de agosto (sha256) y sus parámetros
   efectivos.
3. Comprueba que los predictores de los insumos son los de la corrida de 07.

Recién entonces predice 201910 una vez por modelo distinto, con el corte fijo de 3.300 envíos. Una corrida de 07 con
`--prueba` solo se acepta con `--hasta-modelos`, que se detiene antes de leer 201910.

### Referencia grupal 4a42bc6

08 no importa la ganancia del árbol de trabajo. Con `git show 4a42bc6:<archivo>` lee `comun/ganancia.py`,
`comun/datos.py`, `comun/baseline.py` y `tests/test_ganancia.py`, guarda las copias en
`<corrida>/referencia_grupo/` e importa la ganancia de esa copia. Así el resultado no cambia si `comun/` cambia
después. Sobre ese código verifica, y se detiene si algo no coincide:

- **importes:** +1.072.500 por cada BAJA+2 y −27.500 por cada otro estimulado;
- **fórmula y desempate:** la fórmula `np.where(es_baja2, …)` y el `argsort` estable, de modo que a igual
  probabilidad entra el menor `numero_de_cliente`, que es el orden del panel del grupo;
- **SQL de la etiqueta:** macros, `create table crudo` y `etiqueta`, comparados con el texto que ejecuta 08;
- **constantes:** meses de train, validación y test, y rango del crudo.

Después corre las pruebas sintéticas:

- el test de 10 scores del grupo;
- BAJA+1 cuesta como CONTINUA;
- desempate por menor cliente;
- implementación propia igual al módulo del grupo con muchos empates, en cualquier orden de filas y en cualquier
  corte;
- SQL de etiqueta del grupo igual a la regla de `insumos.py`, con casos borde (clientes que faltan un mes y vuelven,
  altas, una sola observación).

Con los datos reales, compara cliente por cliente las etiquetas del grupo sobre el crudo con el target del paquete,
201910 incluido. La ganancia se calcula de tres maneras, que tienen que coincidir: la propia, el módulo del grupo y
su `curva_de_corte`. El reporte informa si esos archivos cambiaron entre 4a42bc6 y HEAD; hasta `54bd6fc` no
cambiaron. `--repo-grupal` permite apuntar a otro clon.

## Qué se reproduce con la prueba rápida y qué requiere la corrida completa

| Qué | Pruebas (paso 0, `--solo-pruebas`) | Recorrido corto | Corrida completa |
|---|---|---|---|
| Grilla de 06: 20 configuraciones, orden y sha256 | ✓ (se regeneran) | ✓ | ✓ |
| Muestras de H3 (`comun.muestreo`) iguales a las de 07, sha256 de las 10 | ✓ | ✓ (2 semillas) | ✓ |
| Ganancia, desempate y etiqueta contra 4a42bc6 (sintético) | ✓ | ✓ | ✓ |
| Features con huecos, nulos y negativos (sintético) | ✓ | — | — |
| CSV de `resultados/` coherentes con lo que dice este README | ✓ | — | — |
| Insumos idénticos a los de las corridas (huella por mes de 04) | — | `insumos --solo-verificar` | `insumos` |
| Datos de train y 201908: sha256 de claves, y y X float64 | — | ✓ | ✓ |
| Partición de 201908 (sha256 y conteos) | — | ✓ | ✓ |
| AUC de 06 reproducido exactamente por Control | — | configuraciones 2 y 12 | las 20, y las predicciones de los finales 13 y 16 |
| Paso de 07 a 08: elecciones recalculadas, modelos y predicción de agosto | — | ✓ (`--hasta-modelos`) | ✓ |
| Elección de H3 en las 10 muestras, delta, Spearman, tiempos | — | — | ✓ |
| Etiquetas del grupo sobre el crudo, 201910 y ganancia con 3.300 envíos | — | — | ✓ |

Recorrido corto, unos 5 minutos con los insumos ya generados (verificar ~1 min, 07 `--prueba` 2–4 min, 08 ~30 s):

```bash
python -m experimentos.h3.sensibilidad_muestra.insumos --solo-verificar
python -m experimentos.h3.sensibilidad_muestra.sensibilidad_07 --prueba      # cfg 2 y 12, semillas 20261102-03: 6 ajustes
python -m experimentos.h3.sensibilidad_muestra.ganancia_08 --corrida-07 <carpeta que imprime> --hasta-modelos
```

Los tiempos de ajuste varían con la carga de la máquina, así que no se comparan con los reportados.
La reproducción exacta de AUC, predicciones y parámetros efectivos se verificó en la misma máquina y con las mismas
versiones. LightGBM corre con `deterministic=false` (default) y 4 hilos, de modo que en otro procesador u otra
versión los valores pueden diferir en los últimos decimales. Si eso pasa, 07 lo informa en
`control_evaluacion.json` → `reproduccion_06` y 08 se detiene en la verificación de modelos.

## Reproducción en la VM (incorporar-aportes, D5)

Corrida del 9–10-nov-2026 en una VM `n2-highmem-8` (Linux, Python 3.14.4, **LightGBM 4.7.0, numpy 2.5.2**, las versiones
fijas de `requirements.txt`; las originales eran Python 3.12.0 en Windows 11), 4 hilos. 07 en
`ledger/martin/07/.../20261109T235232_15814` y 08 sobre esa corrida en `ledger/martin/08/.../20261110T005130_12983`
(el primer intento de 08 falló por falta de git). Se compara el sha256 con fin de línea LF contra `sha256_lf` de
`resultados/procedencia.json`; el script es `python -m experimentos.sampling_1.exploratorios.comparar_martin`.

| salida | sha256 del archivo | columnas sin tiempo | resultado | explicación |
|---|---|---|---|---|
| `07_resumen_por_semilla.csv`: elecciones, AUC, delta, Spearman | no coincide | las 10 filas, iguales | idéntico | el archivo difiere solo en `tiempo_busqueda_s` y `tiempo_ajuste_completo_reutilizado_s` |
| `07_resumen_por_semilla.csv`: tiempos | no coincide | — | distinto | dependen de la máquina (p. ej. búsqueda 167,0 s contra 378,2 s en la primera semilla); no se comparan |
| `08_ganancia_por_semilla.csv` | coincide | — | idéntico | mismo sha256 |
| `08_ganancia_por_configuracion.csv`: ganancias, envíos, empates | no coincide | las 4 filas, iguales | idéntico | difiere solo en `segundos_prediccion` |
| `08_ganancia_por_configuracion.csv`: `segundos_prediccion` | — | — | distinto | tiempo de máquina; no se compara |

Las elecciones, los AUC y las ganancias salieron idénticos pese al cambio de sistema, de Python y de procesador.

## Protocolo (el de las corridas reportadas, sin cambios)

- **Datos.** Solo 2019. Train 201903–201906 completo (506.871 filas, 5.313 positivos) y validación 201908
  (131.775 filas). 201909 no se lee y 201910 solo en 08. Positivo = BAJA+1 ∪ BAJA+2.
- **Features.** 760 predictores: las 152 columnas originales más lag1, delta1, lag2 y delta2 de cada una, en el
  orden de `manifiesto.json`.
  - El lag es la k-ésima observación previa del cliente, como en el panel del grupo.
  - BIGINT pasa a float64 de forma exacta (|x| ≤ 2^53, verificado) y DOUBLE queda igual.
  - NULL pasa a NaN, sin imputar. **Nunca float32.**
- **Grilla.** [`referencia/grilla_06.json`](https://github.com/agustinarazanov/dmeyf-experimento-sampling/blob/main/experimentos/h3/sensibilidad_muestra/referencia/grilla_06.json): las 20 configuraciones de 06, en su orden.
  - Generador: `SeedSequence(20261102).spawn(2)[1]`.
  - Espacio: `num_leaves` en [8, 64], `learning_rate` log-uniforme en [0,01; 0,10], `min_data_in_leaf`
    log-uniforme en [100, 2000], y `feature_fraction` y `bagging_fraction` en [0,5; 1,0].
  - 07 la regenera con el generador y se detiene si no es idéntica. No hace falta la carpeta de la corrida 06.
- **Modelo.** `lgb.train` con nombres canónicos:
  - 100 árboles sin early stopping, `objective=binary`, `metric=auc`, `bagging_freq=1`, 4 hilos y
    `seed=20261102`, sin pesos de clase y con el resto en defaults;
  - después de cada ajuste se comparan los parámetros efectivos con los pedidos.
- **Partición de 201908.** Por (`numero_de_cliente`, `foto_mes`), estratificada por clase, con
  `default_rng(20261102)`.
  - Selección: 65.887 filas y 601 positivos.
  - Evaluación: 65.888 filas y 601 positivos.
- **Muestras de H3.** `comun.muestreo.indices_uniformes(506871, 0.25, s)`, con s = 20261102…20261111: 126.718 filas
  cada una. Es idéntico a `default_rng(s).choice(n, 126718, replace=False)` ordenado; el script lo comprueba.
- **Regla de selección.**
  - En Control y en cada muestra gana la configuración con mayor AUC en la mitad de selección; a igual AUC, la de
    menor id.
  - El ranking de Control se congela en `control_seleccion.json` antes de calcular cualquier AUC en la mitad de
    evaluación.
  - El final de H3 es el ajuste completo de Control de la configuración elegida (06 mostró que reentrenarlo da
    exactamente lo mismo).
- **Ganancia.** Corte fijo de 3.300 envíos, el N\* del control del grupo en 201908 (`h3/README.md`).
  - +1.072.500 por cada BAJA+2 y −27.500 por cada otro estimulado.
  - A igual probabilidad, el menor `numero_de_cliente`.

## Archivos

| Archivo | Qué es | Viene de (repo de origen `experimento_sampling/`) |
|---|---|---|
| `insumos.py` | crudo → 2019 tipado → target → features + manifiesto | 02, 03 y 04 (la lógica de features de `pipeline_competencia02/features.py`), reducidos a lo necesario |
| `carga.py` | unión 1:1, BIGINT → float64 exacto, memmaps | funciones de 05, sin cambios de lógica |
| `busqueda.py` | generador de la grilla, ajuste y verificación de parámetros | funciones de 06 y la carga de la grilla de 07 |
| `sensibilidad_07.py` | 07 | 07 |
| `ganancia_08.py` | 08 | 08 |
| `rutas.py` | rutas bajo `DATOS_DIR` | — |
| `referencia/grilla_06.json` | las 20 configuraciones, fijos, semillas y regla de selección | `06/20261102T215551_12584/configuraciones.json` |
| `referencia/corrida_06.json` | AUC de 06 por configuración y finales (parámetros efectivos y sha256 de sus probabilidades) | resultados y reporte de 06 |
| `referencia/huellas_datos.json` | sha256 de claves, y y X de train, 201908 y 201910; partición; muestras; etiquetas por mes | `diseno.json` de 07 y `reporte.json` de 08 |
| `referencia/esquema_2019.json` | columnas y tipos de 2019, filas por mes y huella de las features por mes | Parquet de 02 y manifiesto de 04 |
| `resultados/*.csv` | salidas agregadas de 07 y 08 | copias byte a byte |
| `resultados/resumen.json`, `procedencia.json` | agregados de los reportes y sha256 de las copias | `reporte.json` de 07 y 08 |
| `tests/test_h3sm_*.py` | pruebas sin datos (13) | — |

**Qué se reutiliza del grupo:**

- `comun.baseline`: `DATOS_DIR`, meses de train, validación y test;
- `comun.datos`: ruta y descarga del crudo;
- `comun.muestreo.indices_uniformes`: las muestras;
- `comun.rutas`;
- `comun/ganancia.py` de 4a42bc6, como referencia de la ganancia.

**Qué no se reutiliza, y por qué:**

- el panel de `comun.datos` se guarda en float32 y con otros nombres de columna, y el protocolo de las corridas
  reportadas es float64;
- el SQL de la etiqueta del grupo da las mismas etiquetas que `insumos.py` (verificado), pero solo existe dentro de la
  construcción del panel.

**Diferencias con el repo de origen:**

- las rutas;
- la grilla y las comprobaciones de reproducción salen de `referencia/` y no de las carpetas de corridas;
- 07 compara las huellas de los datos con la referencia (antes comparaba el orden del train con la muestra de 06);
- 08 recibe la corrida de 07 por argumento y suma `--hasta-modelos`.

**Qué no está en el repo:** datasets, claves de clientes, predicciones individuales, modelos ni temporales.

## Insumos desde el dataset autorizado

`insumos.py` parte de `competencia_02_crudo.csv.gz`, el crudo del curso que usa `comun.datos`. En el repo de origen,
01–04 partían de un `competencia_02_2019.csv.gz` aparte, con fin de línea `\r\n`. El 4-nov-2026 se comprobó que las
1.563.565 filas de 2019 del crudo, tipadas con `referencia/esquema_2019.json`, son **idénticas** al Parquet de 2019
que usaron las corridas: 0 filas de diferencia en un `EXCEPT ALL` en ambos sentidos, con las mismas 154 columnas en
el mismo orden. Las verificaciones de 01–04 que aquí no se repiten (auditoría de faltantes, relectura celda por celda
con pandas, recálculo de lags en numpy) quedan reemplazadas por la comparación con las huellas de las corridas
reportadas.
