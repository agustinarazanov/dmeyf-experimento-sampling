## ADDED Requirements

### Requirement: Muestras de búsqueda informadas por clase
El corredor SHALL poder armar la muestra de optimización con todas las filas positivas del train más una fracción f de
las negativas, elegidas de una de dos formas:
- **uniforme**: al azar entre todas las negativas;
- **difícil**: al azar dentro del pozo de negativos difíciles.

El pozo es el 35 % de los negativos con mayor probabilidad según una sonda: un LightGBM de 40 árboles, 31 hojas y
`learning_rate` 0,08, entrenado sobre el 10 % uniforme del train. En la réplica k, la sonda y los sorteos usan la
semilla k.

El tiempo de la sonda SHALL sumarse al tiempo de optimización de la variante.

#### Scenario: Muestra difícil
- **WHEN** se optimiza `H4H-0.1` en la réplica 2
- **THEN** la muestra tiene todas las bajas del train y el 10 % de las CONTINUA, todas dentro del pozo de la sonda
  entrenada con semilla 2, y la fila del ledger suma el tiempo de la sonda

#### Scenario: Misma cantidad de filas
- **WHEN** se optimizan `H4H-0.1` y `H4U-0.1` en la misma réplica
- **THEN** las dos muestras tienen la misma cantidad de positivos y de negativos, y solo cambia cómo se eligieron los
  negativos

### Requirement: Muestra de búsqueda por cliente
El corredor SHALL poder armar la muestra de optimización sorteando una fracción r de los clientes del train, con la
semilla de la réplica, y tomando todas las filas de esos clientes.

#### Scenario: Búsqueda de H3K-0.1
- **WHEN** se optimiza `H3K-0.1`
- **THEN** cada cliente del train está con todas sus filas o no está, y la cantidad de filas queda cerca del 10 % del
  train (se registra la cantidad exacta)

### Requirement: Final submuestreado con pesos
El corredor SHALL poder entrenar el modelo final con todas las filas positivas y una fracción f de las negativas,
sorteadas con la semilla final, y con peso 1/f en las negativas, para que la proporción ponderada de clases sea la del
train completo.

#### Scenario: Final de H4F-0.05
- **WHEN** se corre un final de `H4F-0.05` con la semilla 100003 en la réplica 0
- **THEN** usa los hiperparámetros del estudio `U0.05`, entrena con todas las bajas y el 50 % de las CONTINUA con peso
  2, y registra la cantidad de filas de entrenamiento

### Requirement: Reescalado de hiperparámetros al entrenar con todo
Una variante de H3 SHALL poder declarar un reescalado de `min_data_in_leaf` al pasar de la muestra de búsqueda (tasa r)
al train completo:
- `raiz`: multiplica por √(1/r);
- `lineal`: multiplica por 1/r.

El resultado se redondea y se recorta a [1; 8000]. Los demás hiperparámetros no cambian. Los hiperparámetros
efectivos SHALL quedar en la fila del ledger.

#### Scenario: Lineal contra raíz
- **WHEN** se corren finales de `H3L-0.1` y `H3R-0.1` en la misma réplica
- **THEN** los dos leen el mismo estudio, y su `min_data_in_leaf` efectivo es el del estudio × 10 y × 3,16
  respectivamente, recortado a [1; 8000]
