# Design

## Context

La motivación está en `proposal.md`. El estado actual que condiciona el enfoque:

- **Generador.** `comun/reporte.py` escribe bloques entre `<!-- generado:… -->` en las páginas que devuelve
  `destinos(exp)`. Para `sampling_1` escribe `mapa`, `bloque-a`, `bloque-a-completo`, `varianza`, `diferencias`,
  `tiempo-igual` y `figuras` en `sampling_1/README.md`, y `bloque-b` en `exploratorios/README.md`. En `index.md` y
  `sitio/hipotesis/README.md` escribe `tarjetas`. `scripts/comparar_rondas.py` escribe `rondas`. Si falta un marcador,
  falla sin escribir nada.
- **Verificadores.** `scripts/verificar_readme.py` y `scripts/verificar_informe_h3.py` leen `bloque-a-completo` de
  `sampling_1/README.md`. Sus tests están en `tests/test_verificadores.py`.
- **Dependencias.** `comun/variantes.py` lee `## Dependencias` del README de cada experimento, `sampling_1` incluido.
- **Datos para las figuras nuevas.** Ya existen:
  - curvas por semilla en `ledger/curvas/`, que hoy usa `fig_curva_diferencia`;
  - predicciones por semilla en `ledger/predicciones/`, que hoy usa el bootstrap de tiempo igual (`_probs`);
  - tiempos por fase en `estudios.csv` y `resultados.csv`;
  - el ledger de la ronda anterior en `ledger/ronda_201903-201906/`, que hoy usa `fig_rondas`.

  No hace falta correr nada.
- **Gráficos de los compañeros.** Los reportes de los exploratorios son HTML con PNG embebidos en base64: cuatro en
  `validacion_20_semillas/originales/reporte_h{1..4}.html` y cinco en `validacion_50_semillas/reporte_original.html` y
  `resultados/reporte_50_semillas_original.html`. `sensibilidad_muestra` no tiene gráficos, pero sí CSV
  (`08_ganancia_por_semilla.csv`).
- **Sitio.** MkDocs Material 9.8.1 con `navigation.indexes`. El nav tiene etiquetas cortas («H1»…). El CSS limita el
  texto a 75ch, mientras las figuras y las tablas ocupan todo el ancho, así que hay anchos distintos. Hay un solo modo
  de color.
- **Cambio en paralelo.** `tiempos-confiables-y-consistencia` corre en su rama, y sus tareas nombran
  `bloque-a-completo` en `sampling_1/README.md`.

## Goals / Non-Goals

**Goals:**
- Que Inicio cuente el resultado completo en una pantalla y media, y que Resultados se lea de arriba abajo sin tablas
  de consulta en el medio.
- Que los gráficos que hicieron los compañeros aparezcan, y que los datos del experimento tengan sus equivalentes.
- Que todas las páginas tengan una sola columna y un modo oscuro que se recuerda.
- Que lo que hoy pasa (generador, verificadores, `variantes --verificar`, `sitio.sh`) siga en verde después de mover
  bloques.

**Non-Goals:**
- Cambiar números, veredictos, ledgers o corridas.
- Rehacer los gráficos de los exploratorios con su protocolo: se muestran tal como salieron de sus reportes. Lo único
  generado de nuevo para un exploratorio es la figura de `sensibilidad_muestra`, desde su CSV.
- Gráficos interactivos.
- Tocar `tiempos-confiables-y-consistencia`.

## Decisions

### D1. Mapa de páginas y bloques

