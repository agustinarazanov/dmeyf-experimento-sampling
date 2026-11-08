"""Registro de tokens de Claude Code por sesión y etapa, desde los transcripts locales (nada sale de la máquina).

    python -m comun.tokens [--experimento sampling_1]

Lee `~/.claude/projects/<repo>/*.jsonl`, clasifica cada sesión por la etapa que declara la `docs/bitacora.md` de algún
experimento (o su `ledger/sesiones/costos.csv`) y escribe `experimentos/<experimento>/ledger/tokens.csv` con las
sesiones que ese experimento declara; la sesión que ninguno declara va a `sampling_1`, y si dos experimentos declaran
la misma, falla. Sin `--experimento` regenera el de todos. El archivo sale ordenado y sin datos volátiles: correrlo dos veces
sin sesiones nuevas no cambia el archivo. El costo sale del `cost-state` que Claude Code guarda en el transcript
(USD por modelo) y, para las sesiones headless de `scripts/etapa.sh`, de `ledger/sesiones/costos.csv`, que tiene
prioridad. Una sesión sin ninguna de las dos fuentes queda con el costo vacío: no se estima con precios supuestos.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PROYECTOS = Path.home() / ".claude" / "projects"

#: Línea de base de octubre (sesiones en `dmeyf2026`) y objetivo del proyecto (`specs/registro-tokens`).
BASE_CONTEXTO = 400_000
BASE_TURNOS = 2_509
BASE_COSTO_USD = 694
OBJETIVO_CONTEXTO = 100_000

#: Etapa de una sesión headless según el grupo de `tasks.md` que aplicó (`scripts/etapa.sh`).
ETAPA_DE_GRUPO = {"1": "hipotesis", "2": "diseno", "3": "codigo", "4": "codigo", "5": "corridas", "6": "informe"}
#: La etapa sale del cambio y del grupo: cada cambio numera sus grupos distinto. Un `costos.csv` sin columna `cambio`
#: (o con el campo vacío) es del cambio archivado `experimento-sampling-velocidad`.
ETAPA_DE_GRUPO_POR_CAMBIO = {
    "experimento-sampling-velocidad": ETAPA_DE_GRUPO,
    "separar-hipotesis": {"1": "codigo", "2": "codigo", "3": "codigo", "4": "diseno", "5": "informe", "6": "codigo"},
    "renombrar-brazos": {"1": "codigo", "2": "codigo", "3": "informe", "4": "informe"},
}
DUENO_SIN_DECLARAR = "sampling_1"
COLUMNAS = [
    "sesion", "fecha", "etapa", "modelo", "turnos", "tokens_salida", "tokens_cache_leidos", "contexto_promedio",
    "contexto_maximo", "costo_usd", "costo_fuente", "supera_objetivo", "linea_base_contexto", "objetivo_contexto",
]
_UUID = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"


def etapas_de_la_bitacora(texto: str) -> dict[str, str]:
    """sesión -> etapa, según las entradas (`### …`) de la bitácora. La primera declaración de una sesión manda."""
    etapas: dict[str, str] = {}
    for entrada in re.split(r"^### ", texto, flags=re.M)[1:]:
        m = re.search(r"etapa:?\s*\*\*(\w+)\*\*", entrada) or re.search(r"como etapa `(\w+)`", entrada)
        if not m:
            continue
        for sesion in re.findall(rf"`({_UUID})`", entrada):
            etapas.setdefault(sesion, m.group(1))
    return etapas


def leer_transcript(ruta: Path) -> dict:
    """Turnos (mensajes de assistant únicos por id) con su contexto, y el último `cost-state`."""
    turnos: dict[str, dict] = {}
    costo = None
    primera = None
    for linea in ruta.read_text().splitlines():
        try:
            d = json.loads(linea)
        except json.JSONDecodeError:
            continue
        ts = d.get("timestamp")
        if ts and (primera is None or ts < primera):
            primera = ts
        if d.get("type") == "cost-state":
            costo = d
        m = d.get("message")
        if d.get("type") == "assistant" and isinstance(m, dict) and m.get("usage") and m.get("model") != "<synthetic>":
            u = m["usage"]
            turnos[m.get("id") or d.get("uuid")] = {
                "modelo": m.get("model", ""),
                "contexto": u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
                "salida": u.get("output_tokens", 0),
                "leidos": u.get("cache_read_input_tokens", 0),
            }
    return {"turnos": list(turnos.values()), "costo": costo, "fecha": primera}


def fila_de_sesion(sesion: str, ruta: Path | None, etapa: str, costo_etapa: float | None) -> dict:
    t = leer_transcript(ruta) if ruta else {"turnos": [], "costo": None, "fecha": None}
    turnos = t["turnos"]
    n = len(turnos)
    modelos = sorted({x["modelo"] for x in turnos}, key=lambda m: -sum(1 for x in turnos if x["modelo"] == m))
    if costo_etapa is not None:
        costo, fuente = costo_etapa, "costos.csv"
    elif t["costo"]:
        costo, fuente = round(t["costo"]["totalCostUSD"], 4), "cost-state"
    else:
        costo, fuente = None, ""
    promedio = round(sum(x["contexto"] for x in turnos) / n) if n else None
    return {
        "sesion": sesion,
        "fecha": (t["fecha"] or "")[:19],
        "etapa": etapa,
        "modelo": ";".join(modelos),
        "turnos": n,
        "tokens_salida": sum(x["salida"] for x in turnos),
        "tokens_cache_leidos": sum(x["leidos"] for x in turnos),
        "contexto_promedio": promedio,
        "contexto_maximo": max((x["contexto"] for x in turnos), default=None),
        "costo_usd": costo,
        "costo_fuente": fuente,
        "supera_objetivo": bool(promedio and promedio > OBJETIVO_CONTEXTO),
        "linea_base_contexto": BASE_CONTEXTO,
        "objetivo_contexto": OBJETIVO_CONTEXTO,
    }


def costos_csv(ruta: Path) -> dict[str, tuple[str, float]]:
    """sesión -> (etapa, costo USD) de las sesiones headless que dejó `scripts/etapa.sh`."""
    if not ruta.exists():
        return {}
    salida = {}
    for f in csv.DictReader(ruta.open()):
        grupos = ETAPA_DE_GRUPO_POR_CAMBIO.get(f.get("cambio") or "experimento-sampling-velocidad", {})
        etapa = "revision" if f.get("rol") == "revisar" else grupos.get(f.get("grupo", ""), "sin-etapa")
        if f.get("sesion"):
            salida[f["sesion"]] = (etapa, float(f["costo_usd"] or 0))
    return salida


def declaraciones(experimento: str, raiz: Path) -> tuple[dict[str, str], dict[str, tuple[str, float]]]:
    """(bitácora, costos.csv) de un experimento: lo que ese experimento declara de cada sesión."""
    exp = raiz / "experimentos" / experimento
    bitacora = exp / "docs" / "bitacora.md"
    return (etapas_de_la_bitacora(bitacora.read_text()) if bitacora.exists() else {},
            costos_csv(exp / "ledger" / "sesiones" / "costos.csv"))


def experimentos_de(raiz: Path) -> list[str]:
    return sorted(p.name for p in (raiz / "experimentos").iterdir() if (p / "docs").is_dir())


def duenos(raiz: Path) -> dict[str, str]:
    """sesión -> experimento que la declara; falla si dos experimentos declaran la misma."""
    dueno: dict[str, str] = {}
    for e in experimentos_de(raiz):
        bitacora, headless = declaraciones(e, raiz)
        for s in set(bitacora) | set(headless):
            if dueno.setdefault(s, e) != e:
                raise SystemExit(f"la sesión {s} la declaran {dueno[s]} y {e}: dejar una sola declaración")
    return dueno


def registrar(experimento: str = "sampling_1", raiz: Path = RAIZ, proyectos: Path = PROYECTOS) -> list[dict]:
    exp = raiz / "experimentos" / experimento
    dueno = duenos(raiz)
    declaradas, headless = declaraciones(experimento, raiz)
    proyecto = proyectos / re.sub(r"[^A-Za-z0-9]", "-", str(raiz))
    en_repo = {p.stem: p for p in proyecto.glob("*.jsonl")}
    ids = set(declaradas) | set(headless)
    if experimento == DUENO_SIN_DECLARAR:
        ids |= {s for s in en_repo if s not in dueno}
    filas = []
    for s in ids:
        ruta = en_repo.get(s) or next(iter(proyectos.glob(f"*/{s}.jsonl")), None)  # p. ej. la planificación, en dmeyf2026
        etapa = declaradas.get(s) or (headless[s][0] if s in headless else "sin-etapa")
        filas.append(fila_de_sesion(s, ruta, etapa, headless[s][1] if s in headless else None))
    filas.sort(key=lambda f: (f["fecha"] or "9999", f["sesion"]))
    destino = exp / "ledger" / "tokens.csv"
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)
    return filas


def resumen(filas: list[dict]) -> str:
    out = [f"línea de base de octubre: {BASE_CONTEXTO:,} tokens de contexto por turno, {BASE_TURNOS:,} turnos, "
           f"≈ US$ {BASE_COSTO_USD}; objetivo < {OBJETIVO_CONTEXTO:,}"]
    for f in filas:
        marca = "  ← SUPERA EL OBJETIVO: anotar en la bitácora qué la infló" if f["supera_objetivo"] else ""
        sin = "  [sin etapa: clasificar en la bitácora]" if f["etapa"] == "sin-etapa" else ""
        out.append(f"{f['etapa']:<13} {f['sesion'][:8]} {f['turnos']:>4} turnos  contexto {f['contexto_promedio'] or 0:>9,}  "
                   f"US$ {f['costo_usd'] if f['costo_usd'] is not None else '?'}{marca}{sin}")
    return "\n".join(out)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--experimento", help="uno solo; sin esto se regeneran todos")
    a = p.parse_args()
    for e in [a.experimento] if a.experimento else experimentos_de(RAIZ):
        print(f"== {e}")
        print(resumen(registrar(e)))


if __name__ == "__main__":
    main()
