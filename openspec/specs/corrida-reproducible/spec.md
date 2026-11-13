# corrida-reproducible Specification

## Purpose
Define cómo se ejecuta una configuración del experimento de forma determinística y comparable entre máquinas y personas,
y qué mide cada ejecución.

## Requirements

### Requirement: Un punto de entrada por configuración
El repo SHALL ofrecer un único comando, en `comun/`, que ejecute una configuración identificada por método (`uniforme`,
`bagging`, `goss`, `opt-muestra`), tasa, semilla y etapa (`optimizar` o `final`), usando el baseline fijo del 28-oct, con
la aclaración del 9-nov (Zulip 211210), para todo lo demás. La etapa `optimizar` SHALL entrenar con train 201903–201906 y
evaluar en validación (201908). La etapa `final` SHALL entrenar con 201903–201908 y evaluar en test (201910). El comando
SHALL terminar escribiendo exactamente una fila en el ledger del experimento dueño de la variante, según el registro de
variantes.

#### Scenario: Ejecución de una configuración
- **WHEN** se invoca el comando con método, tasa, semilla válidos y etapa `optimizar`
- **THEN** entrena con 201903–201906 con lags y deltas de orden 1 y 2, ordena los trials por AUC en 201908, no lee 201907
  ni 201910 y escribe la fila en `experimentos/<dueño>/ledger/`

#### Scenario: Ejecución de un final
- **WHEN** se invoca el comando con etapa `final`
- **THEN** entrena con 201903–201908 (aplicando el método y la tasa de la variante sobre esos seis meses), evalúa en
  201910 y escribe la fila con métricas, tiempos y la ventana del final

#### Scenario: Configuración inválida
- **WHEN** la tasa está fuera de (0, 1] o el método no existe
- **THEN** el comando falla antes de cargar datos con un mensaje que nombra el parámetro inválido

#### Scenario: Final que usa un estudio ajeno
- **WHEN** se corre un final de una variante cuyo estudio pertenece a otro experimento (`H3-0.1` sobre `U0.1`)
- **THEN** el comando lee los hiperparámetros del ledger del dueño del estudio y escribe la fila en el ledger del dueño
  de la variante

### Requirement: Determinismo por semilla
Dos ejecuciones de la misma configuración con la misma semilla en la misma máquina SHALL producir la misma muestra, el
mismo modelo y las mismas métricas, con el tiempo de pared como única diferencia admitida.

#### Scenario: Repetir una corrida
- **WHEN** se ejecuta dos veces la misma configuración y semilla
- **THEN** las columnas de métricas del ledger coinciden y la muestra tiene el mismo hash

### Requirement: El baseline es el control
La configuración método `uniforme`, tasa 1, con hiperparámetros optimizados sobre el 100% de las filas SHALL ser
idéntica al baseline del 28-oct, SHALL correrse con las mismas semillas que las variantes experimentales y SHALL
registrarse en `experimentos/control/ledger/`.

#### Scenario: Comparación apareada posible
- **WHEN** se consulta el ledger de `control` para una semilla cualquiera de la grilla
- **THEN** existe la fila de control de esa semilla con la misma máquina y la misma versión del código

### Requirement: Medición de tiempo comparable
Cada corrida SHALL medir por separado el tiempo de pared de la preparación de datos, de la optimización y del
entrenamiento final, SHALL registrar el tipo de máquina y el número de hilos, y las corridas que entran en una comparación
de tiempos SHALL haberse hecho en el mismo tipo de máquina con el mismo número de hilos.

#### Scenario: Tiempo medido en máquinas distintas
- **WHEN** dos corridas comparadas tienen tipos de máquina distintos
- **THEN** el análisis las excluye de las curvas de tiempo y lo informa

### Requirement: Mismo código en todas partes
El comando SHALL registrar el commit del código con el que corrió, y una corrida con el árbol de trabajo sucio SHALL
quedar marcada como tal en el ledger.

#### Scenario: Corrida desde un árbol sucio
- **WHEN** hay cambios sin commitear al ejecutar
- **THEN** la fila lleva `codigo_sucio = true` y el análisis la trata como exploratoria

### Requirement: Datos fuera del repo
El dataset y los artefactos intermedios SHALL vivir fuera del repositorio versionado, en una ruta configurable, y el
comando SHALL construir el panel 2019 con lags y deltas una sola vez por máquina y reutilizarlo.

