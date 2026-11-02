# corrida-reproducible Specification

## Purpose
Define cómo se ejecuta una configuración del experimento de forma determinística y comparable entre máquinas y personas,
y qué mide cada ejecución.

## Requirements

### Requirement: Un punto de entrada por configuración
Cada experimento SHALL ofrecer un único comando, dentro de su carpeta, que ejecute una configuración identificada por método (`uniforme`, `bagging`,
`goss`, `opt-muestra`), tasa, semilla y etapa (`optimizar` o `final`), usando el baseline fijo del 28-oct para todo lo
demás, y que termine escribiendo exactamente una fila en el ledger.

#### Scenario: Ejecución de una configuración
- **WHEN** se invoca el comando con método, tasa, semilla y etapa válidos
- **THEN** entrena sobre 201903–201906 con lags y deltas de orden 2, evalúa en 201908 (optimización) o en 201910
  (final) y escribe la fila con métricas y tiempos

#### Scenario: Configuración inválida
- **WHEN** la tasa está fuera de (0, 1] o el método no existe
- **THEN** el comando falla antes de cargar datos con un mensaje que nombra el parámetro inválido

### Requirement: Determinismo por semilla
Dos ejecuciones de la misma configuración con la misma semilla en la misma máquina SHALL producir la misma muestra, el
mismo modelo y las mismas métricas, con el tiempo de pared como única diferencia admitida.

#### Scenario: Repetir una corrida
- **WHEN** se ejecuta dos veces la misma configuración y semilla
- **THEN** las columnas de métricas del ledger coinciden y la muestra tiene el mismo hash

### Requirement: El baseline es el control
La configuración método `uniforme`, tasa 1, con hiperparámetros optimizados sobre el 100% de las filas SHALL ser
idéntica al baseline del 28-oct y SHALL correrse con las mismas semillas que los brazos experimentales.

#### Scenario: Comparación apareada posible
- **WHEN** se consulta el ledger para una semilla cualquiera de la grilla
- **THEN** existe la fila de control de esa semilla con la misma máquina y la misma versión del código

### Requirement: Medición de tiempo comparable
Cada corrida SHALL medir por separado el tiempo de pared de la preparación de datos, de la optimización y del
entrenamiento final, SHALL registrar el tipo de máquina y el número de hilos, y las corridas que entran en una comparación
de tiempos SHALL haberse hecho en el mismo tipo de máquina con el mismo número de hilos.

#### Scenario: Tiempo medido en máquinas distintas
- **WHEN** dos corridas comparadas tienen tipos de máquina distintos
- **THEN** el análisis las excluye de las curvas de tiempo y lo informa

### Requirement: Mismo código en todas partes
El comando SHALL registrar el commit del código con el que corrió, y una corrida con el árbol de trabajo sucio SHALL
quedar marcada como tal en el ledger.

#### Scenario: Corrida desde un árbol sucio
- **WHEN** hay cambios sin commitear al ejecutar
- **THEN** la fila lleva `codigo_sucio = true` y el análisis la trata como exploratoria

### Requirement: Datos fuera del repo
El dataset y los artefactos intermedios SHALL vivir fuera del repositorio versionado, en una ruta configurable, y el
comando SHALL construir el panel 2019 con lags y deltas una sola vez por máquina y reutilizarlo.

#### Scenario: Primera corrida en una máquina
- **WHEN** no existe el panel preparado en la ruta de datos
- **THEN** el comando lo construye desde el crudo, lo guarda y recién entonces entrena

#### Scenario: Corridas siguientes
- **WHEN** el panel preparado existe
- **THEN** el comando lo carga sin reconstruirlo y lo anota en el tiempo de preparación
