import sys
from pathlib import Path

import pandas as pd

from comun import ledger as lg

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experimentos" / "sampling_1"))
from src import consolidar  # noqa: E402


def corrida(led, brazo, semilla, escala, etapa="final"):
    id_ = f"{brazo}_{semilla}"
    envios = list(range(50, 301, 50))
    for mes in (201908, 201910):
        pd.DataFrame({"envios": envios, "ganancia": [escala * e for e in envios]}).to_csv(led / "curvas" / f"{id_}_{mes}.csv", index=False)
    f = {c: "" for c in lg.COLUMNAS}
    f.update(id=id_, fecha="2026-11-01T10:00:00", brazo=brazo, metodo="uniforme", tasa=1 if brazo == "C" else 0.5,
             semilla=semilla, etapa=etapa, etapa_corrida=etapa, estudio=brazo, valida=True, commit="abc",
             auc_test=0.9, tiempo_entrenamiento_s=10.0, maquina="n2", cpu="ice", hilos=8,
             curva_201908=f"curvas/{id_}_201908.csv", curva_201910=f"curvas/{id_}_201910.csv")
    lg.escribir_fila(led / "corridas", f)


def test_consolidar_de_punta_a_punta(tmp_path):
    (tmp_path / "curvas").mkdir()
    for s in (1, 2, 3):
        corrida(tmp_path, "C", s, 100.0)
    for s in (2, 3, 4):
        corrida(tmp_path, "U0.5", s, 101.0)
    r = consolidar.consolidar(tmp_path)
    ap = r["apareado"].iloc[0]
    assert ap["n_estrella"] == 300 and ap["n_semillas"] == 2
    assert ap["delta_g_media"] == 300.0
    assert (tmp_path / "resultados.csv").exists() and (tmp_path / "apareado.csv").exists()


def test_graficar_banda(tmp_path):
    import importlib.util
    ruta = Path(__file__).resolve().parents[1] / "experimentos" / "sampling_1" / "scripts" / "graficar.py"
    spec = importlib.util.spec_from_file_location("graficar", ruta)
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    (tmp_path / "curvas").mkdir()
    for s in (1, 2):
        corrida(tmp_path, "C", s, 100.0)
        corrida(tmp_path, "U0.5", s, 99.0)
    consolidar.consolidar(tmp_path)
    g.LEDGER = tmp_path
    fin = pd.read_csv(tmp_path / "resultados.csv")
    png = g.graficar("U0.5", fin, 201910, tmp_path / "f.png")
    assert png.exists() and png.stat().st_size > 0
