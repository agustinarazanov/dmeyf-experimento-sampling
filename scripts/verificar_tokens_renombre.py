"""Tarea 1.2 de renombrar-brazos: `comun/tokens.py` no depende de "brazo" en `ledger/sesiones/` ni en las bitácoras.

Copia `experimentos/*/docs/bitacora.md` y `experimentos/*/ledger/sesiones/` a `DATOS_DIR/renombre/tokens/`, regenera
cada `tokens.csv` en la copia (A), reemplaza brazo -> variante (conservando mayúsculas) y vuelve a regenerar (B). Sale con
0 si A y B son idénticos. Se compara copia contra copia (no contra el `tokens.csv` del repo) porque la sesión en curso
sigue creciendo entre una corrida y otra.
"""
import filecmp
import re
import shutil
import sys
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(raiz))
from comun import baseline as bl  # noqa: E402
from comun import tokens  # noqa: E402


def variante(m: re.Match) -> str:
    s = m.group(0)
    nuevo = "variante" + s[5:]
    return nuevo.upper() if s.isupper() else (nuevo[0].upper() + nuevo[1:] if s[0].isupper() else nuevo)


def regenerar(copia: Path, proyectos: Path, salida: Path) -> dict[str, int]:
    n = {}
    for e in tokens.experimentos_de(copia):
        n[e] = len(tokens.registrar(e, raiz=copia, proyectos=proyectos))
        destino = salida / f"{e}_tokens.csv"
        destino.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(copia / "experimentos" / e / "ledger" / "tokens.csv", destino)
    return n


def main() -> int:
    base = bl.DATOS_DIR / "renombre" / "tokens"
    shutil.rmtree(base, ignore_errors=True)
    copia = base / "repo"
    for e in tokens.experimentos_de(raiz):
        for rel in [Path("docs/bitacora.md"), Path("ledger/sesiones")]:
            origen = raiz / "experimentos" / e / rel
            if not origen.exists():
                continue
            destino = copia / "experimentos" / e / rel
            destino.parent.mkdir(parents=True, exist_ok=True)
            if origen.is_dir():
                shutil.copytree(origen, destino)
            else:
                shutil.copy(origen, destino)
    # los transcripts son los del repo real: la copia los ve por un enlace con el nombre de proyecto que le toca
    proyectos = base / "proyectos"
    proyectos.mkdir()
    real = tokens.PROYECTOS / re.sub(r"[^A-Za-z0-9]", "-", str(raiz))
    (proyectos / re.sub(r"[^A-Za-z0-9]", "-", str(copia))).symlink_to(real)
    for otro in tokens.PROYECTOS.iterdir():
        if otro != real and not (proyectos / otro.name).exists():
            (proyectos / otro.name).symlink_to(otro)

    a = regenerar(copia, proyectos, base / "A")
    cambiados = 0
    for f in copia.rglob("*"):
        if f.is_file() and f.name != "tokens.csv":
            try:
                t = f.read_text()
            except UnicodeDecodeError:
                continue
            nuevo = re.sub(r"(?<!renombrar-)brazo", variante, t, flags=re.I)  # D8: el nombre del cambio queda
            if nuevo != t:
                f.write_text(nuevo)
                cambiados += 1
    print(f"archivos de la copia con 'brazo' reemplazado: {cambiados}")
    b = regenerar(copia, proyectos, base / "B")
    dif = 0
    for e in a:
        igual = filecmp.cmp(base / "A" / f"{e}_tokens.csv", base / "B" / f"{e}_tokens.csv", shallow=False)
        print(f"{e}: {a[e]} filas antes, {b[e]} después, {'idéntico' if igual else 'DIFERENTE'}")
        dif += not igual
    return 1 if dif else 0


if __name__ == "__main__":
    sys.exit(main())
