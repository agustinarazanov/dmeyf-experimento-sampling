# Proposal

## Why

El tutor preguntó (Aramendía, Zulip 212124, 12-nov) si H4 "dialoga con la H1", si el undersampling usa "los mismos
cortes" y si "se verá alguna diferencia", y pidió "medir tiempos de forma confiable". Una revisión del repo (13-nov)
encontró tres cosas.

**La aceleración A no se calcula igual en todas las filas.** Las variantes sin réplicas (`U*`, `B*`, `GOSS`) dividen por
el T de la réplica 0 del control (797 s); las que tienen réplicas, por la mediana del control (1.002 s). El T del control
varía de 682 a 1.264 s entre las 8 réplicas de Optuna, y U0.5 queda con A = 2,25, cerca del umbral A ≥ 2 de "vale la
pena".

**Las hipótesis no comparten grilla.** Cada una eligió sus tasas y su cantidad de réplicas, así que la pregunta del tutor
solo se puede contestar en dos puntos. Lo que hay hoy:

| cómo se muestrea | dónde | 0,5 | 0,25 | 0,1 | 0,05 | réplicas |
|---|---|---|---|---|---|---|
| al azar (H1, `U`) | búsqueda y final | ✓ | ✓ | ✓ | ✓ | 1 |
| al azar (H3) | solo búsqueda | falta | ✓ | ✓ | ✓ | 8 |
| bajas + f de CONTINUA con peso (`H4O`) | búsqueda y final | ✓ | falta | falta | falta | 8 |
| bajas + f de CONTINUA | solo búsqueda | falta | falta | ✓ sin peso (`H4U`) | falta | 8 |
| dentro de LightGBM (H2, `B`) | cada árbol | ✓ | ✓ | ✓ | falta | 1 |

**Los informes tienen frases que contradicen las tablas** o quedaron de rondas anteriores.

Sobre los tiempos, la máquina no parece la fuente principal del ruido. Todas las corridas usaron la misma CPU, con un
trabajo por VM, y el tiempo del mismo modelo entre semillas varía poco dentro de una VM (el número exacto sale del
ledger en la tarea 1.1; la revisión midió entre el 1,8 y el 6,1 %). El ruido grande viene de los hiperparámetros que recorre
y elige Optuna. Entre VMs la única evidencia es `C-rep` (una repetición, 4 %), así que este cambio lo mide.

## What Changes

**Tiempos**

- **A con una sola referencia**: en todas las filas del bloque A, A = mediana de T_C entre réplicas / T de la variante.
  Junto a A va su intervalo, que no depende de cómo se emparejen las réplicas. Cambian los A de `U*`, `B*` y `GOSS` en `tabla_resultados.md`, los informes y el README. Este
  cambio es deliberado: modifica la regla "tabla de resultados intacta" del spec vigente.
- **Medición a hiperparámetros fijos** (nueva, exploratoria y pre-registrada): con los hiperparámetros de las 8 réplicas
  del control, entrenar sobre r = 1; 0,5; 0,25; 0,1; 0,05 del train 201903–201906, con la muestra al azar de H1 y con
  la receta de H4 (bajas + f de CONTINUA con peso), prediciendo 201908 como un trial, con repeticiones. Separa la
  aceleración que da el tamaño de los datos de la que da la elección de Optuna.
- **Calibración por máquina** (nueva): cada VM de la fase corre el mismo entrenamiento fijo al empezar y al terminar su
  lista, y guarda el nombre de la instancia. Mide el ruido entre VMs y la deriva dentro de una VM, y se ancla a las fases
  anteriores con tiempos que ya están guardados (el mejor trial de cada estudio del control y un final de `C`).
- **Búsqueda, final y preparación por separado**: el reporte muestra, por variante, cuánto de T es búsqueda y cuánto es
  final, y cuánto lleva la preparación de datos, que no entra en T.

**Grilla común** (variantes y corridas nuevas, todas con predicción escrita antes de correr)

- **Las mismas cuatro tasas** (0,5; 0,25; 0,1; 0,05) en las cinco filas de la tabla de arriba:
  - `H3-0.5`: búsqueda sobre el 50 % al azar (estudio `U0.5`), final completo.
  - `H4O-0.25`, `H4O-0.1`, `H4O-0.05`: la receta de `H4O-0.5` (bajas + f de CONTINUA con peso 1/f, en búsqueda y final)
    en las tasas de H1. Es la comparación que pide el tutor.
  - `H4P-0.5`, `H4P-0.25`, `H4P-0.1`, `H4P-0.05` (método nuevo): la misma búsqueda con peso que `H4O` (comparten
    estudio) y final completo. Es a `H4O` lo que H3 es a H1. `H4U-0.1`, sin peso, queda como está.
  - `B0.05`: bagging con f = 0,05.
