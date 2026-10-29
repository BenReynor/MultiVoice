import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import frases  # noqa: E402
import multivoice as mv  # noqa: E402
import perfiles  # noqa: E402


def nueva():
    return {"phrases": {}}


def test_agregar_crea_categoria_y_limpia():
    cfg = nueva()
    f = frases.agregar(cfg, " Chistes ", "  Hola  ", "SCP-079")
    assert f == {"text": "Hola", "profile": "SCP-079"}
    assert frases.categorias(cfg) == ["Chistes"]
    with pytest.raises(ValueError):
        frases.agregar(cfg, "X", "   ")


def test_editar_frase():
    cfg = nueva()
    frases.agregar(cfg, "A", "uno")
    frases.editar(cfg, "A", 0, texto="dos", perfil="Narrador")
    assert frases.frases(cfg, "A") == [{"text": "dos", "profile": "Narrador"}]
    with pytest.raises(ValueError):
        frases.editar(cfg, "A", 0, texto="")
    with pytest.raises(KeyError):
        frases.editar(cfg, "A", 5, texto="x")


def test_borrar_frase():
    cfg = nueva()
    frases.agregar(cfg, "A", "uno")
    assert frases.borrar(cfg, "A", 0) is True
    assert frases.borrar(cfg, "A", 0) is False
    assert frases.borrar(cfg, "Z", 0) is False


def test_mover_entre_categorias():
    cfg = nueva()
    frases.agregar(cfg, "A", "uno")
    frases.agregar(cfg, "A", "dos")
    frases.mover(cfg, "A", 0, "B")
    assert [f["text"] for f in frases.frases(cfg, "A")] == ["dos"]
    assert [f["text"] for f in frases.frases(cfg, "B")] == ["uno"]
    with pytest.raises(KeyError):
        frases.mover(cfg, "A", 9, "B")
    with pytest.raises(ValueError):
        frases.mover(cfg, "A", 0, " ")


def test_categorias_crear_renombrar_borrar():
    cfg = nueva()
    frases.crear_categoria(cfg, "A")
    frases.crear_categoria(cfg, "B")
    with pytest.raises(ValueError):
        frases.crear_categoria(cfg, "A")
    frases.agregar(cfg, "A", "x")
    frases.renombrar_categoria(cfg, "A", "C")
    assert frases.categorias(cfg) == ["C", "B"]
    assert frases.frases(cfg, "C")[0]["text"] == "x"
    with pytest.raises(ValueError):
        frases.renombrar_categoria(cfg, "C", "B")
    with pytest.raises(KeyError):
        frases.renombrar_categoria(cfg, "Z", "Y")
    assert frases.borrar_categoria(cfg, "C") is True
    assert frases.borrar_categoria(cfg, "C") is False
    assert frases.categorias(cfg) == ["B"]


def test_atajos_numeran_las_nueve_primeras_en_orden():
    cfg = nueva()
    for i in range(12):
        frases.agregar(cfg, "A" if i < 6 else "B", f"f{i}")
    num = frases.numeradas(cfg)
    assert [n for n, *_ in num] == list(range(1, 10))
    assert [f["text"] for *_, f in num] == [f"f{i}" for i in range(9)]
    assert frases.frase_numero(cfg, 7)["text"] == "f6"
    assert frases.frase_numero(cfg, 10) is None
    frases.borrar(cfg, "A", 0)
    assert frases.frase_numero(cfg, 1)["text"] == "f1"


def test_config_antiguo_recibe_ejemplos_y_vacio_se_respeta(tmp_path, monkeypatch):
    ruta = tmp_path / "config.json"
    ruta.write_text(json.dumps({"rate": 3}))
    monkeypatch.setattr(mv, "CONFIG_PATH", str(ruta))
    cfg = mv.load_config()
    assert frases.categorias(cfg) == ["Saludos", "Reacciones"]
    ruta.write_text(json.dumps({"phrases": {}}))
    assert frases.categorias(mv.load_config()) == []


def test_frases_viajan_por_config_json(tmp_path, monkeypatch):
    ruta = tmp_path / "config.json"
    monkeypatch.setattr(mv, "CONFIG_PATH", str(ruta))
    cfg = mv.load_config()
    frases.agregar(cfg, "Mías", "Hola", "Narrador")
    mv.save_config(cfg)
    otra = mv.load_config()
    assert frases.frases(otra, "Mías") == [{"text": "Hola", "profile": "Narrador"}]


def test_job_con_perfil_propio():
    cfg = {"profiles": {}}
    perfiles.guardar(cfg, "R", {"engine": "robot", "voice": "🤖 Robot Sound",
                                "rate": 0, "pitch": 0, "volume": 0, "metal": 50})
    job = frases.job_desde_perfil("hola", perfiles.cargar(cfg, "R"))
    assert job["engine"] == "robot" and job["opts"]["robot_metal"] == 0.5
    perfiles.guardar(cfg, "E", {"engine": "edge", "voice": "es-MX-JorgeNeural",
                                "rate": 5})
    job = frases.job_desde_perfil("hola", perfiles.cargar(cfg, "E"))
    assert job["engine"] == "edge" and job["opts"]["rate"] == 5
    assert job["opts"]["voice"]
