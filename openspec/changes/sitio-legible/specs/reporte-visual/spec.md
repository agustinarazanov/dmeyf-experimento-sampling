# Spec Delta

## MODIFIED Requirements

### Requirement: Reporte regenerable desde el ledger
Cada experimento SHALL tener un comando que escriba sus tablas y figuras dentro de su `README.md`, entre marcadores de
bloque generado. Los datos salen de su ledger, del ledger de los experimentos de los que depende y de las curvas
guardadas, sin números escritos a mano. El comando SHALL poder correrse en cualquier momento con los resultados que haya
y SHALL NOT tocar el texto fuera de los marcadores. Un mismo comando SHALL poder regenerar todos los README del repo.

#### Scenario: Regenerar con resultados parciales
- **WHEN** se regenera y a una variante le faltan semillas o no tiene corridas
- **THEN** la variante aparece como pendiente con lo que tiene, y ningún bloque falla ni muestra un número inventado

#### Scenario: Regenerar dos veces
- **WHEN** se regenera dos veces sin corridas nuevas
- **THEN** cada README y cada figura quedan iguales, salvo la fecha de generación

#### Scenario: Texto escrito a mano intacto
- **WHEN** se regenera el README de H3 después de editar su sección Limitaciones
- **THEN** solo cambian los bloques entre marcadores, y la sección editada queda igual

#### Scenario: Marcador faltante
- **WHEN** un README no tiene el marcador de un bloque que el generador produce
- **THEN** el comando falla nombrando el archivo y el marcador, sin escribir nada

#### Scenario: Mismos números que antes de separar
- **WHEN** se regeneran los README después de fundir los informes y reportes
- **THEN** cada Δ, IC, A, ΔAUC y veredicto coincide con el de `tabla_resultados.md` y los `reporte.html` anteriores al
  cambio

### Requirement: Comparación de todas las variantes en una vista
Resultados (`experimentos/sampling_1/README.md`) SHALL mostrar todas las variantes de todas las hipótesis contra el
control, en una tabla (ganancia media, diferencia apareada con su intervalo, tiempo, aceleración, veredicto) y en estos
gráficos, cada uno con la forma que corresponde a su pregunta:
- **mapa del tradeoff:** aceleración A en escala logarítmica contra Δ con su IC, un punto por variante coloreado por
  veredicto, con la zona de «no pierde» (Δ > −δ) sombreada y la línea A = 1;
- **Δ contra tasa:** una línea por familia de variantes con más de una tasa, con su banda de IC y la línea de −δ;
- **desglose del tiempo:** barras apiladas por variante y para el control, con el tiempo de optimización, el de
  entrenamiento final y el de predicción;
- **semillas y réplicas:** el Δ de cada semilla como un punto por variante, con las réplicas de Optuna distinguidas,
  para ver la dispersión y no solo el intervalo;
- **grilla de veredictos:** familia contra tasa, cada celda con el color y el texto del veredicto, y vacía si esa
  combinación no se corrió;
- **tiempo igual:** cada variante con su intervalo;
- **diferencias entre variantes:** cada par comparado, con su IC;
- **comparación entre rondas:** para cada variante, el Δ de la ronda anterior y el de la vigente unidos por un
  segmento.

La página de cada hipótesis SHALL mostrar su mapa del tradeoff y la curva de diferencia con el control: ganancia de la
variante menos la del control según la cantidad de envíos, con la banda entre semillas, la línea de 0 y el corte N\*.

Las figuras SHALL ser vectoriales, guardadas como archivo junto al README y enlazadas desde él, con tres condiciones:
- ninguna etiqueta de variante SHALL quedar encima de otra;
- un gráfico sin datos SHALL salir como pendiente, sin fallar;
- cada figura SHALL tener un título que diga qué mirar, no solo qué se grafica.

#### Scenario: Leer el veredicto de una hipótesis
- **WHEN** se abre la página de una hipótesis
- **THEN** se ve su predicción, el resultado de cada variante y el veredicto (no pierde, pierde, indeterminado,
  pendiente), con la tabla y las figuras que lo sostienen

#### Scenario: Comparación a tiempo igual
- **WHEN** el control y al menos una variante tienen todas sus semillas
- **THEN** Resultados incluye la comparación a tiempo igual (ensamble de K semillas de la variante contra el control),
  con el K usado y el intervalo de cada variante dibujado

#### Scenario: Hipótesis nueva en `sampling_1`
- **WHEN** se registra un experimento nuevo con variantes (por ejemplo `h5`)
- **THEN** Resultados lo incluye en la tabla y en cada gráfico sin cambiar el generador

