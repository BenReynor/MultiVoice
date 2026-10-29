import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pronunciacion as pr  # noqa: E402


def regla(texto, dice, completa=True):
    return {"text": texto, "say": dice, "whole": completa}


def test_palabra_completa_no_toca_dentro_de_otra():
    reglas = [regla("xd", "equis de")]
    assert pr.aplicar("xd jaja xd", reglas) == "equis de jaja equis de"
    assert pr.aplicar("xdxd y exdx", reglas) == "xdxd y exdx"
    assert pr.aplicar("¡xd!", reglas) == "¡equis de!"


def test_sin_palabra_completa_reemplaza_en_cualquier_sitio():
    assert pr.aplicar("holaxd", [regla("xd", "ja", False)]) == "holaja"


def test_no_distingue_mayusculas():
    reglas = [regla("xd", "equis de")]
    assert pr.aplicar("XD y Xd", reglas) == "equis de y equis de"


def test_varios_reemplazos_y_caracteres_especiales():
    reglas = [regla("xq", "porque"), regla("c++", "ce más más", False)]
    assert pr.aplicar("xq amo c++", reglas) == "porque amo ce más más"


def test_desactivado_devuelve_el_texto_igual():
    assert pr.aplicar("xd", [regla("xd", "equis de")], activo=False) == "xd"


def test_regla_vacia_se_ignora_y_texto_vacio():
    assert pr.aplicar("hola", [regla("", "x")]) == "hola"
    assert pr.aplicar("", [regla("a", "b")]) == ""


def test_config_antiguo_recibe_ejemplos_y_vacio_se_respeta():
    cfg = {}
    assert any(r["text"] == "xd" and r["say"] == "equis de"
               for r in pr.reglas(cfg))
    assert pr.activo(cfg)
    cfg = {"pronunciacion": {"enabled": False, "rules": []}}
    assert pr.reglas(cfg) == [] and not pr.activo(cfg)


def test_aplicar_cfg_respeta_el_interruptor():
    cfg = {}
    assert pr.aplicar_cfg("xd", cfg) == "equis de"
    pr.activar(cfg, False)
    assert pr.aplicar_cfg("xd", cfg) == "xd"


def test_agregar_editar_borrar():
    cfg = {"pronunciacion": {"enabled": True, "rules": []}}
    pr.agregar(cfg, " k ", " qué ")
    assert pr.reglas(cfg) == [regla("k", "qué")]
    pr.editar(cfg, 0, dice="que", completa=False)
    assert pr.reglas(cfg) == [regla("k", "que", False)]
    with pytest.raises(ValueError):
        pr.agregar(cfg, "  ", "x")
    assert pr.borrar(cfg, 0) and not pr.borrar(cfg, 0)


def test_viaja_por_config_json():
    cfg = {}
    pr.asegurar(cfg)
    copia = json.loads(json.dumps(cfg))
    assert pr.aplicar_cfg("xd", copia) == "equis de"
