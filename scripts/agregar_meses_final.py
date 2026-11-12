"""Agrega la columna `meses_final` a los ledgers (cambio final-con-julio-agosto, D4).

Recorre los CSV de ledger bajo una raíz que tienen el esquema de corridas (cabecera con `etapa_corrida`: `corridas/*.csv`,
`exploracion/corridas/*.csv`, `resultados.csv`, `estudios.csv`, `reemplazadas.csv`; se saltea `sesiones/`) y, justo
después de `estudio`, agrega `meses_final`: `201903-201906` en las filas de `etapa_corrida = final` (todos los finales
previos al cambio) y vacío en el resto. Las demás columnas no cambian.

    python scripts/agregar_meses_final.py --aplicar experimentos --respaldo $DATOS_DIR/meses_final/original/repo
    python scripts/agregar_meses_final.py --aplicar $DATOS_DIR/meses_final/bucket --respaldo $DATOS_DIR/meses_final/original/bucket
    python scripts/agregar_meses_final.py --verificar experimentos --contra $DATOS_DIR/meses_final/original/repo

`--aplicar` copia cada archivo original a `--respaldo` (misma ruta relativa) antes de tocarlo y no toca los que ya tienen
la columna. `--verificar` compara cada archivo del respaldo con el de la raíz y sale con 0 solo si: al sacarle
`meses_final`, cada archivo queda idéntico al original byte a byte (el resto no cambió); los finales viejos tienen
`201903-201906` y el resto vacío; y ningún archivo con el esquema de corridas carece de la columna.
"""
import argparse
import csv
import io
import shutil
import sys
from pathlib import Path

COLUMNA = "meses_final"
DESPUES_DE = "estudio"
VENTANA_VIEJA = "201903-201906"


def es_de_corridas(rel: Path) -> bool:
    return "ledger" in rel.parts and "sesiones" not in rel.parts and rel.suffix == ".csv"


def _filas(datos: bytes) -> list[list[str]]:
    return list(csv.reader(io.StringIO(datos.decode("utf-8"), newline="")))


def _a_bytes(filas: list[list[str]]) -> bytes:
    sal = io.StringIO(newline="")
    csv.writer(sal, lineterminator="\n").writerows(filas)
    return sal.getvalue().encode("utf-8")


def tiene_esquema(datos: bytes) -> bool:
    cab = datos.split(b"\n", 1)[0].decode("utf-8").rstrip("\r").split(",")
    return "etapa_corrida" in cab and DESPUES_DE in cab


def archivos(raiz: Path) -> list[Path]:
    out = []
    for p in sorted(raiz.rglob("*.csv")):
        if p.is_file() and es_de_corridas(p.relative_to(raiz)) and tiene_esquema(p.read_bytes()):
            out.append(p)
    return out


def con_columna(datos: bytes) -> bytes | None:
    """El CSV con `meses_final`, o None si ya la tiene. Falla si reescribir sin tocar nada no reproduce el original."""
    filas = _filas(datos)
    cab = filas[0]
    if COLUMNA in cab:
        return None
    if _a_bytes(filas) != datos:
        raise ValueError("el CSV no se reproduce byte a byte al leerlo y escribirlo")
    i, j = cab.index(DESPUES_DE) + 1, cab.index("etapa_corrida")
    nuevas = [cab[:i] + [COLUMNA] + cab[i:]]
    for f in filas[1:]:
        nuevas.append(f[:i] + [VENTANA_VIEJA if f[j] == "final" else ""] + f[i:])
    return _a_bytes(nuevas)


def sin_columna(datos: bytes) -> tuple[bytes, list[tuple[str, str]]]:
    """El CSV sin `meses_final` y los pares (etapa_corrida, meses_final) de sus filas."""
    filas = _filas(datos)
    k, j = filas[0].index(COLUMNA), filas[0].index("etapa_corrida")
    pares = [(f[j], f[k]) for f in filas[1:]]
    return _a_bytes([f[:k] + f[k + 1:] for f in filas]), pares


def aplicar(raiz: Path, respaldo: Path) -> int:
    n = 0
    for p in archivos(raiz):
        nuevo = con_columna(p.read_bytes())
        if nuevo is None:
            continue
        destino = respaldo / p.relative_to(raiz)
        destino.parent.mkdir(parents=True, exist_ok=True)
        if not destino.exists():
            shutil.copy2(p, destino)
        p.write_bytes(nuevo)
        n += 1
    print(f"{n} archivos reescritos en {raiz}")
    return 0


def verificar(raiz: Path, contra: Path) -> int:
    errores = []
    originales = archivos(contra)
    for orig in originales:
        rel = orig.relative_to(contra)
        p = raiz / rel
        if not p.exists():
            errores.append(f"falta {rel}")
            continue
        datos = p.read_bytes()
        if COLUMNA not in datos.split(b"\n", 1)[0].decode("utf-8").split(","):
            errores.append(f"sin {COLUMNA}: {rel}")
            continue
        resto, pares = sin_columna(datos)
        if resto != orig.read_bytes():
            errores.append(f"el resto del archivo cambió: {rel}")
        if any(v != (VENTANA_VIEJA if e == "final" else "") for e, v in pares):
            errores.append(f"{COLUMNA} distinto de {VENTANA_VIEJA} en los finales o no vacío en el resto: {rel}")
    for p in archivos(raiz):
        if p.relative_to(raiz) not in {o.relative_to(contra) for o in originales}:
            errores.append(f"no está en el respaldo: {p.relative_to(raiz)}")
    for e in errores[:50]:
        print(e)
    print(f"{len(originales)} archivos comparados, {len(errores)} errores")
    return 1 if errores else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--aplicar", type=Path, metavar="RAIZ")
    g.add_argument("--verificar", type=Path, metavar="RAIZ")
    ap.add_argument("--respaldo", type=Path)
    ap.add_argument("--contra", type=Path)
    a = ap.parse_args()
    if a.aplicar:
        if not a.respaldo:
            ap.error("--aplicar necesita --respaldo")
        return aplicar(a.aplicar, a.respaldo)
    if not a.contra:
        ap.error("--verificar necesita --contra")
    return verificar(a.verificar, a.contra)


if __name__ == "__main__":
    sys.exit(main())
