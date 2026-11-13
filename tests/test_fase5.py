"""Las listas de la fase 5 (`h3-semillas-optuna` D3) cubren las 37 celdas y los 28 estudios nuevos sin repetir."""

from collections import Counter

import pytest

from comun import correr, rutas, variantes

LISTAS = rutas.experimento("sampling_1") / "scripts"
NOMBRES = [f"fase5_r{k}" for k in range(8)]
VARIANTES = ["C", "H3-0.25", "H3-0.1", "H3-0.05", "H3R-0.1"]
YA_CORRIDAS = {("C", 0), ("H3-0.25", 0), ("H3-0.1", 0)}


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


def test_37_celdas_nuevas_sin_repetir(corridas):
    celdas = [(cx.variante, cx.replica) for cs in corridas.values() for cx in cs if cx.a.etapa == "final"]
    assert not [c for c, n in Counter(celdas).items() if n > 1]
    esperadas = {(v, k) for v in VARIANTES for k in range(8)} - YA_CORRIDAS
    assert len(esperadas) == 37 and set(celdas) == esperadas


def test_28_estudios_nuevos_sin_repetir(corridas):
    estudios = [cx.estudio for cs in corridas.values() for cx in cs if cx.a.etapa == "optimizar"]
    assert not [e for e, n in Counter(estudios).items() if n > 1]
    esperados = {f"{e}@{k}" for e in ("C", "U0.25", "U0.1", "U0.05") for k in range(1, 8)}
    assert len(esperados) == 28 and set(estudios) == esperados


def test_las_semillas_son_las_de_siempre_y_los_finales_son_todas(corridas):
    for cs in corridas.values():
        for cx in cs:
            assert cx.a.semilla == ("0" if cx.a.etapa == "optimizar" else "todas")


def test_destinos_de_ledger_y_de_hp(corridas):
    for cs in corridas.values():
        for cx in cs:
            if cx.replica == 0:
                assert cx.raiz == rutas.ledger("h3") and cx.ruta_hp().parent.parent in (rutas.ledger("h1"),)
            elif cx.variante == "C":
                assert cx.raiz == rutas.ledger("control") and cx.ruta_hp().parent.parent == rutas.ledger("control")
            else:
                # D10: los estudios `U{r}@k` son de h1, aunque los lea una variante de h3
                assert cx.raiz == rutas.ledger(variantes.dueno_variante(cx.variante, cx.replica))
                assert cx.ruta_hp().parent.parent == rutas.ledger(variantes.dueno_estudio(cx.estudio))
                assert cx.ruta_hp().name == f"{cx.estudio}.json"


def test_cada_final_tiene_su_optimizacion_en_la_misma_lista_o_ya_existe(corridas):
    for k, nombre in enumerate(NOMBRES[1:], start=1):
        estudios = {cx.estudio for cx in corridas[nombre] if cx.a.etapa == "optimizar"}
        finales = {cx.estudio for cx in corridas[nombre] if cx.a.etapa == "final"}
        assert finales <= estudios, nombre
    for cx in corridas["fase5_r0"]:  # k = 0: los estudios son de h1
        assert cx.ruta_hp().exists() or cx.explora
