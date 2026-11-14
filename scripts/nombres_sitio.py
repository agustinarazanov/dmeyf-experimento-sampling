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


def main() -> int:
    hallazgos = buscar()
    if hallazgos:
        print("Nombres de personas en páginas publicadas (redacción impersonal, sitio-legible D8):", file=sys.stderr)
        print("\n".join(hallazgos), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
