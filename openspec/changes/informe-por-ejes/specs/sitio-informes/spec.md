# Spec Delta

## MODIFIED Requirements

### Requirement: Portada orientada a la conclusión
La página de inicio SHALL ser un resumen que se lee sin ir a otra página: la pregunta, la hipótesis general, la
respuesta corta, el mapa del tradeoff con dos o tres líneas que digan cómo leerlo, las limitaciones principales en un
recuadro, un enlace destacado a Resultados y una tarjeta por hipótesis. La respuesta corta SHALL ser el mismo texto que
el recuadro «Respuesta» de Resultados, palabra por palabra. La portada SHALL NOT nombrar personas, copiar tablas ni
mostrar otra figura que el mapa del tradeoff: el desglose del tiempo y el ensamble quedan en Resultados.

#### Scenario: Primera visita del tutor
- **WHEN** alguien abre la dirección del sitio
- **THEN** ve la pregunta, la hipótesis general, la respuesta en pocas líneas, el mapa del tradeoff, las limitaciones
  principales, un enlace destacado a Resultados y una tarjeta por hipótesis, y nada más

#### Scenario: Misma respuesta en dos páginas
- **WHEN** se compara el recuadro «Respuesta» de la portada con el de Resultados
- **THEN** el texto es el mismo, y un verificador falla nombrando la diferencia si no lo es

#### Scenario: Figuras de la ronda vigente
- **WHEN** se regenera con una ronda nueva
- **THEN** la figura de la portada y su título cambian solos, sin editar el texto escrito a mano

### Requirement: Páginas con estructura visual
Cada página publicada SHALL ayudar a leer con elementos visuales y no solo con texto:
- los veredictos y las limitaciones van en recuadros destacados;
- cada hipótesis tiene un diagrama del pipeline que marca dónde corta;
- Control y reglas tiene los meses que usa cada etapa (una fila por etapa, una columna por mes) y la regla de
  veredicto como diagrama;
- Corridas tiene los pasos del recorrido de una corrida, de la VM al ledger y a las páginas;
- Exploratorios tiene un diagrama de qué motivó cada estudio en el experimento.

Una secuencia sin ramas (una caja por paso) SHALL ir como lista de pasos numerados unidos por una línea, no como
diagrama de flujo. Los colores de los diagramas SHALL leerse en claro y en oscuro: tintes semitransparentes con borde
de color, nunca un fondo claro fijo. Un texto largo SHALL NOT ir dentro de una celda de tabla.

#### Scenario: Página de H3
- **WHEN** se abre la página de H3
- **THEN** antes de los números hay un diagrama que muestra que H3 achica solo la optimización, y el veredicto va en un
  recuadro destacado

#### Scenario: Exploratorios
- **WHEN** se abre la página de exploratorios
- **THEN** cada estudio es una sección con sus párrafos y sus cifras, no una fila de tabla con texto

#### Scenario: Fases de las corridas
- **WHEN** se abre Corridas
- **THEN** ve el protocolo, la máquina, los pasos de una corrida de la VM a la página, qué cuenta como evidencia y el
  costo total, y un enlace en GitHub al registro de fases

## ADDED Requirements

### Requirement: Páginas en estado final
Las páginas publicadas SHALL describir el diseño, los resultados, el veredicto y las limitaciones como quedaron, no cómo
se llegó a ellos. Fuera de la sección Predicción, ningún título SHALL nombrar un cambio de OpenSpec, una fecha de
trabajo, una fase o un mensaje de Zulip. El texto SHALL NOT presentar una sección como respuesta a una pregunta
recibida. Un mensaje de Zulip puede citarse como fuente de una regla del curso (por ejemplo, el baseline 208135),
nunca como motivo de una sección. La sección Predicción queda como se fijó: sus fechas y commits son la prueba de que
se escribió antes de correr. Cada hipótesis SHALL tener un solo veredicto, el que sale con réplicas. El historial de
rondas, fases y veredictos anteriores SHALL quedar en la bitácora y en el Anexo, no en el cuerpo de la página.

#### Scenario: Títulos de una hipótesis
- **WHEN** se listan los títulos de `experimentos/h4/README.md` fuera de § Predicción
- **THEN** ninguno contiene «cambio», un nombre de cambio entre comillas invertidas, una fecha ni «Zulip»

#### Scenario: Un veredicto por hipótesis
- **WHEN** se abre la página de H1
- **THEN** hay un solo recuadro de veredicto, el de réplicas, y no hay un recuadro que reemplace a otro

#### Scenario: Verificación automática
- **WHEN** corre `scripts/sitio.sh`
- **THEN** falla nombrando la página y el título si un título fuera de § Predicción nombra un cambio, una fecha o Zulip
