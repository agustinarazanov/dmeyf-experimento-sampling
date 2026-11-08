## ADDED Requirements

### Requirement: Comparación limpia en dos bloques
El reporte y el `informe.md` de `sampling_1` SHALL presentar todos los resultados en dos bloques separados.

**Bloque A, mismo protocolo.** Una fila por variante del registro con:
- ganancia media;
- Δ apareado de la réplica 0 con su IC;
- Δ con réplicas, su IC y el número de réplicas, cuando existe;
- T y A, con T como mediana entre réplicas cuando hay varias;
- tiempo igual con su intervalo;
- el veredicto, que es el de Δ con réplicas cuando existe y si no el de Δ apareado. La columna dice cuál se usó.

**Bloque B, exploratorios.** Una fila por estudio exploratorio declarado con:
- autor;
- pregunta;
- protocolo;
- las cifras que su manifiesto marca como principales, leídas de sus CSV;
- la advertencia de su manifiesto.

El bloque B SHALL decir que sus cifras no se comparan una a una con las del bloque A. Ninguna cifra de ninguno de los dos
bloques SHALL estar escrita a mano en el generador.

#### Scenario: Variante con réplicas
- **WHEN** `H3-0.1` tiene 8 réplicas
- **THEN** su fila en el bloque A muestra el Δ apareado de la réplica 0 y el Δ con réplicas, y el veredicto dice
  "con réplicas (8)"

#### Scenario: Exploratorio sin CSV
- **WHEN** el manifiesto de un exploratorio apunta a un CSV que no está en el repo
- **THEN** su fila del bloque B sale como pendiente, con el nombre del archivo faltante, y el resto del reporte se genera

#### Scenario: Gráfico de tiempo contra ganancia con réplicas
- **WHEN** una variante tiene varias réplicas
- **THEN** su punto en el gráfico de tiempo contra ganancia lleva una barra con el rango entre réplicas, y las
  variantes de una sola réplica se dibujan sin barra

### Requirement: Tiempo igual con intervalo
La comparación a tiempo igual SHALL tener intervalo:
- si la variante y el control tienen al menos dos réplicas, se calcula por réplica (ensamble de K semillas de la
  variante contra la media del control en la misma réplica) y se da la media con IC t entre réplicas;
- en todos los casos se suma un IC 95% por bootstrap de clientes de 201910 (1.000 remuestreos, semilla fija), con el
  corte N\* escalado a la cantidad de clientes del remuestreo.

#### Scenario: Variante de una sola réplica
- **WHEN** `U0.5` tiene solo la réplica 0
- **THEN** su tiempo igual sale con el IC del bootstrap de clientes y la nota "sin réplicas"

#### Scenario: Bootstrap reproducible
- **WHEN** se regenera el reporte dos veces sin corridas nuevas
- **THEN** los intervalos del bootstrap son idénticos
