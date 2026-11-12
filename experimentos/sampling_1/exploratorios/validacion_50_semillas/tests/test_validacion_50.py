"""Sin datos: semillas, estrategias, reescalados, hp original contra ledger, presupuesto y que 201910 no ordena ni elige."""
import types

import numpy as np
import pandas as pd
import pytest

from comun import baseline as bl
from comun import muestreo
from experimentos.sampling_1.exploratorios.validacion_50_semillas import estrategias as es
from experimentos.sampling_1.exploratorios.validacion_50_semillas import presupuesto as pr
from experimentos.sampling_1.exploratorios.validacion_50_semillas import validacion as va


# --- semillas y estrategias ---------------------------------------------------------------------------------------------

def test_semillas_son_las_de_luis():
    s = es.semillas(50)
    assert s[:10] == bl.SEMILLAS_OFICIALES
    assert s[10:] == [110017 + i * 19937 for i in range(40)]
    assert len(set(s)) == 50


def test_semillas_extendidas_siguen_la_formula_y_conservan_las_50():
    s = es.semillas(70)
    assert s[:50] == es.semillas(50)
    assert s[50:] == [110017 + i * 19937 for i in range(40, 60)]
    assert es.semillas(4) == bl.SEMILLAS_OFICIALES[:4]


def test_nueve_estrategias_numeradas_de_1():
    assert [e.id for e in es.ESTRATEGIAS] == list(range(1, 10))
    assert es.estrategia(7).estudio == "H4_Hard"
    assert {e.id for e in es.ESTRATEGIAS if e.modo == "h4_50_pesos"} == {8, 9}
    with pytest.raises(ValueError):
        es.estrategia(10)


def test_escalar_hp_recorta_y_solo_toca_min_data_por_defecto():
    hp = {"num_leaves": 36, "learning_rate": 0.03, "min_data_in_leaf": 427, "feature_fraction": 0.2, "bagging_fraction": 0.9}
    assert es.escalar_hp(hp, mult_min_data=3.16)["min_data_in_leaf"] == 1349
    assert es.escalar_hp(hp, mult_min_data=100)["min_data_in_leaf"] == 8000
    assert es.escalar_hp(hp, mult_min_data=0.001)["min_data_in_leaf"] == 10
    sin = es.escalar_hp(hp)
    assert {k: v for k, v in sin.items() if k != "min_data_in_leaf"} == {k: v for k, v in hp.items() if k != "min_data_in_leaf"}


def test_idea_a_multiplica_min_data():
    assert es.hp_de(es.estrategia(5))[0]["min_data_in_leaf"] == 653 * 2
    assert es.hp_de(es.estrategia(6))[0]["min_data_in_leaf"] == round(427 * 3.16)


@pytest.mark.parametrize("id_", [1, 2, 3, 4, 5, 6, 8, 9])
def test_hp_original_y_ledger_coinciden_en_C_y_U(id_):
    e = es.estrategia(id_)
    hp_o, t_o = es.hp_de(e, "original")
    hp_l, t_l = es.hp_de(e, "ledger")
    assert hp_o == hp_l
    assert t_l == pytest.approx(t_o, abs=0.01)


def test_hp_ledger_de_h4_hard_sale_de_nh01_y_avisa_si_falta(tmp_path):
    with pytest.raises(FileNotFoundError, match="NH0.1"):
        es.hp_de(es.estrategia(7), "ledger", raiz=tmp_path)
    assert es.LEDGER_HP["H4_Hard"] == ("h4", "NH0.1")


def test_hp_invalido():
    with pytest.raises(ValueError):
        es.hp_de(es.estrategia(1), "otro")


# --- el fast-retrain de Luis es el de comun/muestreo --------------------------------------------------------------------

