# Spec Delta

## Purpose
Define cómo el informe agrupa las hipótesis registradas (H1 a H4) en dos ejes de lectura, «dónde achicar» y «cómo
muestrear», sin renombrarlas ni tocar sus predicciones, para que Resultados responda la pregunta del experimento por
ejes y no hipótesis por hipótesis.

## ADDED Requirements

### Requirement: Ejes declarados en el registro
Cada familia de variantes del registro SHALL declarar en qué lugar del pipeline achica (eje «dónde»: `todo`,
`lightgbm`, `busqueda`, `final`) y cómo elige las filas (eje «cómo»: `azar`, `bajas`, `bajas-peso`, `dificiles`,
`interno`). En `final` entran las familias que achican el modelo final, con o sin la búsqueda. Los valores SHALL salir
del registro, no del texto de una página. La verificación del registro SHALL fallar nombrando la familia que no declara
alguno de los dos ejes. El control no tiene ejes.

#### Scenario: Familia sin eje
- **WHEN** se registra una familia nueva sin el eje «cómo»
- **THEN** `python -m comun.variantes --verificar` falla nombrando esa familia y el eje que falta

#### Scenario: Ejes de las familias actuales
- **WHEN** se leen los ejes del registro
- **THEN** `U` es (todo, azar); `B` y `GOSS` son (lightgbm, interno); `H3`, `H3K`, `H3R` y `H3L` son (busqueda, azar);
  `H4U` es (busqueda, bajas); `H4H` es (busqueda, dificiles); `H4P` es (busqueda, bajas-peso); `H4O` y `H4F` son
  (final, bajas-peso)

### Requirement: Los ejes no reemplazan a las hipótesis
Los ejes SHALL ser una forma de leer los resultados: las hipótesis H1 a H4 conservan su nombre, su carpeta, sus
variantes, su predicción y su veredicto. Ninguna página SHALL presentar un eje como hipótesis nueva ni darle un
veredicto propio. Una conclusión por eje SHALL citar los veredictos y los pares ya registrados en los que se apoya.

#### Scenario: Conclusión del eje «dónde»
- **WHEN** Resultados concluye que achicar la búsqueda no pierde y achicar el final al azar sí
- **THEN** el párrafo cita los veredictos de `H3-{r}` y `U{r}` y el par `U{r}` − `H3-{r}` del Anexo, y no dice
  «se confirma el eje»

#### Scenario: Predicción intacta
- **WHEN** se aplica este cambio
- **THEN** la sección Predicción de cada `README.md` de `control` y `h1` a `h4` es igual, byte a byte, a la de antes
  del cambio

### Requirement: Mapa de ejes en Resultados
Resultados SHALL mostrar, en un bloque generado, una tabla «dónde × cómo» con una fila por valor de «dónde» y una
columna por valor de «cómo». Cada celda SHALL listar las familias que caen ahí, con su hipótesis y la cantidad de
variantes que valen la pena sobre las que tiene. Una celda sin familias SHALL quedar vacía, sin texto. La tabla no
repite números de otro gráfico: da la ubicación y el conteo, no Δ ni A.

#### Scenario: Celda de la búsqueda al azar
- **WHEN** se abre Resultados
- **THEN** la celda (búsqueda, azar) lista `H3`, `H3K`, `H3R` y `H3L` de H3 con «9 de 9 valen la pena»

#### Scenario: Familia nueva
- **WHEN** se registra una familia con sus ejes y se regenera
- **THEN** aparece en su celda sin editar el generador ni la página
