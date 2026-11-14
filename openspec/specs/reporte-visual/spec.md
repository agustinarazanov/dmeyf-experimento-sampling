# reporte-visual Specification

## Purpose
Define el reporte visual del experimento: tablas y figuras regenerables desde el ledger, escritas en bloques dentro del
README de cada experimento, que comparan todos los resultados en un solo lugar, para el sitio y el video.

## Requirements

### Requirement: Reporte regenerable desde el ledger
Cada experimento SHALL tener un comando que escriba sus tablas y figuras dentro de sus páginas (su `README.md` y, en
`sampling_1`, también el anexo y la portada), entre marcadores de bloque generado. Los datos salen de su ledger, del
ledger de los experimentos de los que depende y de las curvas guardadas, sin números escritos a mano. El comando SHALL
poder correrse en cualquier momento con los resultados que haya y SHALL NOT tocar el texto fuera de los marcadores. Un
mismo comando SHALL poder regenerar todas las páginas del repo.

#### Scenario: Regenerar con resultados parciales
- **WHEN** se regenera y a una variante le faltan semillas o no tiene corridas
- **THEN** la variante aparece como pendiente con lo que tiene, y ningún bloque falla ni muestra un número inventado

#### Scenario: Regenerar dos veces
- **WHEN** se regenera dos veces sin corridas nuevas
- **THEN** cada página y cada figura quedan iguales, salvo la fecha de generación

#### Scenario: Texto escrito a mano intacto
- **WHEN** se regenera el README de H3 después de editar su sección Limitaciones
- **THEN** solo cambian los bloques entre marcadores, y la sección editada queda igual

#### Scenario: Marcador faltante
- **WHEN** una página no tiene el marcador de un bloque que el generador produce
- **THEN** el comando falla nombrando el archivo y el marcador, sin escribir nada

#### Scenario: Mismos números que antes de separar
- **WHEN** se regeneran las páginas después de mover bloques de Resultados al Anexo
- **THEN** cada Δ, IC, A, ΔAUC y veredicto coincide con el de las tablas completas anteriores al cambio

### Requirement: Comparación de todas las variantes en una vista
Resultados (`experimentos/sampling_1/README.md`) SHALL mostrar todas las variantes de todas las hipótesis contra el
control, en una tabla (ganancia media, diferencia apareada con su intervalo, tiempo, aceleración, veredicto) y en
gráficos, cada uno con la forma que corresponde a su pregunta. Resultados SHALL ordenarse por pregunta: qué conviene
achicar, cuánto se puede achicar, qué se hace con el tiempo ahorrado y qué tan estable es el resultado; después,
limitaciones comunes, conclusiones y qué sigue. Gráficos:
- **mapa del tradeoff:** aceleración A en escala logarítmica contra Δ con su IC, un punto por variante coloreado por
  veredicto, con la zona de «no pierde» (Δ > −δ) sombreada y la línea A = 1;
- **Δ contra tasa:** una línea por familia de variantes con más de una tasa, con su banda de IC y la línea de −δ;
- **desglose del tiempo:** barras apiladas por variante y para el control, con el tiempo de optimización, el de
  entrenamiento final y el de predicción;
- **semillas y réplicas:** la distribución por variante (caja, media y puntos), con el Δ de cada semilla como un
  punto y las réplicas de Optuna distinguidas, para ver la dispersión y no solo el intervalo;
- **grilla de veredictos:** familia contra tasa, cada celda con el color y el texto del veredicto, y vacía si esa
  combinación no se corrió;
- **tiempo igual:** cada variante con su intervalo;
- **ensamble según K y según el tiempo:** la ganancia del ensamble de las primeras K semillas de cada variante contra K y
  contra el tiempo acumulado T_opt + K·T_final, con la ganancia y el tiempo del control como referencia.

El Anexo (`experimentos/sampling_1/anexo.md`) SHALL mostrar, además de las tablas completas, estos gráficos:
- **diferencias entre variantes:** cada par comparado, con su IC;
- **comparación entre rondas:** para cada variante, el Δ de la ronda anterior y el de la vigente unidos por un
  segmento;
- **IC por ronda:** para cada variante, el IC de Δ de la ronda anterior y el de la vigente uno al lado del otro, con −δ
  marcado, para ver cuánto se angosta.

La portada SHALL mostrar el mapa del tradeoff, el desglose del tiempo y el ensamble según el tiempo, desde los mismos
archivos.

La página de cada hipótesis SHALL mostrar su mapa del tradeoff, las curvas de ganancia (ganancia de cada variante y del
control según la cantidad de envíos, con banda P10–P90 entre semillas y el corte N\*) y la curva de diferencia con el
control (ganancia de la variante menos la del control, con la banda entre semillas, la línea de 0 y N\*).

Las figuras SHALL ser vectoriales, guardadas como archivo junto a la página y enlazadas desde ella, con tres
condiciones:
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
- **THEN** Resultados y el Anexo lo incluyen en sus tablas y en cada gráfico sin cambiar el generador

#### Scenario: Ver el tradeoff de un vistazo
- **WHEN** se abre Resultados
- **THEN** antes de las tablas aparece el mapa del tradeoff en cuatro paneles, uno por hipótesis con su color: Δ e IC
  contra la aceleración, el control como referencia y las que valen la pena con su etiqueta en negrita
- **AND** a 1440 px entra en la columna sin etiquetas pisadas

