"""`pares.csv` (`tiempos-confiables-y-consistencia` D12): pares entre experimentos con la cuenta de `ledger.replicas`."""

import numpy as np
import pandas as pd
import pytest

from comun import consolidar, variantes
from comun import ledger as lg

SEMILLAS = list(range(20))


def finales(variante, replicas, media, rng, filas=1000, semillas=SEMILLAS, sd_rep=20.0, sd_sem=10.0):
    filas_ = []
    for k in replicas:
        centro = media + rng.normal(0, sd_rep)
        for s in semillas:
            filas_.append({"variante": variante, "replica_opt": k, "semilla": s, "g": centro + rng.normal(0, sd_sem),
                           "filas_train": filas, "metodo": "x", "tasa": 0.1})
    return pd.DataFrame(filas_)


@pytest.fixture
def tres(request):
    rng = np.random.default_rng(3)
    return {"A": finales("A", range(4), 1030.0, rng, 1200), "B": finales("B", range(4), 1000.0, rng, 1000),
            "C": finales("C", range(4), 1010.0, rng, 900)}


def test_un_par_de_un_solo_experimento_da_lo_mismo_que_su_replicas_csv(tres):
    todo = pd.concat(tres.values(), ignore_index=True)
    r = lg.replicas(todo, 5.0, pares=[("A", "B")], pares_welch=[("A", "C")]).set_index("variante")
    p = lg.pares_directos(todo, [("A", "B")], [("A", "C")]).set_index("variante")
    for par in ("A - B", "A - C"):
        for col in ("n_replicas", "n_semillas", "delta_g_media", "delta_g_se", "delta_g_ic_inf", "delta_g_ic_sup", "veredicto"):
            assert p.loc[par, col] == pytest.approx(r.loc[par, col]) if col != "veredicto" else p.loc[par, col] == r.loc[par, col]
        assert p.loc[par, "estado"] == "completo"
    assert p.loc["A - B", "filas_train_a"] == 1200 and p.loc["A - B", "filas_train_b"] == 1000


def test_un_par_al_que_le_falta_un_lado_sale_pendiente_con_el_nombre_de_la_variante_que_falta(tres):
    p = lg.pares_directos(tres["A"], [("A", "B")], [("A", "C"), ("Z", "A")])
    assert list(p["estado"]) == ["pendiente"] * 3 and list(p["veredicto"]) == ["pendiente"] * 3
    faltan = dict(zip(p["variante"], p["faltan"]))
    assert faltan == {"A - B": "B", "A - C": "C", "Z - A": "Z"}
    assert "B" in p.loc[0, "nota"]


def test_una_replica_incompleta_no_entra_y_el_par_dice_cuantas_uso(tres):
    b = tres["B"]
    b = b[~((b["replica_opt"] == 3) & (b["semilla"] >= 15))]  # la réplica 3 de B tiene 15 semillas
    todo = pd.concat([tres["A"], b], ignore_index=True)
    p = lg.pares_directos(todo, [("A", "B")], []).iloc[0]
    assert (p["estado"], p["n_replicas"], p["replicas"], p["n_semillas"]) == ("completo", 3, "0 1 2", 60)
    assert "usa 3 réplicas" in p["nota"] and "A: 4" in p["nota"]
    welch = lg.pares_directos(todo, [], [("A", "B")]).iloc[0]
    assert welch["n_replicas"] == 3 and welch["replicas"] == "0 1 2"


def test_con_menos_de_dos_replicas_completas_en_comun_es_pendiente_y_no_falta_ninguna_variante(tres):
    solo_una = tres["B"][tres["B"]["replica_opt"] == 0]
    p = lg.pares_directos(pd.concat([tres["A"], solo_una], ignore_index=True), [("A", "B")], []).iloc[0]
    assert p["estado"] == "pendiente" and p["faltan"] == "" and "menos de dos réplicas completas" in p["nota"]


def test_los_pares_declarados_aparecen_todos_y_traen_lo_que_aislan(tres):
    todo = pd.concat(tres.values(), ignore_index=True)
    info = {("A", "B"): ("algo", True)}
    p = lg.pares_directos(todo, [("A", "B")], [("A", "C")], info)
    assert list(p["variante"]) == ["A - B", "A - C"]
    assert (p.loc[0, "aisla"], bool(p.loc[0, "principal"])) == ("algo", True) and not p.loc[1, "principal"]
    assert set(p["tipo"]) == {"apareado", "Welch"}


def test_el_registro_declara_todos_los_pares_y_pares_csv_los_trae_a_todos():
    pares = [*variantes.PARES_APAREADOS, *variantes.PARES_WELCH]
    t = lg.pares_directos(pd.DataFrame(columns=["variante", "replica_opt", "semilla", "g", "filas_train"]),
                          variantes.PARES_APAREADOS, variantes.PARES_WELCH, variantes.PARES_INFO)
    assert {(a, b) for a, b in zip(t["a"], t["b"])} == set(pares)
    assert set(t["estado"]) == {"pendiente"} and (t["faltan"] != "").all()


def test_consolidar_arma_pares_csv_desde_los_resultados_de_todos_los_duenos():
    t = consolidar.pares_entre_experimentos()
    pares = [*variantes.PARES_APAREADOS, *variantes.PARES_WELCH]
    assert len(t) == len(pares) and set(zip(t["a"], t["b"])) == set(pares)
    assert (t["n_estrella"] == 3300).all()
    with pytest.raises(ValueError, match="vigente"):
        consolidar.pares_entre_experimentos("201903-201906")
