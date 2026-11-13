"""Los verificadores de números leen el bloque `bloque-a-completo` de `sampling_1/README.md` (sitio-legible D9): un número
alterado a mano falla nombrándolo, y lo que está dentro de un bloque generado no se revisa."""
import sys

from scripts import verificar_informe_h3 as v3
from scripts import verificar_readme as vr

BLOQUE = "<!-- generado:bloque-a-completo -->\n| U0.5 | 10.50 | 3.25 |\n<!-- /generado:bloque-a-completo -->\n"


def test_verificar_readme_acepta_y_rechaza_un_numero_alterado(tmp_path, monkeypatch, capsys):
    (tmp_path / "experimentos/sampling_1").mkdir(parents=True)
    tabla = tmp_path / "experimentos/sampling_1/README.md"
    tabla.write_text("# Resultados\n\n" + BLOQUE)
    readme = tmp_path / "README.md"
    for modulo_attr, valor in (("RAIZ", tmp_path), ("README", readme), ("TABLA", tabla)):
        monkeypatch.setattr(vr, modulo_attr, valor)
    readme.write_text("El Δ de U0.5 es 3,25 M$.\n")
    assert vr.main() == 0
    readme.write_text("El Δ de U0.5 es 3,26 M$.\n")
    assert vr.main() == 1
    assert "3,26" in capsys.readouterr().out


def test_verificar_readme_sin_bloque_falla(tmp_path, monkeypatch, capsys):
    tabla = tmp_path / "README.md"
    tabla.write_text("sin bloque\n")
    monkeypatch.setattr(vr, "TABLA", tabla)
    monkeypatch.setattr(vr, "RAIZ", tmp_path)
    assert vr.main() == 1
    assert "bloque-a-completo" in capsys.readouterr().out


def test_verificar_h3_ignora_los_bloques_generados_y_nombra_el_numero_alterado(tmp_path, monkeypatch, capsys):
    tabla = tmp_path / "README.md"
    tabla.write_text(BLOQUE)
    monkeypatch.setattr(v3, "TABLA", tabla)
    monkeypatch.setattr(v3, "_fuentes", lambda bloque: [10.5, 3.25])
    h = tmp_path / "h9.md"
    h.write_text("Texto con 3,25.\n\n<!-- generado:resultado -->\nnúmero libre 77,7\n<!-- /generado:resultado -->\n")
    monkeypatch.setattr(sys, "argv", ["v", "--informe", str(h)])
    assert v3.main() == 0
    h.write_text("Texto con 3,26.\n\n<!-- generado:resultado -->\nnúmero libre 77,7\n<!-- /generado:resultado -->\n")
    assert v3.main() == 1
    salida = capsys.readouterr().out
    assert "3,26" in salida and "h9.md:1" in salida and "77,7" not in salida
