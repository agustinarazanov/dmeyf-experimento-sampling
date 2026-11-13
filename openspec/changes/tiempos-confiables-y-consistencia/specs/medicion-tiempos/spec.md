## ADDED Requirements

### Requirement: Aceleración con una sola referencia del control
La aceleración A de toda variante SHALL calcularse como T_C / T(variante), donde T_C es la mediana del T del control
entre todas sus réplicas de Optuna, calculada una sola vez. Es la misma T_C para todas las filas, tengan réplicas o no.
T(variante) SHALL ser la mediana entre réplicas cuando la variante tiene varias y el T de la réplica 0 cuando no. La
definición de T no cambia.

#### Scenario: Variante sin réplicas
- **WHEN** una variante tiene solo la réplica 0 y el control tiene 8 réplicas
- **THEN** su A es la mediana de T_C entre las 8 réplicas dividida por el T de la variante, y no T_C de la réplica 0
  dividido por el T de la variante

#### Scenario: Misma referencia en todas las filas
- **WHEN** se regenera el bloque A, con alguna variante a la que le faltan réplicas
- **THEN** para cada fila A × T(variante) da la misma T_C, con diferencias solo de redondeo

### Requirement: Intervalo de la aceleración
Junto a cada A, el bloque A de `tabla_resultados.md` y del reporte HTML SHALL mostrar un intervalo del 95 % obtenido por
bootstrap del cociente de medianas, remuestreando por separado las réplicas del control y las de la variante, con
semilla fija. El intervalo no SHALL depender de cómo se emparejen las réplicas de una y otra.

#### Scenario: Qué mide
- **WHEN** se lee el intervalo de A en el informe
- **THEN** el texto dice que mide la variación entre réplicas, que junta la de Optuna y la de la VM en que corrió cada
  réplica

#### Scenario: Reordenar las réplicas
- **WHEN** se cambia el orden o el número k de las réplicas de una variante sin cambiar sus tiempos
- **THEN** el intervalo de A es el mismo

#### Scenario: A cerca del umbral
- **WHEN** el intervalo de A de una variante que *no pierde* contiene el 2
- **THEN** el informe la marca como "vale la pena" según la mediana y aclara que el intervalo cruza el umbral

#### Scenario: Fila sin réplicas
- **WHEN** una variante del bloque A tiene solo la réplica 0
- **THEN** solo se remuestrea el control, y su intervalo lleva la nota de que no incluye la variación de su propia
  búsqueda

### Requirement: Medición a hiperparámetros fijos
Un script SHALL medir el tiempo de un trial con hiperparámetros fijos para cada juego de hiperparámetros de las réplicas
del control, con al menos 3 repeticiones por celda y en orden aleatorio con semilla fija, sobre dos recetas de muestra
del train 201903–201906: al azar y con todas las bajas más una fracción de las CONTINUA con peso. El script SHALL correr
solo en `n2-highmem-8`, y la predicción y su regla SHALL quedar escritas en `docs/hipotesis.md` antes de la corrida.

#### Scenario: Celdas
- **WHEN** se corre la medición con sus valores por defecto
- **THEN** mide la muestra al azar en las tasas 1; 0,5; 0,25; 0,1 y 0,05 y la receta con bajas en 0,5; 0,25; 0,1 y 0,05,
  cada una con los 8 juegos de hiperparámetros del control

#### Scenario: Una medición
- **WHEN** se mide una celda
- **THEN** se sortea la muestra con la semilla de la repetición, se arma el `Dataset`, se entrena con los parámetros
  fijos del control y se predice 201908, y queda una fila con receta, tasa, juego de hiperparámetros, repetición,
  semilla, filas de la muestra, los tres tiempos, tipo de máquina, instancia, CPU, carga y commit

#### Scenario: Reporte de la medición
- **WHEN** existe la medición consolidada
- **THEN** el informe conjunto muestra, para cada tasa, la aceleración a hiperparámetros fijos (mediana y rango entre
  juegos de hiperparámetros) al lado del A del bloque A de la variante al azar y de la variante con bajas de esa tasa

#### Scenario: Ruido dentro de la máquina
- **WHEN** se repite la misma celda
- **THEN** el informe reporta el coeficiente de variación entre repeticiones como medida del ruido dentro de la máquina,
  separado del rango entre juegos de hiperparámetros

#### Scenario: Misma tasa, dos recetas
- **WHEN** se midieron la muestra al azar y la receta con bajas a la misma tasa
- **THEN** el informe muestra el cociente de sus tiempos al lado del cociente de sus filas

### Requirement: Calibración por máquina
Cada VM que corre una lista de corridas SHALL ejecutar la misma calibración antes de la primera corrida y después de la
última, y SHALL guardar cada medición con la lista, el nombre de la instancia y el momento. El informe conjunto SHALL
reportar el coeficiente de variación entre VMs y, por VM, el cociente entre el final y el inicio. Ninguna corrida SHALL
descartarse por su calibración después de conocer su ganancia.

#### Scenario: Qué se corre
- **WHEN** una VM calibra
- **THEN** repite al menos dos veces un trial con los hiperparámetros de la réplica 0 del control sobre el train
  201903–201906 completo, y corre un final de `C` de la réplica 0 que ya está en el ledger, sin escribir en el ledger de
  `control`

#### Scenario: Ruido entre máquinas
- **WHEN** las VMs de una fase corrieron sus listas con calibración
- **THEN** el informe da el coeficiente de variación entre las medias de calibración de todas, y dice que junta la VM y
  la hora si se lanzaron en tandas

#### Scenario: Ancla con las fases anteriores
- **WHEN** se consolida la calibración
- **THEN** cada VM se compara con la duración guardada del mismo trial en el estudio del control y con el tiempo del
  mismo final en el ledger de la ronda, sin corridas extra

#### Scenario: Máquina fuera de rango
- **WHEN** la calibración de una VM queda fuera del rango pre-registrado
- **THEN** el informe nombra la lista, marca sus filas en la sección de tiempos y no las saca del bloque A

### Requirement: Mediciones de tiempo que vuelven de la VM
Las mediciones a hiperparámetros fijos y las de calibración SHALL escribirse un archivo por celda o por lista y momento,
en una subcarpeta del ledger de `sampling_1` que se sincroniza con el bucket igual que las corridas. Un paso local SHALL
consolidarlas en un CSV de cada tipo.

#### Scenario: Varias VMs a la vez
- **WHEN** dos VMs terminan su calibración y suben sus archivos
- **THEN** ninguna pisa el archivo de la otra, y las dos calibraciones están en el consolidado

#### Scenario: La VM se borra
- **WHEN** una VM termina bien y se borra
- **THEN** sus mediciones están en el bucket y vuelven al repo con los ledgers

### Requirement: Búsqueda, final y preparación por separado
El reporte de `sampling_1` SHALL mostrar, para cada variante del bloque A, la mediana del tiempo de búsqueda, la mediana
del tiempo del final, la fracción de T que corresponde a la búsqueda y la mediana del tiempo de preparación de datos,
con la nota de que la preparación no entra en T. T y A no cambian.

#### Scenario: Dónde se va el tiempo
- **WHEN** se lee la sección de tiempos del reporte
- **THEN** para el control y para cada variante se ve cuántos segundos son búsqueda, cuántos son final y cuántos lleva
  la preparación