| página | bloques generados | contenido escrito a mano |
|---|---|---|
| `index.md` (Inicio) | `hallazgo-tradeoff`, `hallazgo-tiempo`, `hallazgo-ensamble`, `tarjetas` | pregunta, respuesta, 2–3 líneas por hallazgo, recuadro de limitaciones, botón |
| `sampling_1/README.md` (Resultados) | `mapa`, `grilla`, `desglose`, `bloque-a`, `fraccion`, `ensamble`, `tiempo-igual`, `semillas` | las cuatro preguntas, limitaciones, conclusiones, qué sigue, exploratorios en una línea, dependencias |
| `sampling_1/anexo.md` (Anexo, nuevo) | `bloque-a-completo`, `varianza`, `diferencias`, `ic-rondas`, `rondas` | una línea por sección y el resultado de la predicción de la ronda |
| `sampling_1/exploratorios/README.md` | `bloque-b` (una sección por estudio, con figuras y cifras) | diagrama de motivaciones, texto por estudio |
| `hN/README.md` | `resultado` (suma las curvas de ganancia) | sin cambios |

Hoy el bloque `figuras` tiene tres figuras juntas. Se separa en `grilla`, `desglose` y `fraccion`, para que cada una
quede en la sección de su pregunta.

Resultados, de arriba abajo:
1. Pregunta y respuesta.
2. ¿Qué conviene achicar? Lleva la grilla, el desglose, el bloque A resumen con el detalle plegado y los hallazgos por
   hipótesis.
3. ¿Cuánto se puede achicar? Lleva Δ contra tasa.
4. ¿Qué se hace con el tiempo ahorrado? Lleva el ensamble según el tiempo y el tiempo igual con su tabla plegada.
5. ¿Qué tan estable es? Lleva las cajas por semilla, el resumen de rondas en tres puntos con enlace al Anexo, y AUC y
   ganancia.
6. Limitaciones comunes.
7. Conclusiones.
8. Qué sigue.
9. Exploratorios, en una línea.
10. Dependencias.

Se mudan:
- la predicción conjunta, a `control/README.md` § Predicción, como «Predicción del experimento (1-nov)»;
- el diseño, a `corridas.md` § Protocolo;
- la bibliografía, a `docs/metodo.md` § Bibliografía.

En Resultados, Conclusiones dice si la predicción acertó, y enlaza.

Alternativa descartada: partir Resultados en una página por pregunta. Son más clics, y el escenario «cada resultado en
una sola página» se cumple igual con el Anexo.

### D2. El generador escribe en más de un archivo por experimento

`destinos(exp)` ya devuelve una lista de páginas. Para `sampling_1` suma `anexo.md` e `index.md` con sus bloques. La
validación de marcadores de todas las páginas sigue ocurriendo antes de escribir. `scripts/comparar_rondas.py` pasa a
escribir `rondas` en `anexo.md`. Los verificadores leen `bloque-a-completo` de `anexo.md`.

`verificar_readme.py` revisa además los números escritos a mano de `index.md` y de `sampling_1/README.md` fuera de los
marcadores. Cada número se busca en `bloque-a-completo` y en los títulos de las figuras generadas. Así, el 94 % de la
portada se valida contra el título del desglose.

### D3. Figuras nuevas, equivalentes a las de los exploratorios

Antes de escribir código de gráficos se carga la skill `dataviz`. Las figuras siguen las reglas de `reporte-visual`:
título que dice qué mirar, sin etiquetas pisadas, pendiente sin datos y SVG con `hashsalt` fijo.

| figura | archivo | forma | datos | página |
|---|---|---|---|---|
| ensamble según K y según el tiempo | `ensamble.svg` | dos paneles: G del ensamble de las primeras K semillas contra K, y contra T_opt + K·T_final; una línea por variante que vale la pena más el control; línea vertical en T(C) | `ledger/predicciones/` (como `_probs`) y tiempos | Resultados (pregunta 4), Inicio |
| cajas por semilla | `semillas_replicas.svg` (se amplía) | caja Q1–Q3 con media y puntos por semilla; réplicas con otro marcador | `resultados.csv`, `replicas.csv` | Resultados (pregunta 5) |
| IC por ronda | `ic_rondas.svg` | por variante, dos segmentos de IC (ronda anterior gris, vigente color), −δ punteado | ledger de la ronda anterior y vigente | Anexo |
| curvas de ganancia | `curvas_<H>.svg` | paneles por variante; G contra envíos con banda P10–P90 de la variante y del control, mediana punteada del control, N\* | `ledger/curvas/` | página de cada hipótesis |
| sensibilidad de la muestra | `exploratorios/figuras/sensibilidad_muestra.svg` | Δ de ganancia por muestra (puntos con su mediana), en M$ | `08_ganancia_por_semilla.csv` | Exploratorios |

