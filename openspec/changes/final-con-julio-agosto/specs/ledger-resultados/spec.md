## MODIFIED Requirements

### Requirement: Una fila por corrida con columnas obligatorias
Cada corrida SHALL registrarse con: id de corrida, fecha, método, tasa, semilla, etapa, hiperparámetros, filas de
entrenamiento, AUC en el mes evaluado, ganancia en 201910 y curva de ganancia (ruta), tiempos de preparación,
optimización y entrenamiento, memoria máxima, tipo de máquina, hilos, commit, `codigo_sucio`, persona que la corrió,
`valida` y, en los finales, la ventana del final (`meses_final`, por ejemplo `201903-201908`).

#### Scenario: Fila incompleta
- **WHEN** falta una columna obligatoria
- **THEN** el corredor no escribe la fila y falla con el nombre de la columna

#### Scenario: Final sin ventana
- **WHEN** un final llega al ledger sin `meses_final`
- **THEN** el corredor no escribe la fila y falla nombrando la columna

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
- **WHEN** una variante tiene réplicas con menos semillas que las de su ronda, o el control y la variante no tienen las
  mismas réplicas
- **THEN** cada réplica se promedia con las semillas que tiene, el IC se calcula con las réplicas presentes y
  `replicas.csv` registra cuántas réplicas y semillas entraron

#### Scenario: Descomposición de la varianza
- **WHEN** `C` tiene 8 réplicas de 20 semillas
- **THEN** `replicas.csv` tiene, para `C`, el desvío entre réplicas y el desvío medio entre semillas dentro de una
  réplica, y su suma de cuadrados reproduce la varianza total de las 160 ganancias

## ADDED Requirements

### Requirement: Rondas del final sin mezclar
Una ronda es el conjunto de finales con la misma ventana del final. El consolidado SHALL usar solo los finales de una
ronda, la vigente salvo que se pida otra, y SHALL aparear control y variante dentro de esa ronda. Ninguna fila de una
ronda anterior SHALL borrarse ni reescribirse, salvo para agregarle la columna `meses_final`. Las tablas consolidadas de
la ronda anterior SHALL guardarse aparte, en el `ledger/` de cada experimento, antes de consolidar la nueva.

#### Scenario: Migración de los finales viejos
- **WHEN** se agrega `meses_final` a los ledgers existentes
- **THEN** todos los finales previos quedan con `201903-201906`, las demás columnas no cambian byte a byte y un
  `--verificar` lo comprueba

#### Scenario: Consolidar la ronda anterior
- **WHEN** se consolida pidiendo la ventana `201903-201906`
- **THEN** `apareado.csv` y `replicas.csv` coinciden con las copias guardadas de esa ronda

#### Scenario: Ronda nueva incompleta
- **WHEN** la ronda vigente todavía no tiene los finales del control
- **THEN** el consolidado falla diciendo que falta `C` en esa ronda, sin usar los `C` de otra ronda
