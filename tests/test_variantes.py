import shutil

import pandas as pd
import pytest

from comun import variantes, correr, metodos, rutas

GRILLA = [("uniforme", 1.0), *[("uniforme", r) for r in (0.5, 0.25, 0.1, 0.05)],
          *[("bagging", f) for f in (0.5, 0.25, 0.1)], ("goss", 1.0), *[("opt-muestra", r) for r in (0.25, 0.1)]]


def _t(x):
    return f"{x:g}"


def estudio_viejo(metodo, tasa):  # la regla de src/metodos.py antes de pasar al registro
    if metodo in ("uniforme", "opt-muestra"):
        return "C" if (metodo == "uniforme" and tasa == 1) else f"U{_t(tasa)}"
    return f"B{_t(tasa)}" if metodo == "bagging" else "GOSS"


def variante_vieja(metodo, tasa):
    return f"H3-{_t(tasa)}" if metodo == "opt-muestra" else estudio_viejo(metodo, tasa)


def test_cada_variante_y_estudio_de_los_ledgers_tiene_dueno():
    ledgers = sorted(rutas.EXPERIMENTOS.glob("*/ledger"))
    ap = [pd.read_csv(f) for l in ledgers for f in (l / "apareado.csv", l / "apareado_previo.csv") if f.exists()]
    es = [pd.read_csv(l / "estudios.csv") for l in ledgers if (l / "estudios.csv").exists()]
    assert ap and es
    for b in pd.concat(ap)["variante"].unique():
        assert variantes.dueno_variante(b)
    for e in pd.concat(es)["estudio"].unique():
        assert variantes.dueno_estudio(e)


def test_cada_variante_apunta_a_un_estudio_registrado():
    for b in variantes.VARIANTES.values():
        assert b.estudio in variantes.ESTUDIOS
    assert variantes.dueno_estudio(variantes.variante("H3-0.25").estudio) == "h1"


def test_variante_desconocido_falla_nombrandolo():
    with pytest.raises(ValueError, match="X9"):
        variantes.dueno_variante("X9")
    with pytest.raises(ValueError, match="U0.3"):
        metodos.variante("uniforme", 0.3)
    with pytest.raises(ValueError, match="Z1"):
        variantes.dueno_estudio("Z1")


@pytest.mark.parametrize("metodo,tasa", GRILLA)
def test_nombres_de_la_grilla_iguales_a_los_de_antes(metodo, tasa):
    assert metodos.estudio(metodo, tasa) == estudio_viejo(metodo, tasa)
    assert metodos.variante(metodo, tasa) == variante_vieja(metodo, tasa)


@pytest.mark.parametrize("nombre", list(variantes.VARIANTES))
def test_el_corredor_resuelve_el_destino_de_cada_variante(nombre):
    b = variantes.variante(nombre)
    extra = ["--variante", "C-rep"] if nombre == "C-rep" else []
    a = correr.parsear(["--metodo", b.metodo, "--tasa", str(b.tasa), "--semilla", "1", "--etapa", "final",
                        "--filas", "100", *extra])
    cx = correr.Contexto(a)
    assert cx.variante == nombre and cx.estudio == b.estudio
    assert cx.raiz == rutas.ledger(b.dueno)
    assert cx.base == cx.raiz / "exploracion"  # con --filas es exploratoria
    assert cx.ruta_hp() == rutas.ledger(variantes.ESTUDIOS[b.estudio]) / "exploracion" / "hp" / f"{b.estudio}.json"


def test_final_de_h3_lee_los_hp_de_h1_y_escribe_en_h3():
    a = correr.parsear(["--metodo", "opt-muestra", "--tasa", "0.25", "--semilla", "1", "--etapa", "final"])
    cx = correr.Contexto(a)
    assert cx.raiz == rutas.ledger("h3")
    assert cx.ruta_hp() == rutas.ledger("h1") / ("exploracion" if cx.explora else "") / "hp" / "U0.25.json"


def test_el_corredor_rechaza_un_variante_sin_dueno_antes_de_cargar_datos(capsys):
    with pytest.raises(SystemExit):
        correr.parsear(["--metodo", "uniforme", "--tasa", "0.3", "--semilla", "1", "--etapa", "final"])
    assert "U0.3" in capsys.readouterr().err


def test_rutas():
    assert rutas.ledger("h1") == rutas.RAIZ / "experimentos" / "h1" / "ledger"
    assert rutas.docs("h1").name == "docs" and rutas.informe("h1").name == "informe"


# --- dependencias -------------------------------------------------------------------------


def _experimento(raiz, nombre, dependencias):
    d = raiz / "experimentos" / nombre
    d.mkdir(parents=True)
    cuerpo = "".join(f"- `{x}`: algo\n" for x in dependencias)
    (d / "README.md").write_text(f"# Exp\n\n## Diseño\n\n### Variantes\n\ntexto\n\n## Dependencias\n\n{cuerpo}\n## Otra\n\n`h9`\n")


def _arbol_completo(raiz):
    for exp, deps in variantes.implicitas().items():
        _experimento(raiz, exp, sorted(deps))


def test_las_dependencias_implicitas_del_registro():
    dep = variantes.implicitas()
    assert dep["control"] == set() and dep["h1"] == {"control"} and dep["h2"] == {"control"}
    assert dep["h3"] == {"control", "h1"}
    assert dep["h4"] == {"control", "h1", "h3"}
    assert dep["sampling_1"] == {"control", "h1", "h2", "h3", "h4"}


