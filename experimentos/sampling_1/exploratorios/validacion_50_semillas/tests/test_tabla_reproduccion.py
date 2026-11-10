"""El README del paquete coincide con las fuentes (tarea 5.2): ningún número de las tablas está escrito a mano."""

from experimentos.sampling_1.exploratorios.validacion_50_semillas import tabla_reproduccion as tr


def test_readme_coincide_con_fuentes():
    texto = tr.README.read_text()
    for clave, f in tr.GENERADORES.items():
        i, j = tr.bloque(texto, clave)
        assert texto[i:j] == "\n" + f() + "\n", clave


def test_cada_fila_tiene_las_cinco_columnas():
    for linea in tr.tabla().splitlines():
        assert linea.count(" | ") >= 4 and linea.startswith("| ") and linea.endswith(" |")


def test_formato_en_millones_con_coma():
    assert tr.m(1234567.0) == "1,23"
    assert tr.m(-2310000.0, True) == "-2,31"
