"""Foto de D6 (cambio renombrar-brazos): copia cada `apareado.csv` y la tabla de resultados de cada `reporte.html`
(extraída a CSV) a `DATOS_DIR/renombre/<antes|despues>/`.

    python scripts/foto_renombre.py antes
    python scripts/foto_renombre.py despues
"""
import csv
import shutil
import sys
from html.parser import HTMLParser
from pathlib import Path

raiz = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(raiz))
from comun import baseline as bl  # noqa: E402


class Tablas(HTMLParser):
    """Extrae cada <table> como lista de filas de texto (sin dependencias)."""

    def __init__(self) -> None:
        super().__init__()
        self.tablas: list[list[list[str]]] = []
        self._celda: list[str] | None = None

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.tablas.append([])
        elif tag == "tr" and self.tablas:
            self.tablas[-1].append([])
        elif tag in ("td", "th") and self.tablas and self.tablas[-1]:
            self._celda = []

    def handle_data(self, data):
        if self._celda is not None:
            self._celda.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._celda is not None:
            self.tablas[-1][-1].append(" ".join("".join(self._celda).split()))
            self._celda = None


def main() -> None:
    momento = sys.argv[1] if len(sys.argv) > 1 else "antes"
    dest = bl.DATOS_DIR / "renombre" / momento
    dest.mkdir(parents=True, exist_ok=True)
    for carpeta in sorted((raiz / "experimentos").iterdir()):
        if not (carpeta / "informe").is_dir() and not (carpeta / "ledger").is_dir():
            continue
        exp = carpeta.name
        ap = carpeta / "ledger" / "apareado.csv"
        if ap.exists():
            shutil.copy(ap, dest / f"{exp}_apareado.csv")
        html = carpeta / "informe" / "reporte.html"
        if html.exists():
            shutil.copy(html, dest / f"{exp}_reporte.html")
            p = Tablas()
            p.feed(html.read_text())
            for i, t in enumerate(p.tablas):
                with open(dest / f"{exp}_reporte_tabla{i}.csv", "w", newline="") as f:
                    csv.writer(f).writerows(t)
    print(dest)
    for f in sorted(dest.iterdir()):
        print(f"{f.name}\t{f.stat().st_size}")


if __name__ == "__main__":
    main()
