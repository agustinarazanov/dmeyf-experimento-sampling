"""Comprueba que los números del README, de `index.md` y de `experimentos/sampling_1/README.md` escritos a mano salen del
bloque `bloque-a-completo` de `experimentos/sampling_1/anexo.md` o del título de una figura generada, y que sus enlaces
existen (cambio `renombrar-brazos`, tarea 4.1; `inicio-y-resultados` D2). Sale con 1 si algo no coincide.

    python -m scripts.verificar_readme

- Números del texto (fuera de los bloques generados, de bloques de código, de `código` y de destinos de enlaces, y sin contar los pegados a letras,
  como `H3` o `h4`): cada uno, leído con coma decimal y punto de miles, tiene que estar en el bloque con los mismos
  decimales. Las excepciones son identificadores que no son resultados y están en `NO_RESULTADOS`.
- Enlaces relativos `[texto](ruta)`: la ruta (sin `#ancla`, con `%20` como espacio) tiene que existir.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

RAIZ = Path(__file__).resolve().parent.parent
README = RAIZ / "README.md"
TABLA = RAIZ / "experimentos/sampling_1/anexo.md"
PAGINAS = ("index.md", "experimentos/sampling_1/README.md")  # además del README raíz (D2)
BLOQUE = "bloque-a-completo"

# año del curso y de los datos, mensaje de Zulip, versión de Python, fases de las VMs, pasos 07 y 08 de Martín y las 50
# semillas de la pregunta de Luis; desde `final-con-julio-agosto` 4.2, el mensaje de Zulip de la ventana del final y los
# meses de las ventanas (la de la ronda anterior y la corrida que queda como duda)
NO_RESULTADOS = {"2026", "2019", "208986", "3,14", "1", "4", "5", "07", "08", "50", "211210", "201905", "201906"}
# Resultados (sampling_1/README.md): años y volumen de la bibliografía, mensajes de Zulip y los 40 trials. Además, dos razones
# de ancho de IC (0,96 y 1,44) que el texto viejo calcula a mano; las reescribe la tarea 2.1 y se retiran de acá entonces.
NO_RESULTADOS |= {"2002", "2011", "2017", "208135", "211718", "38", "40", "0,96", "1,44"}
# Desde `tiempos-confiables-y-consistencia` 4.2: el mensaje de Zulip de la pregunta de § Diálogo entre H1 y H4.
NO_RESULTADOS |= {"212124"}

NUM_TABLA = re.compile(r"\d[\d,]*(?:\.\d+)?")
NUM_TEXTO = re.compile(r"(?<![\w.,@−-])[−-]?\d+(?:\.\d{3})*(?:,\d+)?(?![\w@])")
ENLACE = re.compile(r"\]\(([^)\s]+)\)")


def leer_bloque(texto: str, nombre: str) -> str:
    """Lo que hay entre `<!-- generado:nombre -->` y `<!-- /generado:nombre -->`; vacío si falta el bloque."""
    m = re.search(rf"<!-- generado:{re.escape(nombre)} -->(.*?)<!-- /generado:{re.escape(nombre)} -->", texto, re.S)
    return m.group(1) if m else ""


RESPUESTA = re.compile(r'^!!! success "Respuesta"\n((?:(?: {4}.*)?\n)+)', re.M)


def cuerpo_respuesta(texto: str) -> str | None:
    """El cuerpo del recuadro `!!! success "Respuesta"` (líneas con sangría de 4, sin la sangría); None si no hay recuadro."""
    m = RESPUESTA.search(texto)
    if not m:
        return None
    return " ".join(linea.strip() for linea in m.group(1).splitlines() if linea.strip())


GENERADO = re.compile(r"<!-- generado:([\w-]+) -->.*?<!-- /generado:\1 -->", re.S)
TITULO_FIGURA = re.compile(r"!\[([^\]]*)\]\(")


def _texto(readme: str) -> str:
    """El README sin bloques generados, sin bloques de código, sin `código` y sin destinos de enlaces."""
    salida, codigo = [], False
    readme = GENERADO.sub("", readme)
    for linea in readme.splitlines():
        if linea.startswith("```"):
            codigo = not codigo
            continue
        if not codigo:
            salida.append(re.sub(r"\]\([^)]*\)", "]", re.sub(r"`[^`]*`", " ", linea)))
    return "\n".join(salida)


def _en_tabla(token: str, tabla: set[float]) -> bool:
    t = token.replace("−", "").replace("-", "").replace(".", "").replace(",", ".")
    d = len(t.split(".")[1]) if "." in t else 0
    return any(round(v, d) == float(t) for v in tabla)


def main() -> int:
    readme = README.read_text()
    bloque = leer_bloque(TABLA.read_text(), BLOQUE) if TABLA.exists() else ""
    if not bloque.strip():
        print(f"✗ no hay bloque `{BLOQUE}` en {TABLA.relative_to(RAIZ)}")
        return 1
    errores: list[str] = []
    paginas = [(README.relative_to(RAIZ).as_posix() if README.is_relative_to(RAIZ) else README.name, readme)]
    paginas += [(p, (RAIZ / p).read_text()) for p in PAGINAS if (RAIZ / p).is_file()]
    titulos = " ".join(t for _, texto in paginas for t in TITULO_FIGURA.findall(texto))
    rondas = leer_bloque(TABLA.read_text(), "rondas")  # δ de cada ronda
    # filas de cada lado de los pares de § Diálogo entre H1 y H4 (`tiempos-confiables-y-consistencia` 6.5)
    diferencias = leer_bloque(TABLA.read_text(), "diferencias")
    tabla = {float(x.replace(",", "")) for x in NUM_TABLA.findall(" ".join((bloque, titulos, rondas, diferencias)))}

    numeros, enlaces = set(), []
    for nombre, texto in paginas:
        for n in sorted(set(NUM_TEXTO.findall(_texto(texto)))):
            numeros.add(n)
            if n not in NO_RESULTADOS and not _en_tabla(n, tabla):
                errores.append(f"{nombre}: número del texto que no está en `bloque-a-completo` ni en un título de figura: {n}")
        base = (RAIZ / nombre).parent if nombre != README.name else RAIZ
        for e in ENLACE.findall(GENERADO.sub("", texto)):
            if re.match(r"[a-z]+://", e) or e.startswith("#"):
                continue
            enlaces.append(e)
            ruta = unquote(e.split("#", 1)[0])
            if ruta and not (base / ruta).exists():
                errores.append(f"{nombre}: enlace roto: {e}")

    # la respuesta de la portada es la de Resultados, palabra por palabra (`informe-por-ejes` 6.2)
    textos = {p: t for p, t in paginas if p in PAGINAS}
    if len(textos) == len(PAGINAS):
        cuerpos = {p: cuerpo_respuesta(t) for p, t in textos.items()}
        for p, c in cuerpos.items():
            if c is None:
                errores.append(f"{p}: falta el recuadro `!!! success \"Respuesta\"`")
        if None not in cuerpos.values() and len(set(cuerpos.values())) > 1:
            errores.append('el recuadro "Respuesta" de index.md y el de Resultados no son el mismo texto')

    print(f"{len(numeros)} números del texto, {len(enlaces)} enlaces")
    for err in errores:
        print("✗", err)
    if not errores:
        print("✓ todos los números están en el bloque bloque-a-completo y todos los enlaces existen")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
