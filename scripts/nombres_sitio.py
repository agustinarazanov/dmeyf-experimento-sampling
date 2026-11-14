"""Busca nombres de personas en lo que se publica (sitio-legible D8).

Revisa las páginas del `nav` de mkdocs.yml y el README raíz, sin distinguir mayúsculas. Si encuentra algo que no
está en EXCEPCIONES, imprime archivo:línea y sale con 1. Lo corre scripts/sitio.sh antes del build.

uso:  python scripts/nombres_sitio.py
"""

import re
import sys
from pathlib import Path

import yaml

RAIZ = Path(__file__).resolve().parent.parent
PROHIBIDOS = re.compile(r"tutor|bolaños|aramend|agustina|martín|luis|laguinge|razanov|lópez|autor", re.IGNORECASE)
# Las direcciones del repo y del sitio llevan el usuario de GitHub; los enlaces a archivos no publicados tienen que ir
# ahí (sitio-informes § Enlaces internos verificados), así que se quitan antes de buscar.
URLS_DEL_REPO = re.compile(r"https://(github\.com/agustinarazanov|agustinarazanov\.github\.io)/dmeyf-experimento-sampling\S*")

# (archivo, línea): motivo. Cada excepción lleva motivo; una línea que se mueve deja de estar exceptuada y vuelve a
# fallar, a propósito.
EXCEPCIONES: dict[tuple[str, int], str] = {}


class _Cargador(yaml.SafeLoader):
    """SafeLoader que ignora las etiquetas de Python de mkdocs.yml (`!!python/name:`)."""


_Cargador.add_multi_constructor("tag:yaml.org,2002:python/", lambda cargador, sufijo, nodo: None)


def _rutas_nav(nav) -> list[str]:
    rutas = []
    for item in nav:
        valor = next(iter(item.values())) if isinstance(item, dict) else item
        if isinstance(valor, list):
            rutas += _rutas_nav(valor)
        elif isinstance(valor, str) and not re.match(r"https?://", valor):
            rutas.append(valor)
    return rutas


def paginas_publicadas() -> list[str]:
    config = yaml.load((RAIZ / "mkdocs.yml").read_text(encoding="utf-8"), Loader=_Cargador)
    return _rutas_nav(config["nav"]) + ["README.md"]


def buscar() -> list[str]:
    hallazgos = []
    for ruta in paginas_publicadas():
        for n, linea in enumerate((RAIZ / ruta).read_text(encoding="utf-8").splitlines(), start=1):
            m = PROHIBIDOS.search(URLS_DEL_REPO.sub("", linea))
            if m and (ruta, n) not in EXCEPCIONES:
                hallazgos.append(f"{ruta}:{n}: «{m.group(0)}»: {linea.strip()[:120]}")
    return hallazgos


# Títulos de proceso (informe-por-ejes D7): cuentan cómo se llegó al informe en lugar de qué dice. Se aceptan solo en
# `## Predicción`, que es pre-registro y no se reescribe.
TITULO = re.compile(r"^#{1,4} (.*)$")
PROCESO = re.compile(r"cambio|\b\d{1,2}-[a-z]{3}\b|\d{4}-\d{2}-\d{2}|zulip", re.IGNORECASE)


def cambios_archivados() -> list[str]:
    """Nombres de los cambios de openspec/changes/archive, sin el prefijo de fecha."""
    carpeta = RAIZ / "openspec" / "changes" / "archive"
    return sorted(re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.name) for p in carpeta.iterdir() if p.is_dir()) if carpeta.is_dir() else []


def titulos_de_proceso(texto: str, archivados: list[str] | None = None) -> list[tuple[int, str, str]]:
    """(línea, título, motivo) de los títulos `#`–`####` de proceso fuera de `## Predicción` (hasta el siguiente `## `)."""
    archivados = cambios_archivados() if archivados is None else archivados
    hallazgos = []
    en_prediccion = False
    en_codigo = False
    for n, linea in enumerate(texto.splitlines(), start=1):
        if linea.lstrip().startswith("```"):
            en_codigo = not en_codigo
        m = None if en_codigo else TITULO.match(linea)
        if not m:
            continue
        titulo = m.group(1)
        if linea.startswith("## "):
            en_prediccion = titulo.strip().lower() == "predicción"
        if en_prediccion:
            continue
        p = PROCESO.search(titulo)
        if p:
            hallazgos.append((n, titulo, f"«{p.group(0)}»"))
            continue
        nombre = next((a for a in archivados if a in titulo), None)
        if nombre:
            hallazgos.append((n, titulo, f"cambio archivado «{nombre}»"))
    return hallazgos


def buscar_titulos() -> list[str]:
    archivados = cambios_archivados()
    return [
        f"{ruta}:{n}: título de proceso {motivo}: {titulo[:100]}"
        for ruta in paginas_publicadas()
        for n, titulo, motivo in titulos_de_proceso((RAIZ / ruta).read_text(encoding="utf-8"), archivados)
    ]


def main() -> int:
    hallazgos = buscar()
    if hallazgos:
        print("Nombres de personas en páginas publicadas (redacción impersonal, sitio-legible D8):", file=sys.stderr)
        print("\n".join(hallazgos), file=sys.stderr)
        return 1
    titulos = buscar_titulos()
    if titulos:
        print("Títulos de proceso fuera de ## Predicción (informe-por-ejes D7): el título dice qué hay, no cómo se llegó:", file=sys.stderr)
        print("\n".join(titulos), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
