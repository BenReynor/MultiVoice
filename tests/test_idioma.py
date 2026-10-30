import ast
import json
import os
import sys

import pytest

RAIZ = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, RAIZ)

import idioma  # noqa: E402
import multivoice as mv  # noqa: E402
from idioma import t  # noqa: E402


@pytest.fixture(autouse=True)
def _restaurar_idioma():
    yield
    idioma.set_idioma("en")


def test_ingles_por_defecto():
    assert idioma.idioma() == "en"
    assert t("📁 Library") == "📁 Library"


def test_espanol():
    idioma.set_idioma("es")
    assert idioma.idioma() == "es"
    assert t("📁 Library") == "📁 Biblioteca"
    assert t("🗣 Pronunciation") == "🗣 Pronunciación"


def test_entrada_que_falta_cae_al_ingles():
    idioma.set_idioma("es")
    assert t("Text that is not in the catalog") == "Text that is not in the catalog"


def test_codigo_desconocido_vuelve_al_ingles():
    idioma.set_idioma("fr")
    assert idioma.idioma() == "en"


def test_placeholders(monkeypatch):
    monkeypatch.setitem(idioma._ES, "Hello {name}", "Hola {name}")
    assert t("Hello {name}", name="Ana") == "Hello Ana"
    idioma.set_idioma("es")
    assert t("Hello {name}", name="Ana") == "Hola Ana"


def test_config_sin_language_carga_en(tmp_path, monkeypatch):
    ruta = tmp_path / "config.json"
    ruta.write_text(json.dumps({"theme": "discord"}), encoding="utf-8")
    monkeypatch.setattr(mv, "CONFIG_PATH", str(ruta))
    assert mv.load_config()["language"] == "en"
    assert mv.DEFAULT_CONFIG["language"] == "en"


def test_config_con_language_es(tmp_path, monkeypatch):
    ruta = tmp_path / "config.json"
    ruta.write_text(json.dumps({"language": "es"}), encoding="utf-8")
    monkeypatch.setattr(mv, "CONFIG_PATH", str(ruta))
    assert mv.load_config()["language"] == "es"


def _archivos_py():
    for base, dirs, files in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d not in ("__pycache__", "venv", "tests")]
        for f in files:
            if f.endswith(".py"):
                yield os.path.join(base, f)


def test_todo_literal_de_t_esta_en_el_catalogo():
    faltan = []
    for ruta in _archivos_py():
        with open(ruta, encoding="utf-8") as f:
            arbol = ast.parse(f.read(), ruta)
        for nodo in ast.walk(arbol):
            if not (isinstance(nodo, ast.Call) and nodo.args
                    and isinstance(nodo.func, ast.Name)
                    and nodo.func.id == "t"):
                continue
            arg = nodo.args[0]
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                if arg.value not in idioma._ES:
                    faltan.append(f"{os.path.relpath(ruta, RAIZ)}:"
                                  f"{nodo.lineno}: {arg.value!r}")
    assert not faltan, "Faltan en _ES:\n" + "\n".join(faltan)
