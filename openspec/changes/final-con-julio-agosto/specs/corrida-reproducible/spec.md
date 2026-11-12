## MODIFIED Requirements

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

## ADDED Requirements

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
