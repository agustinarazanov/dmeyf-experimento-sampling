# reporte-visual Specification

## Purpose
Define el reporte visual del experimento: una página regenerable desde el ledger que explica qué se está probando y
compara todos los resultados en un solo lugar, para el grupo, el tutor y el video.

## Requirements

### Requirement: Reporte regenerable desde el ledger
Cada experimento SHALL tener un comando que genere su `informe/reporte.html` a partir de su ledger, del ledger de los
experimentos de los que depende, de las curvas guardadas y de su `docs/hipotesis.md`, sin números escritos a mano, y que
pueda correrse en cualquier momento con los resultados que haya. Un mismo comando SHALL poder regenerar todos los
reportes del repo.

#### Scenario: Regenerar con resultados parciales
- **WHEN** se genera el reporte y a una variante le faltan semillas o no tiene corridas
- **THEN** la variante aparece como pendiente con lo que tiene, y ninguna sección falla ni muestra un número inventado

#### Scenario: Regenerar dos veces
- **WHEN** se genera el reporte dos veces sin corridas nuevas
- **THEN** el archivo resultante es el mismo salvo la fecha de generación

#### Scenario: Mismos números que antes de separar
- **WHEN** se regeneran los reportes después de separar `sampling-velocidad`
- **THEN** cada Δ, IC, A y veredicto de los reportes de `h1`, `h2`, `h3` y `sampling_1` coincide con la tabla de
  resultados de `informe.md` anterior a la separación

### Requirement: Introducción tomada de los documentos
El reporte SHALL abrir con una introducción que explique la pregunta, las hipótesis, el control y la regla de decisión,
tomada de `docs/hipotesis.md` y `docs/diseno.md`, de modo que quien no conoce el experimento entienda qué se mide antes
de ver un número.

#### Scenario: Cambia una hipótesis
- **WHEN** se edita `docs/hipotesis.md` y se regenera el reporte
- **THEN** la introducción refleja el cambio sin tocar el generador

### Requirement: Comparación de todas las variantes en una vista
El reporte de `sampling_1` SHALL mostrar una tabla con todas las variantes de todas las hipótesis contra el control (ganancia
media, diferencia apareada con su intervalo, tiempo, aceleración, veredicto), un gráfico de tiempo contra ganancia con
un punto por variante y el control marcado, y un enlace al reporte de cada hipótesis. El reporte de cada hipótesis SHALL
mostrar las curvas de ganancia (banda entre semillas) de sus variantes junto al control.

#### Scenario: Leer el veredicto de una hipótesis
- **WHEN** se abre el reporte de una hipótesis
- **THEN** se ve su predicción, la regla, el resultado de cada variante y el veredicto (no pierde, pierde, indeterminado,
  pendiente), con la tabla y la figura que lo sostienen

#### Scenario: Comparación a tiempo igual
- **WHEN** el control y al menos una variante tienen sus 10 semillas
- **THEN** el reporte de `sampling_1` incluye la comparación a tiempo igual (ensamble de K semillas de la variante contra el
  control) con el K usado

#### Scenario: Hipótesis nueva en `sampling_1`
- **WHEN** se registra un experimento nuevo con variantes (por ejemplo `h4`)
- **THEN** el reporte de `sampling_1` lo incluye en la tabla y en el gráfico sin cambiar el generador

### Requirement: Legible sin servidor y compartible
El reporte SHALL ser un único archivo HTML con las figuras embebidas, que se abre desde el repo sin servidor ni
dependencias, y SHALL poder publicarse tal cual para el tutor y el grupo.

#### Scenario: Abrir desde un clon limpio
- **WHEN** alguien clona el repo y abre `informe/reporte.html`
- **THEN** ve el reporte completo con sus figuras, sin instalar nada

### Requirement: Informe escrito por hipótesis
Cada experimento de hipótesis SHALL tener un `informe/informe.md` con su resultado, sus limitaciones propias y su
conclusión. El `informe/informe.md` de `sampling_1` SHALL tener la comparación entre hipótesis, la respuesta a la pregunta
del tutor y las limitaciones que comparten todas.

#### Scenario: Leer solo H3
- **WHEN** alguien abre `experimentos/h3/informe/informe.md`
- **THEN** encuentra el veredicto de H3 con su tabla, la dependencia de los estudios de `h1` declarada como limitación
  y un enlace al informe conjunto

### Requirement: Comparación limpia en dos bloques
El reporte y el `informe.md` de `sampling_1` SHALL presentar todos los resultados en dos bloques separados.

**Bloque A, mismo protocolo.** Una fila por variante del registro con:
- ganancia media;
- Δ apareado de la réplica 0 con su IC;
- Δ con réplicas, su IC y el número de réplicas, cuando existe;
- T y A, con T como mediana entre réplicas cuando hay varias;
- tiempo igual con su intervalo;
- el veredicto, que es el de Δ con réplicas cuando existe y si no el de Δ apareado. La columna dice cuál se usó.

**Bloque B, exploratorios.** Una fila por estudio exploratorio declarado con:
- autor;
- pregunta;
- protocolo;
- las cifras que su manifiesto marca como principales, leídas de sus CSV;
- la advertencia de su manifiesto.

El bloque B SHALL decir que sus cifras no se comparan una a una con las del bloque A. Ninguna cifra de ninguno de los dos
bloques SHALL estar escrita a mano en el generador.

#### Scenario: Variante con réplicas
- **WHEN** `H3-0.1` tiene 8 réplicas
- **THEN** su fila en el bloque A muestra el Δ apareado de la réplica 0 y el Δ con réplicas, y el veredicto dice
  "con réplicas (8)"

#### Scenario: Exploratorio sin CSV
- **WHEN** el manifiesto de un exploratorio apunta a un CSV que no está en el repo
- **THEN** su fila del bloque B sale como pendiente, con el nombre del archivo faltante, y el resto del reporte se genera

#### Scenario: Gráfico de tiempo contra ganancia con réplicas
- **WHEN** una variante tiene varias réplicas
- **THEN** su punto en el gráfico de tiempo contra ganancia lleva una barra con el rango entre réplicas, y las
  variantes de una sola réplica se dibujan sin barra

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