#### Scenario: Ver el tradeoff de un vistazo
- **WHEN** se abre Resultados
- **THEN** antes de las tablas aparece el mapa del tradeoff, y las variantes que no pierden y aceleran más quedan
  arriba a la derecha

#### Scenario: Por qué H3 es rápida
- **WHEN** se mira el desglose del tiempo
- **THEN** se ve que en el control la optimización es la mayor parte del tiempo y que H3 la achica sin achicar el
  entrenamiento final

#### Scenario: Dónde se pierde
- **WHEN** se abre la página de H1
- **THEN** la curva de diferencia de `U0.05` queda por debajo de 0 alrededor de N\*, con la banda entre semillas

#### Scenario: Figura nítida a cualquier ancho
- **WHEN** se abre una página con figuras en una pantalla ancha
- **THEN** las figuras se ven nítidas al ancho del contenido
- **AND** con `--figuras` además quedan guardadas como PNG para el video

#### Scenario: Gráfico sin datos
- **WHEN** ninguna variante tiene réplicas
- **THEN** el gráfico de semillas y réplicas muestra solo las semillas, y el resto de las figuras se genera

#### Scenario: Gráfico sin ronda anterior
- **WHEN** una variante solo existe en la ronda vigente
- **THEN** en la comparación entre rondas aparece con un solo punto y sin segmento

### Requirement: Página del sitio, compartible
Los bloques generados SHALL formar parte del `README.md` del experimento, que es una página del sitio: toman la barra
lateral, la búsqueda, el índice y los estilos del sitio, sin dependencias fuera del sitio. Los colores de veredicto (no
pierde, pierde, indeterminado) SHALL verse igual que antes. En github.com el mismo README SHALL leerse completo, con
el veredicto escrito en texto aunque se pierdan los colores. Las tablas generadas SHALL verse con un solo recuadro.

#### Scenario: Abrir desde el sitio
- **WHEN** alguien abre Resultados en el sitio publicado
- **THEN** ve las tablas y las figuras, la barra lateral del sitio y las etiquetas de veredicto coloreadas

#### Scenario: Abrir desde un clon limpio
- **WHEN** alguien clona el repo y quiere ver Resultados con su formato
- **THEN** lo ve completo con sus figuras usando la vista previa local del sitio, sin instalar nada fuera de lo que pide
  el README

#### Scenario: Abrir en GitHub
- **WHEN** alguien abre `experimentos/h2/README.md` en github.com
- **THEN** ve las mismas tablas y figuras, y cada veredicto se lee como texto

#### Scenario: Tabla con un solo recuadro
- **WHEN** se abre en el sitio una tabla generada del bloque A
- **THEN** tiene un único borde y, en pantallas angostas, una sola barra de desplazamiento

#### Scenario: Mismos números después del cambio de formato
- **WHEN** se regeneran los README con un cambio de presentación (formato de página, tablas resumidas, tarjetas)
- **THEN** cada número de las tablas anteriores aparece igual en las nuevas, aunque cambie la tabla o la celda donde se
  muestra

### Requirement: Informe escrito por hipótesis
Cada experimento de hipótesis SHALL tener en su `README.md`, escritos a mano, su idea, su predicción, su diseño, su
veredicto, sus limitaciones propias y su conclusión, junto a los bloques generados. El `README.md` de `sampling_1`
SHALL tener la comparación entre hipótesis, la respuesta a la pregunta del experimento y las limitaciones que comparten
todas. Ninguna conclusión SHALL escribirse en más de una página.

#### Scenario: Leer solo H3
- **WHEN** alguien abre `experimentos/h3/README.md`
- **THEN** encuentra el veredicto de H3 con su tabla, la dependencia de los estudios de `h1` declarada como limitación
  y un enlace a Resultados

### Requirement: Comparación limpia en dos bloques
Los resultados SHALL presentarse en dos bloques separados, cada uno en una sola página: el bloque A en Resultados y el
bloque B en la página de exploratorios (`experimentos/sampling_1/exploratorios/README.md`). Resultados SHALL enlazar el
bloque B en una línea, sin copiar sus cifras.

