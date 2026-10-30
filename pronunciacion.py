"""Diccionario de pronunciación: reemplazos de texto que se aplican antes de
sintetizar, en todos los motores.

La lógica (`aplicar`, alta/edición/borrado) trabaja sobre el dict de
configuración (`cfg["pronunciacion"]`) y no usa la interfaz, así se prueba sin
pantalla. Cada regla es {"text", "say", "whole"}; `whole` pide palabra
completa. Nunca distingue mayúsculas. `PronunciacionMixin` dibuja la pestaña.
"""
import copy
import re

import customtkinter as ctk

from idioma import t


def tab_pronunciacion():
    return t("🗣 Pronunciation")


EJEMPLOS = [
    {"text": "xd", "say": "equis de", "whole": True},
    {"text": "xq", "say": "porque", "whole": True},
    {"text": "pq", "say": "porque", "whole": True},
    {"text": "tqm", "say": "te quiero mucho", "whole": True},
    {"text": "gg", "say": "buena partida", "whole": True},
    {"text": "xoxo", "say": "besos y abrazos", "whole": True},
]


def ejemplos():
    return copy.deepcopy(EJEMPLOS)


def _regla(datos):
    datos = datos if isinstance(datos, dict) else {}
    return {"text": str(datos.get("text") or "").strip(),
            "say": str(datos.get("say") or "").strip(),
            "whole": bool(datos.get("whole", True))}


def aplicar(texto, reglas, activo=True):
    """Texto con los reemplazos hechos (función pura).

    Las reglas se aplican en orden, sin distinguir mayúsculas. Con `whole` solo
    coincide la palabra completa (no dentro de otra). Desactivado, devuelve el
    texto tal cual."""
    if not activo or not texto:
        return texto
    for r in reglas or []:
        r = _regla(r)
        if not r["text"]:
            continue
        patron = re.escape(r["text"])
        if r["whole"]:
            patron = rf"(?<!\w){patron}(?!\w)"
        texto = re.sub(patron, lambda _m, s=r["say"]: s, texto,
                       flags=re.IGNORECASE)
    return texto


def asegurar(cfg):
    """Garantiza cfg["pronunciacion"] = {"enabled", "rules"}. Un config.json
    sin la clave recibe los ejemplos; si existe (aunque vacía) se respeta."""
    datos = cfg.get("pronunciacion")
    if not isinstance(datos, dict):
        cfg["pronunciacion"] = {"enabled": True, "rules": ejemplos()}
    else:
        reglas = datos.get("rules")
        reglas = reglas if isinstance(reglas, list) else []
        cfg["pronunciacion"] = {
            "enabled": bool(datos.get("enabled", True)),
            "rules": [r for r in map(_regla, reglas) if r["text"]]}
    return cfg["pronunciacion"]


def reglas(cfg):
    return asegurar(cfg)["rules"]


def activo(cfg):
    return asegurar(cfg)["enabled"]


def activar(cfg, valor):
    asegurar(cfg)["enabled"] = bool(valor)


def aplicar_cfg(texto, cfg):
    """`aplicar` con las reglas y el interruptor de la configuración."""
    datos = asegurar(cfg)
    return aplicar(texto, datos["rules"], datos["enabled"])


def agregar(cfg, texto, dice, completa=True):
    r = _regla({"text": texto, "say": dice, "whole": completa})
    if not r["text"]:
        raise ValueError("El texto a reemplazar no puede estar vacío")
    reglas(cfg).append(r)
    return r


def editar(cfg, indice, texto=None, dice=None, completa=None):
    lista = reglas(cfg)
    if not 0 <= indice < len(lista):
        raise KeyError(indice)
    r = lista[indice]
    if texto is not None:
        if not texto.strip():
            raise ValueError("El texto a reemplazar no puede estar vacío")
        r["text"] = texto.strip()
    if dice is not None:
        r["say"] = dice.strip()
    if completa is not None:
        r["whole"] = bool(completa)
    return r


def borrar(cfg, indice):
    lista = reglas(cfg)
    if not 0 <= indice < len(lista):
        return False
    del lista[indice]
    return True


