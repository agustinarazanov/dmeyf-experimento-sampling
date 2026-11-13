## ADDED Requirements

### Requirement: Aceleración con una sola referencia del control
La aceleración A de toda variante SHALL calcularse como T_C / T(variante), donde T_C es la mediana del T del control
entre sus réplicas de Optuna. Es la misma T_C para todas las filas, tengan réplicas o no. T(variante) SHALL ser la
mediana entre réplicas cuando la variante tiene varias y el T de la réplica 0 cuando no. La definición de T (suma de
los 40 trials más un armado del `Dataset` más la media del final entre semillas) no cambia.

#### Scenario: Variante sin réplicas
- **WHEN** U0.05 tiene solo la réplica 0 y el control tiene 8 réplicas
- **THEN** su A es la mediana de T_C entre las 8 réplicas dividida por el T de U0.05, y no T_C de la réplica 0 dividido
  por el T de U0.05

#### Scenario: Misma referencia en todas las filas
- **WHEN** se regenera el bloque A
- **THEN** para cada fila A × T(variante) da la misma T_C, con diferencias solo de redondeo

### Requirement: Rango de la aceleración
Junto a cada A, el bloque A de `tabla_resultados.md` y del reporte HTML SHALL mostrar un rango que refleje la
variabilidad de T entre réplicas de Optuna:
- con réplicas en la variante, del mínimo al máximo de T_C(k) / T_v(k) entre réplicas apareadas por k;
- sin réplicas, del mínimo al máximo de T_C(k) / T_v(0) entre las réplicas k del control.

El texto del informe SHALL decir que el rango mide la variación que introduce Optuna y no la de la máquina.

#### Scenario: A cerca del umbral
- **WHEN** el rango de A de una variante que *no pierde* contiene el 2
- **THEN** el informe la marca como "vale la pena" según la mediana y aclara que el rango cruza el umbral

### Requirement: Medición a hiperparámetros fijos
Un script SHALL medir el tiempo de entrenamiento y predicción con hiperparámetros fijos para cada tasa r de una lista
(por defecto 1; 0,5; 0,25; 0,1; 0,05) y cada juego de hiperparámetros de las réplicas del control, con al menos 3
repeticiones por celda. Cada medición SHALL reproducir un trial de Optuna: muestra uniforme del train 201903–201906
sorteada con la semilla de la repetición, `Dataset`, `lgb.train` con los parámetros fijos del control y predicción de
201908.

El script SHALL escribir un CSV en el ledger de `sampling_1`, una fila por medición, con:
- r, réplica de hiperparámetros, repetición y semilla;
- tiempos de `Dataset`, de `lgb.train` y de predicción;
- máquina, CPU, carga y commit.

El script SHALL correr solo en `n2-highmem-8`. La predicción y su regla SHALL quedar escritas en `docs/hipotesis.md`
antes de la corrida.

#### Scenario: Reporte de la medición
- **WHEN** existe el CSV de la medición
- **THEN** el informe conjunto muestra, para cada r, la aceleración a hiperparámetros fijos (mediana y rango entre
  juegos de hiperparámetros) al lado del A del bloque A de la variante U correspondiente

#### Scenario: Ruido de la máquina
- **WHEN** se repite la misma celda (r, juego de hiperparámetros)
- **THEN** el informe reporta el coeficiente de variación entre repeticiones como medida del ruido de la máquina,
  separado del rango entre juegos de hiperparámetros