El ensamble según K se calcula con las mismas probabilidades y el mismo corte N\* que el tiempo igual, sin bootstrap. Se
dibuja solo para las variantes que valen la pena (A ≥ 2, *no pierde*) más el control, para que las líneas se lean. La
leyenda va al costado, no encima.

### D4. Gráficos originales de los exploratorios

Un script de una sola vez, `scripts/extraer_figuras_exploratorios.py`, decodifica los PNG embebidos y los guarda en
`<estudio>/figuras/<nombre>.png`. El nombre sale del `alt` o del título previo. El script es determinista: correrlo dos
veces da los mismos bytes. Cada `exploratorio.json` suma:

```json
"figuras": [{"archivo": "figuras/contraccion_ic.png", "leyenda": "Reporte original (50 semillas, hiperparámetros fijos): IC de Δ con 10 y con 50 semillas"}],
"tablas": [{"csv": "...", "columnas": [{"columna": "g_201908", "etiqueta": "G en 201908", "escala": 1e-6, "unidad": "M$"}]}]
```

Las columnas como texto (formato viejo) siguen valiendo, para no romper un manifiesto que no se actualice.
`comun/variantes.py --verificar` falla si una figura declarada no existe. En `sensibilidad_muestra` la figura se declara
con `"csv"` y `"columna"` en lugar de `"archivo"`, y la genera el bloque B. La leyenda dice de qué reporte o de qué CSV
sale la figura, no quién la hizo. La lista blanca de `mkdocs.yml` suma `!/experimentos/**/figuras/**` para las figuras
de los estudios.

### D5. Diagramas (Mermaid, escritos a mano)

- **Exploratorios:** `sensibilidad_muestra` lleva a R = 8 réplicas; `validacion_50_semillas` lleva a H4 y a las
  extensiones de H3; `validacion_20_semillas` lleva a la ronda vigente con 20 semillas. Se aclara que ninguno decide un
  veredicto.
- **Corridas:**
  - línea de tiempo de las fases 1 a 7 con sus fechas (`gantt` o `timeline`);
  - recorrido de una corrida: `lanzar_fase.sh`, VM, bucket, `gsutil rsync`, ledger, `comun/reporte.py` y páginas;
  - la tabla de fases queda con columnas cortas (fase, fecha, tag, VMs, carga) y lo que corrió cada fase pasa a una
    lista debajo.
- **Cómo trabajamos:**
  - etapas (hipótesis, diseño, código, corridas, análisis, informe), con la revisión en sesión limpia en cada
    compuerta y el modelo de cada una;
  - una etapa sin supervisión: `etapas.sh`, `etapa.sh`, aplicar, revisar, y `bloqueo.txt` o `en_curso.txt`;
  - los pasos de § Agregar una hipótesis como diagrama, antes de la lista.

Mermaid se adapta solo al modo oscuro de Material.

### D6. Una columna y modo oscuro

- **Columna:** `.md-content__inner` tiene un ancho máximo fijo (~36rem, unos 85–90 caracteres de texto; se ajusta
  midiendo), y todo lo de adentro ocupa el 100 %: párrafos, figuras, código, recuadros y plegables. Se quitan los topes
  de 75ch y la regla `calc(89ch …)` de los recuadros. Una tabla más ancha se desplaza en su recuadro. En el teléfono las
  figuras siguen con su ancho mínimo y su desplazamiento propio. Las líneas de código publicadas se cortan a mano en el
  texto, porque no se usa ajuste automático, que rompe los comandos.
