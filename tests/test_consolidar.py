from pathlib import Path

import pandas as pd

from comun import consolidar
from comun import ledger as lg


def corrida(led, variante, semilla, escala, etapa="final", estudio=None):
    id_ = f"{variante}_{semilla}"
    envios = list(range(50, 301, 50))
    for mes in (201908, 201910):
        pd.DataFrame({"envios": envios, "ganancia": [escala * e for e in envios]}).to_csv(led / "curvas" / f"{id_}_{mes}.csv", index=False)
    f = {c: "" for c in lg.COLUMNAS}
    f.update(id=id_, fecha="2026-11-01T10:00:00", variante=variante, metodo="uniforme", tasa=1 if variante == "C" else 0.5,
             semilla=semilla, etapa=etapa, etapa_corrida=etapa, meses_final=lg.MESES_FINAL_VIEJA if etapa == "final" else "", estudio=estudio or variante, valida=True,
             tiempo_optimizacion_s=50.0 if etapa == "optimizar" else 0.0, commit="abc",
             auc_test=0.9, tiempo_entrenamiento_s=10.0, maquina="n2", cpu="ice", hilos=8,
             curva_201908=f"curvas/{id_}_201908.csv", curva_201910=f"curvas/{id_}_201910.csv")
    lg.escribir_fila(led / "corridas", f)


def test_consolidar_de_punta_a_punta(tmp_path):
    (tmp_path / "curvas").mkdir()
    for s in (1, 2, 3):
        corrida(tmp_path, "C", s, 100.0)
    for s in (2, 3, 4):
        corrida(tmp_path, "U0.5", s, 101.0)
    r = consolidar.consolidar(tmp_path, meses_final=lg.MESES_FINAL_VIEJA)
    ap = r["apareado"].iloc[0]
    assert ap["n_estrella"] == 300 and ap["n_semillas"] == 2
    assert ap["delta_g_media"] == 300.0
    assert (tmp_path / "resultados.csv").exists() and (tmp_path / "ronda_201903-201906" / "apareado.csv").exists()


def test_consolidar_con_dos_ledgers(tmp_path):
    """El control en su ledger y U0.5 en el suyo: N* y los finales de C salen del control; H3 toma el tiempo del
    estudio de otro ledger."""
    ctrl, h1 = tmp_path / "control", tmp_path / "h1"
    for led in (ctrl, h1):
        (led / "curvas").mkdir(parents=True)
    for s in (1, 2, 3):
        corrida(ctrl, "C", s, 100.0)
    corrida(ctrl, "C", 0, 100.0, etapa="optimizar")
    for s in (2, 3, 4):
        corrida(h1, "U0.5", s, 101.0)
    corrida(h1, "U0.5", 0, 101.0, etapa="optimizar")
    consolidar.consolidar(ctrl, meses_final=lg.MESES_FINAL_VIEJA)
    assert not (ctrl / "apareado.csv").exists()  # el control solo no tiene variantes que comparar
    r = consolidar.consolidar(h1, control=ctrl, meses_final=lg.MESES_FINAL_VIEJA)
    ap = r["apareado"].iloc[0]
    assert ap["variante"] == "U0.5" and ap["n_estrella"] == 300 and ap["n_semillas"] == 2
    assert ap["delta_g_media"] == 300.0
    assert set(r["resultados"]["variante"]) == {"U0.5"}  # las filas del control no se copian al ledger de h1
    assert not (h1 / "curvas" / "C_1_201908.csv").exists()
    # H3 usa el estudio U0.5 de h1: el tiempo de su estudio sale de h1/estudios.csv
    h3 = tmp_path / "h3"
    (h3 / "curvas").mkdir(parents=True)
    for s in (1, 2):
        corrida(h3, "H3-0.5", s, 99.0, estudio="U0.5")
    r3 = consolidar.consolidar(h3, control=ctrl, ledgers_estudios=[h1], meses_final=lg.MESES_FINAL_VIEJA)
    assert r3["apareado"].iloc[0]["tiempo_total_s"] == 60.0  # 50 s del estudio de h1 + 10 s del final


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
    consolidar.consolidar(tmp_path, meses_final=lg.MESES_FINAL_VIEJA)
    g.LEDGER = tmp_path
    fin = pd.read_csv(tmp_path / "resultados.csv")
    png = g.graficar("U0.5", fin, 201910, tmp_path / "f.png")
    assert png.exists() and png.stat().st_size > 0
