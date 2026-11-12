"""`consolidar --meses-final` (D3, D4): N* fijo en la ronda nueva, rondas separadas y falla sin `C`."""
import pandas as pd
import pytest

from comun import baseline as bl
from comun import consolidar
from comun import ledger as lg

NUEVA = bl.VENTANA_FINAL
VIEJA = lg.MESES_FINAL_VIEJA


def corrida(led, variante, semilla, escala, ventana, con_201908):
    id_ = f"{variante}_{semilla}_{ventana}"
    envios = list(range(100, 3601, 100))
    meses = (201908, 201910) if con_201908 else (201910,)
    for mes in meses:
        pd.DataFrame({"envios": envios, "ganancia": [escala * e for e in envios]}).to_csv(
            led / "curvas" / f"{id_}_{mes}.csv", index=False)
    f = {c: "" for c in lg.COLUMNAS}
    f.update(id=id_, fecha="2026-11-01T10:00:00", variante=variante, metodo="uniforme", tasa=1 if variante == "C" else 0.5,
             semilla=semilla, etapa="final", etapa_corrida="final", meses_final=ventana, estudio=variante, valida=True,
             commit="abc", auc_test=0.9, tiempo_entrenamiento_s=10.0, maquina="n2", cpu="ice", hilos=8,
             curva_201908=f"curvas/{id_}_201908.csv" if con_201908 else "", curva_201910=f"curvas/{id_}_201910.csv")
    lg.escribir_fila(led / "corridas", f)


def armar(tmp_path):
    (tmp_path / "curvas").mkdir()
    for s in (1, 2, 3):
        corrida(tmp_path, "C", s, 100.0, VIEJA, True)
        corrida(tmp_path, "C", s, 120.0, NUEVA, False)
    for s in (2, 3, 4):
        corrida(tmp_path, "U0.5", s, 101.0, VIEJA, True)
        corrida(tmp_path, "U0.5", s, 130.0, NUEVA, False)


def test_ronda_nueva_usa_n_estrella_fijo_sin_curva_de_201908(tmp_path):
    armar(tmp_path)
    ap = consolidar.consolidar(tmp_path)["apareado"].iloc[0]
    assert ap["n_estrella"] == bl.N_ESTRELLA == 3300
    assert ap["delta_g_media"] == pytest.approx(10.0 * 3300)  # 130 - 120 por envío, al corte 3300
    assert (tmp_path / "apareado.csv").exists()


def test_ronda_vieja_usa_corte_control_y_va_a_su_carpeta(tmp_path):
    armar(tmp_path)
    ap = consolidar.consolidar(tmp_path, meses_final=VIEJA)["apareado"].iloc[0]
    assert ap["n_estrella"] == 3600 and ap["delta_g_media"] == pytest.approx(1.0 * 3600)
    assert (tmp_path / "ronda_201903-201906" / "apareado.csv").exists()
    assert not (tmp_path / "apareado.csv").exists()  # la tabla vigente no se toca


def test_las_rondas_no_se_mezclan_en_resultados(tmp_path):
    armar(tmp_path)
    r = consolidar.consolidar(tmp_path)
    assert set(r["resultados"]["meses_final"]) == {VIEJA, NUEVA} and len(r["resultados"]) == 12
    assert r["apareado"]["n_semillas"].iloc[0] == 2


def test_falla_si_la_ronda_no_tiene_c(tmp_path):
    (tmp_path / "curvas").mkdir()
    for s in (1, 2):
        corrida(tmp_path, "C", s, 100.0, VIEJA, True)
        corrida(tmp_path, "U0.5", s, 101.0, NUEVA, False)
    with pytest.raises(ValueError, match="no tiene finales del control"):
        consolidar.consolidar(tmp_path)


def test_absolutas_deja_vacia_la_curva_que_no_existe():
    import numpy as np
    import pandas as pd
    from pathlib import Path
    from comun import consolidar as cons

    f = pd.DataFrame({"curva_201908": [np.nan, ""], "curva_201910": ["a.csv", "b.csv"]})
    out = cons._absolutas(f, Path("/x"))
    assert out["curva_201908"].isna().iloc[0] and out["curva_201908"].iloc[1] == ""
    assert list(out["curva_201910"]) == ["/x/a.csv", "/x/b.csv"]
