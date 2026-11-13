# Spec Delta

## MODIFIED Requirements

### Requirement: Contenido publicado
El sitio SHALL publicar como páginas solo los documentos de lectura: la portada, el `README.md` de cada experimento
(`sampling_1`, `control`, `h1` a `h4`), el anexo de resultados, la página de corridas, la de exploratorios,
`docs/metodo.md` y las páginas de sección. El sitio SHALL NOT publicar bitácoras, el archivo de Zulip, las specs,
`docs/revision.md`, el guion del video, los README de cada exploratorio, código, tests, scripts, ledgers, la plantilla,
la configuración de Claude ni los cambios de OpenSpec. Lo que queda fuera se enlaza en GitHub desde «Cómo trabajamos».

#### Scenario: Documento de un experimento
- **WHEN** se abre en el sitio la página de H4
- **THEN** se ve `experimentos/h4/README.md` con su idea, predicción, diseño, resultado, veredicto y limitaciones, y sus
  tablas y figuras

#### Scenario: Anexo publicado
- **WHEN** se abre en el sitio la ruta de `experimentos/sampling_1/anexo.md`
- **THEN** se ven las tablas completas del bloque A, la varianza, las diferencias entre variantes y la comparación entre
  rondas

#### Scenario: Bitácora fuera del sitio
- **WHEN** se pide en el sitio la ruta de `experimentos/h3/docs/bitacora.md` o de una spec de `openspec/specs/`
- **THEN** el sitio responde que la página no existe, y «Cómo trabajamos» tiene el enlace a ese archivo en GitHub

#### Scenario: Código excluido
- **WHEN** se pide en el sitio la ruta de `comun/reporte.py` o de un archivo de `openspec/changes/`
- **THEN** el sitio responde que la página no existe

### Requirement: Navegación por secciones
El sitio SHALL tener una barra lateral con estas secciones en este orden: Inicio, Resultados (con el Anexo como hija),
Hipótesis (H1 a H4), Cómo medimos (control y reglas, corridas, exploratorios) y Cómo trabajamos. Cada entrada de la
barra SHALL llevar el título de su página (por ejemplo «H4 · Muestras informadas por clase»). Cada resultado SHALL tener
una sola página donde buscarlo. El sitio SHALL tener búsqueda de texto completo sobre todas las páginas publicadas.

#### Scenario: Buscar un resultado
- **WHEN** alguien quiere el Δ de `H3-0.1`
- **THEN** lo encuentra en Resultados y en la página de H3, con su detalle completo en el Anexo, y no existe otra página
  de resultados entre las que elegir

#### Scenario: Título en la barra
- **WHEN** se abre la sección Hipótesis en la barra lateral
- **THEN** cada entrada dice «HN · <título de la hipótesis>», igual que el título de su página

#### Scenario: Llegar a una bitácora
- **WHEN** alguien busca la bitácora de h3
- **THEN** no la encuentra en la barra lateral, y «Cómo trabajamos» tiene el enlace a ese archivo en GitHub

#### Scenario: Buscar un término
- **WHEN** se busca «GOSS» en el sitio
- **THEN** la búsqueda devuelve la página de H2

### Requirement: Portada orientada a la conclusión
La página de inicio SHALL ser un resumen que se lee sin ir a otra página: la pregunta, la respuesta corta, tres
hallazgos con su figura y dos o tres líneas cada uno (qué vale la pena, por qué alcanza con achicar la optimización,
qué se hace con el tiempo ahorrado), las limitaciones principales en un recuadro, un enlace destacado a Resultados y una
tarjeta por hipótesis. La portada SHALL NOT nombrar personas ni copiar tablas.

#### Scenario: Primera visita del tutor
- **WHEN** alguien abre la dirección del sitio
- **THEN** ve la pregunta, la respuesta en pocas líneas, el mapa del tradeoff, el desglose del tiempo y la comparación a
  tiempo igual con su explicación, las limitaciones principales, un enlace destacado a Resultados y una tarjeta por
  hipótesis

#### Scenario: Figuras de la ronda vigente
- **WHEN** se regenera con una ronda nueva
- **THEN** las tres figuras de la portada y sus títulos cambian solos, sin editar el texto escrito a mano

### Requirement: Cada dato en un solo lugar
Cada número de una tabla SHALL aparecer en un solo lugar del sitio: la tabla resumen del bloque A en Resultados, las
tablas completas en el Anexo y las de cada hipótesis en su página. Una figura generada SHALL poder mostrarse en más de
una página, porque es el mismo archivo. Los números escritos a mano en la portada y en Resultados SHALL estar en las
tablas completas del Anexo. Las conclusiones SHALL escribirse una vez: las de cada hipótesis en su página, la
comparación y la respuesta en Resultados; la portada las resume y enlaza. Una página SHALL NOT abrir con un párrafo que
explique dónde están otras páginas.

#### Scenario: Tabla del bloque A
- **WHEN** se busca en el sitio la fila de `U0.25` del bloque A
- **THEN** su resumen aparece solo en Resultados y su fila completa solo en el Anexo

#### Scenario: Número de la portada
- **WHEN** la portada dice que en el control la optimización es el 94 % del tiempo, o cita un Δ o una aceleración
- **THEN** el verificador de números encuentra ese valor en las tablas completas del Anexo o en un bloque generado, y
  falla nombrándolo si no está

