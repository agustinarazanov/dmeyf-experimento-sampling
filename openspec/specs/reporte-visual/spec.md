# reporte-visual Specification

## Purpose
Define el reporte visual del experimento: una página regenerable desde el ledger que explica qué se está probando y
compara todos los resultados en un solo lugar, para el grupo, el tutor y el video.

## Requirements

### Requirement: Reporte regenerable desde el ledger
El experimento SHALL tener un comando que genere `informe/reporte.html` a partir de `ledger/resultados.csv`,
`ledger/apareado.csv`, las curvas guardadas y `docs/hipotesis.md`, sin números escritos a mano, y que pueda correrse en
cualquier momento con los resultados que haya.

#### Scenario: Regenerar con resultados parciales
- **WHEN** se genera el reporte y a un brazo le faltan semillas o no tiene corridas
- **THEN** el brazo aparece como pendiente con lo que tiene, y ninguna sección falla ni muestra un número inventado

#### Scenario: Regenerar dos veces
- **WHEN** se genera el reporte dos veces sin corridas nuevas
- **THEN** el archivo resultante es el mismo salvo la fecha de generación

### Requirement: Introducción tomada de los documentos
El reporte SHALL abrir con una introducción que explique la pregunta, las hipótesis, el control y la regla de decisión,
tomada de `docs/hipotesis.md` y `docs/diseno.md`, de modo que quien no conoce el experimento entienda qué se mide antes
de ver un número.

#### Scenario: Cambia una hipótesis
- **WHEN** se edita `docs/hipotesis.md` y se regenera el reporte
- **THEN** la introducción refleja el cambio sin tocar el generador

### Requirement: Comparación de todos los brazos en una vista
El reporte SHALL mostrar una tabla con todos los brazos contra el control (ganancia media, diferencia apareada con su
intervalo, tiempo, aceleración, veredicto) y un gráfico de tiempo contra ganancia con un punto por brazo y el control
marcado, más una sección por hipótesis con las curvas de ganancia (banda entre semillas) de sus brazos junto al control.

#### Scenario: Leer el veredicto de una hipótesis
- **WHEN** se abre la sección de una hipótesis
- **THEN** se ve su predicción, la regla, el resultado de cada brazo y el veredicto (no pierde, pierde, indeterminado,
  pendiente), con la tabla y la figura que lo sostienen

#### Scenario: Comparación a tiempo igual
- **WHEN** el control y al menos un brazo tienen sus 10 semillas
- **THEN** el reporte incluye la comparación a tiempo igual (ensamble de K semillas del brazo contra el control) con el
  K usado

### Requirement: Legible sin servidor y compartible
El reporte SHALL ser un único archivo HTML con las figuras embebidas, que se abre desde el repo sin servidor ni
dependencias, y SHALL poder publicarse tal cual para el tutor y el grupo.

#### Scenario: Abrir desde un clon limpio
- **WHEN** alguien clona el repo y abre `informe/reporte.html`
- **THEN** ve el reporte completo con sus figuras, sin instalar nada
