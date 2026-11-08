# Spec Delta

## Purpose

Define qué registra cada corrida del experimento, cómo se acumulan los resultados sin pisarse entre personas y qué se
deriva de ellos para el análisis.

## ADDED Requirements

### Requirement: Una fila por corrida con columnas obligatorias
Cada corrida SHALL registrarse con: id de corrida, fecha, método, tasa, semilla, etapa, hiperparámetros, filas de
entrenamiento, AUC en el mes evaluado, ganancia en 201910 y curva de ganancia (ruta), tiempos de preparación,
optimización y entrenamiento, memoria máxima, tipo de máquina, hilos, commit, `codigo_sucio`, persona que la corrió y
`valida`.

#### Scenario: Fila incompleta
- **WHEN** falta una columna obligatoria
- **THEN** el corredor no escribe la fila y falla con el nombre de la columna

### Requirement: Acumulación sin conflictos
Cada corrida SHALL escribirse en su propio archivo bajo el `ledger/corridas/` del experimento, y un comando de
consolidación SHALL producir el `ledger/resultados.csv` de ese experimento ordenado y sin duplicados por clave (variante, método, tasa, semilla, etapa). El commit no forma parte de la clave: una corrida repetida con código más nuevo reemplaza a la anterior, porque la misma semilla no puede contar dos veces en el apareado.

#### Scenario: Dos personas corren en paralelo
- **WHEN** dos integrantes registran corridas y hacen push
- **THEN** no hay conflicto de merge y la consolidación incluye ambas

#### Scenario: Corrida repetida
- **WHEN** se consolida una clave que ya existe
- **THEN** se conserva la más reciente y la anterior queda marcada como reemplazada

#### Scenario: Misma semilla corrida en dos commits
- **WHEN** una fase se relanza y vuelve a correr una variante y una semilla ya registradas con otro commit
- **THEN** en `resultados.csv` queda una sola fila por variante y semilla (la más reciente) y la otra va a `reemplazadas.csv`

### Requirement: Tablas apareadas por semilla
El sistema SHALL derivar del ledger, para cada variante experimental, la diferencia contra el control apareada por semilla
(media, desvío, intervalo) en ganancia, AUC y tiempo, y el número de semillas en que la variante gana.

#### Scenario: Variante con semillas faltantes
- **WHEN** una variante tiene menos semillas que el control
- **THEN** la tabla usa solo las semillas en común y lo indica

### Requirement: Curvas de ganancia por variante
El sistema SHALL guardar la curva de ganancia acumulada de 201910 de cada corrida final y SHALL poder graficar la banda
entre semillas de cada variante junto al control.

#### Scenario: Gráfico de una variante
- **WHEN** se pide la curva de un método y tasa
- **THEN** se obtiene la banda (mínimo, mediana, máximo entre semillas) y la del control en el mismo eje

### Requirement: Predicciones de cada corrida final
Cada corrida final SHALL guardar sus predicciones del mes de test en `ledger/predicciones/<id>.parquet` con las columnas
`numero_de_cliente`, `prob` y `es_baja2` en el orden del mes de test, y la fila del ledger SHALL referenciarlas en la
columna `predicciones_201910`. Los parquet no van a git: viajan por el bucket y la máquina que consolida los trae junto
con el resto del ledger. Las filas anteriores a esta columna siguen siendo legibles.

#### Scenario: Ensamble de K semillas
- **WHEN** el reporte arma la comparación a tiempo igual de una variante con K ≥ 2
- **THEN** promedia las probabilidades de las primeras K semillas de la variante fila a fila y calcula la ganancia al corte N* sobre `es_baja2`, sin volver a entrenar

#### Scenario: Corrida sin predicciones
- **WHEN** una fila no tiene `predicciones_201910` o el archivo no está
- **THEN** la comparación a tiempo igual de esa variante sale como pendiente y el resto del reporte no se ve afectado
