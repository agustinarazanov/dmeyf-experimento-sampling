import pandas as pd
import pytest

from comun import ledger as lg


def fila(**kw):
    base = {c: "" for c in lg.COLUMNAS}
    base.update(id="x", fecha="2026-11-01T10:00:00", etapa="final", valida=True)
    base.update(kw)
    return base


def test_falta_una_columna_y_se_nombra(tmp_path):
    f = fila()
    del f["memoria_max_mb"]
    with pytest.raises(ValueError, match="memoria_max_mb"):
        lg.escribir_fila(tmp_path, f)
    assert not list(tmp_path.glob("*.csv"))


def test_fila_completa_se_escribe(tmp_path):
    lg.escribir_fila(tmp_path, fila())
    assert lg.existe_fila(tmp_path, "x")
    assert list(lg.leer_corridas(tmp_path).columns) == lg.COLUMNAS


def sintetica(brazo, semillas, gs, **kw):
    return pd.DataFrame({
        "brazo": brazo, "metodo": "uniforme", "tasa": 0.5, "semilla": semillas, "g": gs, "auc_test": 0.9,
        "tiempo_entrenamiento_s": 10.0, "estudio": brazo, "maquina": "n2", "cpu": "ice", "hilos": 8, **kw,
    })


def test_apareado_usa_solo_semillas_en_comun():
    ctrl = sintetica("C", [1, 2, 3], [100.0, 100.0, 100.0])
    arm = sintetica("U0.5", [2, 3, 4], [101.0, 103.0, 0.0])  # la semilla 4 no está en el control
    out = lg.apareado(pd.concat([ctrl, arm], ignore_index=True))
    r = out.iloc[0]
    assert r["n_semillas"] == 2 and r["semillas"] == "2 3"
    assert r["delta_g_media"] == pytest.approx(2.0)
    assert r["semillas_ganadas"] == 2
    assert "2 semillas en común de 3" in r["nota"]


def test_veredictos_cubren_todo():
    assert lg.veredicto(5, 1, 2) == "gana"
    assert lg.veredicto(0, -1, 2) == "no pierde"
    assert lg.veredicto(-3, -9, 2) == "pierde"
    assert lg.veredicto(-1, -9, 2) == "indeterminado"
    assert lg.veredicto(0, float("nan"), 2) == "indeterminado"


def test_consolidar_conserva_la_mas_reciente_y_marca_la_anterior():
    a = fila(id="a", fecha="2026-11-01T10:00:00", brazo="C", metodo="uniforme", tasa=1, semilla=1, commit="abc")
    b = fila(id="b", fecha="2026-11-01T11:00:00", brazo="C", metodo="uniforme", tasa=1, semilla=1, commit="abc")
    sucia = fila(id="c", fecha="2026-11-01T12:00:00", brazo="C", metodo="uniforme", tasa=1, semilla=2, commit="abc", valida=False)
    res, rem = lg.consolidar_corridas(pd.DataFrame([a, b, sucia]))
    assert list(res["id"]) == ["b"]
    assert list(rem["id"]) == ["a"] and list(rem["reemplazada_por"]) == ["b"]
