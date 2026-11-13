## ADDED Requirements

### Requirement: Diferencias entre variantes de experimentos distintos
Las diferencias entre dos variantes de experimentos distintos SHALL calcularse en el agregador `sampling_1`, desde los
resultados de todos los dueños, con la misma cuenta que las diferencias dentro de un experimento, y SHALL guardarse en
`experimentos/sampling_1/ledger/pares.csv`. Las diferencias entre variantes de un mismo experimento SHALL seguir en el
`replicas.csv` de ese experimento. Ningún experimento SHALL leer los finales de otro para calcular un par.

#### Scenario: Par entre h4 y h1
- **WHEN** se consolida `sampling_1` con `H4O-0.1` y `U0.1` corridas en 8 réplicas
- **THEN** `pares.csv` tiene `H4O-0.1 - U0.1` con su diferencia, su IC de Welch entre réplicas, su veredicto y las filas
  de entrenamiento de cada lado, y el `replicas.csv` de `h4` no lo tiene

#### Scenario: Par declarado sin datos
- **WHEN** a un par declarado en el registro le faltan las corridas de una de sus variantes
- **THEN** el par figura como pendiente, con el nombre de la variante que falta, y no se saltea en silencio

#### Scenario: Quién lo arma
- **WHEN** se corre `python -m comun.consolidar` sin `--experimento`, o con `--experimento sampling_1`
- **THEN** `pares.csv` queda escrito después de consolidar a los dueños

#### Scenario: Réplica incompleta
- **WHEN** una réplica no tiene las 20 semillas en alguno de los dos lados de un par
- **THEN** no entra en el par, que se calcula con las réplicas completas y dice cuántas son

#### Scenario: Misma cuenta que dentro de un experimento
- **WHEN** un par de un solo experimento se calcula también con el agregador
- **THEN** da la misma diferencia y el mismo IC que en el `replicas.csv` de su experimento