#### Scenario: Resultados entra en la pantalla
- **WHEN** se recorre Resultados a 1440 × 900
- **THEN** ninguna figura ni tabla mide más de 800 px de alto
- **AND** cada hipótesis tiene el mismo color en todas las figuras
- **AND** el bloque A está en pestañas, con «Lo mejor de cada hipótesis» abierta (una fila por hipótesis), mientras
  el Anexo tiene la tabla entera

#### Scenario: Regenerar con las predicciones fuera del repo
- **WHEN** se corre `python -m comun.reporte --todos` tres veces seguidas con las predicciones en `DATOS_DIR`
- **THEN** las tres dan el mismo resultado y `git status` no cambia
- **AND** una fila del ledger con la ruta vieja de predicciones se resuelve igual si el archivo está solo en el repo

#### Scenario: Tabla de una hipótesis sin redundancias
- **WHEN** se lee el bloque `resultado` de `h3/README.md` y todas sus variantes tienen 20 semillas
- **THEN** no hay columnas «hipótesis» ni «semillas», una línea debajo dice que todas tienen 20 semillas, las semillas
  ganadas se ven como una barrita con su número, y los encabezados dicen «aceleración (×)», «ganancia contra el control»
  y «vale la pena (no pierde y ≥ 2×)»

#### Scenario: Clientes contactados
- **WHEN** se busca «envíos» en el sitio generado
- **THEN** no aparece; N\* se lee como «clientes contactados»

#### Scenario: Por qué H3 es rápida
- **WHEN** se mira el desglose del tiempo
- **THEN** se ve que en el control la optimización es la mayor parte del tiempo y que H3 la achica sin achicar el
  entrenamiento final

#### Scenario: Conclusiones cerca de la respuesta
- **WHEN** se lee Resultados de arriba abajo
- **THEN** después de las cuatro preguntas vienen las limitaciones comunes y las conclusiones, sin tablas de consulta
  en el medio

#### Scenario: Qué hacer con el tiempo ahorrado
- **WHEN** se mira el ensamble según el tiempo en Resultados
- **THEN** se ve, para cada variante que vale la pena, cuánta ganancia suma ensamblar semillas hasta gastar el tiempo
  del control, y dónde queda el control

#### Scenario: IC más angosto con más semillas
- **WHEN** se mira el IC por ronda en el Anexo
- **THEN** cada variante muestra los dos intervalos, y se ve que el de la ronda vigente (20 semillas) es más angosto
  salvo donde decide la suerte de Optuna

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
- **THEN** en la comparación entre rondas del Anexo aparece con un solo punto y sin segmento

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
Los resultados SHALL presentarse en dos bloques separados: el bloque A en Resultados (resumen) y en el Anexo (tablas
completas), y el bloque B en la página de exploratorios (`experimentos/sampling_1/exploratorios/README.md`). Resultados
SHALL enlazar el bloque B en una línea, sin copiar sus cifras.

**Bloque A, mismo protocolo.** Una fila por variante del registro con:
- ganancia media;
- Δ apareado de la réplica 0 con su IC;
- Δ con réplicas, su IC y el número de réplicas, cuando existe;
- ΔAUC en 201910 con su IC (con réplicas cuando existen, si no apareado de la réplica 0), al lado de Δ de ganancia;
- T y A, con T como mediana entre réplicas cuando hay varias;
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
- el intervalo va debajo del número, en letra más chica.

El bloque B SHALL NOT mostrar sus cifras como una tabla con texto en las celdas ni como nombres de columna sin etiqueta.

Las tablas completas del bloque A (con las de varianza y de diferencias) SHALL quedar en un bloque generado del Anexo,
con columnas y formato estables, porque las leen los verificadores.

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

#### Scenario: Tabla de resultados intacta
- **WHEN** se regenera con este cambio
- **THEN** el bloque A completo, la tabla de varianza y la de diferencias del Anexo tienen las mismas filas y valores
  que las tablas completas que estaban en Resultados
- **AND** los verificadores de números de la portada, del README raíz, de Resultados y de los README de hipótesis pasan
  leyendo ese bloque

#### Scenario: AUC junto a la ganancia
- **WHEN** se lee la fila de `H3-0.1` en el bloque A
- **THEN** muestra ΔAUC con su IC al lado de Δ de ganancia, y el veredicto sigue saliendo de la ganancia

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

### Requirement: Página a lo ancho
Cada página del sitio SHALL tener una sola columna de contenido, del mismo ancho para el texto, las figuras, los bloques
de código, los recuadros y los plegables, con un largo de línea de ~75 a 90 caracteres en el texto corrido:
- ningún elemento SHALL ser más ancho o más angosto que la columna, salvo una tabla más ancha que la columna, que SHALL
  desplazarse dentro de su recuadro;
- las líneas de los bloques de código publicados SHALL entrar en la columna sin desplazarse;
- en pantallas angostas, la página SHALL NOT desplazarse horizontalmente.

#### Scenario: Escritorio ancho
- **WHEN** se abre Resultados en una ventana de 1920 px
- **THEN** el texto, las figuras, los recuadros y los plegables tienen el mismo borde derecho, y los párrafos no superan
  ~90 caracteres por línea

#### Scenario: Código que entra
- **WHEN** se abre Corridas o Cómo trabajamos en una ventana de 1280 px
- **THEN** ninguna línea de un bloque de código queda cortada ni necesita desplazamiento

#### Scenario: Teléfono
- **WHEN** se abre la misma página a 390 px de ancho
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
