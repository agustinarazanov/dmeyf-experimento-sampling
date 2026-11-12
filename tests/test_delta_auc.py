"""ΔAUC con réplicas en `replicas.csv` (D10): coincide con un cálculo a mano y no cambia el veredicto."""
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from comun import ledger as lg


def finales(auc_v):
    """C y H3-0.1 con 3 réplicas × 2 semillas; la ganancia de H3-0.1 es 5 mil más que la de C en cada réplica."""
    filas = []
    for r in range(3):
        for s in (1, 2):
            filas.append(dict(variante="C", replica_opt=r, semilla=s, g=1_000_000.0 + 1000 * r, auc_test=0.90 + 0.001 * r))
            filas.append(dict(variante="H3-0.1", replica_opt=r, semilla=s, g=1_005_000.0 + 1000 * r,
                              auc_test=auc_v + 0.002 * r))
    return pd.DataFrame(filas)


def test_delta_auc_con_replicas_coincide_con_el_calculo_a_mano():
    rep = lg.replicas(finales(0.91), delta=20_000.0).set_index("variante")
    v = np.array([0.91, 0.912, 0.914])
    c = np.array([0.90, 0.901, 0.902])
    dif = v.mean() - c.mean()
    va, vc = v.var(ddof=1) / 3, c.var(ddof=1) / 3
    gl = (va + vc) ** 2 / (va ** 2 / 2 + vc ** 2 / 2)
    mitad = stats.t.ppf(0.975, gl) * np.sqrt(va + vc)
    fila = rep.loc["H3-0.1"]
    assert fila["delta_auc_media"] == pytest.approx(dif)
    assert fila["delta_auc_ic_inf"] == pytest.approx(dif - mitad)
    assert fila["delta_auc_ic_sup"] == pytest.approx(dif + mitad)
    assert "delta_auc_media" not in rep.columns or pd.isna(rep.loc["C", "delta_auc_media"])


def test_el_veredicto_no_cambia_con_el_auc():
    a = lg.replicas(finales(0.91), delta=20_000.0).set_index("variante").loc["H3-0.1"]
    b = lg.replicas(finales(0.50), delta=20_000.0).set_index("variante").loc["H3-0.1"]
    assert a["veredicto"] == b["veredicto"] and a["delta_g_media"] == b["delta_g_media"]
    assert a["delta_auc_media"] != b["delta_auc_media"]
