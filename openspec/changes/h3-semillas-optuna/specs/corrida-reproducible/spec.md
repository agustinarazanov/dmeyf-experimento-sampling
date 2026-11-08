## ADDED Requirements

### Requirement: Réplicas de la optimización
El comando SHALL aceptar una réplica de optimización k ≥ 0 (por defecto 0). En la réplica k, la semilla del sampler TPE y
la del sorteo de la muestra de optimización SHALL ser k. Las semillas finales SHALL ser las 10 de siempre en todas
las réplicas. La réplica 0 SHALL ser exactamente la optimización que ya existe: mismo estudio, mismos hiperparámetros,
mismas filas. El estudio de la réplica k ≥ 1 SHALL llamarse `<estudio>@k` y SHALL tener como dueño el experimento que
la corre según el registro de variantes. La fila SHALL registrar k en la columna `replica_opt`.

#### Scenario: Réplica 0 igual a lo ya corrido
- **WHEN** se corre la optimización de `C` con `--replica 0` y `--filas 20000`, en la Mac, antes y después del cambio
- **THEN** los hiperparámetros elegidos y el `hash_muestra` son idénticos

#### Scenario: Réplica nueva de H3
- **WHEN** se corre la optimización de `H3-0.1` con `--replica 3`
- **THEN** el estudio se llama `U0.1@3`, la muestra se sortea con semilla 3, los hiperparámetros se guardan en
  `experimentos/h3/ledger/hp/U0.1@3.json` y `experimentos/h1/` no cambia

#### Scenario: Final de una réplica
- **WHEN** se corre un final de `H3R-0.1` con `--replica 3`
- **THEN** lee los hiperparámetros de `U0.1@3`, multiplica `min_data_in_leaf` por √(1/r) y escribe una fila por
  semilla con `replica_opt = 3`

#### Scenario: Réplica inválida
- **WHEN** k es negativo, o se pide una réplica k ≥ 1 de una variante que el registro no habilita para réplicas
- **THEN** el comando falla antes de cargar datos y nombra la variante y la réplica
