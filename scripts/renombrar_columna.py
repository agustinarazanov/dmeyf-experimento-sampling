"""Renombre de la columna `brazo` a `variante` en los ledgers (cambio renombrar-brazos, D2).

Recorre los archivos de ledger bajo una raíz (los CSV con cabecera `brazo` y los `hp/*.json` con clave `brazo`; se
saltea `sesiones/`) y reescribe solo esa cabecera o clave. Registro de la migración; no se usa más después.

    python scripts/renombrar_columna.py --aplicar experimentos --respaldo $DATOS_DIR/renombre/original/repo
    python scripts/renombrar_columna.py --aplicar $DATOS_DIR/renombre/bucket --respaldo $DATOS_DIR/renombre/original/bucket
    python scripts/renombrar_columna.py --verificar experimentos --contra $DATOS_DIR/renombre/original/repo

`--aplicar` copia cada archivo original a `--respaldo` (misma ruta relativa) antes de tocarlo. `--verificar` compara cada
archivo del respaldo con el de la raíz y sale con 0 solo si: las líneas 2..n del CSV son idénticas byte a byte, la
cabecera difiere solo en `brazo` -> `variante`, el resto del JSON es igual, y ningún archivo conserva `brazo`.
"""
import argparse
import json
import re
import shutil
import sys
from pathlib import Path

VIEJO, NUEVO = "brazo", "variante"
CLAVE_JSON = re.compile(rf'^(\s*)"{VIEJO}"(\s*:)', re.M)


def es_de_ledger(rel: Path) -> bool:
    p = rel.parts
    return "ledger" in p and "sesiones" not in p and (rel.suffix == ".csv" or (rel.suffix == ".json" and "hp" in p))


def archivos(raiz: Path):
    return sorted(p for p in raiz.rglob("*") if p.is_file() and es_de_ledger(p.relative_to(raiz)))


def cabecera_csv(datos: bytes) -> tuple[bytes, bytes]:
    i = datos.find(b"\n")
    return (datos, b"") if i < 0 else (datos[: i + 1], datos[i + 1:])


def reescribir_csv(datos: bytes) -> bytes | None:
    cab, resto = cabecera_csv(datos)
    fin = cab[len(cab.rstrip(b"\r\n")):]
    celdas = cab.rstrip(b"\r\n").decode("utf-8").split(",")
    if VIEJO not in celdas:
        return None
    celdas[celdas.index(VIEJO)] = NUEVO
    return ",".join(celdas).encode("utf-8") + fin + resto


def reescribir_json(datos: bytes) -> bytes | None:
    texto = datos.decode("utf-8")
    if len(CLAVE_JSON.findall(texto)) != 1:
        if CLAVE_JSON.search(texto):
            sys.exit("más de una clave 'brazo' en un JSON")
        return None
    return CLAVE_JSON.sub(rf'\1"{NUEVO}"\2', texto, count=1).encode("utf-8")


def aplicar(raiz: Path, respaldo: Path) -> int:
    n = 0
    for p in archivos(raiz):
        datos = p.read_bytes()
        nuevo = reescribir_json(datos) if p.suffix == ".json" else reescribir_csv(datos)
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


def renombrar_claves(obj):
    return {(NUEVO if k == VIEJO else k): v for k, v in obj.items()}


def verificar(raiz: Path, contra: Path) -> int:
    errores = []
    for orig in archivos(contra):
        rel = orig.relative_to(contra)
        p = raiz / rel
        if not p.exists():
            errores.append(f"falta {rel}")
            continue
        a, b = orig.read_bytes(), p.read_bytes()
        if p.suffix == ".json":
            ja, jb = json.loads(a), json.loads(b)
            if list(renombrar_claves(ja).items()) != list(jb.items()):
                errores.append(f"JSON distinto: {rel}")
            continue
        ca, ra = cabecera_csv(a)
        cb, rb = cabecera_csv(b)
        if ra != rb:
            errores.append(f"líneas 2..n distintas: {rel}")
        if ca.replace(VIEJO.encode(), NUEVO.encode(), 1) != cb:
            errores.append(f"cabecera distinta de brazo->variante: {rel}")
    for p in archivos(raiz):
        rel = p.relative_to(raiz)
        datos = p.read_bytes()
        viejo = reescribir_json(datos) if p.suffix == ".json" else reescribir_csv(datos)
        if viejo is not None:
            errores.append(f"conserva '{VIEJO}': {rel}")
    for e in errores[:50]:
        print(e)
    print(f"{len(archivos(contra))} archivos comparados, {len(errores)} errores")
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
