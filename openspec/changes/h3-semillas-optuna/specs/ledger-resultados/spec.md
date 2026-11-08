## MODIFIED Requirements

### Requirement: Acumulación sin conflictos
Cada corrida SHALL escribirse en su propio archivo bajo el `ledger/corridas/` del experimento, y un comando de
consolidación SHALL producir el `ledger/resultados.csv` de ese experimento ordenado y sin duplicados por clave (variante,
método, tasa, réplica de optimización, semilla, etapa). El commit no forma parte de la clave: una corrida repetida con
código más nuevo reemplaza a la anterior, porque la misma semilla no puede contar dos veces en el apareado.

#### Scenario: Dos personas corren en paralelo
- **WHEN** dos integrantes registran corridas y hacen push
- **THEN** no hay conflicto de merge y la consolidación incluye ambas

#### Scenario: Corrida repetida
- **WHEN** se consolida una clave que ya existe
- **THEN** se conserva la más reciente y la anterior queda marcada como reemplazada

#### Scenario: Misma semilla corrida en dos commits
- **WHEN** una fase se relanza y vuelve a correr una variante, una réplica y una semilla ya registradas con otro commit
- **THEN** en `resultados.csv` queda una sola fila por variante, réplica y semilla (la más reciente) y la otra va a
  `reemplazadas.csv`

#### Scenario: Ledger con la columna vieja
- **WHEN** se consolida o se reporta un ledger cuya cabecera dice `brazo` (el bucket, el tag `corridas-v1`)
- **THEN** la columna se lee como `variante`, el resultado es el mismo que con la cabecera nueva y lo que se escribe
  usa siempre `variante`

#### Scenario: Fila anterior a las réplicas
- **WHEN** se consolida una fila sin columna `replica_opt`
- **THEN** se lee como réplica 0 y la consolidación de las corridas ya existentes da el mismo `resultados.csv` que antes,
  salvo la columna nueva

## ADDED Requirements

### Requirement: Diferencia con réplicas de optimización
Para cada variante con al menos dos réplicas, y con el control también en al menos dos, el sistema SHALL derivar:
- la ganancia media de cada réplica, promediando sus semillas finales;
- **Δ con réplicas**: la media de esas ganancias menos la del control, con IC 95% de Welch entre réplicas;
- el veredicto con las reglas comunes de `control`: δ y N\* fijos, sin recalcular;
- la descomposición de la varianza de G en una parte entre réplicas y otra entre semillas finales dentro de cada
  réplica.

La tabla apareada por semilla de la réplica 0 SHALL seguir calculándose igual que antes. Los resultados SHALL guardarse
en el `ledger/replicas.csv` de cada experimento, solo con sus variantes.

#### Scenario: Variante con una sola réplica
- **WHEN** una variante (por ejemplo `U0.25`) tiene solo la réplica 0
- **THEN** no tiene fila en `replicas.csv`, y la comparación muestra su Δ apareado con la nota "1 réplica"

#### Scenario: Réplicas incompletas
- **WHEN** una variante tiene réplicas con menos de 10 semillas, o el control y la variante no tienen las mismas
  réplicas
- **THEN** cada réplica se promedia con las semillas que tiene, el IC se calcula con las réplicas presentes y
  `replicas.csv` registra cuántas réplicas y semillas entraron

#### Scenario: Descomposición de la varianza
- **WHEN** `C` tiene 8 réplicas de 10 semillas
- **THEN** `replicas.csv` tiene, para `C`, el desvío entre réplicas y el desvío medio entre semillas dentro de una
  réplica, y su suma de cuadrados reproduce la varianza total de las 80 ganancias
