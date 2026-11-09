## MODIFIED Requirements

### Requirement: Un punto de entrada por configuración
El repo SHALL ofrecer un único comando, en `comun/`, que ejecute una configuración identificada por método (`uniforme`,
`bagging`, `goss`, `opt-muestra`), tasa, semilla y etapa (`optimizar` o `final`), usando el baseline fijo del 28-oct
para todo lo demás. El comando SHALL terminar escribiendo exactamente una fila en el ledger del experimento dueño del
variante, según el registro de variantes.

#### Scenario: Ejecución de una configuración
- **WHEN** se invoca el comando con método, tasa, semilla y etapa válidos
- **THEN** entrena sobre 201903–201906 con lags y deltas de orden 2, evalúa en 201908 (optimización) o en 201910
  (final) y escribe la fila con métricas y tiempos en `experimentos/<dueño>/ledger/`

#### Scenario: Configuración inválida
- **WHEN** la tasa está fuera de (0, 1] o el método no existe
- **THEN** el comando falla antes de cargar datos con un mensaje que nombra el parámetro inválido

#### Scenario: Final que usa un estudio ajeno
- **WHEN** se corre un final de una variante cuyo estudio pertenece a otro experimento (`H3-0.1` sobre `U0.1`)
- **THEN** el comando lee los hiperparámetros del ledger del dueño del estudio y escribe la fila en el ledger del dueño
  de la variante

### Requirement: El baseline es el control
La configuración método `uniforme`, tasa 1, con hiperparámetros optimizados sobre el 100% de las filas SHALL ser
idéntica al baseline del 28-oct, SHALL correrse con las mismas semillas que las variantes experimentales y SHALL
registrarse en `experimentos/control/ledger/`.

#### Scenario: Comparación apareada posible
- **WHEN** se consulta el ledger de `control` para una semilla cualquiera de la grilla
- **THEN** existe la fila de control de esa semilla con la misma máquina y la misma versión del código
