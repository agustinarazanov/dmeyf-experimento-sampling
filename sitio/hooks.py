"""Hooks de MkDocs para el sitio.

MkDocs informa como INFO un enlace relativo a un archivo excluido (bitácora, spec, código), así que
`mkdocs build --strict` no falla. Ese enlace tiene que ir a GitHub (sitio-informes § Enlaces internos
verificados), así que acá se sube a WARNING y `--strict` lo cuenta.
"""

import logging

_MENSAJE = "which is excluded from the built site"


class _EnlaceExcluido(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if record.levelno < logging.WARNING and _MENSAJE in record.getMessage():
            record.levelno, record.levelname = logging.WARNING, "WARNING"
            record.msg = f"{record.getMessage()} Enlazarlo como URL de GitHub."
            record.args = None
        return True


def on_config(config):
    logger = logging.getLogger("mkdocs.structure.pages")
    if not any(isinstance(f, _EnlaceExcluido) for f in logger.filters):
        logger.addFilter(_EnlaceExcluido())
    return config


_NOMBRE = "Sampling_1 · DMEyF 2026"
_PARTIDO = '<span class="md-ellipsis">\n            Sampling_1<span class="sitio-anio"> · DMEyF 2026</span>\n          </span>'


def on_post_page(output, page, config):
    """Parte el nombre del sitio en el encabezado para que en el teléfono «DMEyF 2026» baje a una segunda línea
    (estilos.css). Es lo que haría un override de partials/header.html, sin copiar la plantilla del tema."""
    marca = f'<span class="md-ellipsis">\n            {_NOMBRE}\n          </span>'
    return output.replace(marca, _PARTIDO, 1)
