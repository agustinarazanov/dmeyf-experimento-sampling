# sitio-informes Specification

## Purpose

Define el sitio público que reúne los documentos del repo (conclusión, evidencia, método y proceso) para que quien lo
lea recorra el experimento desde una sola dirección, sin clonar el repo.

## Requirements

### Requirement: Publicación automática desde main
El sitio SHALL construirse y publicarse en GitHub Pages en cada push a `main`, a partir de lo commiteado, sin pasos
manuales después del push. Si el build falla, SHALL quedar publicada la versión anterior.

#### Scenario: Push con un informe editado
- **WHEN** se commitea un cambio en `experimentos/h3/README.md` y se pushea a `main`
- **THEN** al terminar el workflow la página de H3 en el sitio muestra el cambio

#### Scenario: Build roto
- **WHEN** el build del sitio falla
- **THEN** el workflow termina en error y el sitio sigue mostrando la última versión publicada

### Requirement: Contenido publicado
El sitio SHALL publicar como páginas solo los documentos de lectura: la portada, el `README.md` de cada experimento
(`sampling_1`, `control`, `h1` a `h4`), la página de corridas, la de exploratorios, `docs/metodo.md` y las páginas de
sección. El sitio SHALL NOT publicar bitácoras, el archivo de Zulip, las specs, `docs/revision.md`, el guion del video,
los README de cada exploratorio, código, tests, scripts, ledgers, la plantilla, la configuración de Claude ni los cambios
de OpenSpec. Lo que queda fuera se enlaza en GitHub desde «Cómo trabajamos».

#### Scenario: Documento de un experimento
- **WHEN** se abre en el sitio la página de H4
- **THEN** se ve `experimentos/h4/README.md` con su idea, predicción, diseño, resultado, veredicto y limitaciones, y sus
  tablas y figuras

#### Scenario: Bitácora fuera del sitio
- **WHEN** se pide en el sitio la ruta de `experimentos/h3/docs/bitacora.md` o de una spec de `openspec/specs/`
- **THEN** el sitio responde que la página no existe, y «Cómo trabajamos» tiene el enlace a ese archivo en GitHub

#### Scenario: Código excluido
- **WHEN** se pide en el sitio la ruta de `comun/reporte.py` o de un archivo de `openspec/changes/`
- **THEN** el sitio responde que la página no existe

### Requirement: Navegación por secciones
El sitio SHALL tener una barra lateral con estas secciones en este orden: Inicio, Resultados, Hipótesis (H1 a H4),
Cómo medimos (control y reglas, corridas, exploratorios) y Cómo trabajamos. Cada resultado SHALL tener una sola página
donde buscarlo. El sitio SHALL tener búsqueda de texto completo sobre todas las páginas publicadas.

#### Scenario: Buscar un resultado
- **WHEN** alguien quiere el Δ de `H3-0.1`
- **THEN** lo encuentra en Resultados y en la página de H3, y no existe otra página de resultados entre las que elegir

#### Scenario: Llegar a una bitácora
- **WHEN** alguien busca la bitácora de h3
- **THEN** no la encuentra en la barra lateral, y «Cómo trabajamos» tiene el enlace a ese archivo en GitHub

#### Scenario: Buscar un término
- **WHEN** se busca «GOSS» en el sitio
- **THEN** la búsqueda devuelve la página de H2

### Requirement: Portada orientada a la conclusión
La página de inicio SHALL presentar la pregunta del experimento y su respuesta corta, mostrar el gráfico del tradeoff y
llevar primero a Resultados y después a cada hipótesis. La portada SHALL NOT nombrar personas.

#### Scenario: Primera visita del tutor
- **WHEN** alguien abre la dirección del sitio
- **THEN** ve la pregunta, la respuesta en pocas líneas, el gráfico del tradeoff, un enlace destacado a Resultados y una
  tarjeta por hipótesis

### Requirement: Enlaces relativos conservados
Las páginas SHALL estar en la misma ruta que el archivo del repo, y el `README.md` de una carpeta SHALL ser la página de
esa carpeta. Así, un enlace relativo entre documentos que funciona en github.com funciona también en el sitio, sin
reescribir los documentos.

#### Scenario: Enlace entre Markdown
- **WHEN** en `experimentos/sampling_1/README.md` se sigue el enlace `../h3/README.md`
- **THEN** se abre la página de H3 en el sitio

#### Scenario: Del informe al reporte
- **WHEN** en la página de H1 se sigue el enlace a una figura generada en `figuras/`
- **THEN** se ve la figura dentro del sitio, igual que en github.com

#### Scenario: Carpeta como página
- **WHEN** se abre `experimentos/h1/` en github.com y la misma ruta en el sitio
- **THEN** los dos muestran el contenido de `experimentos/h1/README.md`