class PronunciacionMixin:
    """Pestaña «Pronunciación»: tabla editable de reemplazos."""

    def _build_pronunciacion_tab(self):
        self.pron_tab = self.tabview.add(tab_pronunciacion())
        barra = ctk.CTkFrame(self.pron_tab, fg_color="transparent")
        barra.pack(fill="x", padx=4, pady=(2, 6))
        self.pron_var = ctk.BooleanVar(value=activo(self.cfg))
        self.pron_switch = ctk.CTkSwitch(
            barra, text="Usar diccionario", variable=self.pron_var,
            command=self._pron_alternar, font=self.font())
        self.pron_switch.pack(side="left", padx=(0, 10))
        self._reg(self.pron_switch, lambda w: w.configure(
            progress_color=self._col("--accent"),
            button_color=self._col("--text"),
            button_hover_color=self._col("--text-2"),
            fg_color=self._col("--border-strong"),
            text_color=self._col("--text")))
        self._btn(barra, "＋ Regla", self._pron_agregar).pack(side="left")
        self.pron_lista = ctk.CTkScrollableFrame(self.pron_tab, corner_radius=8)
        self.pron_lista.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self._reg(self.pron_lista, lambda w: w.configure(
            fg_color=self._col("--surface-2")))
        self._refresh_pronunciacion()

    def _refresh_pronunciacion(self):
        if not hasattr(self, "pron_lista"):
            return
        c = self._col
        for w in self.pron_lista.winfo_children():
            w.destroy()
        self.pron_filas = []
        h = self._px("--control-h", 36)
        if not reglas(self.cfg):
            ctk.CTkLabel(self.pron_lista, font=self.font(),
                         text_color=c("--text-3"),
                         text="Sin reglas. Pulsa «＋ Regla».").pack(pady=24)
            return
        for i, r in enumerate(reglas(self.cfg)):
            fila = ctk.CTkFrame(self.pron_lista, fg_color="transparent")
            fila.pack(fill="x", pady=2)
            texto = ctk.CTkEntry(fila, width=120, height=h, font=self.font())
            texto.insert(0, r["text"])
            texto.pack(side="left")
            self._paint_entry(texto)
            ctk.CTkLabel(fila, text="→", font=self.font(),
                         text_color=c("--text-3")).pack(side="left", padx=6)
            dice = ctk.CTkEntry(fila, height=h, font=self.font())
            dice.insert(0, r["say"])
            dice.pack(side="left", fill="x", expand=True)
            self._paint_entry(dice)
            completa = ctk.BooleanVar(value=r["whole"])
            cb = ctk.CTkCheckBox(
                fila, text="Palabra completa", variable=completa,
                font=self.font(),
                command=lambda j=i, v=completa: self._pron_guardar(
                    j, completa=v.get()))
            cb.pack(side="left", padx=8)
            self._reg(cb, self._paint_check)
            b = self._btn(fila, "✕", lambda j=i: self._pron_borrar(j))
            b.configure(width=h)
            b.pack(side="right")
            for campo in (texto, dice):
                campo.bind("<FocusOut>", lambda e, j=i, t=texto, d=dice:
                           self._pron_guardar(j, texto=t.get(), dice=d.get()))
            self.pron_filas.append((texto, dice, completa))

    def _pron_alternar(self):
        activar(self.cfg, self.pron_var.get())
        self._save_soon()
        self.set_status("🗣 Diccionario " + ("activado" if self.pron_var.get()
                                             else "desactivado"))

    def _pron_guardar(self, indice, **campos):
        try:
            editar(self.cfg, indice, **campos)
        except (ValueError, KeyError) as exc:
            self.set_status(f"⚠ {exc}")
            return
        self._save_soon()

    def _pron_agregar(self):
        agregar(self.cfg, "nueva", "cómo se dice")
        self._save_soon()
        self._refresh_pronunciacion()

    def _pron_borrar(self, indice):
        if borrar(self.cfg, indice):
            self._save_soon()
            self._refresh_pronunciacion()
