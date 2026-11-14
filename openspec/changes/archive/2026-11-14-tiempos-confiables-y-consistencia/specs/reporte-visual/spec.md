## MODIFIED Requirements

### Requirement: Comparación limpia en dos bloques
Los resultados SHALL presentarse en dos bloques separados: el bloque A en Resultados (resumen) y en el Anexo (tablas
completas), y el bloque B en la página de exploratorios (`experimentos/sampling_1/exploratorios/README.md`). Resultados
SHALL enlazar el bloque B en una línea, sin copiar sus cifras.

**Bloque A, mismo protocolo.** Una fila por variante del registro con:
- ganancia media;
- Δ apareado de la réplica 0 con su IC;
- Δ con réplicas, su IC y el número de réplicas, cuando existe;
- ΔAUC en 201910 con su IC (con réplicas cuando existen, si no apareado de la réplica 0), al lado de Δ de ganancia;
- T, con T como mediana entre réplicas cuando hay varias;
- A, calculada contra la mediana de T_C entre réplicas en todas las filas, con su intervalo (capacidad `medicion-tiempos`);
- tiempo igual con su intervalo;
- el veredicto, que es el de Δ con réplicas cuando existe y si no el de Δ apareado, junto con cuál de los dos se usó.

**Bloque B, exploratorios.** Una sección por estudio exploratorio declarado con:
- pregunta, en un recuadro;
- protocolo;
- las figuras que declara su manifiesto, con su leyenda, que dice de qué reporte o de qué CSV salen;
- las cifras que su manifiesto marca como principales, leídas de sus CSV, con la etiqueta y la escala que declara (por
  ejemplo, M$), en una tabla solo numérica plegada;
- la advertencia de su manifiesto, en un recuadro.

La página de exploratorios SHALL abrir con un diagrama de qué motivó cada estudio en el experimento.

El bloque B SHALL decir que sus cifras no se comparan una a una con las del bloque A, y SHALL NOT mostrar autor. Ninguna
cifra de ninguno de los dos bloques SHALL estar escrita a mano en el generador.

El bloque A SHALL mostrar en Resultados un resumen con variante, hipótesis, Δ, A y veredicto. El resto de las columnas
SHALL ir en un detalle plegable. Reglas de las celdas:
- ninguna celda repite una nota que vale para toda la columna: el número de réplicas va en su propia columna, y lo que
  no aplica es `—` con una nota al pie;
- el intervalo va debajo del número, en letra más chica; el de A también.

El bloque B SHALL NOT mostrar sus cifras como una tabla con texto en las celdas ni como nombres de columna sin etiqueta.

Las tablas completas del bloque A (con las de varianza y de diferencias) SHALL quedar en bloques generados del Anexo
(`bloque-a-completo`, `varianza` y `diferencias` de `experimentos/sampling_1/anexo.md`), con columnas y formato
estables, porque las leen los verificadores. Las únicas columnas nuevas son el intervalo de A, al final de la tabla del
bloque A, y qué aísla cada par y las filas de cada lado, al final de la tabla de diferencias (capacidad `grilla-comun`).
La nota del bloque A SHALL decir que A usa la mediana de T_C entre réplicas en todas las filas.

#### Scenario: Variante con réplicas
- **WHEN** `H3-0.1` tiene 8 réplicas
- **THEN** su fila en el bloque A muestra el Δ apareado de la réplica 0 y el Δ con réplicas, y el veredicto dice que
  salió de las réplicas (8)

#### Scenario: Exploratorio sin CSV
- **WHEN** el manifiesto de un exploratorio apunta a un CSV que no está en el repo
- **THEN** su entrada del bloque B sale como pendiente, con el nombre del archivo faltante, y el resto se genera

#### Scenario: Figuras de un exploratorio
- **WHEN** se abre la sección de `validacion_50_semillas` en la página de exploratorios
- **THEN** se ven las figuras de su reporte original, cada una con una leyenda que dice que salen de ese reporte y de
  su protocolo, y sin autor

#### Scenario: Gráfico de tiempo contra ganancia con réplicas
- **WHEN** una variante tiene varias réplicas
- **THEN** su punto en el mapa del tradeoff lleva una barra con el rango entre réplicas, y las variantes de una sola
  réplica se dibujan sin barra

#### Scenario: Resumen corto
- **WHEN** se abre el bloque A en Resultados
- **THEN** la tabla visible tiene a lo sumo seis columnas
- **AND** ninguna celda tiene más de una cifra con su intervalo

#### Scenario: AUC junto a la ganancia
- **WHEN** se lee la fila de `H3-0.1` en el bloque A
- **THEN** muestra ΔAUC con su IC al lado de Δ de ganancia, y el veredicto sigue saliendo de la ganancia

#### Scenario: Tabla de resultados intacta
- **WHEN** se regeneran los bloques del Anexo con este cambio y sin corridas nuevas
- **THEN** en las filas que ya existían de `bloque-a-completo` cambian solo las columnas A e intervalo de A, y solo en
  las filas sin réplicas cambia el valor de A
- **AND** las filas que ya existían de las tablas de varianza y de diferencias conservan sus valores
- **AND** los verificadores de números de la portada, del README raíz, de Resultados y de los README de hipótesis pasan
  leyendo ese bloque, después de actualizar el texto con los A nuevos
