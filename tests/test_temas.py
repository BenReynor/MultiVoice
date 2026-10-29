"""Tests de temas.py: lectura de temas, variante de modo y nombres antiguos."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import temas  # noqa: E402

CONTRATO = ["--bg", "--surface", "--surface-2", "--text", "--text-2", "--accent",
            "--accent-hover", "--accent-text", "--danger", "--focus",
            "--radius-sm", "--radius", "--radius-lg", "--control-h"]


def test_lee_tema_discord():
    p = temas.paleta("discord")
    assert p["--bg"] == "#313338"
    assert p["--accent-text"] == "#ffffff"
    assert p["color-scheme"] == "dark"


@pytest.mark.parametrize("tema", list(temas.TEMAS))
def test_todos_los_temas_cumplen_el_contrato(tema):
    p = temas.paleta(tema)
    for token in CONTRATO:
        assert token in p, (tema, token)


def test_lista_de_temas_en_espanol():
    lista = dict(temas.lista_temas())
    assert len(lista) == 10
    assert lista["calido"] == "Cálido"
    assert lista["discord"] == "Discord"


def test_variante_de_modo_sobrescribe_la_base():
    oscuro = temas.paleta("minimal", "oscuro")
    claro = temas.paleta("minimal", "claro")
    assert oscuro["--bg"] != claro["--bg"]
    assert claro["color-scheme"] == "light"
    assert "--radius" in claro  # lo no redefinido viene de la base


def test_modo_invalido_usa_la_base():
    assert temas.paleta("minimal", "noir") == temas.paleta("minimal")


@pytest.mark.parametrize("antiguo", list(temas.NOMBRES_ANTIGUOS))
def test_nombres_antiguos_se_traducen(antiguo):
    tema, modo = temas.traducir_nombre(antiguo)
    assert tema in temas.TEMAS
    assert modo is None or modo in temas.modos(tema)
    assert temas.paleta(antiguo)["--bg"]


def test_light_pasa_a_minimal_claro():
    assert temas.traducir_nombre("light") == ("minimal", "claro")


def test_nombre_desconocido_usa_el_defecto():
    assert temas.traducir_nombre("xyz") == (temas.TEMA_POR_DEFECTO, None)
    assert temas.traducir_nombre(None) == (temas.TEMA_POR_DEFECTO, None)


def test_temas_desde_codigo_fuente(monkeypatch):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    esperado = os.path.join(os.path.dirname(os.path.abspath(temas.__file__)), "assets", "temas")
    assert temas.carpeta_temas() == esperado
    assert len(temas.lista_temas()) == len(temas.TEMAS)


def test_temas_desde_meipass_de_pyinstaller(monkeypatch, tmp_path):
    import shutil
    origen = os.path.join(os.path.dirname(os.path.abspath(temas.__file__)), "assets", "temas")
    shutil.copytree(origen, tmp_path / "assets" / "temas")
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert temas.carpeta_temas() == str(tmp_path / "assets" / "temas")
    assert len(temas.lista_temas()) == len(temas.TEMAS)
    assert temas.paleta("discord")["--bg"] == "#313338"
