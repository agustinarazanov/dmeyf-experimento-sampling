"""Los CSV agregados de resultados/ son coherentes entre sí y con lo que documenta el README."""
import hashlib
import json

import numpy as np
import pandas as pd

from experimentos.h3.sensibilidad_muestra import rutas

R = rutas.RESULTADOS


def test_procedencia_sha256():
    proc = json.loads((R / "procedencia.json").read_text(encoding="utf-8"))
    for nombre, info in proc["archivos"].items():
        # se compara sin depender del fin de línea con que git haya hecho el checkout
        texto = (R / nombre).read_bytes().replace(b"\r\n", b"\n")
        assert hashlib.sha256(texto).hexdigest() == info["sha256_lf"], nombre


def test_resumen_07():
    t = pd.read_csv(R / "07_resumen_por_semilla.csv")
    res = json.loads((R / "resumen.json").read_text(encoding="utf-8"))["07"]
    assert len(t) == 10 and (t["config_h3"] == 6).sum() == 7
    assert sorted(t.loc[t["config_h3"] != 6, "config_h3"]) == [3, 13, 16]
    assert np.median(t["delta"]) == 0
    ahorro = 1 - np.median(t["tiempo_busqueda_s"]) / res["tiempo_control_20_ajustes_s"]
    assert round(ahorro, 2) == 0.69


def test_ganancia_08():
    s = pd.read_csv(R / "08_ganancia_por_semilla.csv")
    c = pd.read_csv(R / "08_ganancia_por_configuracion.csv").set_index("config")
    t7 = pd.read_csv(R / "07_resumen_por_semilla.csv")
    assert list(s["config_h3"]) == list(t7["config_h3"])
    assert (c["envios"] == 3300).all() and (c["ganancia"] == c["ganancia_modulo_grupo"]).all()
    assert (c["ganancia"] == 1_072_500 * c["baja2"] - 27_500 * (c["envios"] - c["baja2"])).all()
    assert (s["ganancia_h3"] == c.loc[s["config_h3"], "ganancia"].to_numpy()).all()
    assert (s["delta"] == 0).sum() == 7
    assert (round(s["delta_pct"].min(), 2), round(s["delta_pct"].max(), 2)) == (-3.62, 3.22)
    # las 10 muestras usan 4 modelos distintos (3, 6, 13 y 16); la 6 es también el Control
    assert set(s["config_h3"]) | set(c.index[c["rol"] == "control"]) == {3, 6, 13, 16}
