"""Las listas de la fase 8 (`tiempos-confiables-y-consistencia` D15): 67 estudios y 2.560 finales, sin repetir, y los
lanzadores en seco."""

import re
import subprocess
from collections import Counter

import pandas as pd
import pytest

from comun import correr, rutas, variantes

LISTAS = rutas.experimento("sampling_1") / "scripts"
NOMBRES = [f"fase8_r{k}_{s}" for k in range(8) for s in "ab"] + ["fase8_medicion"]
CON_CORRIDAS = [n for n in NOMBRES if n != "fase8_medicion"]
# Los chequeos de antes de lanzar dejan de aplicar cuando la fase ya corrió (14-nov-2026): la calibración es su rastro.
YA_CORRIDA = pytest.mark.skipif((rutas.ledger("sampling_1") / "calibracion.csv").exists(), reason="la fase 8 ya corrió")


def leer(nombre):
    """Contextos de cada línea de corrida de la lista (las líneas `@ módulo` no son corridas de `comun.correr`)."""
    out = []
    for linea in (LISTAS / f"{nombre}.txt").read_text().splitlines():
        if not linea.strip() or linea.lstrip().startswith(("#", "@")):
            continue
        metodo, tasa, semilla, etapa, *resto = linea.split()
        argv = ["--metodo", metodo, "--tasa", tasa, "--semilla", semilla, "--etapa", etapa]
        if resto and resto[0] != "-":
            argv += ["--variante", resto[0]]
        if len(resto) > 1:
            argv += ["--replica", resto[1]]
        out.append(correr.Contexto(correr.parsear(argv)))
    return out


@pytest.fixture(scope="module")
def corridas():
    return {n: leer(n) for n in CON_CORRIDAS}


def test_17_listas_y_cada_una_de_una_sola_replica(corridas):
    assert len(NOMBRES) == 17 and all((LISTAS / f"{n}.txt").exists() for n in NOMBRES)
    for n in CON_CORRIDAS:
        k = int(re.match(r"fase8_r(\d)_", n).group(1))
        assert {cx.replica for cx in corridas[n]} == {k}, n


def test_67_estudios_y_2560_finales_sin_repetir(corridas):
    estudios = [cx.estudio for n in CON_CORRIDAS for cx in corridas[n] if cx.a.etapa == "optimizar"]
    finales = [(cx.variante, cx.replica) for n in CON_CORRIDAS for cx in corridas[n] if cx.a.etapa == "final"]
    assert len(estudios) == 67 and not [e for e, n in Counter(estudios).items() if n > 1]
    assert len(finales) * 20 == 2560 and not [f for f, n in Counter(finales).items() if n > 1]
    assert all(cx.a.semilla == "todas" for n in CON_CORRIDAS for cx in corridas[n] if cx.a.etapa == "final")


def test_los_estudios_y_los_finales_son_los_de_d15(corridas):
    por_lista = {n: ([cx.estudio for cx in c if cx.a.etapa == "optimizar"], sorted(cx.variante for cx in c if cx.a.etapa == "final"))
                 for n, c in corridas.items()}
    assert por_lista["fase8_r0_a"][0] == ["F0.25", "F0.1", "F0.05"]
    assert por_lista["fase8_r0_a"][1] == sorted(["H3-0.5", "H4O-0.25", "H4O-0.1", "H4O-0.05", "H4P-0.5", "H4P-0.25", "H4P-0.1", "H4P-0.05"])
    assert por_lista["fase8_r0_b"] == (["B0.05"], ["B0.05"])
    for k in range(1, 8):
        a, b = por_lista[f"fase8_r{k}_a"], por_lista[f"fase8_r{k}_b"]
        assert a[0] == [f"U0.5@{k}", f"F0.25@{k}", f"F0.1@{k}", f"F0.05@{k}"] and len(a[1]) == 12
        assert b[0] == [f"B0.5@{k}", f"B0.25@{k}", f"B0.1@{k}", f"B0.05@{k}", f"GOSS@{k}"]
        assert b[1] == sorted(["B0.5", "B0.25", "B0.1", "B0.05", "GOSS"])


@YA_CORRIDA
def test_cada_estudio_va_antes_que_sus_finales_y_ninguna_a_lee_de_una_b(corridas):
    propios_b = {cx.estudio for n in CON_CORRIDAS if n.endswith("_b") for cx in corridas[n] if cx.a.etapa == "optimizar"}
    for n, cs in corridas.items():
        hechos = set()
        for cx in cs:
            if cx.a.etapa == "optimizar":
                hechos.add(cx.estudio)
                assert not cx.ruta_hp().exists(), f"{n}: {cx.estudio} ya está corrido (no se repite)"
            else:
                assert cx.estudio in hechos or cx.ruta_hp().exists(), f"{n}: {cx.variante} lee {cx.estudio}, que no está antes ni existe"
                if n.endswith("_a"):
                    assert cx.estudio not in propios_b, f"{n} lee {cx.estudio} de una lista b"


