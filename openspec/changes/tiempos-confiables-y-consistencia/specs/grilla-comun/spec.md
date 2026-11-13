## ADDED Requirements

### Requirement: Las mismas tasas en cada forma de muestrear
Cada forma de muestrear del experimento SHALL tener una variante en cada una de las tasas 0,5; 0,25; 0,1 y 0,05. Las
formas son:
- al azar, en la búsqueda y en el final (`U{r}`, de `h1`);
- al azar, solo en la búsqueda (`H3-{r}`, de `h3`);
- todas las bajas y una fracción de las CONTINUA con peso, en la búsqueda y en el final (`H4O-{f}`, de `h4`);
- todas las bajas y una fracción de las CONTINUA con peso, solo en la búsqueda (`H4P-{f}`, de `h4`);
- dentro de LightGBM, por árbol (`B{f}`, de `h2`).

Las variantes que cruzan o extienden estas formas (`H4F-*`, `H4H-0.1`, `H4U-0.1`, `H3R-*`, `H3L-*`, `H3K-0.1`, `GOSS`)
no necesitan estar en las cuatro tasas.

#### Scenario: Grilla completa
- **WHEN** se lista el registro de variantes
- **THEN** hay 20 variantes de la grilla: cinco formas por cuatro tasas

#### Scenario: Misma tasa, dos formas
- **WHEN** el tutor pregunta si conservar las bajas cambia algo respecto de muestrear al azar en una tasa
- **THEN** existen `U{r}` y `H4O-{r}` para esa tasa, con la misma ronda, las mismas semillas y el mismo corte

### Requirement: Ocho réplicas en todo el bloque A
Toda variante del bloque A SHALL tener 8 réplicas de optimización (k = 0…7) con las 20 semillas finales de la ronda, y
su veredicto SHALL salir de Δ con réplicas. La única excepción es `C-rep`, que es la repetición del control.

#### Scenario: Variante que tenía una sola búsqueda
- **WHEN** se consolida `U0.5` después de este cambio
- **THEN** tiene fila en `replicas.csv` con 8 réplicas, y su veredicto en el bloque A dice que salió de las réplicas

#### Scenario: Réplicas incompletas
- **WHEN** a una variante del bloque A le faltan réplicas o semillas
- **THEN** el reporte la muestra con las que tiene y la tabla de cobertura dice cuántas son

### Requirement: Tabla de cobertura
El reporte de `sampling_1`, `tabla_resultados.md` y el informe conjunto SHALL mostrar una tabla de cobertura armada del
registro de variantes: una fila por forma de muestrear, una columna por tasa y, en cada celda, la variante y su cantidad
de réplicas. Una celda sin variante SHALL decir que no se corrió y el motivo, que sale de una lista declarada junto al
registro. Debajo de la tabla SHALL ir la lista de las variantes fuera de la grilla, con una línea que dice qué cruza o
extiende cada una. Ninguna celda SHALL estar escrita a mano en el generador.

#### Scenario: Celda sin correr
- **WHEN** el registro no tiene variante para una forma y una tasa
- **THEN** la celda dice "no se corrió" con su motivo, y si el motivo no está declarado el generador falla nombrando la
  celda

#### Scenario: Variante fuera de la grilla
- **WHEN** se lee la tabla de cobertura
- **THEN** `H4F-0.05` aparece debajo, como búsqueda al azar con final de bajas y la mitad de las CONTINUA

### Requirement: Comparaciones directas declaradas
Los pares de variantes que difieren en una sola decisión SHALL declararse en el registro antes de correr, cada uno con
la decisión que aísla y con si es un contraste principal. La tabla de diferencias entre variantes SHALL mostrar, para
cada par, la diferencia con su IC, el tipo de IC (apareado cuando las dos variantes comparten estudio, de Welch cuando
no) y la decisión que aísla, y SHALL marcar los principales. Los pares de este cambio son:
- conservar las bajas, en búsqueda y final: `H4O-{r}` − `U{r}` en las cuatro tasas, que son los principales;
- conservar las bajas, solo en la búsqueda: `H4P-{r}` − `H3-{r}` en las cuatro tasas;
- muestrear también el final, al azar: `U{r}` − `H3-{r}` en las cuatro tasas;
- muestrear también el final, con bajas: `H4O-{r}` − `H4P-{r}` en las cuatro tasas;
- el peso en la búsqueda: `H4P-0.1` − `H4U-0.1`.

#### Scenario: Contraste principal
- **WHEN** `H4O-0.1` y `U0.1` tienen 8 réplicas cada una
- **THEN** la tabla de diferencias muestra `H4O-0.1 − U0.1` con IC de Welch entre réplicas, marcado como principal y
  con "conservar las bajas, en búsqueda y final" como lo que aísla

#### Scenario: Par sin corridas
- **WHEN** una de las dos variantes de un par declarado todavía no tiene corridas
- **THEN** el par sale como pendiente y el resto del reporte se genera

### Requirement: Variante nueva en la grilla
`docs/metodo.md` SHALL pedir, para toda variante nueva, que declare qué forma de muestrear de la grilla ocupa, que se
corra en las cuatro tasas con 8 réplicas y que declare sus pares directos; o que declare, antes de correr, el hueco y
su motivo en la lista de la tabla de cobertura. `docs/revision.md` SHALL tener un ítem que lo verifique en la compuerta
de diseño.

#### Scenario: Variante en una sola tasa
- **WHEN** alguien registra una variante nueva en una sola tasa sin declarar los huecos
- **THEN** la revisión de diseño la marca con ✗ y la etapa no cierra