**Bloque A, mismo protocolo.** Una fila por variante del registro con:
- ganancia media;
- Δ apareado de la réplica 0 con su IC;
- Δ con réplicas, su IC y el número de réplicas, cuando existe;
- ΔAUC en 201910 con su IC (con réplicas cuando existen, si no apareado de la réplica 0), al lado de Δ de ganancia;
- T y A, con T como mediana entre réplicas cuando hay varias;
- tiempo igual con su intervalo;
- el veredicto, que es el de Δ con réplicas cuando existe y si no el de Δ apareado, junto con cuál de los dos se usó.

**Bloque B, exploratorios.** Una entrada por estudio exploratorio declarado con:
- pregunta;
- protocolo;
- las cifras que su manifiesto marca como principales, leídas de sus CSV;
- la advertencia de su manifiesto.

El bloque B SHALL decir que sus cifras no se comparan una a una con las del bloque A, y SHALL NOT mostrar autor. Ninguna
cifra de ninguno de los dos bloques SHALL estar escrita a mano en el generador.

El bloque A SHALL mostrar primero un resumen con variante, hipótesis, Δ, A y veredicto. El resto de las columnas SHALL
ir en un detalle plegable. Reglas de las celdas:
- ninguna celda repite una nota que vale para toda la columna: el número de réplicas va en su propia columna, y lo que
  no aplica es `—` con una nota al pie;
- el intervalo va debajo del número, en letra más chica.

El bloque B SHALL mostrarse como una sección por estudio, con sus cifras en una lista o una tabla solo numérica, no como
una tabla con texto en las celdas.

Las tablas completas del bloque A (con las de varianza y de diferencias) SHALL quedar en un bloque generado de Resultados,
con columnas y formato estables, porque las leen los verificadores.

#### Scenario: Variante con réplicas
- **WHEN** `H3-0.1` tiene 8 réplicas
- **THEN** su fila en el bloque A muestra el Δ apareado de la réplica 0 y el Δ con réplicas, y el veredicto dice que
  salió de las réplicas (8)

#### Scenario: Exploratorio sin CSV
- **WHEN** el manifiesto de un exploratorio apunta a un CSV que no está en el repo
- **THEN** su entrada del bloque B sale como pendiente, con el nombre del archivo faltante, y el resto se genera

#### Scenario: Gráfico de tiempo contra ganancia con réplicas
- **WHEN** una variante tiene varias réplicas
- **THEN** su punto en el mapa del tradeoff lleva una barra con el rango entre réplicas, y las variantes de una sola
  réplica se dibujan sin barra

#### Scenario: Resumen corto
- **WHEN** se abre el bloque A en Resultados
- **THEN** la tabla visible tiene a lo sumo seis columnas
- **AND** ninguna celda tiene más de una cifra con su intervalo

#### Scenario: Tabla de resultados intacta
- **WHEN** se regenera Resultados con este cambio
- **THEN** el bloque A completo, la tabla de varianza y la de diferencias tienen las mismas filas y valores que el
  `tabla_resultados.md` anterior
- **AND** los verificadores de números del README raíz y de los README de hipótesis pasan leyendo ese bloque

#### Scenario: AUC junto a la ganancia
- **WHEN** se lee la fila de `H3-0.1` en el bloque A
- **THEN** muestra ΔAUC con su IC al lado de Δ de ganancia, y el veredicto sigue saliendo de la ganancia

### Requirement: Página a lo ancho
En pantallas de escritorio, cada página del sitio SHALL usar todo el ancho disponible entre la barra lateral y el
índice de la página:
- el texto corrido SHALL tener un largo de línea de ~75 caracteres como máximo;
- las tablas y las figuras SHALL ocupar el ancho completo del contenido;
- en pantallas angostas, una tabla más ancha que la pantalla SHALL desplazarse por su cuenta, sin que se desplace la
  página entera.

#### Scenario: Escritorio ancho
- **WHEN** se abre Resultados en una ventana de 1920 px
- **THEN** las figuras y tablas se extienden hasta el borde del contenido, junto al índice, y los párrafos no superan
  ~75 caracteres por línea

#### Scenario: Teléfono
- **WHEN** se abre la misma página a 390 px de ancho
- **THEN** la página no se desplaza horizontalmente y cada tabla ancha se desplaza dentro de su recuadro

## REMOVED Requirements

### Requirement: Introducción tomada de los documentos
**Reason**: La pregunta, las hipótesis, el control y la regla de decisión ya están escritos en el mismo `README.md` que
contiene los bloques generados. Copiarlos en el reporte repetía el texto.
**Migration**: La introducción es la parte escrita a mano del README (Idea, Predicción, Diseño), arriba de los bloques
generados. El generador deja de leer `docs/hipotesis.md` y `docs/diseno.md`.