@YA_CORRIDA
def test_ningun_final_de_la_fase_8_esta_ya_corrido(corridas):
    ya = set()
    for e in variantes.duenos():
        f = rutas.ledger(e) / "resultados.csv"
        if f.exists():
            r = pd.read_csv(f)
            r = r[(r["etapa"] == "final") & (r["meses_final"] == "201903-201908")]
            ya |= {(v, int(k)) for v, k in zip(r["variante"], r["replica_opt"].fillna(0))}
    nuevas = {(cx.variante, cx.replica) for n in CON_CORRIDAS for cx in corridas[n] if cx.a.etapa == "final"}
    assert not (nuevas & ya), sorted(nuevas & ya)[:5]


def test_la_medicion_trae_las_dos_lineas_de_modulo():
    lineas = [l for l in (LISTAS / "fase8_medicion.txt").read_text().splitlines() if l.startswith("@")]
    assert lineas == ["@ experimentos.sampling_1.scripts.tiempos_hp_fijos", "@ experimentos.sampling_1.scripts.tiempos_hp_fijos --anclas"]


def _en_seco(*cmd):
    r = subprocess.run(cmd, cwd=rutas.RAIZ, capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_lanzar_fase_en_seco_de_todas_las_listas_trae_las_corridas_de_cada_una():
    out = _en_seco("scripts/lanzar_fase.sh", "--en-seco", *NOMBRES)
    assert out.count("== lista ") == 17
    assert out.count("--etapa optimizar") == 67
    assert out.count("--etapa final") * 20 == 2560
    assert out.count("python -m experimentos.sampling_1.scripts.tiempos_hp_fijos") == 2


def test_lanzar_carriles_en_seco_reparte_17_listas_en_cuatro_carriles():
    out = _en_seco("bash", "scripts/lanzar_carriles.sh", "--en-seco")
    assert "4 carriles, 17 listas" in out and out.count("== carril ") == 4
    carriles = re.split(r"== carril \d", out)[1:]
    assert carriles[0].index("fase8_medicion") < carriles[0].index("fase8_r0_a") < carriles[0].index("fase8_r0_b")
    for c in carriles:  # primero la medición y las `_a`, al final las `_b`
        listas = re.findall(r"(fase8_\w+) -> VM", c)
        assert listas == sorted(listas, key=lambda x: x.endswith("_b"))
    assert sorted(re.findall(r"(fase8_\w+) -> VM", out)) == sorted(NOMBRES)
    assert "32 vCPU" in out


def test_vm_sh_calibra_antes_y_despues_y_sube_otra_vez_y_los_filtros_dejan_pasar_tiempos():
    out = _en_seco("bash", "scripts/vm.sh", str(LISTAS / "fase8_r1_a.txt"), "--en-seco")
    assert "calibracion_fase8_r1_a_inicio.csv" in out
    remoto = out[out.index("-- script remoto"):]
    assert remoto.index("calibrar inicio") < remoto.index("while read") < remoto.index("calibrar fin") < remoto.index("echo DONE")
    cal = remoto[remoto.index("calibrar() {"):remoto.index("calibrar inicio")]
    assert "--calibracion" in cal and "subir" in cal  # la calibración del final llega al bucket antes de DONE
    # los dos filtros de vm.sh (subir y bajar) no excluyen `tiempos/`, y sí los CSV de la raíz y `sesiones/`
    for filtro in re.findall(r"-x '([^']+)'", remoto):
        assert not re.search(filtro, "tiempos/calibracion_fase8_r1_a_inicio.csv")
        assert not re.search(filtro, "tiempos/hp_fijos/azar_1_C_0.csv")
        assert re.search(filtro, "resultados.csv") and re.search(filtro, "sesiones/vm_f8.log")
    sin = _en_seco("bash", "scripts/vm.sh", str(LISTAS / "fase8_r1_a.txt"), "--filas", "20000", "--en-seco")
    assert "calibración: no" in sin


def test_dos_listas_no_escriben_el_mismo_archivo_de_calibracion():
    nombres = {f"calibracion_{n}_{m}.csv" for n in NOMBRES for m in ("inicio", "fin")}
    assert len(nombres) == 34