def test_fast_retrain_igual_a_la_receta_del_script_original():
    rng_y = np.random.default_rng(3)
    y = (rng_y.random(2000) < 0.05).astype(int)
    s = 100003
    # receta del script (commit 9e1889e): negativos al azar con default_rng(s), todas las bajas, peso 2 en los negativos
    idx_pos, idx_neg = np.where(y == 1)[0], np.where(y == 0)[0]
    neg_s = np.random.default_rng(s).choice(idx_neg, size=int(round(len(idx_neg) * 0.50)), replace=False)
    esperado = np.sort(np.concatenate([idx_pos, neg_s]))
    idx = muestreo.indices_por_clase(y, es.FRACCION_FAST, s)
    assert np.array_equal(idx, esperado)
    w = muestreo.peso_inverso(y[idx], es.FRACCION_FAST)
    assert np.array_equal(w, np.where(y[idx] == 0, 2.0, 1.0))


# --- presupuesto ---------------------------------------------------------------------------------------------------------

def test_k_presupuesto_con_tiempos_sinteticos():
    assert pr.k_presupuesto(747.938, 35.0) == 4          # el control: 4 semillas en 900 s
    assert pr.k_presupuesto(66.923, 12.3) == 67          # fast-retrain: más de 60
    assert pr.k_presupuesto(900.0, 10.0) == 0
    assert pr.k_presupuesto(1000.0, 10.0) == 0
    assert pr.k_presupuesto(0.0, 100.0, presupuesto=450) == 4
    with pytest.raises(ValueError):
        pr.k_presupuesto(10.0, 0.0)


def _sintetico(g_va, g_te, n=12, t_opt=100.0, t_fin=50.0):
    """Resumen y ensambles de dos estrategias: `g_va`/`g_te` = (G de la estrategia 1, G de la 2)."""
    filas, ens = [], []
    for e, (gv, gt) in enumerate(zip(g_va, g_te), start=1):
        for k in range(1, n + 1):
            filas.append({"estrategia": e, "nombre": f"E{e}", "hp": "original", "t_opt_s": t_opt, "orden": k, "semilla": k,
                          "tiempo_s": t_fin, "g_201908": gv + k, "gmax_201908": gv + 1000, "auc_201908": 0.9,
                          "g_201910": gt + k, "auc_201910": 0.9})
            ens.append({"estrategia": e, "k": k, "g_201908": gv + 10 * k, "g_201910": gt + 10 * k})
    return pd.DataFrame(filas), pd.DataFrame(ens)


def test_tabla_presupuesto_k_mayor_que_las_semillas_corridas():
    res, ens = _sintetico((1e6, 2e6), (1e6, 2e6), n=12, t_opt=100.0, t_fin=50.0)   # K = 16 > 12
    t = pr.tabla_presupuesto(res, ens, 900.0)
    assert list(t["k_presupuesto"]) == [16, 16]
    assert not t["k_alcanzado"].any()
    assert t["ens_k_201908"].iloc[0] == 1e6 + 10 * 12          # con las 12 disponibles
    res, ens = _sintetico((1e6, 2e6), (1e6, 2e6), n=12, t_opt=100.0, t_fin=100.0)  # K = 8 <= 12
    t = pr.tabla_presupuesto(res, ens, 900.0)
    assert t["k_alcanzado"].all() and t["ens_k_201908"].iloc[0] == 1e6 + 10 * 8


# --- 201908 ordena y decide; 201910 solo se informa ----------------------------------------------------------------------

def test_ranking_y_curva_no_miran_201910():
    # en 201908 gana la 1; en 201910 gana la 2
    res, ens = _sintetico((5e6, 3e6), (1e6, 9e6))
    r = va.ranking_201908(res)
    assert list(r["estrategia"]) == [1, 2]
    # sin ninguna columna de 201910 el resultado es el mismo: no las usa
    sin = va.ranking_201908(res.drop(columns=["g_201910", "auc_201910"]))
    pd.testing.assert_frame_equal(r, sin)
    # envenenar 201910 tampoco cambia nada
    env = res.assign(g_201910=np.nan, auc_201910=np.nan)
    pd.testing.assert_frame_equal(r, va.ranking_201908(env))
    assert set(va.curva_k_201908(ens.drop(columns=["g_201910"])).columns) == {"estrategia", "k", "g_201908"}
    e10 = va.ensambles_201908(r, ens.drop(columns=["g_201910"]))
    assert list(e10["estrategia"]) == [1, 2] and not any("201910" in c for c in e10.columns)


