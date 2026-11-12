# Spec Delta

## Purpose

Define el sitio público que reúne los documentos del repo (conclusión, evidencia, método y proceso) para que el grupo y
el tutor lean el experimento navegando desde una sola dirección, sin clonar el repo.

## ADDED Requirements

### Requirement: Publicación automática desde main
El sitio SHALL construirse y publicarse en GitHub Pages en cada push a `main`, a partir de lo commiteado, sin pasos
manuales después del push. Si el build falla, SHALL quedar publicada la versión anterior.

#### Scenario: Push con un informe editado
- **WHEN** se commitea un cambio en `experimentos/h3/informe/informe.md` y se pushea a `main`
- **THEN** al terminar el workflow la página del informe de h3 en el sitio muestra el cambio

#### Scenario: Build roto
- **WHEN** el build del sitio falla
- **THEN** el workflow termina en error y el sitio sigue mostrando la última versión publicada

### Requirement: Contenido publicado
El sitio SHALL publicar como páginas, por cada experimento, su informe, su reporte, su hipótesis, su diseño y su
bitácora, además de `docs/metodo.md`, `docs/revision.md`, las specs vigentes de `openspec/specs/` y los documentos
enlazados desde los informes. El sitio SHALL NOT publicar código, tests, scripts, la plantilla, la configuración de
Claude ni los cambios de OpenSpec.

#### Scenario: Documento de un experimento
- **WHEN** se abre en el sitio la hipótesis de h4
- **THEN** se ve `experimentos/h4/docs/hipotesis.md` como página, con sus tablas renderizadas

#### Scenario: Código excluido
- **WHEN** se pide en el sitio la ruta de `comun/reporte.py` o de un archivo de `openspec/changes/`
- **THEN** el sitio responde que la página no existe

### Requirement: Navegación por secciones
El sitio SHALL tener una barra lateral con secciones en este orden: Resultados (informe conjunto, reporte conjunto,
tabla de resultados, decisiones, guion), Experimentos (control, h1 a h4, cada uno con informe, reporte, hipótesis y
diseño, y los exploratorios), Método, Proceso (bitácoras) y Especificaciones. El sitio SHALL tener búsqueda de texto completo sobre todas
las páginas.

#### Scenario: Llegar a una bitácora
- **WHEN** alguien busca la bitácora de h3
- **THEN** la encuentra en la sección Proceso de la barra lateral, no entre los resultados

#### Scenario: Buscar un término
- **WHEN** se busca «GOSS» en el sitio
- **THEN** la búsqueda devuelve las páginas de H2 que lo mencionan

### Requirement: Portada orientada a la conclusión
La página de inicio SHALL presentar el experimento (pregunta del tutor, integrantes, comisión) y llevar primero al
informe conjunto de `sampling_1`, y después a los reportes, las hipótesis y el método.

#### Scenario: Primera visita del tutor
- **WHEN** el tutor abre la dirección del sitio
- **THEN** ve la pregunta, un enlace destacado al informe conjunto y la barra lateral con el resto

### Requirement: Enlaces relativos conservados
Las páginas SHALL estar en la misma ruta que el archivo del repo, de modo que un enlace relativo entre documentos que
funciona en github.com funcione también en el sitio, sin reescribir los documentos.

#### Scenario: Del informe al reporte
- **WHEN** en el informe de h1 se sigue el enlace `reporte.html`
- **THEN** se abre la página del reporte de h1 dentro del sitio

#### Scenario: Enlace entre Markdown
- **WHEN** en el informe conjunto se sigue el enlace `../../h3/docs/diseno.md`
- **THEN** se abre la página del diseño de h3 en el sitio

### Requirement: Enlaces internos verificados
El build SHALL fallar si alguna página publicada tiene un enlace interno o una imagen que no resuelve dentro del sitio.
Los enlaces externos SHALL NOT hacer fallar el build.

#### Scenario: Enlace a un documento borrado
- **WHEN** un informe enlaza a un `.md` que ya no existe
- **THEN** el build falla nombrando la página y el enlace roto, y no se publica

#### Scenario: Enlace externo caído
- **WHEN** un enlace a Zulip o a un sitio externo no responde
- **THEN** el build pasa igual

### Requirement: Vista previa local
El sitio SHALL poder construirse y verse localmente con un solo comando documentado, con el mismo contenido y la misma
verificación de enlaces que el build publicado.

#### Scenario: Revisar antes de pushear
- **WHEN** Agustina corre el comando documentado en el README
- **THEN** el sitio queda servido en `localhost` y la verificación de enlaces informa lo mismo que en CI
