## MODIFIED Requirements

### Requirement: Comparación limpia en dos bloques
El reporte y el `informe.md` de `sampling_1` SHALL presentar todos los resultados en dos bloques separados.

**Bloque A, mismo protocolo.** Una fila por variante del registro con:
- ganancia media;
- Δ apareado de la réplica 0 con su IC;
- Δ con réplicas, su IC y el número de réplicas, cuando existe;
- ΔAUC en 201910 con su IC (con réplicas cuando existen, si no apareado de la réplica 0), al lado de Δ de ganancia;
- T, con T como mediana entre réplicas cuando hay varias;
- A, calculada contra la mediana de T_C entre réplicas en todas las filas, con su rango (capacidad `medicion-tiempos`);
- tiempo igual con su intervalo;
- el veredicto, que es el de Δ con réplicas cuando existe y si no el de Δ apareado, junto con cuál de los dos se usó.

**Bloque B, exploratorios.** Una entrada por estudio exploratorio declarado con:
- autor;
- pregunta;
- protocolo;
- las cifras que su manifiesto marca como principales, leídas de sus CSV;
- la advertencia de su manifiesto.

El bloque B SHALL decir que sus cifras no se comparan una a una con las del bloque A. Ninguna cifra de ninguno de los dos
bloques SHALL estar escrita a mano en el generador.

En el reporte HTML, el bloque A SHALL mostrar primero un resumen con variante, hipótesis, Δ, A y veredicto. El resto de
las columnas SHALL ir en un detalle plegable. Reglas de las celdas:
- ninguna celda repite una nota que vale para toda la columna: el número de réplicas va en su propia columna, y lo que
  no aplica es `—` con una nota al pie;
- el intervalo va debajo del número, en letra más chica; el rango de A también.

En el reporte HTML, el bloque B SHALL mostrarse como una tarjeta por estudio, no como una tabla. En
`tabla_resultados.md`, como una lista por estudio.

El bloque A de `tabla_resultados.md`, con sus tablas de varianza y de diferencias, SHALL conservar sus columnas y su
formato, porque lo copian los `informe.md` y lo leen los verificadores. Las únicas columnas nuevas son el rango de A, al
final de la tabla del bloque A, y qué aísla cada par, al final de la tabla de diferencias (capacidad `grilla-comun`). La
nota del bloque A SHALL decir que A usa la mediana de T_C entre réplicas en todas las filas.

Este requisito parte de la versión que deja `final-con-julio-agosto` (ΔAUC junto a la ganancia) y de la que dejó
`reporte-graficos-y-ancho` (resumen y detalle plegable): las dos se conservan.

#### Scenario: Variante con réplicas
- **WHEN** `H3-0.1` tiene 8 réplicas
- **THEN** su fila en el bloque A muestra el Δ apareado de la réplica 0 y el Δ con réplicas, y el veredicto dice que
  salió de las réplicas (8)

#### Scenario: Exploratorio sin CSV
- **WHEN** el manifiesto de un exploratorio apunta a un CSV que no está en el repo
- **THEN** su entrada del bloque B sale como pendiente, con el nombre del archivo faltante, y el resto del reporte se
  genera

#### Scenario: Gráfico de tiempo contra ganancia con réplicas
- **WHEN** una variante tiene varias réplicas
- **THEN** su punto en el gráfico de tiempo contra ganancia lleva una barra con el rango entre réplicas, y las
  variantes de una sola réplica se dibujan sin barra

#### Scenario: Resumen corto
- **WHEN** se abre el bloque A en el reporte de `sampling_1`
- **THEN** la tabla visible tiene a lo sumo seis columnas
- **AND** ninguna celda tiene más de una cifra con su intervalo o rango

#### Scenario: AUC junto a la ganancia
- **WHEN** se lee la fila de `H3-0.1` en el bloque A
- **THEN** muestra ΔAUC con su IC al lado de Δ de ganancia, y el veredicto sigue saliendo de la ganancia

#### Scenario: Tabla de resultados intacta
- **WHEN** se regenera `tabla_resultados.md` con este cambio y sin corridas nuevas
- **THEN** en las filas que ya existían del bloque A cambian solo las columnas A y rango de A, y solo en las filas sin
  réplicas cambia el valor de A
- **AND** las filas que ya existían de las tablas de varianza y de diferencias conservan sus valores
- **AND** `python -m scripts.verificar_readme` pasa después de actualizar el README con los A nuevos
