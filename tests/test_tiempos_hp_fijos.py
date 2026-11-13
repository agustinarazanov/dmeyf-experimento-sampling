"""`experimentos/sampling_1/scripts/tiempos_hp_fijos.py` (D4, D6), sin datos reales."""

import numpy as np
import pandas as pd
import pytest

from comun import datos as dt
from experimentos.sampling_1.scripts import tiempos_hp_fijos as t


def test_216_mediciones_en_orden_aleatorio_de_semilla_fija_y_sin_repetir():
    c = t.celdas(t.JUEGOS)
    assert len(c) == 216 and sum(x["receta"] == "azar" for x in c) == 120 and sum(x["receta"] == "bajas" for x in c) == 96
    assert len({t.nombre_archivo(x) for x in c}) == 216
    assert c == t.celdas(t.JUEGOS) and c != sorted(c, key=t.nombre_archivo)  # mismo orden siempre, y no el lexicográfico
    assert {x["tasa"] for x in c if x["receta"] == "azar"} == {1.0, 0.5, 0.25, 0.1, 0.05}
    assert {x["tasa"] for x in c if x["receta"] == "bajas"} == {0.5, 0.25, 0.1, 0.05}
    assert {x["juego"] for x in c} == {"C", *("C@" + str(k) for k in range(1, 8))}


def test_se_niega_a_correr_fuera_de_la_vm_salvo_con_prueba(monkeypatch):
    monkeypatch.setattr(t.correr, "tipo_de_maquina", lambda: "local")
    with pytest.raises(SystemExit, match="n2-highmem-8"):
        t.main([])
    with pytest.raises(SystemExit, match="n2-highmem-8"):
        t.main(["--calibracion", "x", "inicio"])


def test_la_receta_de_bajas_pesa_1_sobre_f_y_la_de_azar_no_pesa():
    rng = np.random.default_rng(0)
    y = (rng.random(4000) < 0.1).astype(int)
    train = pd.DataFrame({dt.ID: np.arange(4000), dt.Y: y, "a": rng.normal(size=4000)})
    d, _, peso = t.muestra("azar", train, 0.25, 1001)
    assert peso is None and len(d) == 1000
    d, _, peso = t.muestra("bajas", train, 0.1, 1001)
    assert d[dt.Y].sum() == y.sum() and set(np.unique(peso[d[dt.Y].to_numpy() == 0])) == {10.0}


def test_consolidar_arma_los_dos_csv_y_suma_las_anclas(tmp_path, monkeypatch):
    monkeypatch.setattr(t.rutas, "EXPERIMENTOS", tmp_path / "experimentos")
    base = t.raiz_tiempos()
    (base / "hp_fijos").mkdir(parents=True)
    for k in range(3):
        pd.DataFrame([{"receta": "azar", "tasa": 1.0, "juego": "C", "repeticion": k, "t_medicion_s": 20 + k}]).to_csv(
            base / "hp_fijos" / ("azar_1_C_" + str(k) + ".csv"), index=False)
    for momento, tt in (("inicio", 27.0), ("fin", 28.0)):
        pd.DataFrame([{"tipo": "trial", "repeticion": 0, "t_s": tt, "lista": "l1", "momento": momento},
                      {"tipo": "final", "repeticion": 0, "t_s": 45.0, "lista": "l1", "momento": momento}]).to_csv(
            base / ("calibracion_l1_" + momento + ".csv"), index=False)
    pd.DataFrame([{"estudio": "C", "duracion_s": 27.15}]).to_csv(base / "anclas_trials.csv", index=False)
    ctrl = t.rutas.ledger("control")
    ctrl.mkdir(parents=True)
    f = {"etapa": "final", "meses_final": t.VENTANA_FASE7, "semilla": t.SEMILLA_FINAL_CALIBRACION, "replica_opt": 0}
    pd.DataFrame([dict(f, variante="C", tiempo_entrenamiento_s=50.0), dict(f, variante="C-rep", tiempo_entrenamiento_s=45.0)]
                 ).to_csv(ctrl / "resultados.csv", index=False)
    hp, cal = t.consolidar()
    assert len(pd.read_csv(hp)) == 3
    c = pd.read_csv(cal)
    assert len(c) == 4 and set(c["momento"]) == {"inicio", "fin"}
    tr, fi = c[c["tipo"] == "trial"], c[c["tipo"] == "final"]
    assert (tr["ancla_trial_s"] == 27.15).all() and (fi["ancla_final_fase7_s"] == 50.0).all() and (fi["ancla_final_crep_s"] == 45.0).all()
    assert fi["cociente_ancla_crep"].tolist() == [1.0, 1.0]


def test_dos_listas_no_escriben_el_mismo_archivo_de_calibracion(tmp_path, monkeypatch):
    monkeypatch.setattr(t.rutas, "EXPERIMENTOS", tmp_path / "experimentos")
    nombres = {t.raiz_tiempos() / ("calibracion_" + lista + "_" + m + ".csv")
               for lista in ("fase8_r0_a", "fase8_r1_a", "fase8_r0_b") for m in t.MOMENTOS}
    assert len(nombres) == 6
