"""Perfiles de voz: motor, voz, velocidad, tono, volumen y metal con un nombre.

La lógica (guardar, renombrar, borrar) trabaja sobre el dict de configuración
(`cfg["profiles"]`) y no usa la interfaz, así se prueba sin pantalla.
`PerfilesMixin` añade el desplegable y los botones a la barra de voz.
"""
import copy

import customtkinter as ctk

from idioma import t

CAMPOS = ("engine", "voice", "rate", "pitch", "volume", "metal")

PERFILES_EJEMPLO = {
    "SCP-079": {"engine": "robot", "voice": "🤖 Robot Sound", "rate": -15,
                "pitch": -25, "volume": 0, "metal": 85},
    "Narrador": {"engine": "edge", "voice": "es-MX-JorgeNeural", "rate": -5,
                 "pitch": -10, "volume": 0, "metal": 0},
}


def sin_perfil():
    """Texto del desplegable cuando no hay perfil activo (según el idioma)."""
    return t("— No profile —")


def ejemplos():
    return copy.deepcopy(PERFILES_EJEMPLO)


def _entero(valor, defecto, lo, hi):
    try:
        v = int(round(float(valor)))
    except (TypeError, ValueError):
        v = defecto
    return max(lo, min(hi, v))


def normalizar(datos):
    """Devuelve un perfil completo y con valores en rango."""
    datos = datos if isinstance(datos, dict) else {}
    return {
        "engine": str(datos.get("engine") or "edge"),
        "voice": str(datos.get("voice") or ""),
        "rate": _entero(datos.get("rate"), 0, -50, 100),
        "pitch": _entero(datos.get("pitch"), 0, -50, 50),
        "volume": _entero(datos.get("volume"), 0, -50, 50),
        "metal": _entero(datos.get("metal"), 0, 0, 100),
    }


def asegurar(cfg):
    """Garantiza cfg["profiles"]. Un config.json antiguo, sin la clave, recibe
    los perfiles de ejemplo; si la clave existe (aunque vacía) se respeta."""
    perfiles = cfg.get("profiles")
    if not isinstance(perfiles, dict):
        cfg["profiles"] = ejemplos()
    else:
        cfg["profiles"] = {str(n): normalizar(p) for n, p in perfiles.items()
                           if str(n).strip()}
    return cfg["profiles"]


def nombres(cfg):
    return list(asegurar(cfg))


def cargar(cfg, nombre):
    """Copia del perfil, o None si no existe."""
    p = asegurar(cfg).get(nombre)
    return dict(p) if p else None


def guardar(cfg, nombre, datos):
    """Crea o sobrescribe un perfil. Devuelve el nombre limpio."""
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError(t("The profile needs a name"))
    asegurar(cfg)[nombre] = normalizar(datos)
    return nombre


def renombrar(cfg, viejo, nuevo):
    nuevo = (nuevo or "").strip()
    perfiles = asegurar(cfg)
    if viejo not in perfiles:
        raise KeyError(viejo)
    if not nuevo:
        raise ValueError(t("The profile needs a name"))
    if nuevo != viejo and nuevo in perfiles:
        raise ValueError(t("A profile «{name}» already exists", name=nuevo))
    cfg["profiles"] = {(nuevo if n == viejo else n): p
                       for n, p in perfiles.items()}
    if cfg.get("active_profile") == viejo:
        cfg["active_profile"] = nuevo
    return nuevo


def borrar(cfg, nombre):
    """Quita el perfil; devuelve True si existía."""
    existia = asegurar(cfg).pop(nombre, None) is not None
    if cfg.get("active_profile") == nombre:
        cfg["active_profile"] = ""
    return existia


