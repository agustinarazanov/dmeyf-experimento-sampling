"""Reparte el ledger de `sampling_1` entre los dueños de cada brazo (cambio `separar-hipotesis`, D4). Se corre una vez.

    python -m scripts.separar_ledger --origen experimentos/sampling_1/ledger            # separa
    python -m scripts.separar_ledger --origen experimentos/sampling_1/ledger --verificar  # comprueba contra el manifiesto

`resultados.csv`, `estudios.csv` y `reemplazadas.csv` se filtran por `brazo`; `hp/` va al dueño del estudio; `corridas/`,
`curvas/` y `predicciones/` van por el prefijo del `id` (el nombre del brazo). Se mueve, no se copia: una sola fuente de
verdad. Lo que no tiene brazo (`exploracion/`, `sesiones/`, `tokens.csv`, `apareado*.csv`) queda en el origen.
Antes de mover se escribe `separacion_manifiesto.json` en el origen con los `id` y los archivos de cada tabla; `--verificar`
comprueba que ningún `id` ni archivo se perdió ni se duplicó. Queda en el repo como registro de cómo se hizo.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

import pandas as pd

from comun import brazos, rutas

TABLAS = ("resultados", "estudios", "reemplazadas")
CARPETAS = ("corridas", "curvas", "predicciones")  # por prefijo del id
MANIFIESTO = "separacion_manifiesto.json"


def _brazo_de_archivo(nombre: str) -> str:
    """El brazo es lo que va antes del primer `_` del nombre (los ids son `<brazo>_<método>_<tasa>_...`)."""
    return nombre.split("_", 1)[0]


def _ids(tabla: pd.DataFrame) -> list[str]:
    return sorted(tabla["id"])


def leer_origen(origen: Path) -> dict:
    """Todo lo que hay que repartir, antes de mover nada: tablas, hp y archivos por carpeta."""
    out: dict = {"tablas": {}, "hp": [], "archivos": {}}
    for t in TABLAS:
        f = origen / f"{t}.csv"
        if f.exists():
            out["tablas"][t] = pd.read_csv(f, dtype=str, keep_default_na=False)
    hp = origen / "hp"
    out["hp"] = sorted(p.name for p in hp.glob("*.json")) if hp.is_dir() else []
    for c in CARPETAS:
        d = origen / c
        out["archivos"][c] = sorted(p.name for p in d.iterdir() if p.is_file()) if d.is_dir() else []
    return out


def planificar(datos: dict) -> dict:
    """Reparto: `{dueño: {tabla: DataFrame, 'hp': [archivos], carpeta: [archivos]}}`. Un brazo o estudio que no está en el
    registro falla nombrándolo (`comun/brazos.py`)."""
    plan: dict[str, dict] = {}

    def de(exp: str) -> dict:
        return plan.setdefault(exp, {**{t: None for t in TABLAS}, "hp": [], **{c: [] for c in CARPETAS}})

    for t, tabla in datos["tablas"].items():
        duenos = tabla["brazo"].map(brazos.dueno_brazo)
        for exp, parte in tabla.groupby(duenos, sort=True):
            de(exp)[t] = parte.reset_index(drop=True)
    for nombre in datos["hp"]:
        de(brazos.dueno_estudio(Path(nombre).stem))["hp"].append(nombre)
    for c, nombres in datos["archivos"].items():
        for nombre in nombres:
            de(brazos.dueno_brazo(_brazo_de_archivo(nombre)))[c].append(nombre)
    return plan


def conservacion(datos: dict, plan: dict) -> list[str]:
    """Problemas de conservación: `id` o archivo que se pierde o se duplica entre el origen y el reparto."""
    problemas: list[str] = []
    for t, tabla in datos["tablas"].items():
        repartidos = [i for p in plan.values() if p[t] is not None for i in _ids(p[t])]
        if sorted(repartidos) != _ids(tabla):
            problemas.append(f"{t}.csv: los id repartidos no son los del origen "
                             f"({len(repartidos)} repartidos, {len(tabla)} en el origen)")
        if len(set(repartidos)) != len(repartidos):
            problemas.append(f"{t}.csv: hay id duplicados en el reparto")
    for clave, origen in [("hp", datos["hp"]), *datos["archivos"].items()]:
        repartidos = sorted(n for p in plan.values() for n in p[clave])
        if repartidos != sorted(origen):
            problemas.append(f"{clave}/: los archivos repartidos no son los del origen")
        if len(set(repartidos)) != len(repartidos):
            problemas.append(f"{clave}/: hay archivos duplicados en el reparto")
    return problemas


def manifiesto(datos: dict, plan: dict) -> dict:
    return {
        "tablas": {t: _ids(tabla) for t, tabla in datos["tablas"].items()},
        "hp": datos["hp"],
        "archivos": datos["archivos"],
        "destino": {exp: {"tablas": {t: _ids(p[t]) for t in TABLAS if p[t] is not None},
                          "hp": p["hp"], **{c: p[c] for c in CARPETAS}} for exp, p in plan.items()},
    }


def separar(origen: Path, raiz: Path | None = None) -> dict:
    """Mueve todo a `<raiz>/experimentos/<dueño>/ledger/` (por defecto, el de `comun/rutas.py`). Falla sin mover nada si
    la conservación no cierra. Devuelve el manifiesto."""
    destino = (lambda e: raiz / "experimentos" / e / "ledger") if raiz else rutas.ledger
    datos = leer_origen(origen)
    plan = planificar(datos)
    problemas = conservacion(datos, plan)
    if problemas:
        raise ValueError("el reparto no conserva el origen: " + "; ".join(problemas))
    man = manifiesto(datos, plan)
    (origen / MANIFIESTO).write_text(json.dumps(man, indent=1, sort_keys=True) + "\n")
    for exp, p in plan.items():
        d = destino(exp)
        if d.resolve() == origen.resolve():
            # lo que queda en el origen: se reescribe la tabla filtrada y no se mueven archivos
            for t in TABLAS:
                if p[t] is not None:
                    p[t].to_csv(origen / f"{t}.csv", index=False)
            continue
        d.mkdir(parents=True, exist_ok=True)
        for t in TABLAS:
            if p[t] is not None:
                p[t].to_csv(d / f"{t}.csv", index=False)
        for sub, nombres in [("hp", p["hp"]), *[(c, p[c]) for c in CARPETAS]]:
            if nombres:
                (d / sub).mkdir(exist_ok=True)
            for n in nombres:
                if (d / sub / n).exists():
                    raise FileExistsError(f"{d / sub / n} ya existe: no se pisa")
                shutil.move(origen / sub / n, d / sub / n)
    # El origen ya no tiene brazos: sus tablas se quitan (la fuente de verdad es el dueño).
    if not any(destino(e).resolve() == origen.resolve() for e in plan):
        for t in datos["tablas"]:
            (origen / f"{t}.csv").unlink()
    return man


def verificar(origen: Path, raiz: Path | None = None) -> list[str]:
    """Compara los destinos con el manifiesto: mismos `id` y archivos que el origen, ninguno de más ni duplicado."""
    destino = (lambda e: raiz / "experimentos" / e / "ledger") if raiz else rutas.ledger
    man = json.loads((origen / MANIFIESTO).read_text())
    problemas: list[str] = []
    for t, ids in man["tablas"].items():
        encontrados = []
        for exp in man["destino"]:
            f = destino(exp) / f"{t}.csv"
            if f.exists():
                encontrados += list(pd.read_csv(f, dtype=str, keep_default_na=False)["id"])
        if sorted(encontrados) != sorted(ids):
            problemas.append(f"{t}.csv: la unión de los dueños tiene {len(encontrados)} id y el origen tenía {len(ids)}")
        if len(set(encontrados)) != len(encontrados):
            problemas.append(f"{t}.csv: id duplicados entre dueños")
    for clave in ("hp", *CARPETAS):
        esperados = man["hp"] if clave == "hp" else man["archivos"][clave]
        encontrados = []
        for exp in man["destino"]:
            d = destino(exp) / clave
            if d.is_dir():
                encontrados += [p.name for p in d.iterdir() if p.is_file() and (clave != "hp" or p.suffix == ".json")]
        if sorted(encontrados) != sorted(esperados):
            problemas.append(f"{clave}/: la unión de los dueños tiene {len(encontrados)} archivos y el origen tenía "
                             f"{len(esperados)}")
    for exp, d in man["destino"].items():
        for t, ids in d["tablas"].items():
            f = destino(exp) / f"{t}.csv"
            tabla = pd.read_csv(f, dtype=str, keep_default_na=False)
            ajenos = [b for b in tabla["brazo"].unique() if brazos.dueno_brazo(b) != exp]
            if ajenos:
                problemas.append(f"{exp}/{t}.csv tiene brazos de otro dueño: {ajenos}")
    for clave in ("hp", *CARPETAS):
        quedan = [p.name for p in (origen / clave).iterdir()] if (origen / clave).is_dir() else []
        if quedan:
            problemas.append(f"{clave}/ del origen todavía tiene {len(quedan)} archivos: {quedan[:3]}")
    return problemas


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--origen", type=Path, required=True, help="ledger que se reparte (experimentos/sampling_1/ledger)")
    p.add_argument("--verificar", action="store_true", help="no mueve nada: comprueba los destinos contra el manifiesto")
    a = p.parse_args()
    if a.verificar:
        problemas = verificar(a.origen)
        for pr in problemas:
            print("PROBLEMA", pr)
        print("conservación OK: ningún id ni archivo se perdió ni se duplicó" if not problemas else "")
        raise SystemExit(1 if problemas else 0)
    man = separar(a.origen)
    for exp, d in man["destino"].items():
        print(f"{exp}: " + ", ".join(f"{t}={len(i)}" for t, i in d["tablas"].items())
              + f", hp={len(d['hp'])}, " + ", ".join(f"{c}={len(d[c])}" for c in CARPETAS))


if __name__ == "__main__":
    main()
