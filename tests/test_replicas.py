"""Réplicas de optimización (`h3-semillas-optuna` grupo 2): registro, dueños de `@k`, reescalado y corredor."""

import pytest

from comun import correr, ledger as lg, metodos, rutas, variantes


def _ctx(*argv):
    return correr.Contexto(correr.parsear(["--filas", "100", *argv]))


def test_regla_de_duenos_de_los_estudios_con_replica():
    assert variantes.dueno_estudio("U0.1") == "h1"
    assert variantes.dueno_estudio("U0.1@3") == "h3"
    assert variantes.dueno_estudio("U0.05@7") == "h3"
    assert variantes.dueno_estudio("C") == "control"
    assert variantes.dueno_estudio("C@2") == "control"


def test_estudios_sin_replicas_o_con_replica_mal_escrita_fallan_nombrandolos():
    with pytest.raises(ValueError, match="B0.5@1"):
        variantes.dueno_estudio("B0.5@1")
    with pytest.raises(ValueError, match="U0.5@1"):
        variantes.dueno_estudio("U0.5@1")  # U0.5 no tiene variante H3 en el registro
    with pytest.raises(ValueError, match="U0.1@0"):
        variantes.dueno_estudio("U0.1@0")
    with pytest.raises(ValueError, match="U0.1@x"):
        variantes.dueno_estudio("U0.1@x")


def test_nombre_de_estudio_con_replica():
    assert variantes.nombre_estudio("U0.1", 0) == "U0.1"
    assert variantes.nombre_estudio("U0.1", 3) == "U0.1@3"
    assert variantes.partir_estudio("U0.1@3") == ("U0.1", 3)
    assert variantes.partir_estudio("C") == ("C", 0)


def test_variantes_que_admiten_replicas():
    admiten = {b.nombre for b in variantes.VARIANTES.values() if b.replicas}
    assert admiten == {"C", "H3-0.25", "H3-0.1", "H3-0.05", "H3R-0.1", "H3R-0.25", "H3L-0.25", "H3L-0.1", "H3K-0.1",
                       "H4H-0.1", "H4U-0.1", "H4F-0.05", "H4F-0.25"}
    assert variantes.variante("H3R-0.1").estudio == "U0.1" and variantes.variante("H3R-0.1").dueno == "h3"
    assert variantes.variante("H3-0.05").estudio == "U0.05"


@pytest.mark.parametrize("nombre", ["U0.1", "B0.5", "GOSS", "C-rep"])
def test_replica_no_habilitada_falla_nombrando_variante_y_replica(nombre):
    with pytest.raises(ValueError, match=rf"{nombre}.*réplica 2"):
        variantes.validar_replica(nombre, 2)
    variantes.validar_replica(nombre, 0)  # la réplica 0 siempre vale


def test_replica_negativa_falla():
    with pytest.raises(ValueError, match="H3-0.1"):
        variantes.validar_replica("H3-0.1", -1)


def test_dueno_de_la_fila_de_una_optimizacion_con_replica():
    assert variantes.dueno_variante("U0.1") == "h1"
    assert variantes.dueno_variante("U0.1", 3) == "h3"
    assert variantes.dueno_variante("C", 3) == "control"
    assert variantes.dueno_variante("H3-0.1", 3) == "h3"


def test_dependencias_implicitas_no_cambian_con_las_variantes_nuevas():
    dep = variantes.implicitas()
    assert dep["h3"] == {"control", "h1"} and dep["h1"] == {"control"}


@pytest.mark.parametrize("r,min_leaf,esperado", [(0.1, 35, 111), (0.1, 1752, 5540), (0.1, 5000, 8000), (0.25, 10, 20),
                                                 (0.05, 1, 4), (1.0, 7, 7)])
def test_reescalado_de_min_data_in_leaf(r, min_leaf, esperado):
    hp = {"num_leaves": 12, "min_data_in_leaf": min_leaf}
    nuevo = metodos.ajustar_hp("opt-muestra-reescalado", r, hp)
    assert nuevo["min_data_in_leaf"] == esperado and nuevo["num_leaves"] == 12
    assert hp["min_data_in_leaf"] == min_leaf  # no muta la entrada


