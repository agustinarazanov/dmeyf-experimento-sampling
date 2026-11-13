"""Las listas de la fase 7 (`final-con-julio-agosto` D8) cubren las 121 celdas y los 8 estudios `F0.5@k` sin repetir."""

from collections import Counter

import pytest

from comun import baseline as bl
from comun import correr, rutas, variantes

LISTAS = rutas.experimento("sampling_1") / "scripts"
NOMBRES = [f"fase7_r{k}" for k in range(8)]


def leer(nombre):
    """Contextos de cada línea de la lista, con la misma lectura de columnas que vm.sh."""
    out = []
    for linea in (LISTAS / f"{nombre}.txt").read_text().splitlines():
        if not linea.strip() or linea.lstrip().startswith("#"):
            continue
        metodo, tasa, semilla, etapa, *resto = linea.split()
        variante = resto[0] if resto else "-"
        replica = resto[1] if len(resto) > 1 else None
        argv = ["--metodo", metodo, "--tasa", tasa, "--semilla", semilla, "--etapa", etapa]
        if variante != "-":
            argv += ["--variante", variante]
        if replica:
            argv += ["--replica", replica]
        out.append(correr.Contexto(correr.parsear(argv)))
    return out


@pytest.fixture(scope="module")
def corridas():
    return {n: leer(n) for n in NOMBRES}


def test_cada_lista_es_de_una_sola_replica(corridas):
    for k, nombre in enumerate(NOMBRES):
        assert {cx.replica for cx in corridas[nombre]} == {k}, nombre


def test_121_celdas_sin_repetir_con_todas_las_semillas(corridas):
    finales = [(cx.variante, cx.replica) for n in NOMBRES for cx in corridas[n] if cx.a.etapa == "final"]
    assert len(finales) == 121 and not [c for c, n in Counter(finales).items() if n > 1]
    # el registro de entonces: sin las variantes de `tiempos-confiables-y-consistencia` (D8) y con réplicas solo donde ya las había (D9)
    nuevas = {"H3-0.5", "B0.05", *[f"H4{x}-{f}" for x in "OP" for f in ("0.25", "0.1", "0.05")], "H4P-0.5"}
    sin_replicas = {"U0.5", "U0.25", "U0.1", "U0.05", "B0.5", "B0.25", "B0.1", "GOSS", "C-rep"}
    esperadas = {(b.nombre, k) for b in variantes.VARIANTES.values() if b.nombre not in nuevas
                 for k in (range(8) if b.replicas and b.nombre not in sin_replicas else [0])}
    assert set(finales) == esperadas
    assert all(cx.a.semilla == "todas" for n in NOMBRES for cx in corridas[n] if cx.a.etapa == "final")
    assert len(bl.SEMILLAS_FINALES) == 20 and len(set(bl.SEMILLAS_FINALES)) == 20


def test_8_estudios_f05_y_cada_lista_empieza_por_el_estudio(corridas):
    estudios = [cx.estudio for n in NOMBRES for cx in corridas[n] if cx.a.etapa == "optimizar"]
    assert sorted(estudios) == sorted(["F0.5"] + [f"F0.5@{k}" for k in range(1, 8)])
    for n in NOMBRES:
        assert corridas[n][0].a.etapa == "optimizar" and corridas[n][0].variante == "H4O-0.5"


def test_r0_suma_h1_h2_y_c_rep(corridas):
    v0 = {cx.variante for cx in corridas["fase7_r0"]}
    assert {"U0.5", "U0.25", "U0.1", "U0.05", "B0.5", "B0.25", "B0.1", "GOSS", "C-rep", "H4O-0.5"} <= v0
    for n in NOMBRES[1:]:
        assert not {cx.variante for cx in corridas[n]} & {"U0.5", "B0.5", "GOSS", "C-rep"}
