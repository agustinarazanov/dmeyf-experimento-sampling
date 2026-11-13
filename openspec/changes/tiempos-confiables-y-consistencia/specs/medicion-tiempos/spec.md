## ADDED Requirements

### Requirement: Aceleración con una sola referencia del control
La aceleración A de toda variante SHALL calcularse como T_C / T(variante), donde T_C es la mediana del T del control
entre sus réplicas de Optuna. Es la misma T_C para todas las filas, tengan réplicas o no. T(variante) SHALL ser la
mediana entre réplicas cuando la variante tiene varias y el T de la réplica 0 cuando no. La definición de T (suma de
los 40 trials más un armado del `Dataset` más la media del final entre semillas) no cambia.

#### Scenario: Variante sin réplicas
- **WHEN** una variante tiene solo la réplica 0 y el control tiene 8 réplicas
- **THEN** su A es la mediana de T_C entre las 8 réplicas dividida por el T de la variante, y no T_C de la réplica 0
  dividido por el T de la variante

#### Scenario: Misma referencia en todas las filas
- **WHEN** se regenera el bloque A
- **THEN** para cada fila A × T(variante) da la misma T_C, con diferencias solo de redondeo

### Requirement: Rango de la aceleración
Junto a cada A, el bloque A de `tabla_resultados.md` y del reporte HTML SHALL mostrar un rango que refleje la
variabilidad de T entre réplicas de Optuna:
- con réplicas en la variante, del mínimo al máximo de T_C(k) / T_v(k) entre réplicas apareadas por k;
- sin réplicas, del mínimo al máximo de T_C(k) / T_v(0) entre las réplicas k del control.

El texto del informe SHALL decir que el rango mide la variación que introduce Optuna y no la de la máquina. En una fila
sin réplicas, el reporte SHALL decir que el rango solo mueve el control y es un piso de la incertidumbre de A.

#### Scenario: A cerca del umbral
- **WHEN** el rango de A de una variante que *no pierde* contiene el 2
- **THEN** el informe la marca como "vale la pena" según la mediana y aclara que el rango cruza el umbral

#### Scenario: Fila sin réplicas
- **WHEN** una variante del bloque A tiene solo la réplica 0
- **THEN** su rango de A lleva la nota de que no incluye la variación de su propia búsqueda

### Requirement: Medición a hiperparámetros fijos
Un script SHALL medir el tiempo de entrenamiento y predicción con hiperparámetros fijos para cada juego de
hiperparámetros de las réplicas del control, con al menos 3 repeticiones por celda, sobre dos recetas de muestra del
train 201903–201906:
- al azar, para cada tasa r de una lista (por defecto 1; 0,5; 0,25; 0,1; 0,05);
- todas las bajas más una fracción f de las CONTINUA con peso 1/f, para cada f de una lista (por defecto 0,5; 0,25;
  0,1; 0,05).

Cada medición SHALL reproducir un trial de Optuna: muestra sorteada con la semilla de la repetición, `Dataset`,
`lgb.train` con los parámetros fijos del control y predicción de 201908. El orden de las mediciones SHALL ser aleatorio
con una semilla fija.

El script SHALL escribir un CSV en el ledger de `sampling_1`, una fila por medición, con:
- receta, tasa, réplica de hiperparámetros, repetición y semilla;
- filas de la muestra;
- tiempos de `Dataset`, de `lgb.train` y de predicción;
- tipo de máquina, nombre de la instancia, CPU, carga y commit.

El script SHALL correr solo en `n2-highmem-8`. La predicción y su regla SHALL quedar escritas en `docs/hipotesis.md`
antes de la corrida.

#### Scenario: Reporte de la medición
- **WHEN** existe el CSV de la medición
- **THEN** el informe conjunto muestra, para cada r, la aceleración a hiperparámetros fijos (mediana y rango entre
  juegos de hiperparámetros) al lado del A del bloque A de la variante al azar y de la variante con bajas de esa tasa

#### Scenario: Ruido dentro de la máquina
- **WHEN** se repite la misma celda (receta, tasa, juego de hiperparámetros)
- **THEN** el informe reporta el coeficiente de variación entre repeticiones como medida del ruido dentro de la máquina,
  separado del rango entre juegos de hiperparámetros

#### Scenario: Misma tasa, dos recetas
- **WHEN** se midieron la muestra al azar y la receta con bajas a la misma tasa
- **THEN** el informe muestra el cociente de sus tiempos, con la cantidad de filas de cada una

### Requirement: Calibración por máquina
Cada VM que corre una lista de corridas SHALL ejecutar el mismo entrenamiento de calibración antes de la primera corrida
y después de la última: hiperparámetros de la réplica 0 del control, train 201903–201906 completo y predicción de
201908, con al menos 2 repeticiones cada vez. Cada medición SHALL quedar en un CSV del ledger de `sampling_1` con la
lista, el nombre de la instancia, el momento (inicio o fin), la repetición, los tiempos, la CPU, la carga y el commit.

El informe conjunto SHALL reportar el coeficiente de variación entre VMs y, por VM, el cociente entre la calibración del
final y la del inicio. Ninguna corrida SHALL descartarse por su calibración después de conocer su ganancia.

#### Scenario: Ruido entre máquinas
- **WHEN** nueve VMs corrieron sus listas con calibración
- **THEN** el informe da el coeficiente de variación entre las medias de calibración de las nueve

#### Scenario: Máquina fuera de rango
- **WHEN** la calibración de una VM queda fuera del rango pre-registrado
- **THEN** el informe nombra la lista, marca sus filas en la sección de tiempos y no las saca del bloque A

#### Scenario: Fases anteriores
- **WHEN** se leen los tiempos de corridas anteriores a la calibración
- **THEN** el informe dice que para ellas la única medición entre VMs es la repetición del control (`C-rep`)

### Requirement: Búsqueda y final por separado
El reporte de `sampling_1` SHALL mostrar, para cada variante del bloque A, la mediana del tiempo de búsqueda, la mediana
del tiempo del final y la fracción de T que corresponde a la búsqueda. T y A no cambian.

#### Scenario: Dónde se va el tiempo
- **WHEN** se lee la sección de tiempos del reporte
- **THEN** para el control y para cada variante se ve cuántos segundos son búsqueda y cuántos son final