def test_arbol_consistente_pasa_y_dice_que_se_rompe(tmp_path):
    _arbol_completo(tmp_path)
    problemas, informe = variantes.verificar(tmp_path)
    assert problemas == []
    assert "si falta experimentos/h1/ se rompen: h3, h4, sampling_1" in informe


def test_declaracion_distinta_del_registro(tmp_path):
    _arbol_completo(tmp_path)
    (tmp_path / "experimentos" / "h3" / "README.md").write_text("## Dependencias\n\n- `control`\n")
    problemas, _ = variantes.verificar(tmp_path)
    assert any("h3" in p and "h1" in p for p in problemas)


def test_ciclo_armado_a_mano(tmp_path):
    _arbol_completo(tmp_path)
    (tmp_path / "experimentos" / "h1" / "README.md").write_text("## Dependencias\n\n- `control`\n- `h3`\n")
    problemas, _ = variantes.verificar(tmp_path)
    assert any(p.startswith("ciclo de dependencias") and "h1" in p and "h3" in p for p in problemas)
    assert variantes.ciclos({"a": {"b"}, "b": {"c"}, "c": {"a"}}) == [["a", "b", "c", "a"]]
    assert variantes.ciclos({"a": {"b"}, "b": set()}) == []


def test_seccion_en_el_archivo_viejo_falla_nombrando_experimento_y_archivo(tmp_path):
    _arbol_completo(tmp_path)
    viejo = tmp_path / "experimentos" / "h2" / "docs"
    viejo.mkdir()
    (viejo / "diseno.md").write_text("## Dependencias\n\n- `control`\n")
    problemas, _ = variantes.verificar(tmp_path)
    assert any("h2" in p and "docs/diseno.md" in p and "experimentos/h2/README.md" in p for p in problemas)


def test_readme_sin_la_seccion_falla(tmp_path):
    _arbol_completo(tmp_path)
    (tmp_path / "experimentos" / "h2" / "README.md").write_text("# H2\n\nsin sección\n")
    problemas, _ = variantes.verificar(tmp_path)
    assert any("h2" in p and "README.md" in p and "falta la sección" in p for p in problemas)


def test_carpeta_faltante_lista_lo_que_se_rompe(tmp_path):
    _arbol_completo(tmp_path)
    shutil.rmtree(tmp_path / "experimentos" / "h1")
    problemas, informe = variantes.verificar(tmp_path)
    assert any("falta la carpeta experimentos/h1/" in p for p in problemas)
    assert "si falta experimentos/h1/ se rompen: h3, h4, sampling_1" in informe
    assert "si falta experimentos/h2/ se rompen: sampling_1" in informe


def _exploratorio(raiz, **cambios):
    import json
    carpeta = raiz / "experimentos" / "h3" / "sensibilidad_muestra"
    carpeta.mkdir(parents=True)
    (carpeta / "README.md").write_text("# x\n")
    datos = dict(autor="A", fecha="2026-11-04", pregunta="p", protocolo="p", advertencia="a",
                 tablas=[dict(csv="r.csv", columnas=["x"])])
    datos.update(cambios)
    (carpeta / "exploratorio.json").write_text(json.dumps(datos))


def test_exploratorio_completo_pasa(tmp_path):
    _arbol_completo(tmp_path)
    _exploratorio(tmp_path)
    assert variantes.verificar(tmp_path)[0] == []


def test_exploratorio_sin_advertencia_falla_nombrando_carpeta_y_campo(tmp_path):
    _arbol_completo(tmp_path)
    _exploratorio(tmp_path, advertencia="")
    problemas, _ = variantes.verificar(tmp_path)
    assert any("h3/sensibilidad_muestra" in p and "advertencia" in p for p in problemas)


def test_figura_declarada_que_no_existe_falla_y_con_el_archivo_pasa(tmp_path):
    _arbol_completo(tmp_path)
    _exploratorio(tmp_path, figuras=[dict(archivo="figuras/a.png", leyenda="Reporte original")])
    problemas, _ = variantes.verificar(tmp_path)
    assert any("h3/sensibilidad_muestra" in p and "figuras/a.png" in p for p in problemas)
    (tmp_path / "experimentos/h3/sensibilidad_muestra/figuras").mkdir()
    (tmp_path / "experimentos/h3/sensibilidad_muestra/figuras/a.png").write_bytes(b"png")
    assert variantes.verificar(tmp_path)[0] == []


def test_figura_generada_desde_un_csv_no_necesita_archivo(tmp_path):
    _arbol_completo(tmp_path)
    _exploratorio(tmp_path, figuras=[dict(csv="r.csv", columna="x", leyenda="Δ por muestra")])
    assert variantes.verificar(tmp_path)[0] == []
    _exploratorio_sin_leyenda = [dict(csv="r.csv", columna="x")]
    (tmp_path / "experimentos/h3/sensibilidad_muestra/exploratorio.json").unlink()
    _exploratorio_json = tmp_path / "experimentos/h3/sensibilidad_muestra"
    import json
    (_exploratorio_json / "exploratorio.json").write_text(json.dumps(dict(
        autor="A", fecha="d", pregunta="p", protocolo="p", advertencia="a", tablas=[dict(csv="r.csv", columnas=["x"])],
        figuras=_exploratorio_sin_leyenda)))
    assert any("leyenda" in p for p in variantes.verificar(tmp_path)[0])
