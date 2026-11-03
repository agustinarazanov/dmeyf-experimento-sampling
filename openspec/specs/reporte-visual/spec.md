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
- **WHEN** se genera el reporte y a un brazo le faltan semillas o no tiene corridas
- **THEN** el brazo aparece como pendiente con lo que tiene, y ninguna sección falla ni muestra un número inventado

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

### Requirement: Comparación de todos los brazos en una vista
El reporte de `sampling_1` SHALL mostrar una tabla con todos los brazos de todas las hipótesis contra el control (ganancia
media, diferencia apareada con su intervalo, tiempo, aceleración, veredicto), un gráfico de tiempo contra ganancia con
un punto por brazo y el control marcado, y un enlace al reporte de cada hipótesis. El reporte de cada hipótesis SHALL
mostrar las curvas de ganancia (banda entre semillas) de sus brazos junto al control.

#### Scenario: Leer el veredicto de una hipótesis
- **WHEN** se abre el reporte de una hipótesis
- **THEN** se ve su predicción, la regla, el resultado de cada brazo y el veredicto (no pierde, pierde, indeterminado,
  pendiente), con la tabla y la figura que lo sostienen

#### Scenario: Comparación a tiempo igual
- **WHEN** el control y al menos un brazo tienen sus 10 semillas
- **THEN** el reporte de `sampling_1` incluye la comparación a tiempo igual (ensamble de K semillas del brazo contra el
  control) con el K usado

#### Scenario: Hipótesis nueva en `sampling_1`
- **WHEN** se registra un experimento nuevo con brazos (por ejemplo `h4`)
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
