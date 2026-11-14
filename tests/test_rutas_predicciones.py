"""D18: las predicciones se resuelven primero en `DATOS_DIR` y, si no están, en la ruta vieja del repo."""

import pandas as pd

from comun import baseline as bl
from comun import reporte, rutas

REL = "predicciones/x_0.parquet"


def _escribir(ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text("x")


def test_resuelve_en_datos_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(bl, "DATOS_DIR", tmp_path)
    monkeypatch.setattr(rutas, "EXPERIMENTOS", tmp_path / "repo")
    _escribir(tmp_path / "ledger" / "h9" / REL)
    assert rutas.prediccion("h9", REL) == tmp_path / "ledger" / "h9" / REL


def test_resuelve_en_la_ruta_vieja_del_repo(tmp_path, monkeypatch):
    monkeypatch.setattr(bl, "DATOS_DIR", tmp_path / "datos")
    monkeypatch.setattr(rutas, "EXPERIMENTOS", tmp_path / "repo")
    _escribir(tmp_path / "repo" / "h9" / "ledger" / REL)
    assert rutas.prediccion("h9", REL) == tmp_path / "repo" / "h9" / "ledger" / REL


def test_si_esta_en_los_dos_gana_datos_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(bl, "DATOS_DIR", tmp_path / "datos")
    monkeypatch.setattr(rutas, "EXPERIMENTOS", tmp_path / "repo")
    _escribir(tmp_path / "datos" / "ledger" / "h9" / REL)
    _escribir(tmp_path / "repo" / "h9" / "ledger" / REL)
    assert rutas.prediccion("h9", REL) == tmp_path / "datos" / "ledger" / "h9" / REL


def test_el_reporte_absolutiza_las_predicciones_con_esa_funcion(tmp_path, monkeypatch):
    monkeypatch.setattr(bl, "DATOS_DIR", tmp_path / "datos")
    monkeypatch.setattr(rutas, "EXPERIMENTOS", tmp_path / "repo")
    _escribir(tmp_path / "datos" / "ledger" / "h9" / REL)
    fin = pd.DataFrame({"predicciones_201910": [REL, None], "curva_201910": ["curvas/x.csv", None]})
    out = reporte._absolutas(fin, "h9")
    assert out["predicciones_201910"][0] == str(tmp_path / "datos" / "ledger" / "h9" / REL)
    assert out["curva_201910"][0] == str(tmp_path / "repo" / "h9" / "ledger" / "curvas" / "x.csv")
    assert pd.isna(out["predicciones_201910"][1])