def test_reescalado_recorta_a_1_y_8000():
    assert metodos.ajustar_hp("opt-muestra-reescalado", 1e-8, {"min_data_in_leaf": 5000})["min_data_in_leaf"] == 8000
    assert metodos.ajustar_hp("opt-muestra-reescalado", 1.0, {"min_data_in_leaf": 0})["min_data_in_leaf"] == 1


@pytest.mark.parametrize("metodo", ["uniforme", "bagging", "goss", "opt-muestra"])
def test_los_otros_metodos_no_tocan_los_hp(metodo):
    hp = {"min_data_in_leaf": 1752, "num_leaves": 12}
    assert metodos.ajustar_hp(metodo, 0.1, hp) == hp


def test_h3r_valida_como_h3():
    metodos.validar("opt-muestra-reescalado", 0.1)
    with pytest.raises(ValueError, match="opt-muestra-reescalado"):
        metodos.validar("opt-muestra-reescalado", 1.0)


# --- corredor -----------------------------------------------------------------


def test_replica_0_conserva_estudio_semilla_e_id():
    cx = _ctx("--metodo", "uniforme", "--tasa", "1", "--etapa", "optimizar")
    assert (cx.replica, cx.semilla_opt, cx.estudio) == (0, 0, "C")
    assert "@" not in cx.id(0, "optimizar")


def test_replica_3_de_h3_usa_estudio_semilla_y_dueno_de_la_replica():
    a = correr.parsear(["--metodo", "opt-muestra", "--tasa", "0.1", "--etapa", "optimizar", "--replica", "3"])
    cx = correr.Contexto(a)
    assert (cx.replica, cx.semilla_opt, cx.estudio, cx.variante) == (3, 3, "U0.1@3", "U0.1")
    assert cx.raiz == rutas.ledger("h3") and cx.ruta_hp() == rutas.ledger("h3") / ("exploracion" if cx.explora else "") / "hp" / "U0.1@3.json"
    assert "U0.1@3_" in cx.id(3, "optimizar") or cx.id(3, "optimizar").startswith("exp-U0.1@3_")
    assert cx.fila()["replica_opt"] == 3


def test_final_de_h3r_con_replica_lee_el_estudio_de_la_replica_y_escribe_en_h3():
    cx = correr.Contexto(correr.parsear(["--metodo", "opt-muestra-reescalado", "--tasa", "0.1", "--etapa", "final",
                                         "--semilla", "todas", "--replica", "3"]))
    assert (cx.variante, cx.estudio, cx.raiz) == ("H3R-0.1", "U0.1@3", rutas.ledger("h3"))
    assert "H3R-0.1@3_" in cx.id(100003, "final") or "exp-H3R-0.1@3_" in cx.id(100003, "final")


def test_replica_del_control_va_al_ledger_del_control():
    cx = correr.Contexto(correr.parsear(["--metodo", "uniforme", "--tasa", "1", "--etapa", "optimizar", "--replica", "2"]))
    assert (cx.estudio, cx.raiz) == ("C@2", rutas.ledger("control"))


@pytest.mark.parametrize("argv,nombre", [
    (["--metodo", "uniforme", "--tasa", "0.25", "--etapa", "optimizar", "--replica", "1"], "U0.25"),
    (["--metodo", "bagging", "--tasa", "0.5", "--etapa", "final", "--replica", "1"], "B0.5"),
    (["--metodo", "opt-muestra", "--tasa", "0.1", "--etapa", "final", "--replica", "-1"], "H3-0.1"),
])
def test_el_corredor_rechaza_replicas_invalidas_antes_de_cargar_datos(argv, nombre, capsys):
    with pytest.raises(SystemExit):
        correr.parsear(argv)
    assert nombre in capsys.readouterr().err


def test_la_columna_replica_opt_es_del_esquema_y_de_la_clave():
    assert "replica_opt" in lg.COLUMNAS and "replica_opt" in lg.CLAVE
