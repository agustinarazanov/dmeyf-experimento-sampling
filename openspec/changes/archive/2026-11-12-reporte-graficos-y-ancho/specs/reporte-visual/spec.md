# Spec Delta

## MODIFIED Requirements

### Requirement: Comparación de todas las variantes en una vista
El reporte de `sampling_1` SHALL mostrar todas las variantes de todas las hipótesis contra el control, en una tabla
(ganancia media, diferencia apareada con su intervalo, tiempo, aceleración, veredicto) y en estos gráficos:
- **tradeoff por variante:** una fila por variante con Δ e IC a un lado y la aceleración A al otro, coloreada por
  veredicto, con las líneas de 0 y de −δ;
- **Δ contra fracción de muestra:** una línea por familia de variantes que tenga más de una fracción;
- **tiempo contra ganancia:** un panel por hipótesis, con el control marcado en cada uno;
- **tiempo igual:** cada variante con su intervalo;
- **réplicas:** la ganancia de cada réplica como un punto, junto a las del control, para las variantes con réplicas;
- **varianza:** sd entre réplicas y sd entre semillas de cada variante;
- **diferencias entre variantes:** cada par comparado, con su IC.

Además SHALL tener un enlace al reporte de cada hipótesis. El reporte de cada hipótesis SHALL mostrar las curvas de
ganancia (banda entre semillas) de sus variantes junto al control, y el gráfico de tradeoff de sus variantes.

Las figuras SHALL ser vectoriales y embebidas en la página, con dos condiciones:
- ninguna etiqueta de variante SHALL quedar encima de otra;
- un gráfico sin datos SHALL salir como pendiente, sin fallar.

#### Scenario: Leer el veredicto de una hipótesis
- **WHEN** se abre el reporte de una hipótesis
- **THEN** se ve su predicción, la regla, el resultado de cada variante y el veredicto (no pierde, pierde, indeterminado,
  pendiente), con la tabla y las figuras que lo sostienen

#### Scenario: Comparación a tiempo igual
- **WHEN** el control y al menos una variante tienen todas sus semillas
- **THEN** el reporte de `sampling_1` incluye la comparación a tiempo igual (ensamble de K semillas de la variante contra el
  control) con el K usado y el intervalo de cada variante dibujado

#### Scenario: Hipótesis nueva en `sampling_1`
- **WHEN** se registra un experimento nuevo con variantes (por ejemplo `h4`)
- **THEN** el reporte de `sampling_1` lo incluye en la tabla y en cada gráfico sin cambiar el generador

#### Scenario: Ver el tradeoff de un vistazo
- **WHEN** se abre el reporte de `sampling_1`
- **THEN** antes de las tablas aparece el gráfico de tradeoff, con cada variante ordenada por hipótesis y su
  aceleración al lado

#### Scenario: Figura nítida a cualquier ancho
- **WHEN** se abre el reporte en una pantalla ancha
- **THEN** las figuras se ven nítidas al ancho de la página
- **AND** con `--figuras` además quedan guardadas como imagen para el video

#### Scenario: Gráfico sin datos
- **WHEN** ninguna variante tiene réplicas
- **THEN** el gráfico de réplicas sale como pendiente y el resto del reporte se genera

### Requirement: Comparación limpia en dos bloques
El reporte y el `informe.md` de `sampling_1` SHALL presentar todos los resultados en dos bloques separados.

**Bloque A, mismo protocolo.** Una fila por variante del registro con:
- ganancia media;
- Δ apareado de la réplica 0 con su IC;
- Δ con réplicas, su IC y el número de réplicas, cuando existe;
- T y A, con T como mediana entre réplicas cuando hay varias;
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
- el intervalo va debajo del número, en letra más chica.

En el reporte HTML, el bloque B SHALL mostrarse como una tarjeta por estudio, no como una tabla. En
`tabla_resultados.md`, como una lista por estudio.

El bloque A de `tabla_resultados.md`, con sus tablas de varianza y de diferencias, SHALL conservar sus columnas y su
formato, porque lo copian los `informe.md` y lo leen los verificadores.

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
- **AND** ninguna celda tiene más de una cifra con su intervalo