- **Modo oscuro:** `theme.palette` con dos esquemas (`default` y `slate`), cada uno con su `toggle` (icono y
  etiqueta), y `media: "(prefers-color-scheme: …)"` para la primera visita. Material guarda la elección en
  `localStorage` (documentado en «Changing the colors › Color palette toggle»). En `sitio/estilos.css`, los colores de
  veredicto, pills, `.icbar` e `.ic` pasan a variables CSS con valores para `[data-md-color-scheme="slate"]`.
- **Figuras en oscuro:** las figuras conservan su fondo blanco (lo tienen los SVG generados y los PNG de los
  exploratorios), con un borde redondeado y un margen interno. Así se leen igual en los dos modos, sin regenerar.
  Alternativa descartada: fondo transparente y texto con `currentColor`. No funciona en `<img>` y rompería los PNG del
  video.

### D7. Barra lateral con títulos

En `nav` las páginas van sin etiqueta, y MkDocs toma el título de su H1: «H4 · Muestras informadas por clase»,
«Control y reglas», «Anexo de resultados». Las secciones conservan su etiqueta («Hipótesis», «Cómo medimos»).
Resultados se vuelve sección, con `sampling_1/README.md` como índice y `anexo.md` como hija. Con `navigation.indexes`,
el README es el índice. `anexo.md` no se llama README, así que no lo toma por índice.

### D7b. Encabezado

`site_name: Sampling_1 · DMEyF 2026`. En pantallas angostas (menos de 60em, donde Material esconde la barra lateral),
`sitio/estilos.css` sube la altura de `.md-header` (por ejemplo, a 3.6rem) y muestra el título en dos líneas. Para eso,
un override del parcial `header.html` (`theme.custom_dir: sitio/overrides`) envuelve «DMEyF 2026» en un `<span>` que en
escritorio va en línea y en el teléfono pasa a la segunda línea, en letra más chica. Hay que ajustar el desplazamiento
del contenido y del menú lateral (`.md-main`, `.md-sidebar`), que asumen la altura estándar. Alternativa descartada:
achicar la letra hasta que entre en una línea, porque a 390 px se lee mal.

### D8. Inicio sin copiar

El texto de cada hallazgo explica qué mirar y por qué, en 2–3 líneas. Los números que escribe a mano (por ejemplo,
94 %) los valida D2. El recuadro de limitaciones resume tres de las de Resultados («Test ya mirado», «Un mes, un año,
una máquina», «Réplicas solo en parte de las variantes») en una línea cada una, con enlace a Resultados § Limitaciones
comunes.

## Risks / Trade-offs

- [Unir `main` en la rama de `tiempos-confiables-y-consistencia` choca con `sampling_1/README.md` y con
  `comun/reporte.py`] → Este cambio se archiva antes. La bitácora de `sampling_1` deja anotado qué bloques se mudaron, y
  esa rama regenera después de unir, porque sus números entran solo regenerando.
- [El guion del video cita figuras y secciones] → Los nombres de las figuras existentes no cambian. Una tarea revisa el
  guion y anota las figuras nuevas que conviene mostrar (ensamble según el tiempo).
- [Los PNG de los exploratorios pesan] → Unos 100–300 KB cada uno, nueve en total. Se aceptan, porque están en el repo
  dentro de los HTML.
- [Ancho fijo angosto en pantallas de 1920 px] → Se acepta: queda aire a los costados, y es el pedido. Las tablas anchas
  se desplazan.
- [Los PNG de los exploratorios llevan textos con nombres de estrategia («Campeon», «IdeaC_…»)] → No nombran personas.
  La búsqueda de nombres de `scripts/sitio.sh` revisa el texto, no las imágenes, y la leyenda no dice el autor.
- [Fecha de entrega, 23-nov] → El grupo 1 deja el sitio en verde aunque el texto de Resultados todavía sea el viejo,
  reordenado en lo mínimo. El grupo 2 se puede cortar por página si no alcanza el tiempo.
