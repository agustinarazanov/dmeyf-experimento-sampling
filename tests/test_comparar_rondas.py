"""`scripts/comparar_rondas.py` con ledgers sintéticos de dos rondas (D9)."""
import importlib.util
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("comparar_rondas", RAIZ / "scripts" / "comparar_rondas.py")
cr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cr)


def ap(path, filas):
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(filas).to_csv(path, index=False)


def fila(v, delta_g, margen, ver):
    return dict(variante=v, delta_g_media=delta_g, delta_g_ic_inf=delta_g - 1e6, delta_g_ic_sup=delta_g + 1e6,
                delta_g_margen=margen, veredicto=ver)


def armar(tmp_path):
    led = tmp_path / "h1" / "ledger"
    ap(led / "ronda_201903-201906" / "apareado.csv", [fila("U0.5", 2e6, 5e6, "no pierde"), fila("U0.1", -8e6, 5e6, "pierde")])
    ap(led / "apareado.csv", [fila("U0.5", 3e6, 6e6, "gana"), fila("U0.1", -9e6, 6e6, "pierde"), fila("H4O-0.5", 1e6, 6e6, "no pierde")])
    return tmp_path


def test_una_fila_por_variante_de_la_ronda_anterior_y_los_dos_delta(tmp_path):
    texto = cr.tabla(armar(tmp_path))
    assert "δ = 5.00 M$" in texto and "δ = 6.00 M$" in texto
    filas = [l for l in texto.splitlines() if l.startswith("| U") or l.startswith("| H4O")]
    assert len(filas) == 2 and not any("H4O-0.5" in l for l in filas)
    u05 = next(l for l in filas if l.startswith("| U0.5"))
    assert "2.00 [1.00; 3.00]" in u05 and "3.00 [2.00; 4.00]" in u05  # Δ de cada ronda, sin mezclar
    assert u05.rstrip().endswith("| sí |")  # no pierde -> gana
    assert next(l for l in filas if l.startswith("| U0.1")).rstrip().endswith("| no |")


def test_sin_ronda_nueva_queda_pendiente(tmp_path):
    led = tmp_path / "h1" / "ledger"
    ap(led / "ronda_201903-201906" / "apareado.csv", [fila("U0.5", 2e6, 5e6, "no pierde")])
    texto = cr.tabla(tmp_path)
    assert "pendiente" in texto and "δ = — M$" in texto