- **8 réplicas de optimización en todo el bloque A**: se suman las 7 que faltan de `U0.5`, `U0.25`, `U0.1`, `U0.05`,
  `B0.5`, `B0.25`, `B0.1` y `GOSS`. Los estudios `U0.25@k`, `U0.1@k` y `U0.05@k` ya existen (los corrió H3): para esas
  tasas de H1 solo faltan los finales.
- **Los estudios `U{r}@k` pasan a ser de `h1`** (hoy son de `h3`), para que H1 tenga sus réplicas en su ledger sin un
  ciclo de dependencias entre `h1` y `h3`. Se mueven sin cambiar su contenido.
- **Tabla de cobertura** en el reporte y el informe conjunto: qué celda de la grilla se corrió, con cuántas réplicas, y
  qué no se corrió y por qué. Sale del registro de variantes.
- **Comparaciones directas**: los pares de variantes que se comparan (cómo, dónde, peso) quedan declarados en el
  registro antes de correr y salen en la tabla de diferencias, con las filas de entrenamiento de cada lado. Los pares
  entre hipótesis distintas se calculan en `sampling_1`: hoy el código solo compara variantes de una misma hipótesis.
  Los contrastes principales de este cambio son `H4O-r − U r` en las cuatro tasas. Comparan a igual tasa de CONTINUA,
  no a igual cantidad de filas: la receta con bajas tiene entre un 1 % y un 20 % más de filas y lleva peso, y se
  declara.
- **Regla para variantes nuevas** en `docs/metodo.md` y `docs/revision.md`: toda variante nueva dice qué celda de la
  grilla ocupa, usa las cuatro tasas y 8 réplicas, o declara el hueco en la tabla de cobertura antes de correr.

**Respuesta a la pregunta del tutor, en el informe**

- El informe conjunto suma una sección «Diálogo entre H1 y H4». Primero, apenas cierra la etapa de hipótesis, con lo que
  ya se sabe: contesta las dos lecturas de "mismos cortes" (las tasas de muestreo y el corte N* = 3.300), da las dos
  comparaciones que ya existen (`U0.5` y `H4O-0.5` tienen Δ contra el control casi iguales; `H4U-0.1` pierde y `H3-0.1`
  no), aclara que todavía no hay un contraste directo entre H1 y H4 y dice qué se va a correr. Después, al cerrar el
  informe, con la grilla completa y los tiempos.
- El informe conjunto deja de decir que no se toca la proporción de clases sin matiz (H4 la toca) y justifica el corte
  fijo N* = 3.300 en las variantes cuyo final entrena con otra proporción reponderada.
- El repo no guarda borradores de mensajes de Zulip y ninguna sesión escribe ni manda mensajes: los escribe y los manda
  Agustina, leyendo el informe.

**Correcciones de texto**

  - **H4U-0.1**: "los dos IC enteros debajo de −δ" (`h4/informe/informe.md:78`, `sampling_1/informe/informe.md:177`).
    El IC de `H4U-0.1` no queda entero debajo de −δ.
  - **`decisiones.md`**: se marca como de la ronda de las fases 1–4 o se actualiza.
  - **"Diez variantes"** (`informe.md:44`): el informe ya tiene 21. Se agrega además que H3 también reusa U0.05.
  - **Rangos de varianza entre réplicas** (`guion.md:18`, `informe.md:196`): el rango real va del 17 al 58 %.
  - **ΔAUC contra Δ de H3** (`informe.md:188`): la frase se generaliza de más.
  - **h4 en el README** de `sampling_1`.
  - **Tabla de rondas**: tiene una fila `C | pendiente` y no explica por qué no está `H4O-0.5`.
  - **A de la réplica 0 en `h3/informe`**: sin explicación.
  - **Figuras**: falta `bandas_H4` en la lista.
  - **"Misma máquina"** en `guion.md`.
  - **δ = 5,52 en H3**: el informe de H3 no avisa que se reemplaza.
  - **Hipótesis de H1** (`h1/informe/informe.md:11`): se redacta como predicción pre-registrada, para que no se lea
    como resultado.

Fuera de alcance: `Experimentos guion.md` en la raíz, a pedido de Agustina.

## Capabilities

### New Capabilities

- `medicion-tiempos`: cómo se mide y reporta el tiempo de una variante. Incluye la referencia única del control, el
  intervalo de A, la medición a hiperparámetros fijos, la calibración por máquina y la separación entre búsqueda,
  final y preparación.
- `grilla-comun`: qué tasas y cuántas réplicas tiene cada forma de muestrear, la tabla de cobertura, las comparaciones
  directas declaradas y la regla para variantes nuevas.

### Modified Capabilities

