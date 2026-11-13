## MODIFIED Requirements

### Requirement: Réplicas de la optimización
El comando SHALL aceptar una réplica de optimización k ≥ 0 (por defecto 0). En la réplica k, la semilla del sampler TPE y
la del sorteo de la muestra de optimización SHALL ser k. Las semillas finales SHALL ser las 20 de la ronda vigente en
todas las réplicas: las 10 oficiales y las 10 de `110017 + i·19937` (i = 0…9), en ese orden. La réplica 0 SHALL ser
exactamente la optimización que ya existe: mismo estudio, mismos hiperparámetros, mismas filas. El estudio de la réplica
k ≥ 1 SHALL llamarse `<estudio>@k` y SHALL tener el mismo dueño que el estudio de la réplica 0 según el registro de
variantes. La fila SHALL registrar k en la columna `replica_opt`.

Los estudios `U{r}@k` que ya existían en el ledger de `h3` SHALL pasar al de `h1`, en el repo y en el bucket, sin
cambiar sus ids, sus hiperparámetros ni sus tiempos.

#### Scenario: Réplica 0 igual a lo ya corrido
- **WHEN** se corre la optimización de `C` con `--replica 0` y `--filas 20000`, en la Mac, antes y después del cambio
- **THEN** los hiperparámetros elegidos y el `hash_muestra` son idénticos

#### Scenario: Réplica nueva de H3
- **WHEN** se corre la optimización de `H3-0.5` con `--replica 3`
- **THEN** el estudio se llama `U0.5@3`, la muestra se sortea con semilla 3 y los hiperparámetros se guardan en
  `experimentos/h1/ledger/hp/U0.5@3.json`, que es también el estudio de `U0.5` en la réplica 3

#### Scenario: Final de una réplica de H1
- **WHEN** se corre un final de `U0.25` con `--replica 3` y `--semilla todas`
- **THEN** lee los hiperparámetros de `U0.25@3`, sortea la muestra del 25 % con cada semilla final y escribe 20 filas
  con `replica_opt = 3` en el ledger de `h1`

#### Scenario: Final de una réplica
- **WHEN** se corre un final de `H3R-0.1` con `--replica 3` y `--semilla todas`
- **THEN** lee los hiperparámetros de `U0.1@3`, multiplica `min_data_in_leaf` por √(1/r) y escribe una fila por cada una
  de las 20 semillas con `replica_opt = 3`

#### Scenario: Estudios que cambian de dueño
- **WHEN** se mueven `U0.25@k`, `U0.1@k` y `U0.05@k` del ledger de `h3` al de `h1`
- **THEN** las tablas consolidadas y los reportes de `h3`, `h4` y `sampling_1` son los mismos que antes de mover, y
  `python -m comun.variantes --verificar` no encuentra ciclos

#### Scenario: Los estudios movidos no vuelven
- **WHEN** una VM sincroniza los ledgers con el bucket después de mover los estudios
- **THEN** ningún `U{r}@k` reaparece en el ledger de `h3`

#### Scenario: Réplica inválida
- **WHEN** k es negativo, o se pide una réplica k ≥ 1 de una variante que el registro no habilita para réplicas
- **THEN** el comando falla antes de cargar datos y nombra la variante y la réplica

## ADDED Requirements

### Requirement: Receta con bajas y peso en cualquier fracción
El corredor SHALL poder optimizar y entrenar el final con la misma receta para una fracción f de 0,5; 0,25; 0,1 o
0,05: todas las filas positivas y una fracción f de las negativas, con peso 1/f en las negativas. La variante SHALL
llamarse `H4O-{f}` y su estudio `F{f}` (`F{f}@k`), con dueño `h4`. `H4O-0.5` y `H4F-*` SHALL seguir siendo exactamente
las que ya existen.

#### Scenario: Optimización de H4O-0.1
- **WHEN** se corre la optimización de `H4O-0.1` con `--replica 2`
- **THEN** el estudio `F0.1@2` entrena cada trial con todas las bajas y el 10 % de las CONTINUA de 201903–201906,
  sorteadas con semilla 2 y con peso 10, y mide el AUC en 201908 completo y sin pesos

#### Scenario: Final de H4O-0.1
- **WHEN** se corre un final de `H4O-0.1` en la réplica 2
- **THEN** aplica la misma receta a los meses del final con la semilla final y lee los hiperparámetros de `F0.1@2`

#### Scenario: H4F no cambia de fracción
- **WHEN** se corre un final de `H4F-0.05`
- **THEN** entrena con todas las bajas y el 50 % de las CONTINUA con peso 2, igual que antes

#### Scenario: Lo ya corrido no cambia
- **WHEN** se corre la optimización de `H4O-0.5` con `--replica 0` y `--filas 20000`, antes y después del cambio
- **THEN** los hiperparámetros elegidos y el `hash_muestra` son idénticos

#### Scenario: Misma cantidad de negativas que la muestra al azar
- **WHEN** se arman la muestra de búsqueda de `H4O-0.1` y la de `U0.1`
- **THEN** la primera tiene todas las bajas y round(0,1 · CONTINUA) negativas, y el ledger registra la cantidad de filas
  de las dos

### Requirement: Búsqueda con bajas y peso, final completo
El corredor SHALL poder entrenar el final con todas las filas y sin pesos usando los hiperparámetros del estudio
`F{f}`. La variante SHALL llamarse `H4P-{f}`, con dueño `h4`, y SHALL compartir el estudio con `H4O-{f}` en cada
réplica. El tiempo de optimización de `H4P-{f}` SHALL ser el de ese estudio.

#### Scenario: Estudio compartido
- **WHEN** se corren los finales de `H4P-0.1` y de `H4O-0.1` en la réplica 2
- **THEN** los dos leen `F0.1@2`, y el estudio se optimiza una sola vez

#### Scenario: Final de H4P-0.1
- **WHEN** se corre un final de `H4P-0.1`
- **THEN** entrena con todas las filas de los meses del final, sin pesos, y registra esa cantidad de filas

#### Scenario: Optimizar H4P no usa el estudio al azar
- **WHEN** se pide la optimización de `H4P-0.1`
- **THEN** corre el estudio `F0.1` con la receta de bajas y peso, y no el estudio `U0.1`

#### Scenario: Misma muestra que la búsqueda sin peso
- **WHEN** se arman las muestras de búsqueda de `H4P-0.1` y de `H4U-0.1` en la misma réplica
- **THEN** tienen las mismas filas, y solo cambia el peso
