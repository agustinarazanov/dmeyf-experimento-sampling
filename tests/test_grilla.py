"""`tiempos-confiables-y-consistencia` D8, D9, D11, D12: la grilla común y los pares directos del registro."""

from comun import variantes

V = variantes.VARIANTES


def test_la_grilla_tiene_20_variantes_cinco_formas_por_cuatro_tasas():
    en_grilla = [b for b in V.values() if b.grilla in variantes.FILAS_GRILLA]
    assert len(en_grilla) == 20
    for fila in variantes.FILAS_GRILLA:
        assert sorted(b.tasa for b in en_grilla if b.grilla == fila) == sorted(variantes.TASAS_GRILLA), fila
    duenos = {fila: {b.dueno for b in en_grilla if b.grilla == fila} for fila in variantes.FILAS_GRILLA}
    assert duenos == {"U": {"h1"}, "H3": {"h3"}, "H4O": {"h4"}, "H4P": {"h4"}, "B": {"h2"}}


def test_toda_variante_esta_en_la_grilla_es_control_o_dice_que_cruza():
    for b in V.values():
        assert b.grilla in variantes.FILAS_GRILLA or b.grilla == "control" or b.nombre in variantes.FUERA_DE_GRILLA, b.nombre
    assert set(variantes.FUERA_DE_GRILLA) == {b.nombre for b in V.values() if not b.grilla}


def test_cada_celda_de_la_grilla_tiene_variante_o_motivo_declarado():
    for fila in variantes.FILAS_GRILLA:
        for tasa in variantes.TASAS_GRILLA:
            hay = [b for b in V.values() if b.grilla == fila and b.tasa == tasa]
            assert len(hay) == 1 or (not hay and variantes.CELDAS_SIN_CORRER.get((fila, tasa))), (fila, tasa)
    for celda in variantes.CELDAS_SIN_CORRER:  # un hueco declarado que ya tiene variante está de más
        assert not [b for b in V.values() if (b.grilla, b.tasa) == celda]


def test_8_replicas_en_todo_el_bloque_a_menos_c_rep():
    assert all(b.replicas for b in V.values() if b.nombre != "C-rep")


def test_cada_par_declarado_dice_que_aisla_y_los_principales_son_los_cuatro_h4o_menos_u():
    pares = [*variantes.PARES_APAREADOS, *variantes.PARES_WELCH]
    assert set(pares) == set(variantes.PARES_INFO) and len(pares) == len(set(pares))
    assert all(a in V and b in V for a, b in pares)
    assert all(variantes.PARES_INFO[p][0] for p in pares)
    principales = {p for p, (_, principal) in variantes.PARES_INFO.items() if principal}
    assert principales == {("H4O-" + f"{r:g}", "U" + f"{r:g}") for r in variantes.TASAS_GRILLA}


def test_17_contrastes_de_la_grilla():
    t = variantes.TASAS_GRILLA
    nuevos = ([("U" + f"{r:g}", "H3-" + f"{r:g}") for r in t] + [("H4O-" + f"{r:g}", "H4P-" + f"{r:g}") for r in t]
              + [("H4O-" + f"{r:g}", "U" + f"{r:g}") for r in t] + [("H4P-" + f"{r:g}", "H3-" + f"{r:g}") for r in t]
              + [("H4P-0.1", "H4U-0.1")])
    assert len(nuevos) == 17
    pares = {*variantes.PARES_APAREADOS, *variantes.PARES_WELCH}
    assert set(nuevos) <= pares


def test_los_pares_apareados_comparten_estudio_y_h4o_contra_u_no():
    for a, b in variantes.PARES_APAREADOS:
        assert V[a].estudio == V[b].estudio, (a, b)
    for r in variantes.TASAS_GRILLA:
        assert V["H4O-" + f"{r:g}"].estudio != V["U" + f"{r:g}"].estudio
    assert V["H4P-0.1"].estudio != V["H4U-0.1"].estudio  # no comparten estudio: Welch


def test_dependencias_implicitas_con_la_grilla():
    dep = variantes.implicitas()
    assert dep["h1"] == {"control"} and dep["h3"] == {"control", "h1"} and dep["h4"] == {"control", "h1"}
