"""`verificar_predicciones` compara la sección Predicción de cada README con la del commit base: pasa en el estado
actual y falla nombrando el archivo si una línea cambia."""
from scripts import verificar_predicciones as vp


def test_pasa_en_el_estado_actual(capsys):
    assert vp.main() == 0


def test_una_linea_cambiada_falla_nombrando_el_archivo(tmp_path, monkeypatch, capsys):
    (tmp_path / "experimentos/h1").mkdir(parents=True)
    copia = tmp_path / "experimentos/h1/README.md"
    original = vp.texto_base("experimentos/h1/README.md")
    linea = next(l for l in vp.seccion(original).splitlines()[2:] if l.strip())
    copia.write_text(original.replace(linea, linea + " y además esto", 1))
    monkeypatch.setattr(vp, "RAIZ", tmp_path)
    monkeypatch.setattr(vp, "READMES", ["experimentos/h1/README.md"])
    monkeypatch.setattr(vp, "texto_base", lambda ruta: original)
    assert vp.main() == 1
    assert "experimentos/h1/README.md" in capsys.readouterr().out
    copia.write_text(original)
    assert vp.main() == 0


def test_un_cambio_fuera_de_la_seccion_no_falla(tmp_path, monkeypatch):
    (tmp_path / "experimentos/h1").mkdir(parents=True)
    original = vp.texto_base("experimentos/h1/README.md")
    (tmp_path / "experimentos/h1/README.md").write_text(original + "\n## Otra sección\n\ntexto nuevo\n")
    monkeypatch.setattr(vp, "RAIZ", tmp_path)
    monkeypatch.setattr(vp, "READMES", ["experimentos/h1/README.md"])
    monkeypatch.setattr(vp, "texto_base", lambda ruta: original)
    assert vp.main() == 0
