"""Instancia única, paso de mensajes y atajo global (sin GUI ni pynput)."""
import os
import socket
import sys
import threading
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import atajo  # noqa: E402
import instancia  # noqa: E402


def _esperar(evento):
    assert evento.wait(3), "no llegó el mensaje"


def test_comando_de_args():
    assert instancia.comando_de_args(["--decir"]) == instancia.CMD_DECIR
    assert instancia.comando_de_args([]) == instancia.CMD_MOSTRAR


def test_la_primera_instancia_escucha_y_la_segunda_avisa():
    recibidos, hecho = [], threading.Event()

    def llega(cmd):
        recibidos.append(cmd)
        hecho.set()

    srv, avisada = instancia.arrancar([], llega, puerto=0)
    assert srv is not None and avisada is None
    try:
        # la segunda ejecución no puede escuchar en el mismo puerto
        srv2, avisada2 = instancia.arrancar(["--decir"], lambda c: None,
                                            puerto=srv.puerto)
        assert srv2 is None and avisada2 is True
        _esperar(hecho)
        assert recibidos == [instancia.CMD_DECIR]
    finally:
        srv.cerrar()


def test_sin_decir_pide_mostrar_la_ventana():
    recibidos, hecho = [], threading.Event()
    srv, _ = instancia.arrancar([], lambda c: (recibidos.append(c), hecho.set()),
                                puerto=0)
    try:
        assert instancia.enviar(instancia.CMD_MOSTRAR, srv.puerto)
        _esperar(hecho)
        assert recibidos == [instancia.CMD_MOSTRAR]
    finally:
        srv.cerrar()


def test_enviar_sin_instancia_devuelve_false():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    puerto = s.getsockname()[1]
    s.close()  # puerto libre: nadie escucha
    assert instancia.enviar(instancia.CMD_DECIR, puerto, timeout=0.5) is False


def test_ordenes_desconocidas_o_rotas_se_ignoran():
    recibidos = []
    srv, _ = instancia.arrancar([], recibidos.append, puerto=0)
    try:
        for basura in (b"no es json\n", b'{"cmd": "rm -rf"}\n', b"[1]\n"):
            with socket.create_connection(("127.0.0.1", srv.puerto), 2) as c:
                c.sendall(basura)
                c.settimeout(2)
                assert c.recv(8) != b"ok\n"
        # y sigue sirviendo órdenes buenas
        assert instancia.enviar(instancia.CMD_MOSTRAR, srv.puerto)
    finally:
        srv.cerrar()
    assert recibidos in ([], [instancia.CMD_MOSTRAR])
    assert "rm -rf" not in recibidos


def test_a_pynput():
    assert atajo.a_pynput("ctrl+alt+h") == "<ctrl>+<alt>+h"
    assert atajo.a_pynput(" Ctrl + Shift + F5 ") == "<ctrl>+<shift>+<f5>"
    assert atajo.a_pynput("ctrl+space") == "<ctrl>+<space>"
    for malo in ("", "h", "ctrl", "ctrl+", "ctrl+alt", "x+h", "ctrl+hola", None):
        assert atajo.a_pynput(malo) is None


def test_a_gnome():
    assert atajo.a_gnome("ctrl+alt+h") == "<Primary><Alt>h"
    assert atajo.a_gnome("ctrl+shift+f5") == "<Primary><Shift>F5"
    assert atajo.a_gnome("cmd+space") == "<Super>space"
    assert atajo.a_gnome("nada") is None


def test_comando_decir():
    assert atajo.comando_decir(frozen=True).endswith("--decir")
    cmd = atajo.comando_decir(frozen=False, fuente="/x/multivoice.py",
                              home="/no/existe")
    assert cmd.endswith('"/x/multivoice.py" --decir')


def test_comando_decir_prefiere_el_lanzador_instalado(tmp_path):
    bin_ = tmp_path / ".local" / "bin"
    bin_.mkdir(parents=True)
    (bin_ / "multivoice").write_text("#!/bin/bash\n")
    cmd = atajo.comando_decir(frozen=False, home=str(tmp_path))
    assert cmd == f'"{bin_ / "multivoice"}" --decir'


def test_es_gnome():
    ok = lambda _: "/usr/bin/gsettings"  # noqa: E731
    assert atajo.es_gnome({"XDG_CURRENT_DESKTOP": "ubuntu:GNOME"}, ok)
    assert not atajo.es_gnome({"XDG_CURRENT_DESKTOP": "KDE"}, ok)
    assert not atajo.es_gnome({"XDG_CURRENT_DESKTOP": "GNOME"}, lambda _: None)


def _gsettings_falso(lista_actual="@as []"):
    llamadas = []

    def run(cmd, **kw):
        llamadas.append(cmd)
        salida = lista_actual if cmd[1] == "get" else ""
        return types.SimpleNamespace(returncode=0, stdout=salida, stderr="")
    return run, llamadas


def test_crear_atajo_gnome_con_gsettings():
    run, llamadas = _gsettings_falso()
    tecla = atajo.crear_atajo_gnome("ctrl+alt+h", "multivoice --decir", run)
    assert tecla == "<Primary><Alt>h"
    sets = [c for c in llamadas if c[1] == "set"]
    assert sets[0][-2:] == ["custom-keybindings", f"['{atajo._RUTA_GNOME}']"]
    valores = {c[-2]: c[-1] for c in sets[1:]}
    assert valores == {"name": "MultiVoice: decir",
                       "command": "multivoice --decir",
                       "binding": "<Primary><Alt>h"}


def test_crear_atajo_gnome_conserva_los_existentes_y_no_duplica():
    otro = "/org/otro/"
    run, llamadas = _gsettings_falso(f"['{otro}']")
    atajo.crear_atajo_gnome("ctrl+alt+h", "x", run)
    lista = [c for c in llamadas if c[1:3] == ["set", atajo._SCHEMA_GNOME]][0]
    assert otro in lista[-1] and atajo._RUTA_GNOME in lista[-1]
    # si ya está, no se reescribe la lista
    run, llamadas = _gsettings_falso(f"['{atajo._RUTA_GNOME}']")
    atajo.crear_atajo_gnome("ctrl+alt+h", "x", run)
    assert not [c for c in llamadas
                if c[1:4] == ["set", atajo._SCHEMA_GNOME, "custom-keybindings"]]


def test_crear_atajo_gnome_errores():
    with pytest.raises(RuntimeError):
        atajo.crear_atajo_gnome("mal", "x", _gsettings_falso()[0])

    def falla(cmd, **kw):
        return types.SimpleNamespace(returncode=1, stdout="", stderr="boom")
    with pytest.raises(RuntimeError, match="boom"):
        atajo.crear_atajo_gnome("ctrl+alt+h", "x", falla)

    def sin_gsettings(cmd, **kw):
        raise FileNotFoundError("gsettings")
    with pytest.raises(RuntimeError):
        atajo.crear_atajo_gnome("ctrl+alt+h", "x", sin_gsettings)


def test_global_windows_no_revienta_sin_pynput_y_con_atajo_malo():
    g = atajo.GlobalWindows(lambda: None)
    assert g.registrar("mal") is False
    g.detener()
