# Spec Delta

## RENAMED Requirements

- FROM: `### Requirement: Legible sin servidor y compartible`
- TO: `### Requirement: Página del sitio, compartible`

## MODIFIED Requirements

### Requirement: Página del sitio, compartible
El reporte SHALL ser una página del sitio de informes: un único archivo con encabezado YAML y cuerpo HTML, con las
figuras embebidas y sin dependencias fuera del sitio, que toma la barra lateral, la búsqueda y los estilos del sitio.
Los colores de veredicto (no pierde, pierde, indeterminado) SHALL verse igual que antes. El reporte SHALL NOT llevar
`<html>`, `<head>` ni estilos propios.

#### Scenario: Abrir desde el sitio
- **WHEN** alguien abre el reporte de `sampling_1` en el sitio publicado
- **THEN** ve el reporte completo con sus figuras, la barra lateral del sitio y las celdas de veredicto coloreadas

#### Scenario: Abrir desde un clon limpio
- **WHEN** alguien clona el repo y quiere ver `informe/reporte.html`
- **THEN** lo ve completo con sus figuras usando la vista previa local del sitio, sin instalar nada fuera de lo que pide
  el README

#### Scenario: Mismos números después del cambio de formato
- **WHEN** se regeneran los reportes con el formato de página del sitio
- **THEN** cada tabla de cada `reporte.html` coincide celda por celda con la del reporte anterior al cambio
