# Tasks

Cada grupo se cierra con `python -m pytest -q`, `python -m scripts.verificar_readme`,
`python -m scripts.verificar_informe_h3`, `python -m comun.variantes --verificar` y `scripts/sitio.sh` en verde, una
entrada en `experimentos/sampling_1/docs/bitacora.md`, commit y push. Antes de cada commit, las secciones Predicción
de `control` y `h1` a `h4` tienen que ser iguales a las de `main` antes del cambio (tarea 1.1).

## 1. Resguardo de las predicciones

- [x] 1.1 `scripts/verificar_predicciones.py`: extrae `## Predicción` (hasta el siguiente `## `) de cada README de
  `control` y `h1`–`h4`, y la compara con la del commit base guardado en el script (`1a5c0da1`). Falla nombrando el
  archivo. Se llama desde `scripts/sitio.sh`. Verificación: pasa en el estado actual, y un test en
  `tests/test_verificar_predicciones.py` cambia una línea de una copia y ve el fallo.

## 2. Ejes en el registro y mapa de ejes

- [ ] 2.1 `EJES` en `comun/variantes.py` (metodo → (dónde, cómo)), con los valores de la spec `lectura-por-ejes`.
  `verificar` falla nombrando un `metodo` sin ejes. Verificación: test que registra una variante de juguete sin ejes y
  ve el error; `--verificar` pasa con el registro real.
- [ ] 2.2 Bloque `ejes` en `comun/reporte.py` (tabla HTML dónde × cómo, «familia (HN): k de n valen la pena», celdas
  vacías sin texto) y en el docstring de bloques. Verificación: test con la celda (busqueda, azar) = H3, H3K, H3R, H3L
  con «9 de 9»; test con una familia de juguete que aparece en su celda sin tocar el generador.
- [ ] 2.3 Rótulo del eje x de `fig_tradeoff` con `fig.supxlabel`, una vez. Verificación: abrir `tradeoff.svg`
  regenerado (PNG por `rsvg-convert`) y ver un solo rótulo sin pisarse; el test de figuras sigue verde.

## 3. Tabla de hipótesis con réplicas

- [ ] 3.1 `bloques_hipotesis` arma la tabla desde el agregado: Δ con réplicas, A con IC, R, veredicto con réplicas,
  G media, ΔAUC, T mediana, vale la pena; nota al pie para una variante sin réplicas. Verificación: test de que
  `U0.5` sale *indeterminado* con −3.64 en el bloque de `h1`, y de que cada veredicto coincide con el del bloque A.
- [ ] 3.2 Bloques `replica0-h1` … `replica0-h4` en el Anexo, en la sección nueva «Réplica 0 por hipótesis», con la tabla
  de hoy (semillas ganadas incluidas). Verificación: `test_reporte` lista los bloques nuevos en `BLOQUES_ANEXO`; el
  Δ −1.38 de `U0.5` aparece solo en el Anexo (grep sobre `site/`).
- [ ] 3.3 Regenerar (`python -m comun.reporte --todos`, `python -m scripts.comparar_rondas`) y revisar el diff: ningún
  número del bloque A cambia. Verificación: `git diff` de `anexo.md` en `bloque-a-completo` vacío.

## 4. Páginas de hipótesis en estado final

- [ ] 4.1 H1 y H2: Diseño sin subtítulos de proceso, un solo recuadro de Veredicto con réplicas (una línea por
  predicción: se cumplió o no), una línea inicial con el eje que responde. Verificación: verificadores en verde, tarea
  1.1 en verde.
- [ ] 4.2 H3: lo mismo; las extensiones (K, R, L) como subsección de Diseño y de Veredicto, no por cambio.
  Verificación: ídem.
- [ ] 4.3 H4: Diseño y Veredicto en tres partes (búsqueda informada, final con bajas, grilla común); las menciones a
  211718 y 212124 pasan a la regla del curso que aplican. Verificación: ídem.
- [ ] 4.4 Control y reglas: títulos de proceso fuera de § Predicción reescritos (p. ej. § Medición de tiempos).
  Verificación: ídem.
- [ ] 4.5 Regla de títulos de proceso en `scripts/nombres_sitio.py` (fuera de § Predicción: «cambio», fechas, «Zulip»,
  nombres de cambios archivados). Verificación: `scripts/sitio.sh` pasa; un test con un título «### X (cambio `y`,
  13-nov-2026)» ve el fallo.

## 5. Resultados por ejes

- [ ] 5.1 Reordenar `experimentos/sampling_1/README.md` según design D3: Respuesta con «valen la pena» primero,
  § Cómo leer las hipótesis (bloque `ejes`), § ¿Dónde achicar?, § ¿Cómo muestrear? (con la tabla H4O−U y la grilla de
  veredictos), y los bullets por hipótesis repartidos sin repetir un veredicto. Verificación: `verificar_readme` en
  verde; cada variante citada una sola vez con su veredicto (grep).
- [ ] 5.2 Conclusiones por eje que citan veredictos y pares registrados, sin «se confirma el eje». Verificación:
  revisión contra la spec `lectura-por-ejes` § Los ejes no reemplazan a las hipótesis.

## 6. Portada y Corridas

- [ ] 6.1 `index.md`: pregunta, hipótesis general, el recuadro Respuesta igual al de Resultados, el mapa del tradeoff,
  limitaciones y tarjetas; sin `hallazgo-tiempo` ni `hallazgo-ensamble` (marcadores y `BLOQUES_INICIO`). Verificación:
  test de bloques de inicio actualizado; la página construida tiene una sola `<img>` de figura.
- [ ] 6.2 `verificar_readme` compara el cuerpo de `!!! success "Respuesta"` de `index.md` y de Resultados.
  Verificación: pasa; un test con un texto distinto ve el fallo.
- [ ] 6.3 § Fases de `corridas.md` a `experimentos/sampling_1/docs/fases.md` sin cambios de texto; Corridas lo enlaza en
  GitHub. Verificación: `scripts/sitio.sh` sin enlaces rotos; `fases.md` no está en `site/`.

## 7. Cierre

- [ ] 7.1 Revisión en sesión limpia (subagente `general-purpose`) con la lista de la compuerta de informe de
  `docs/revision.md` y las specs del cambio; corregir lo que encuentre. Verificación: entrada en la bitácora con los
  ítems revisados.
- [ ] 7.2 `openspec validate informe-por-ejes` en verde y tokens de la sesión con `comun/tokens.py`. Verificación:
  salida de los dos comandos en la bitácora.

## Workflow follow-up

- Archivar con `/opsx:archive` después de la revisión (sincroniza las specs).
- Regenerar los PNG del video (`--figuras`) si el guion usa el mapa del tradeoff.
