"""`comun.consolidar --sanity`, chequeos de la fase 8 (`tiempos-confiables-y-consistencia` D9, D10)."""

import pandas as pd

from comun import baseline as bl
from comun import consolidar, variantes

V = variantes.Variante
REGISTRO = {"U0.5": V("U0.5", "h1", "uniforme", 0.5, "U0.5", replicas=True), "C-rep": V("C-rep", "control", "uniforme", 1.0, "C")}


def finales(celdas):
    """`celdas`: {(variante, réplica): cantidad de semillas}."""
    filas = [{"etapa": "final", "meses_final": bl.VENTANA_FINAL, "variante": v, "replica_opt": k, "semilla": s}
             for (v, k), n in celdas.items() for s in range(n)]
    return pd.DataFrame(filas)


def completo():
    return {**{("U0.5", k): 20 for k in range(8)}, ("C-rep", 0): 20}


def chk(res, corridas=None):
    return consolidar.chequeos_fase8(res, REGISTRO, {} if corridas is None else corridas)


def test_ocho_replicas_por_veinte_semillas_en_cada_variante_del_bloque_a():
    nombre, ok, detalle = chk(finales(completo()))[0]
    assert ok and "9 celdas" in nombre and detalle == ""


def test_falta_una_replica_o_una_semilla_y_dice_cual():
    celdas = completo()
    del celdas[("U0.5", 7)]
    celdas[("U0.5", 3)] = 19
    _, ok, detalle = chk(finales(celdas))[0]
    assert not ok and "U0.5@7: 0" in detalle and "U0.5@3: 19" in detalle and "faltan 2" in detalle


def test_c_rep_se_exige_con_una_sola_replica():
    celdas = completo()
    celdas[("C-rep", 1)] = 20  # una réplica de más no es lo que pide el registro: C-rep no tiene réplicas
    assert chk(finales(celdas))[0][1]
    del celdas[("C-rep", 0)]
    assert not chk(finales(celdas))[0][1]


def test_un_estudio_de_h1_en_corridas_de_h3_falla_y_en_h1_no():
    res = finales(completo())
    sano = {"h1": ["U0.25@1_uniforme_0.25_1_optimizar_abc.csv"], "h3": ["H3-0.25@1_opt-muestra_0.25_1_final_abc.csv"]}
    assert chk(res, sano)[1][1]
    malo = {"h3": ["U0.25@1_uniforme_0.25_1_optimizar_abc.csv"]}
    nombre, ok, detalle = chk(res, malo)[1]
    assert not ok and "h3/U0.25@1_uniforme_0.25_1_optimizar_abc.csv" in detalle


def test_el_repo_no_tiene_estudios_de_otro_dueno_en_corridas():
    assert all(not (n.startswith("U") and e != "h1") for e, nombres in consolidar.nombres_de_corridas().items() for n in nombres)
    assert consolidar.chequeos_fase8(pd.DataFrame({"etapa": [], "meses_final": [], "variante": [], "replica_opt": []}))[1][1]
