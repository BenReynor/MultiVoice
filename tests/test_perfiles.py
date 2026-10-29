import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import multivoice as mv  # noqa: E402
import perfiles  # noqa: E402

VOZ = {"engine": "robot", "voice": "🤖 Robot Sound", "rate": -10,
       "pitch": -20, "volume": 5, "metal": 60}


def test_guardar_y_cargar_perfil():
    cfg = {"profiles": {}}
    assert perfiles.guardar(cfg, "  Mi voz ", VOZ) == "Mi voz"
    assert perfiles.cargar(cfg, "Mi voz") == VOZ
    assert perfiles.cargar(cfg, "nada") is None


def test_guardar_sin_nombre_falla_y_normaliza_valores():
    cfg = {"profiles": {}}
    with pytest.raises(ValueError):
        perfiles.guardar(cfg, "  ", VOZ)
    perfiles.guardar(cfg, "X", {"rate": 999, "pitch": "basura", "metal": -4})
    p = perfiles.cargar(cfg, "X")
    assert (p["rate"], p["pitch"], p["metal"]) == (100, 0, 0)
    assert p["engine"] == "edge"


def test_renombrar_perfil():
    cfg = {"profiles": {}, "active_profile": "A"}
    perfiles.guardar(cfg, "A", VOZ)
    perfiles.guardar(cfg, "B", VOZ)
    perfiles.renombrar(cfg, "A", "C")
    assert perfiles.nombres(cfg) == ["C", "B"]
    assert cfg["active_profile"] == "C"
    with pytest.raises(ValueError):
        perfiles.renombrar(cfg, "C", "B")
    with pytest.raises(KeyError):
        perfiles.renombrar(cfg, "zzz", "D")


def test_borrar_perfil():
    cfg = {"profiles": {}, "active_profile": "A"}
    perfiles.guardar(cfg, "A", VOZ)
    assert perfiles.borrar(cfg, "A") is True
    assert perfiles.borrar(cfg, "A") is False
    assert cfg["profiles"] == {} and cfg["active_profile"] == ""


def test_config_antiguo_sin_perfiles_recibe_los_de_ejemplo(tmp_path, monkeypatch):
    ruta = tmp_path / "config.json"
    ruta.write_text(json.dumps({"voice": "es-MX-JorgeNeural", "rate": 3}))
    monkeypatch.setattr(mv, "CONFIG_PATH", str(ruta))
    cfg = mv.load_config()
    assert cfg["rate"] == 3
    assert set(cfg["profiles"]) == {"SCP-079", "Narrador"}
    assert cfg["profiles"]["SCP-079"]["engine"] == "robot"


def test_sin_config_trae_dos_ejemplos_independientes(tmp_path, monkeypatch):
    monkeypatch.setattr(mv, "CONFIG_PATH", str(tmp_path / "no.json"))
    a, b = mv.load_config(), mv.load_config()
    assert len(a["profiles"]) == 2
    a["profiles"]["SCP-079"]["rate"] = 99
    assert b["profiles"]["SCP-079"]["rate"] != 99


def test_perfiles_viajan_por_config_json(tmp_path, monkeypatch):
    ruta = tmp_path / "config.json"
    monkeypatch.setattr(mv, "CONFIG_PATH", str(ruta))
    cfg = mv.load_config()
    perfiles.borrar(cfg, "Narrador")
    perfiles.guardar(cfg, "Nuevo", VOZ)
    mv.save_config(cfg)
    otra = mv.load_config()
    assert set(otra["profiles"]) == {"SCP-079", "Nuevo"}
    assert otra["profiles"]["Nuevo"] == VOZ


def test_borrar_todos_no_resucita_los_ejemplos(tmp_path, monkeypatch):
    monkeypatch.setattr(mv, "CONFIG_PATH", str(tmp_path / "config.json"))
    cfg = mv.load_config()
    for n in perfiles.nombres(cfg):
        perfiles.borrar(cfg, n)
    mv.save_config(cfg)
    assert mv.load_config()["profiles"] == {}