class PerfilesMixin:
    """Desplegable de perfiles y botones de crear/renombrar/borrar."""

    def _build_perfiles(self, parent):
        h = self._px("--control-h", 36)
        self.lbl_profile = ctk.CTkLabel(
            parent, text=t("Profile"), font=self.font(self._px("--fs-md", 13), True))
        self.lbl_profile.pack(side="left", padx=(0, 8))
        self.profile_menu = ctk.CTkOptionMenu(
            parent, values=[sin_perfil()], width=150, height=h,
            corner_radius=self._px("--radius", 8), font=self.font(),
            dropdown_font=self.font(), command=self._on_profile_selected)
        self.profile_menu.pack(side="left")
        self.profile_buttons = []
        for texto, cmd in (("＋", self.profile_save_new),
                           ("💾", self.profile_update),
                           ("✎", self.profile_rename),
                           ("🗑", self.profile_delete)):
            b = self._btn(parent, texto, cmd, height=h)
            b.configure(width=h)
            b.pack(side="left", padx=(4, 0))
            self.profile_buttons.append(b)
        self._reg(self.lbl_profile,
                  lambda w: w.configure(text_color=self._col("--text")))
        self._reg(self.profile_menu, self._paint_menu)
        self._refresh_profiles()

    def _refresh_profiles(self):
        activo = self.cfg.get("active_profile", "")
        lista = nombres(self.cfg)
        self.profile_menu.configure(values=lista or [sin_perfil()])
        self.profile_menu.set(activo if activo in lista else sin_perfil())

    def _profile_snapshot(self):
        v = self.current_voice()
        return {
            "engine": self.current_engine, "voice": v["label"],
            "rate": self.sliders["rate"].get(),
            "pitch": self.sliders["pitch"].get(),
            "volume": self.sliders["volume"].get(),
            "metal": self.metal_slider.get(),
        }

    def apply_profile(self, nombre):
        p = cargar(self.cfg, nombre)
        if p is None:
            return False
        self._on_engine_changed(p["engine"] if p["engine"] in self.engines_ids()
                                else None)
        labels = [v["label"] for v in self.voices]
        if p["voice"] in labels:
            self.voice_combo.set(p["voice"])
        for key in ("rate", "pitch", "volume"):
            self._set_slider(key, p[key])
        self.metal_slider.set(p["metal"])
        self._on_metal(p["metal"])
        self._on_voice_changed()
        self.cfg["active_profile"] = nombre
        self._save_soon()
        self.set_status(t("🎭 Profile «{name}» applied", name=nombre))
        return True

    @staticmethod
    def engines_ids():
        from ajustes import ENGINES
        return list(ENGINES)

    def _on_profile_selected(self, nombre):
        if nombre == sin_perfil():
            self.cfg["active_profile"] = ""
            self._save_soon()
        else:
            self.apply_profile(nombre)

    def _pedir_nombre(self, titulo, texto, inicial=""):
        dlg = ctk.CTkInputDialog(title=titulo, text=texto)
        if inicial:
            try:
                dlg._entry.insert(0, inicial)
            except Exception:
                pass
        return (dlg.get_input() or "").strip()

    def profile_save_new(self):
        nombre = self._pedir_nombre(t("New profile"), t("Profile name:"))
        if not nombre:
            return
        guardar(self.cfg, nombre, self._profile_snapshot())
        self.cfg["active_profile"] = nombre
        self._save_soon()
        self._refresh_profiles()
        self.set_status(t("🎭 Profile «{name}» saved", name=nombre))

    def profile_update(self):
        nombre = self.profile_menu.get()
        if nombre == sin_perfil():
            return self.profile_save_new()
        guardar(self.cfg, nombre, self._profile_snapshot())
        self._save_soon()
        self.set_status(t("🎭 Profile «{name}» updated", name=nombre))

    def profile_rename(self):
        viejo = self.profile_menu.get()
        if viejo == sin_perfil():
            return
        nuevo = self._pedir_nombre(t("Rename profile"), t("New name:"), viejo)
        if not nuevo or nuevo == viejo:
            return
        try:
            renombrar(self.cfg, viejo, nuevo)
        except ValueError as exc:
            self.set_status(f"⚠ {exc}")
            return
        self._save_soon()
        self._refresh_profiles()
        self.set_status(t("🎭 Profile renamed to «{name}»", name=nuevo))

    def profile_delete(self):
        nombre = self.profile_menu.get()
        if nombre == sin_perfil() or not borrar(self.cfg, nombre):
            return
        self._save_soon()
        self._refresh_profiles()
        self.set_status(t("🎭 Profile «{name}» deleted", name=nombre))