- `reporte-visual`: "Comparación limpia en dos bloques" cambia la fuente de T y A, que antes salían de la réplica 0 en
  las filas sin réplicas, agrega el intervalo de A y admite que el bloque A cambie en este cambio, en lugar de quedar
  idéntico.
- `corrida-reproducible`: la receta de bajas con peso vale para cualquier fracción f y puede usarse solo en la búsqueda
  (`H4P`); los estudios `U{r}@k` son de `h1`.
- `ledger-resultados`: las diferencias entre variantes de experimentos distintos se calculan en `sampling_1`, y un par
  declarado nunca se saltea en silencio.
- `dependencias-entre-experimentos`: con los `U{r}@k` en `h1`, `h3` declara todos los `U{r}` de `h1` y `h4` deja de
  declarar `h3` (agregado en 2b.3, después de unir `sitio-legible`, que pasó las dependencias al README).

Después de `sitio-legible` (2b.3), los documentos que nombra este cambio están en otra parte (`sampling_1/docs/rutas.md`):
los informes y las secciones de `docs/hipotesis.md` y `docs/diseno.md` de cada experimento, en su `README.md`; el
informe conjunto, `tabla_resultados.md`, `decisiones.md` y `comparacion_rondas.md`, en Resultados
(`experimentos/sampling_1/README.md`) y en el Anexo (`anexo.md`); `guion.md`, en `sampling_1/docs/`. Las tareas de los
grupos 3, 4 y 6 ya usan las rutas nuevas.

## Impact

- **Código**:
  - `comun/reporte.py`: A y su intervalo, tabla de cobertura, comparaciones directas, sección de tiempos, y la lectura
    de los estudios desde el ledger de su dueño.
  - `comun/variantes.py`, `comun/metodos.py` y `comun/correr.py`: variantes y pares nuevos, método de `H4P`, fracción
    variable en `fast-retrain-opt`, dueño de `U{r}@k`.
  - `comun/ledger.py` y `comun/consolidar.py`: pares entre experimentos en `sampling_1` y el chequeo de la fase 8.
  - `scripts/comparar_rondas.py`.
  - Un script que mueve los estudios `U{r}@k` de `h3` a `h1`, en el repo y en el bucket, con respaldo, verificación y
    modo en seco.
  - `experimentos/sampling_1/scripts/tiempos_hp_fijos.py` (medición, calibración y su consolidado) y las listas de la
    fase 8.
  - `scripts/vm.sh`, para correr la calibración antes y después de la lista; `scripts/lanzar_carriles.sh`, nuevo; y
    `requirements.txt` con versiones fijas.
  - Los cambios en `comun/` se anuncian en el commit.
- **Ledger**:
  - `h1/ledger`: estudios `U0.5@k`, los `U{r}@k` movidos desde `h3`, y los finales de las réplicas de `U*`.
  - `h2/ledger`: estudios y finales de las réplicas de `B*` y `GOSS`, y `B0.05`.
  - `h3/ledger`: finales de `H3-0.5`; pierde los estudios `U{r}@k`.
  - `h4/ledger`: estudios `F0.25`, `F0.1`, `F0.05` (y `@k`), finales de `H4O-*` y `H4P-*`.
  - `sampling_1/ledger`: `pares.csv`, la carpeta `tiempos/` (un archivo por medición y por lista) y sus consolidados
    `tiempos_hp_fijos.csv` y `calibracion.csv`.
  - El bucket: los 21 estudios `U{r}@k` cambian de carpeta, y queda un respaldo de los ledgers de `h1` y `h3` hasta
    archivar el cambio.
- **Documentos**:
  - Predicciones pre-registradas en `control`, `h1`, `h2`, `h3` y `h4` (`docs/hipotesis.md` y `docs/diseno.md`).
  - Los informes de `sampling_1` y de `h1`–`h4`, más `decisiones.md`, `guion.md`, el README de `sampling_1` y el de la
    raíz, `tabla_resultados.md`, `comparacion_rondas.md` y las figuras.
  - `docs/metodo.md` y `docs/revision.md`.
- **Cómputo**: 67 estudios y 2.560 finales nuevos, más la medición. Unas 36 h de VM `n2-highmem-8` a pedido, en 17
  listas (dos por réplica y una para la medición). La cuota es de 32 vCPU, o sea 4 VMs a la vez, y en el período de
  prueba no se puede pedir más: las listas se reparten en cuatro carriles que se encadenan solos, unas 12 h de reloj.
- **Otro cambio en curso**: `sitio-legible` se aplica en `main` al mismo tiempo. Este cambio corre predicciones, código
  de corridas y corridas en la rama `tiempos-confiables`; el reporte y los informes se hacen después de unir.
- **Specs de base**: `final-con-julio-agosto` quedó archivado el 13-nov. Los deltas de este cambio que modifican
  "Comparación limpia en dos bloques" y "Réplicas de la optimización" parten de la versión que dejó.