#### Scenario: Primera corrida en una máquina
- **WHEN** no existe el panel preparado en la ruta de datos
- **THEN** el comando lo construye desde el crudo, lo guarda y recién entonces entrena

#### Scenario: Corridas siguientes
- **WHEN** el panel preparado existe
- **THEN** el comando lo carga sin reconstruirlo y lo anota en el tiempo de preparación

### Requirement: Réplicas de la optimización
El comando SHALL aceptar una réplica de optimización k ≥ 0 (por defecto 0). En la réplica k, la semilla del sampler TPE y
la del sorteo de la muestra de optimización SHALL ser k. Las semillas finales SHALL ser las 20 de la ronda vigente en
todas las réplicas: las 10 oficiales y las 10 de `110017 + i·19937` (i = 0…9), en ese orden. La réplica 0 SHALL ser
exactamente la optimización que ya existe: mismo estudio, mismos hiperparámetros, mismas filas. El estudio de la réplica
k ≥ 1 SHALL llamarse `<estudio>@k` y SHALL tener como dueño el experimento que la corre según el registro de variantes. La
fila SHALL registrar k en la columna `replica_opt`.

#### Scenario: Réplica 0 igual a lo ya corrido
- **WHEN** se corre la optimización de `C` con `--replica 0` y `--filas 20000`, en la Mac, antes y después del cambio
- **THEN** los hiperparámetros elegidos y el `hash_muestra` son idénticos

#### Scenario: Réplica nueva de H3
- **WHEN** se corre la optimización de `H3-0.1` con `--replica 3`
- **THEN** el estudio se llama `U0.1@3`, la muestra se sortea con semilla 3, los hiperparámetros se guardan en
  `experimentos/h3/ledger/hp/U0.1@3.json` y `experimentos/h1/` no cambia

#### Scenario: Final de una réplica
- **WHEN** se corre un final de `H3R-0.1` con `--replica 3` y `--semilla todas`
- **THEN** lee los hiperparámetros de `U0.1@3`, multiplica `min_data_in_leaf` por √(1/r) y escribe una fila por cada una
  de las 20 semillas con `replica_opt = 3`

#### Scenario: Réplica inválida
- **WHEN** k es negativo, o se pide una réplica k ≥ 1 de una variante que el registro no habilita para réplicas
- **THEN** el comando falla antes de cargar datos y nombra la variante y la réplica

### Requirement: Muestras de búsqueda informadas por clase
El corredor SHALL poder armar la muestra de optimización con todas las filas positivas del train más una fracción f de
las negativas, elegidas de una de dos formas:
- **uniforme**: al azar entre todas las negativas;
- **difícil**: al azar dentro del pozo de negativos difíciles.

El pozo es el 35 % de los negativos con mayor probabilidad según una sonda: un LightGBM de 40 árboles, 31 hojas y
`learning_rate` 0,08, entrenado sobre el 10 % uniforme del train. En la réplica k, la sonda y los sorteos usan la
semilla k.

El tiempo de la sonda SHALL sumarse al tiempo de optimización de la variante.

#### Scenario: Muestra difícil
- **WHEN** se optimiza `H4H-0.1` en la réplica 2
- **THEN** la muestra tiene todas las bajas del train y el 10 % de las CONTINUA, todas dentro del pozo de la sonda
  entrenada con semilla 2, y la fila del ledger suma el tiempo de la sonda

#### Scenario: Misma cantidad de filas
- **WHEN** se optimizan `H4H-0.1` y `H4U-0.1` en la misma réplica
- **THEN** las dos muestras tienen la misma cantidad de positivos y de negativos, y solo cambia cómo se eligieron los
  negativos

### Requirement: Muestra de búsqueda por cliente
El corredor SHALL poder armar la muestra de optimización sorteando una fracción r de los clientes del train, con la
semilla de la réplica, y tomando todas las filas de esos clientes.

#### Scenario: Búsqueda de H3K-0.1
- **WHEN** se optimiza `H3K-0.1`
- **THEN** cada cliente del train está con todas sus filas o no está, y la cantidad de filas queda cerca del 10 % del
  train (se registra la cantidad exacta)

### Requirement: Final submuestreado con pesos
El corredor SHALL poder entrenar el modelo final con todas las filas positivas y una fracción f de las negativas,
sorteadas con la semilla final, y con peso 1/f en las negativas, para que la proporción ponderada de clases sea la del
train completo.

