# Spec Delta

## MODIFIED Requirements

### Requirement: Tablas apareadas por semilla
El sistema SHALL derivar, para cada variante experimental, la diferencia contra el control apareada por semilla (media,
desvío, intervalo) en ganancia, AUC y tiempo, y el número de semillas en que la variante gana. Las filas de la variante SHALL
leerse del ledger de su experimento, y las del control del ledger de `control`. Cada experimento SHALL guardar en su
`ledger/apareado.csv` solo sus variantes.

#### Scenario: Variante con semillas faltantes
- **WHEN** una variante tiene menos semillas que el control
- **THEN** la tabla usa solo las semillas en común y lo indica

#### Scenario: Apareado de h2
- **WHEN** se consolida `h2`
- **THEN** `experimentos/h2/ledger/apareado.csv` tiene una fila por `B0.5`, `B0.25`, `B0.1` y `GOSS`, con N* y Δ
  calculados contra los finales de `C` en `experimentos/control/ledger/`

## ADDED Requirements

### Requirement: Separación sin pérdida del ledger existente
Al repartir el ledger de `sampling-velocidad` entre experimentos, cada fila de `resultados.csv`, `estudios.csv`,
`reemplazadas.csv` y cada archivo de `curvas/`, `corridas/`, `hp/` y `predicciones/` SHALL ir al experimento dueño de su
variante o estudio. Ninguna fila SHALL perderse ni duplicarse. Lo que no tiene variante (exploración, sesiones, tokens)
SHALL quedar en `sampling_1`.

#### Scenario: Conteo después de separar
- **WHEN** se termina de separar el ledger
- **THEN** la unión de los `resultados.csv` de `control`, `h1`, `h2` y `h3` tiene los mismos `id` que el
  `resultados.csv` original, sin repetidos

#### Scenario: Apareado igual al de antes
- **WHEN** se consolida cada experimento después de separar
- **THEN** la unión de sus `apareado.csv` coincide fila por fila con el `apareado.csv` anterior a la separación
