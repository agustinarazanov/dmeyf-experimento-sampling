"""Tabla de rondas (D9): por variante, Δ y veredicto en la ronda 201903-201906 y en la vigente, con los dos δ.

    python scripts/comparar_rondas.py [--experimentos experimentos] [--salida experimentos/sampling_1/informe/comparacion_rondas.md]

Lee, de cada `<exp>/ledger/`, `ronda_201903-201906/{apareado,replicas}.csv` (ronda anterior, copiados antes del cambio) y
`{apareado,replicas}.csv` (ronda vigente). Una fila por variante de la ronda anterior; las que solo existen en la nueva
(`H4O-0.5`) no entran. No mezcla rondas ni compara tiempos (T y A solo se comparan dentro de una ronda). Nada a mano.
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

RONDA_VIEJA = "201903-201906"
VENTANA_NUEVA = "201903-201908"


def _m(x) -> str:
    return "—" if pd.isna(x) else f"{x / 1e6:,.2f}"


def _ic(media, inf, sup) -> str:
    return "—" if pd.isna(media) else f"{_m(media)} [{_m(inf)}; {_m(sup)}]"


def _leer(ruta: Path) -> pd.DataFrame:
    return pd.read_csv(ruta) if ruta.exists() else pd.DataFrame()


def _por_variante(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "variante" not in df.columns:
        return pd.DataFrame()
    return df[~df["variante"].astype(str).str.contains(" - ")].drop_duplicates("variante").set_index("variante")


def ronda(experimentos: Path, vieja: bool) -> tuple[pd.DataFrame, pd.DataFrame, float | None]:
    """(apareado por variante, replicas por variante, δ) de una ronda, juntando los ledgers de todos los experimentos."""
    ap, rep = [], []
    for led in sorted(experimentos.glob("*/ledger")):
        base = led / f"ronda_{RONDA_VIEJA}" if vieja else led
        ap.append(_por_variante(_leer(base / "apareado.csv")))
        rep.append(_por_variante(_leer(base / "replicas.csv")))
    ap = pd.concat([a for a in ap if len(a)]) if any(len(a) for a in ap) else pd.DataFrame()
    rep = pd.concat([r for r in rep if len(r)]) if any(len(r) for r in rep) else pd.DataFrame()
    delta = float(ap["delta_g_margen"].iloc[0]) if len(ap) and "delta_g_margen" in ap else None
    return ap, rep, delta


def _celdas(v: str, ap: pd.DataFrame, rep: pd.DataFrame) -> list[str]:
    r0 = ap.loc[v] if v in ap.index else None
    rr = rep.loc[v] if v in rep.index and pd.notna(rep.loc[v].get("delta_g_media")) else None
    return [
        _ic(r0["delta_g_media"], r0["delta_g_ic_inf"], r0["delta_g_ic_sup"]) if r0 is not None else "pendiente",
        str(r0["veredicto"]) if r0 is not None else "pendiente",
        _ic(rr["delta_g_media"], rr["delta_g_ic_inf"], rr["delta_g_ic_sup"]) if rr is not None else "—",
        str(rr["veredicto"]) if rr is not None else "—",
    ]


def tabla(experimentos: Path) -> str:
    ap_v, rep_v, delta_v = ronda(experimentos, True)
    ap_n, rep_n, delta_n = ronda(experimentos, False)
    variantes = sorted(set(ap_v.index) | set(rep_v.index))
    cab = ["variante", f"Δ réplica 0 {RONDA_VIEJA}", "veredicto", "Δ con réplicas", "veredicto",
           f"Δ réplica 0 {VENTANA_NUEVA}", "veredicto", "Δ con réplicas", "veredicto", "¿cambia el veredicto?"]
    filas = []
    for v in variantes:
        a, b = _celdas(v, ap_v, rep_v), _celdas(v, ap_n, rep_n)
        cambia = [x != y for x, y in ((a[1], b[1]), (a[3], b[3])) if "pendiente" not in (x, y) and "—" not in (x, y)]
        filas.append([v, *a, *b, "sí" if any(cambia) else ("no" if cambia else "pendiente")])
    esc = lambda c: str(c).replace("|", "\\|")
    texto = [
        "# Comparación de rondas\n",
        "Generado por `python scripts/comparar_rondas.py`; no editar a mano. Cada ronda se lee de su propio `apareado.csv` "
        "y `replicas.csv` (G, Δ y δ salen del control de esa ronda); T y A no se comparan entre rondas.\n",
        f"- Ronda {RONDA_VIEJA} (final con 4 meses, 10 semillas, N* de validación): δ = {_m(delta_v)} M$.",
        f"- Ronda {VENTANA_NUEVA} (final con 6 meses, 20 semillas, N* fijo): δ = {_m(delta_n)} M$.\n",
        "Δ en M$ al corte N* de cada ronda, con IC 95%.\n",
        "| " + " | ".join(cab) + " |", "|" + "---|" * len(cab),
        *["| " + " | ".join(esc(c) for c in f) + " |" for f in filas],
    ]
    return "\n".join(texto) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--experimentos", type=Path, default=Path("experimentos"))
    ap.add_argument("--salida", type=Path, default=None)
    a = ap.parse_args()
    salida = a.salida or a.experimentos / "sampling_1" / "informe" / "comparacion_rondas.md"
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(tabla(a.experimentos), encoding="utf-8")
    print(salida)
    return 0


if __name__ == "__main__":
    sys.exit(main())