#### Scenario: Comienzo de una hipótesis
- **WHEN** se abre la página de H1
- **THEN** su primer párrafo dice qué se prueba, no dónde están las reglas ni los números

### Requirement: Páginas de sección como índice
Una entrada de la barra lateral que tiene hijas y no tiene contenido propio (Hipótesis, Cómo medimos) SHALL ser una
página corta con una tarjeta por hija (título y una línea). El contenido SHALL estar en las hijas. Resultados es la
excepción: tiene contenido propio y el Anexo como hija.

#### Scenario: Abrir Hipótesis
- **WHEN** se abre la sección Hipótesis
- **THEN** se ven cuatro tarjetas, H1 a H4, cada una con su idea en una línea y su veredicto

#### Scenario: Abrir Resultados
- **WHEN** se hace clic en Resultados en la barra lateral
- **THEN** se abre la página de Resultados, y el Anexo aparece debajo como hija

### Requirement: Páginas con estructura visual
Cada página publicada SHALL ayudar a leer con elementos visuales y no solo con texto:
- los veredictos y las limitaciones van en recuadros destacados;
- cada hipótesis tiene un diagrama del pipeline que marca dónde corta;
- Cómo medimos tiene la línea de tiempo de meses y la regla de veredicto como diagrama;
- Corridas tiene la línea de tiempo de las fases y un diagrama del recorrido de una corrida, de la VM al ledger y a las
  páginas;
- Cómo trabajamos tiene un diagrama de las etapas con sus compuertas de revisión y uno de los pasos para agregar una
  hipótesis;
- Exploratorios tiene un diagrama de qué motivó cada estudio en el experimento.

Un texto largo SHALL NOT ir dentro de una celda de tabla.

#### Scenario: Página de H3
- **WHEN** se abre la página de H3
- **THEN** antes de los números hay un diagrama que muestra que H3 achica solo la optimización, y el veredicto va en un
  recuadro destacado

#### Scenario: Exploratorios
- **WHEN** se abre la página de exploratorios
- **THEN** cada estudio es una sección con sus párrafos y sus cifras, no una fila de tabla con texto

#### Scenario: Fases de las corridas
- **WHEN** se abre Corridas
- **THEN** las fases se ven en una línea de tiempo y cada fase tiene su sección o su ítem con lo que corrió, sin texto
  largo dentro de una celda de tabla

#### Scenario: Cómo trabajamos
- **WHEN** se abre Cómo trabajamos
- **THEN** antes del detalle hay un diagrama de las etapas, con la revisión en sesión limpia en cada compuerta

### Requirement: Encabezado que entra
El encabezado SHALL decir «Sampling_1 · DMEyF 2026» y SHALL leerse completo en todos los anchos, del teléfono al
escritorio: en una línea en escritorio y, en pantallas angostas, en un encabezado más alto, con «Sampling_1» y «DMEyF
2026» en dos líneas, sin cortar palabras ni tapar los botones de menú, búsqueda y modo.

#### Scenario: Barra lateral en escritorio
- **WHEN** se abre el sitio a 1280 px
- **THEN** el nombre del sitio («Sampling_1 · DMEyF 2026») se ve en una sola línea

#### Scenario: Barras laterales parejas
- **WHEN** se abre una página con índice a 1440 px, en claro y en oscuro
- **THEN** las dos barras muestran su título, arrancan a la misma altura, van en un recuadro, y la página activa y la
  sección que se lee están marcadas

#### Scenario: Veredicto y limitaciones legibles
- **WHEN** se abre la página de H3
- **THEN** Veredicto tiene un solo recuadro (la conclusión) y Limitaciones ninguno: listas con el nombre en negrita
- **AND** el diagrama de la hipótesis entra en la columna a 1440 px con la letra a tamaño de texto

#### Scenario: Encabezado en el teléfono
- **WHEN** se abre el sitio a 390 px
- **THEN** el encabezado es más alto que el de escritorio y muestra «Sampling_1» y «DMEyF 2026» completos, en dos líneas,
  junto a los botones

## ADDED Requirements

### Requirement: Modo oscuro recordado
El sitio SHALL ofrecer un modo claro y uno oscuro, con un botón en el encabezado para cambiar de uno a otro. La primera
visita SHALL seguir la preferencia del sistema, y la elección SHALL recordarse en las visitas siguientes del mismo
navegador. En los dos modos, los colores de veredicto, las barras de IC, las tablas generadas y las figuras SHALL
leerse con contraste suficiente.

#### Scenario: Cambiar a oscuro
- **WHEN** alguien toca el botón de modo en el encabezado
- **THEN** el sitio pasa a oscuro, y al abrir otra página o volver otro día sigue en oscuro

#### Scenario: Tabla de veredictos en oscuro
- **WHEN** se abre Resultados en modo oscuro
- **THEN** las celdas y las etiquetas de *pierde*, *no pierde* e *indeterminado* se distinguen y su texto se lee

#### Scenario: Figura en oscuro
- **WHEN** se abre la portada en modo oscuro
- **THEN** los ejes, las etiquetas y los títulos de las figuras se leen sobre el fondo de la página
