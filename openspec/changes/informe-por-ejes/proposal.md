# Proposal

## Why

El sitio responde la pregunta, pero se lee como el historial de cómo se llegó a la respuesta. Las páginas de cada
hipótesis muestran primero la tabla de la réplica 0 y después un recuadro que la reemplaza con réplicas. Muchos títulos
llevan el nombre del cambio de OpenSpec o de un mensaje de Zulip. Las cuatro hipótesis se presentan como cuatro
experimentos sueltos, aunque responden dos preguntas: dónde achicar y cómo muestrear. La entrega del video es el
23-nov y el informe tiene que estar en su forma final antes de grabarlo.

## What Changes

- **Resultados ordenado por dos ejes.** Arriba van la pregunta, la hipótesis general, la configuración común y la
  respuesta, con las variantes que valen la pena primero. Después, un mapa «dónde × cómo» que ubica cada familia de
  variantes, y una sección por eje:
  - **¿Dónde achicar?** Todo el pipeline (H1), dentro de LightGBM (H2), solo la búsqueda (H3) o también el final (`H4F`, `H4O`).
  - **¿Cómo muestrear?** Al azar contra conservar las bajas, con o sin peso (pares `H4O`−`U`, `H4P`−`H3`, `H4H`/`H4U`).

  Siguen cuánto se puede achicar, qué hacer con el tiempo ahorrado, estabilidad, limitaciones, conclusiones y qué
  sigue. H1–H4 conservan su nombre, su carpeta, sus variantes y su predicción: los ejes son una forma de leerlos, no
  hipótesis nuevas.
- **Páginas de hipótesis en su estado final.**
  - El bloque generado muestra la tabla con réplicas (la misma regla de veredicto que Resultados); la tabla de la
    réplica 0 pasa al Anexo.
  - Un solo recuadro de veredicto, con réplicas, y una línea que dice qué eje responde la hipótesis.
  - Diseño, Veredicto y Limitaciones se escriben como estado final, sin subtítulos con nombre de cambio, fecha o
    mensaje de Zulip. El historial queda en la bitácora.
  - En H4, el diseño y el veredicto se separan por eje: búsqueda informada, final con bajas y grilla común.
  - **La sección Predicción no cambia**: está fijada antes de correr y la spec lo exige.
- **Portada más corta.** Pregunta, hipótesis general, respuesta, el mapa del tradeoff, limitaciones y tarjetas. Las
  figuras de desglose y de ensamble quedan solo en Resultados. La respuesta corta se escribe una vez y la portada
  copia la misma frase.
- **Corridas como anexo de método.** Quedan el protocolo, la máquina, qué cuenta y el costo. El registro de las fases
  (VMs, tandas, retomas) pasa a `experimentos/sampling_1/docs/fases.md`, fuera del sitio, enlazado en GitHub.
- **Arreglo del reporte.** La etiqueta del eje x del mapa del tradeoff se escribe una sola vez para toda la figura, en
  lugar de una por panel, porque hoy se pisan.

## Capabilities

### New Capabilities
- `lectura-por-ejes`: cómo el informe agrupa las hipótesis registradas en los ejes «dónde achicar» y «cómo muestrear».
  Cubre la tabla de ejes como dato del registro de variantes, el mapa que la muestra y la regla de que los ejes no
  renombran hipótesis ni tocan predicciones.

### Modified Capabilities
- `sitio-informes`: la portada pasa a una sola figura y una respuesta idéntica a la de Resultados. Las páginas de
  hipótesis se leen en estado final, sin títulos de proceso. Corridas deja de tener el registro de fases.
- `reporte-visual`: la tabla de cada hipótesis sale con réplicas y la de réplica 0 va al Anexo. Resultados sigue el
  orden por ejes. La etiqueta del eje x del mapa del tradeoff va una sola vez.

## Impact

- `comun/reporte.py`: bloque `resultado` de cada hipótesis, bloque nuevo `ejes` (mapa dónde × cómo), Anexo con las
  tablas de la réplica 0 por hipótesis, portada sin dos figuras, figura del tradeoff.
- `comun/variantes.py`: cada familia declara su eje (dónde y cómo); `--verificar` lo exige.
- Páginas: `index.md`, `experimentos/sampling_1/{README,anexo,corridas}.md`, `experimentos/h1..h4/README.md`, y
  `experimentos/control/README.md` (solo títulos de proceso). Archivo nuevo, no publicado:
  `experimentos/sampling_1/docs/fases.md`.
- Verificadores: `scripts/verificar_readme.py` y `scripts/verificar_informe_h3.py` siguen pasando. Un chequeo nuevo
  compara cada sección Predicción con `HEAD` antes del cambio.
- Fuera de alcance:
  - renombrar hipótesis, variantes o carpetas;
  - nuevas corridas, cambiar números o veredictos;
  - el guion del video;
  - el contenido de las secciones Predicción.