#### Scenario: Tabla de resultados intacta
- **WHEN** se regenera `tabla_resultados.md` con este cambio
- **THEN** su bloque A, la tabla de varianza y la de diferencias son idénticos a los de antes del cambio
- **AND** `python -m scripts.verificar_readme` pasa sin cambios en el README

### Requirement: Página del sitio, compartible
El reporte SHALL ser una página del sitio de informes: un único archivo con encabezado YAML y cuerpo HTML, con las
figuras embebidas y sin dependencias fuera del sitio, que toma la barra lateral, la búsqueda y los estilos del sitio.
Los colores de veredicto (no pierde, pierde, indeterminado) SHALL verse igual que antes. El reporte SHALL NOT llevar
`<html>`, `<head>` ni estilos propios.

#### Scenario: Abrir desde el sitio
- **WHEN** alguien abre el reporte de `sampling_1` en el sitio publicado
- **THEN** ve el reporte completo con sus figuras, la barra lateral del sitio y las celdas de veredicto coloreadas

#### Scenario: Abrir desde un clon limpio
- **WHEN** alguien clona el repo y quiere ver `informe/reporte.html`
- **THEN** lo ve completo con sus figuras usando la vista previa local del sitio, sin instalar nada fuera de lo que pide
  el README

#### Scenario: Mismos números después del cambio de formato
- **WHEN** se regeneran los reportes con un cambio de presentación (formato de página, tablas resumidas, tarjetas)
- **THEN** cada número de las tablas del reporte anterior aparece igual en el nuevo, aunque cambie la tabla o la celda
  donde se muestra

## ADDED Requirements

### Requirement: Página a lo ancho
En pantallas de escritorio, el reporte y las demás páginas del sitio SHALL usar todo el ancho disponible al lado de la
barra lateral:
- el texto corrido SHALL tener un largo de línea de ~75 caracteres como máximo;
- las tablas y las figuras SHALL ocupar el ancho completo;
- en pantallas angostas, una tabla más ancha que la pantalla SHALL desplazarse por su cuenta, sin que se desplace la
  página entera.

#### Scenario: Escritorio ancho
- **WHEN** se abre el reporte de `sampling_1` en una ventana de 1920 px
- **THEN** las figuras y tablas se extienden hasta el borde derecho del contenido, y los párrafos no superan ~75
  caracteres por línea

#### Scenario: Teléfono
- **WHEN** se abre el mismo reporte a 390 px de ancho
- **THEN** la página no se desplaza horizontalmente y cada tabla ancha se desplaza dentro de su recuadro

### Requirement: Resultados resaltados
Las tablas numéricas del reporte SHALL marcar los resultados que importan con reglas fijas que salen de los datos, no
con marcas escritas a mano:
- el veredicto como etiqueta de color (no pierde, pierde, indeterminado, pendiente), con los mismos colores que hoy;
- cuando el IC de Δ no incluye 0, Δ en negrita, en verde si es positivo y en rojo si es negativo;
- una barra del IC de Δ dentro de su celda, en una escala común a toda la columna, con la marca de 0;
- en negrita, la mayor aceleración y el mayor Δ entre las variantes que no pierden.

Ningún color SHALL ser la única señal: el veredicto se lee en el texto de la etiqueta y el signo en el número.

#### Scenario: IC que excluye 0
- **WHEN** `U0.05` tiene Δ = −33,77 con IC [−39,84; −27,70]
- **THEN** su Δ se ve en negrita roja y la barra de su celda queda entera a la izquierda de la marca de 0

#### Scenario: Mejor de la columna
- **WHEN** entre las variantes que no pierden la mayor A es la de `H4F-0.05`
- **THEN** su A se ve en negrita y ninguna otra A de la columna lo está

#### Scenario: Regenerar resalta igual
- **WHEN** se regenera el reporte dos veces sin corridas nuevas
- **THEN** las mismas celdas quedan resaltadas y el archivo resultante es el mismo salvo la fecha de generación
