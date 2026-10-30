"""Atajo global para hablar (`multivoice --decir`).

Windows: atajo global con pynput (import perezoso). Linux: Wayland no deja a
las apps registrar atajos globales, así que se asigna `multivoice --decir` a
una tecla en el sistema; en GNOME se puede crear con gsettings.
"""
import ast
import os
import shutil
import subprocess
import sys

from idioma import t

ATAJO_POR_DEFECTO = "ctrl+alt+h"
_RUTA_GNOME = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/multivoice/"
_SCHEMA_GNOME = "org.gnome.settings-daemon.plugins.media-keys"
_TECLAS_ESPECIALES = {"ctrl", "alt", "shift", "cmd", "space", "enter", "tab",
                      "esc", "up", "down", "left", "right", "home", "end",
                      "backspace", "delete", "page_up", "page_down"}


def a_pynput(texto):
    """'ctrl+alt+h' → '<ctrl>+<alt>+h'. None si no es un atajo válido
    (al menos un modificador y exactamente una tecla)."""
    partes = [p.strip().lower() for p in str(texto or "").split("+")]
    if len(partes) < 2 or not all(partes):
        return None
    *mods, tecla = partes
    if not all(m in ("ctrl", "alt", "shift", "cmd") for m in mods):
        return None
    if tecla in ("ctrl", "alt", "shift", "cmd"):
        return None
    if tecla.startswith("f") and tecla[1:].isdigit():
        tecla = f"<{tecla}>"
    elif tecla in _TECLAS_ESPECIALES:
        tecla = f"<{tecla}>"
    elif len(tecla) != 1:
        return None
    return "+".join([f"<{m}>" for m in mods] + [tecla])


def a_gnome(texto):
    """'ctrl+alt+h' → '<Primary><Alt>h' (formato de GNOME)."""
    pyn = a_pynput(texto)
    if pyn is None:
        return None
    mods = {"ctrl": "<Primary>", "alt": "<Alt>", "shift": "<Shift>",
            "cmd": "<Super>"}
    teclas = {"enter": "Return", "esc": "Escape", "space": "space",
              "backspace": "BackSpace", "page_up": "Page_Up", "page_down": "Page_Down"}
    sal = ""
    for p in pyn.split("+"):
        nombre = p.strip("<>")
        if nombre in mods:
            sal += mods[nombre]
        else:
            sal += teclas.get(nombre, nombre.capitalize()
                              if len(nombre) > 1 else nombre)
    return sal


class GlobalWindows:
    """Registra el atajo global con pynput. Solo en Windows."""

    def __init__(self, al_pulsar):
        self.al_pulsar = al_pulsar
        self._escucha = None

    def registrar(self, texto):
        """True si quedó registrado; False si no es válido o no hay pynput."""
        self.detener()
        combo = a_pynput(texto)
        if combo is None:
            return False
        try:
            from pynput import keyboard
            self._escucha = keyboard.GlobalHotKeys({combo: self.al_pulsar})
            self._escucha.daemon = True
            self._escucha.start()
        except Exception:
            self._escucha = None
            return False
        return True

    def detener(self):
        if self._escucha is not None:
            try:
                self._escucha.stop()
            except Exception:
                pass
            self._escucha = None


def comando_decir(frozen=None, fuente=None, home=None):
    """Comando de shell que dice 'abre el cuadro' en la instancia abierta."""
    frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    if frozen:
        return f'"{sys.executable}" --decir'
    home = home or os.path.expanduser("~")
    lanzador = os.path.join(home, ".local", "bin", "multivoice")
    if os.path.isfile(lanzador):
        return f'"{lanzador}" --decir'
    fuente = fuente or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "multivoice.py")
    return f'"{sys.executable}" "{fuente}" --decir'


def es_gnome(env=None, which=shutil.which):
    env = os.environ if env is None else env
    escritorio = env.get("XDG_CURRENT_DESKTOP", "").upper()
    return "GNOME" in escritorio and which("gsettings") is not None


def _parse_lista(salida):
    """Salida de `gsettings get` de una lista de cadenas → list[str]."""
    texto = salida.strip()
    if texto.startswith("@as"):
        texto = texto[3:].strip()
    try:
        valor = ast.literal_eval(texto)
    except (ValueError, SyntaxError):
        return []
    return [str(v) for v in valor] if isinstance(valor, list) else []


def _gsettings(args, run):
    p = run(["gsettings"] + args, capture_output=True, text=True, timeout=10)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or t("gsettings failed")).strip())
    return p.stdout


def crear_atajo_gnome(texto, comando=None, run=subprocess.run):
    """Crea (o actualiza) el atajo personalizado de GNOME con gsettings.
    Devuelve el texto del atajo en formato GNOME; lanza RuntimeError si falla."""
    tecla = a_gnome(texto)
    if tecla is None:
        raise RuntimeError(t("Invalid shortcut: use e.g. ctrl+alt+h"))
    comando = comando or comando_decir()
    try:
        lista = _parse_lista(_gsettings(["get", _SCHEMA_GNOME,
                                         "custom-keybindings"], run))
        if _RUTA_GNOME not in lista:
            lista.append(_RUTA_GNOME)
            _gsettings(["set", _SCHEMA_GNOME, "custom-keybindings",
                        repr(lista)], run)
        esquema = f"{_SCHEMA_GNOME}.custom-keybinding:{_RUTA_GNOME}"
        _gsettings(["set", esquema, "name", "MultiVoice: decir"], run)
        _gsettings(["set", esquema, "command", comando], run)
        _gsettings(["set", esquema, "binding", tecla], run)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(str(exc)) from exc
    return tecla