def test_tabla_201910_respeta_el_orden_de_201908_aunque_201910_ordene_distinto():
    res, ens = _sintetico((5e6, 3e6), (1e6, 9e6))
    r = va.ranking_201908(res)
    t = va.tabla_201910(r, res, ens, {1: 4, 2: 4})
    assert list(t["estrategia"]) == [1, 2]
    assert t["g_201910"].iloc[1] > t["g_201910"].iloc[0]            # 201910 las ordenaría al revés; la tabla no
    assert t["ens_k_201910"].iloc[0] == 1e6 + 40                    # ensamble del K del presupuesto, no del mejor K
    t0 = va.tabla_201910(r, res, ens, {1: 0, 2: 0})
    assert t0["ens_k_201910"].isna().all()


def _datos_falsos(n_va=60, n_te=70):
    rng = np.random.default_rng(0)
    d = types.SimpleNamespace(x_va=np.zeros((n_va, 1)), x_te=np.zeros((n_te, 1)),
                              b2_va=(rng.random(n_va) < 0.2).astype(int), b2_te=(rng.random(n_te) < 0.2).astype(int),
                              y_va=(rng.random(n_va) < 0.3).astype(int), y_te=(rng.random(n_te) < 0.3).astype(int))
    return d, rng


def test_correr_estrategia_no_calcula_maximo_ni_curva_en_201910(monkeypatch):
    d, rng = _datos_falsos()
    monkeypatch.setattr(va, "entrenar_semilla", lambda e, hp, s, d_: (rng.random(60), rng.random(70), 1.5))
    filas, ens = va.correr_estrategia(es.estrategia(1), {}, 100.0, 3, d)
    assert len(filas) == 3 and [f["semilla"] for f in filas] == bl.SEMILLAS_OFICIALES[:3]
    assert not any(c.startswith("gmax_201910") for c in filas[0])
    assert {"g_201908", "gmax_201908", "auc_201908", "g_201910", "auc_201910"} <= set(filas[0])
    assert [e["k"] for e in ens] == [1, 2, 3]


def test_correr_estrategia_extiende_las_semillas_hasta_el_k_del_presupuesto(monkeypatch):
    d, rng = _datos_falsos()
    monkeypatch.setattr(va, "entrenar_semilla", lambda e, hp, s, d_: (rng.random(60), rng.random(70), 100.0))
    filas, ens = va.correr_estrategia(es.estrategia(1), {}, 0.0, 3, d, presupuesto_s=900.0)   # K = 9
    assert len(filas) == 9 and len(ens) == 9
    assert [f["semilla"] for f in filas] == es.semillas(9)
    filas, _ = va.correr_estrategia(es.estrategia(1), {}, 800.0, 3, d, presupuesto_s=900.0)   # K = 1 < 3: no recorta
    assert len(filas) == 3


def test_agregar_de_punta_a_punta_con_csv_sinteticos(tmp_path):
    res, ens = _sintetico((5e6, 3e6), (1e6, 9e6))
    for e in (1, 2):
        res[res["estrategia"] == e].to_csv(tmp_path / f"semillas_original_e{e}.csv", index=False)
        ens[ens["estrategia"] == e].to_csv(tmp_path / f"ensambles_original_e{e}.csv", index=False)
    out = va.agregar(tmp_path, "original", 900.0)
    assert all(p.exists() for p in out.values())
    assert "201910" in out["html"].read_text(encoding="utf-8")
    assert list(pd.read_csv(out["ranking_201908"])["estrategia"]) == [1, 2]
    with pytest.raises(FileNotFoundError):
        va.agregar(tmp_path, "ledger")