#### Scenario: Final de H4F-0.05
- **WHEN** se corre un final de `H4F-0.05` con la semilla 100003 en la réplica 0
- **THEN** usa los hiperparámetros del estudio `U0.05`, entrena con todas las bajas y el 50 % de las CONTINUA con peso
  2, y registra la cantidad de filas de entrenamiento

### Requirement: Reescalado de hiperparámetros al entrenar con todo
Una variante de H3 SHALL poder declarar un reescalado de `min_data_in_leaf` al pasar de la muestra de búsqueda (tasa r)
al train completo:
- `raiz`: multiplica por √(1/r);
- `lineal`: multiplica por 1/r.

El resultado se redondea y se recorta a [1; 8000]. Los demás hiperparámetros no cambian. Los hiperparámetros
efectivos SHALL quedar en la fila del ledger.

#### Scenario: Lineal contra raíz
- **WHEN** se corren finales de `H3L-0.1` y `H3R-0.1` en la misma réplica
- **THEN** los dos leen el mismo estudio, y su `min_data_in_leaf` efectivo es el del estudio × 10 y × 3,16
  respectivamente, recortado a [1; 8000]

### Requirement: Optimización y final con meses separados
Los hiperparámetros de un final SHALL salir de un estudio que entrenó solo con 201903–201906 y eligió por AUC en 201908.
Un final con la ventana 201903–201908 SHALL reusar los estudios ya guardados sin volver a optimizar. El panel SHALL
incluir 201907 con su clase. 201909 SHALL usarse solo para calcular la clase de 201907 y 201908, y nunca para entrenar,
validar ni evaluar.

#### Scenario: Estudio existente
- **WHEN** se corre el final de `C` con la ventana nueva
- **THEN** lee `experimentos/control/ledger/hp/C.json` sin cambios y no escribe filas de optimización

#### Scenario: Panel sin 201907
- **WHEN** el panel guardado en la máquina no tiene filas de 201907
- **THEN** el comando lo reconstruye desde el crudo antes de entrenar el final

### Requirement: Búsqueda sobre el set del final
La variante `H4O-0.5` de `h4` SHALL optimizar y entrenar su final con la misma receta: todas las bajas y el 50 % de las
CONTINUA, con peso 2 en las CONTINUA. En `optimizar` la receta se aplica a 201903–201906 con la semilla de la réplica y
el AUC se mide en 201908 completo; en el final, a 201903–201908 con la semilla final. Su estudio SHALL ser `F0.5`
(`F0.5@k`), con dueño `h4`, y su tiempo de optimización SHALL ser el de ese estudio.

#### Scenario: Optimización de H4O-0.5
- **WHEN** se corre la optimización de `H4O-0.5` con `--replica 2`
- **THEN** el estudio `F0.5@2` entrena cada trial con todas las bajas y el 50 % de las CONTINUA sorteadas con semilla 2,
  con peso 2, y guarda los hiperparámetros en `experimentos/h4/ledger/hp/F0.5@2.json`

#### Scenario: Final de H4O-0.5
- **WHEN** se corre el final de `H4O-0.5` en la réplica 2 con la semilla 100003
- **THEN** lee `F0.5@2`, entrena con todas las bajas de 201903–201908 y el 50 % de sus CONTINUA sorteadas con 100003,
  con peso 2, y evalúa en 201910

### Requirement: Corte N* fijo entre rondas
N\* SHALL ser 3.300 envíos en toda ronda cuyo final entrene con 201908. Es el valor calculado en validación (201908) en la
ronda con final 201903–201906, con modelos que no vieron 201908. Ninguna curva de 201908 de un final que entrenó con
201908 SHALL usarse para fijar un corte ni para ordenar variantes. δ SHALL seguir la regla de `control`: 2 % de la
ganancia media del control en 201910 al corte N\*, calculada con el control de la misma ronda.

#### Scenario: Consolidar la ronda nueva
- **WHEN** se consolidan los finales con ventana 201903–201908
- **THEN** `apareado.csv` y `replicas.csv` muestran `n_estrella = 3300` y δ calculado con los `C` de esa ronda

#### Scenario: Curva de validación de un final nuevo
- **WHEN** un final entrenó con 201908
- **THEN** su fila no registra AUC ni curva de 201908 como validación
