## MODIFIED Requirements

### Requirement: Comparación limpia en dos bloques
El reporte y el `informe.md` de `sampling_1` SHALL presentar todos los resultados en dos bloques separados.

**Bloque A, mismo protocolo.** Una fila por variante del registro con:
- ganancia media;
- Δ apareado de la réplica 0 con su IC;
- Δ con réplicas, su IC y el número de réplicas, cuando existe;
- ΔAUC en 201910 con su IC (con réplicas cuando existen, si no apareado de la réplica 0), al lado de Δ de ganancia;
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

#### Scenario: AUC junto a la ganancia
- **WHEN** se lee la fila de `H3-0.1` en el bloque A
- **THEN** muestra ΔAUC con su IC al lado de Δ de ganancia, y el veredicto sigue saliendo de la ganancia