### Requirement: Enlaces internos verificados
El build SHALL fallar si alguna página publicada tiene un enlace interno o una imagen que no resuelve dentro del sitio.
Un enlace a un archivo del repo que no se publica SHALL apuntar a GitHub y no hacer fallar el build. Los enlaces
externos SHALL NOT hacer fallar el build.

#### Scenario: Enlace a un documento borrado
- **WHEN** una página enlaza a un `.md` que ya no existe
- **THEN** el build falla nombrando la página y el enlace roto, y no se publica

#### Scenario: Enlace a una página no publicada
- **WHEN** una página publicada enlaza en forma relativa a `docs/bitacora.md`
- **THEN** el build falla, porque ese enlace tiene que apuntar a GitHub

#### Scenario: Enlace externo caído
- **WHEN** un enlace a Zulip o a un sitio externo no responde
- **THEN** el build pasa igual

### Requirement: Vista previa local
El sitio SHALL poder construirse y verse localmente con un solo comando documentado, con el mismo contenido y la misma
verificación de enlaces que el build publicado, usando solo el entorno de Python del repo.

#### Scenario: Revisar antes de pushear
- **WHEN** un integrante corre el comando documentado en el README
- **THEN** el sitio queda servido en `localhost` y la verificación de enlaces informa lo mismo que en CI

### Requirement: Redacción impersonal
Las páginas publicadas y el README raíz SHALL NOT nombrar docentes ni integrantes, ni decir quién hizo cada tarea.
Llevan «el baseline» y no «el baseline de» alguien, «la pregunta del experimento» y no «la pregunta del» alguien, y no
tienen línea de autor. Las fuentes del curso se citan por el id del mensaje de Zulip.

#### Scenario: Buscar nombres
- **WHEN** se busca en las páginas publicadas «tutor», «Bolaños», «autor» o el nombre de un integrante
- **THEN** no hay resultados

#### Scenario: Exploratorio sin autor
- **WHEN** se lee la entrada de un exploratorio en la página de exploratorios
- **THEN** tiene pregunta, protocolo, cifras y advertencia, y no dice quién lo hizo

### Requirement: Cada dato en un solo lugar
Cada número SHALL aparecer en las páginas publicadas en un solo bloque generado por experimento, y las conclusiones
SHALL escribirse una vez: las de cada hipótesis en su página, la comparación y la respuesta en Resultados. La portada
SHALL resumir en pocas líneas y enlazar, sin copiar tablas. Una página SHALL NOT abrir con un párrafo que explique dónde
están otras páginas.

#### Scenario: Tabla del bloque A
- **WHEN** se busca en el sitio la fila de `U0.25` del bloque A
- **THEN** aparece en una sola página, Resultados

#### Scenario: Comienzo de una hipótesis
- **WHEN** se abre la página de H1
- **THEN** su primer párrafo dice qué se prueba, no dónde están las reglas ni los números

### Requirement: Índice de la página
Cada página SHALL mostrar, en pantallas de escritorio, un índice lateral con sus títulos, que marca la sección que se
está leyendo y lleva a cada una con un clic. En pantallas angostas el índice SHALL quedar accesible sin tapar el
contenido.

#### Scenario: Página larga
- **WHEN** se lee Resultados en una ventana de 1440 px y se baja hasta Limitaciones
- **THEN** el índice de la derecha muestra todos los títulos y marca Limitaciones

### Requirement: Páginas de sección como índice
Una entrada de la barra lateral que tiene hijas (Hipótesis, Cómo medimos) SHALL ser una página corta con una tarjeta
por hija (título y una línea). El contenido SHALL estar en las hijas.

#### Scenario: Abrir Hipótesis
- **WHEN** se abre la sección Hipótesis
- **THEN** se ven cuatro tarjetas, H1 a H4, cada una con su idea en una línea y su veredicto

### Requirement: Encabezado que entra
El nombre del sitio en el encabezado SHALL entrar en una línea en todos los anchos, del teléfono al escritorio.

#### Scenario: Barra lateral en escritorio
- **WHEN** se abre el sitio a 1280 px
- **THEN** el nombre del sitio («Sampling_1») se ve en una sola línea

### Requirement: Páginas con estructura visual
Cada página publicada SHALL ayudar a leer con elementos visuales y no solo con texto:
- los veredictos y las limitaciones van en recuadros destacados;
- cada hipótesis tiene un diagrama del pipeline que marca dónde corta;
- Cómo medimos tiene la línea de tiempo de meses y la regla de veredicto como diagrama.

Un texto largo SHALL NOT ir dentro de una celda de tabla.

#### Scenario: Página de H3
- **WHEN** se abre la página de H3
- **THEN** antes de los números hay un diagrama que muestra que H3 achica solo la optimización, y el veredicto va en un
  recuadro destacado

#### Scenario: Exploratorios
- **WHEN** se abre la página de exploratorios
- **THEN** cada estudio es una sección con sus párrafos y sus cifras, no una fila de tabla con texto
