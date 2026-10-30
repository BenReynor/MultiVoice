"""Ventana modal de Ajustes y diálogos modales (mezcla para TTSApp).

Estilo Discord: columna de secciones a la izquierda, contenido a la derecha.
Todos los colores salen de la paleta del tema (`self._col`).
"""
import tkinter as tk

import customtkinter as ctk

import atajo
import idioma
import platform_utils as pu
from idioma import t

ENGINES = {"edge": "Microsoft Edge", "gtts": "Google TTS",
           "robot": "Sonido robot"}
# Las claves identifican la sección; el texto mostrado sale de `_titulo_seccion`.
SECCIONES = ("General", "Audio", "Sonido robot", "Atajos")


def _titulo_seccion(clave):
    """Nombre traducido de una sección (se evalúa al construir la ventana)."""
    return {"General": t("General"), "Audio": t("Audio"),
            "Sonido robot": t("Robot sound"), "Atajos": t("Shortcuts")}[clave]


class AjustesMixin:
    settings_win = None

    # ---------- Modales ----------
    def _modal(self, titulo, ancho, alto):
        """Ventana modal propia, centrada sobre la principal; Escape la cierra."""
        win = ctk.CTkToplevel(self.root)
        win.title(titulo)
        win.configure(fg_color=self._col("--bg"))
        win.resizable(False, False)
        win.transient(self.root)
        try:
            x = self.root.winfo_rootx() + (self.root.winfo_width() - ancho) // 2
            y = self.root.winfo_rooty() + (self.root.winfo_height() - alto) // 2
        except tk.TclError:
            x = y = 100
        win.geometry(f"{ancho}x{alto}+{max(x, 0)}+{max(y, 0)}")
        win.bind("<Escape>", lambda e: win.destroy())
        win.after(150, lambda: self._grab(win))
        return win

    def confirmar(self, titulo, mensaje, texto_ok=None):
        """Diálogo modal Cancelar / confirmar. Devuelve True si se confirma."""
        win = self._modal(titulo, 420, 190)
        texto_ok = texto_ok or t("Delete")
        res = {"ok": False}
        ctk.CTkLabel(win, text=titulo, anchor="w",
                     font=self.font(self._px("--fs-lg", 16), True),
                     text_color=self._col("--text")).pack(
            fill="x", padx=20, pady=(18, 4))
        ctk.CTkLabel(win, text=mensaje, anchor="w", justify="left",
                     wraplength=380, font=self.font(),
                     text_color=self._col("--text-2")).pack(
            fill="x", padx=20)
        barra = ctk.CTkFrame(win, fg_color="transparent")
        barra.pack(side="bottom", fill="x", padx=20, pady=16)

        def cerrar(ok):
            res["ok"] = ok
            win.destroy()

        ok = ctk.CTkButton(barra, text=texto_ok, command=lambda: cerrar(True),
                           height=self._px("--control-h", 36),
                           font=self.font(bold=True))
        self._paint_button(ok, True)
        ok.configure(fg_color=self._col("--danger"),
                     hover_color=self._col("--danger"),
                     text_color="#ffffff")
        ok.pack(side="right")
        cancel = ctk.CTkButton(barra, text=t("Cancel"),
                               command=lambda: cerrar(False),
                               height=self._px("--control-h", 36),
                               font=self.font())
        self._paint_button(cancel, False)
        cancel.pack(side="right", padx=(0, 8))
        cancel.focus_set()
        self.root.wait_window(win)
        return res["ok"]

    @staticmethod
    def _grab(win):
        try:
            if win.winfo_exists():
                win.grab_set()
        except tk.TclError:
            pass  # sin foco o sin pantalla: el diálogo sigue siendo usable

    # ---------- Ajustes ----------
    def open_settings(self, seccion="General"):
        """Ventana modal de Ajustes: General, Audio, Sonido robot y Atajos."""
        if self.settings_win is not None and self.settings_win.winfo_exists():
            self.settings_win.lift()
            self._show_section(seccion)
            return
        c = self._col
        win = self._modal(t("MultiVoice Settings"), 700, 620)
        self.settings_win = win

        nav = ctk.CTkFrame(win, width=190, corner_radius=0,
                           fg_color=c("--surface-2"))
        nav.pack(side="left", fill="y")
        nav.pack_propagate(False)
        ctk.CTkLabel(nav, text=t("SETTINGS"), anchor="w",
                     font=self.font(self._px("--fs-xs", 11), True),
                     text_color=c("--text-3")).pack(fill="x", padx=16,
                                                    pady=(18, 6))
        self._nav_btns = {}
        for nombre in SECCIONES:
            b = ctk.CTkButton(
                nav, text=_titulo_seccion(nombre), anchor="w", height=32, corner_radius=4,
                font=self.font(), fg_color="transparent",
                hover_color=c("--surface-hover"), text_color=c("--text-2"),
                command=lambda n=nombre: self._show_section(n))
            b.pack(fill="x", padx=8, pady=1)
            self._nav_btns[nombre] = b

        cuerpo = ctk.CTkFrame(win, corner_radius=0, fg_color=c("--surface"))
        cuerpo.pack(side="left", fill="both", expand=True)
        pie = ctk.CTkFrame(cuerpo, fg_color="transparent")
        pie.pack(side="bottom", fill="x", padx=16, pady=12)
        cerrar = ctk.CTkButton(pie, text=t("Close"), command=win.destroy,
                               height=self._px("--control-h", 36),
                               font=self.font())
        self._paint_button(cerrar, True)
        cerrar.pack(side="right")
        ctk.CTkLabel(pie, text=t("Esc to close"), font=self.font(),
                     text_color=c("--text-3")).pack(side="left")

        self._sections = {}
        for nombre in SECCIONES:
            fr = ctk.CTkFrame(cuerpo, fg_color="transparent")
            self._sections[nombre] = fr
        self._build_general(self._sections["General"])
        self._build_audio(self._sections["Audio"])
        self._build_robot(self._sections["Sonido robot"])
        self._build_atajos(self._sections["Atajos"])
        self._show_section(seccion)

    def _show_section(self, nombre):
        c = self._col
        for n, fr in self._sections.items():
            fr.pack_forget()
            activo = n == nombre
            self._nav_btns[n].configure(
                fg_color=c("--accent-soft") if activo else "transparent",
                text_color=c("--text") if activo else c("--text-2"))
        self._sections[nombre].pack(fill="both", expand=True)
        self.settings_section = nombre

    # -- piezas
    def _s_titulo(self, parent, txt):
        ctk.CTkLabel(parent, text=txt, anchor="w",
                     font=self.font(self._px("--fs-xl", 20), True),
                     text_color=self._col("--text")).pack(
            fill="x", padx=24, pady=(20, 8))

    def _s_etiqueta(self, parent, txt, ayuda=False):
        ctk.CTkLabel(parent, text=txt, anchor="w", justify="left",
                     wraplength=420, font=self.font(),
                     text_color=self._col("--text-3" if ayuda else "--text-2")
                     ).pack(fill="x", padx=24, pady=(10, 2))

    def _s_check(self, parent, txt, var, key):
        def cambio():
            self.cfg[key] = var.get()
            self._save_soon()
        cb = ctk.CTkCheckBox(parent, text=txt, variable=var, font=self.font(),
                             command=cambio)
        self._paint_check(cb)
        cb.pack(anchor="w", padx=24, pady=4)

    def _s_slider(self, parent, txt, key, lo, hi, unit="", default=0):
        c = self._col
        cur = int(self.cfg.get(key, default))
        fr = ctk.CTkFrame(parent, fg_color="transparent")
        fr.pack(fill="x", padx=24, pady=5)
        ctk.CTkLabel(fr, text=txt, width=150, anchor="w", font=self.font(),
                     text_color=c("--text")).pack(side="left")
        val = ctk.CTkLabel(fr, text=f"{cur}{unit}", width=60, anchor="e",
                           font=self.font(), text_color=c("--text-2"))
        val.pack(side="right")

        def cambio(v):
            v = int(round(float(v)))
            val.configure(text=f"{v}{unit}")
            self.cfg[key] = v
            if key == "robot_metal":
                self.metal_slider.set(v)
                self._on_metal(v)
            self._save_soon()

        s = ctk.CTkSlider(fr, from_=lo, to=hi, command=cambio)
        self._paint_slider(s)
        s.set(cur)
        s.pack(side="left", fill="x", expand=True, padx=8)

    # -- secciones
    def _build_general(self, p):
        self._s_titulo(p, t("General"))
        self._s_etiqueta(p, t("Voice engine"))
        fila = ctk.CTkFrame(p, fg_color="transparent")
        fila.pack(fill="x", padx=24)
        actual = ENGINES.get(self.current_engine, ENGINES["edge"])
        self.settings_engine_menu = ctk.CTkOptionMenu(
            fila, values=list(ENGINES.values()), width=220,
            height=self._px("--control-h", 36), font=self.font(),
            dropdown_font=self.font(), command=self._on_engine_selected)
        self._paint_menu(self.settings_engine_menu)
        self.settings_engine_menu.set(actual)
        self.settings_engine_menu.pack(side="left")
        self._s_etiqueta(p, t("Edge and Google need internet; the robot "
                              "sound works offline."), ayuda=True)
        self._s_etiqueta(p, t("Maximum number of text tabs"))
        self._s_slider(p, t("Tabs"), "max_tabs", 1, 10, default=5)
        self._s_etiqueta(p, t("Library folder"))
        ctk.CTkLabel(p, text=self._get_library_dir(), anchor="w",
                     font=ctk.CTkFont(family=pu.TEXT_FONT, size=12),
                     text_color=self._col("--text")).pack(fill="x", padx=24)
        self._s_etiqueta(p, t("The theme is chosen in the main window."),
                         ayuda=True)
        self._s_etiqueta(p, t("Language / Idioma"))
        fila_idioma = ctk.CTkFrame(p, fg_color="transparent")
        fila_idioma.pack(fill="x", padx=24)
        aviso_idioma = ctk.CTkLabel(p, text="", anchor="w", justify="left",
                                    wraplength=420, font=self.font(),
                                    text_color=self._col("--text-2"))

        def elegir_idioma(nombre):
            codigo = next(c for c, n in idioma.IDIOMAS.items() if n == nombre)
            self.cfg["language"] = codigo
            self._save_soon()
            aviso_idioma.configure(
                text=t("The language changes when you restart MultiVoice."))

        self.settings_language_menu = ctk.CTkOptionMenu(
            fila_idioma, values=list(idioma.IDIOMAS.values()), width=220,
            height=self._px("--control-h", 36), font=self.font(),
            dropdown_font=self.font(), command=elegir_idioma)
        self._paint_menu(self.settings_language_menu)
        self.settings_language_menu.set(
            idioma.IDIOMAS.get(self.cfg.get("language"),
                               idioma.IDIOMAS[idioma.POR_DEFECTO]))
        self.settings_language_menu.pack(side="left")
        aviso_idioma.pack(fill="x", padx=24, pady=(4, 0))

    def _build_audio(self, p):
        self._s_titulo(p, t("Audio"))
        self._s_etiqueta(p, t("After speaking"))
        self._s_check(p, t("Clear the text after speaking"), self.auto_clear_var,
                      "auto_clear")
        self._s_etiqueta(p, t("Playback"))
        self._s_check(p, t("Queue audio (do not interrupt)"), self.queue_var,
                      "queue_enabled")
        self._s_etiqueta(p, t("Library"))
        self._s_check(p, t("Save every spoken audio"), self.auto_save_var,
                      "auto_save")

    def _build_robot(self, p):
        self._s_titulo(p, t("Robot sound"))
        self._s_slider(p, t("Speed (wpm)"), "robot_speed", 40, 450,
                       default=135)
        self._s_slider(p, t("espeak pitch"), "robot_pitch", 1, 99, default=30)
        self._s_slider(p, t("Metal (distortion)"), "robot_metal", 0, 100, "%",
                       default=70)
        self._s_slider(p, t("Volume (dB)"), "robot_volume", -50, 50, "dB")

    def _build_atajos(self, p):
        self._s_titulo(p, t("Shortcuts"))
        for k, v in (
                (f"{pu.MOD_LABEL}+Enter", t("Speak the current tab")),
                ("Enter", t("Speak from the editor")),
                (f"{pu.MOD_LABEL}+T", t("New tab")),
                (f"{pu.MOD_LABEL}+W", t("Close tab")),
                ("F5", t("Test the chosen voice"))):
            fila = ctk.CTkFrame(p, fg_color="transparent")
            fila.pack(fill="x", padx=24, pady=4)
            ctk.CTkLabel(fila, text=k, width=140, anchor="w",
                         font=self.font(bold=True),
                         text_color=self._col("--accent")).pack(side="left")
            ctk.CTkLabel(fila, text=v, font=self.font(),
                         text_color=self._col("--text-2")).pack(side="left")
        self._build_atajo_global(p)

    def _build_atajo_global(self, p):
        """Atajo para hablar desde cualquier app (`multivoice --decir`)."""
        self._s_etiqueta(p, t("Global shortcut to speak"))
        if pu.IS_WIN:
            self._s_etiqueta(
                p, t("Opens an always-on-top box where you type and Enter "
                     "says it. Format: ctrl+alt+h."), ayuda=True)
            fila = ctk.CTkFrame(p, fg_color="transparent")
            fila.pack(fill="x", padx=24, pady=4)
            ent = ctk.CTkEntry(fila, width=200, font=self.font())
            ent.insert(0, self.cfg.get("atajo_global",
                                       atajo.ATAJO_POR_DEFECTO))
            ent.pack(side="left")
            aviso = ctk.CTkLabel(fila, text="", font=self.font(),
                                 text_color=self._col("--text-2"))

            def guardar():
                txt = ent.get().strip().lower()
                if atajo.a_pynput(txt) is None:
                    aviso.configure(text=t("Invalid shortcut"))
                    return
                self.cfg["atajo_global"] = txt
                self._save_soon()
                ok = self.registrar_atajo_global()
                aviso.configure(text=t("Saved") if ok else t("Could not register"))

            b = ctk.CTkButton(fila, text=t("Save"), width=90, command=guardar,
                              height=self._px("--control-h", 36),
                              font=self.font())
            self._paint_button(b, True)
            b.pack(side="left", padx=8)
            aviso.pack(side="left")
            return
        self._s_etiqueta(
            p, t("On Linux (Wayland) apps cannot register global "
                     "shortcuts. Assign the command «multivoice --decir» to a "
                     "key in your system settings (Keyboard → Custom "
                     "shortcuts) and it will open an always-on-top box where "
                     "you type and Enter says it."), ayuda=True)
        ctk.CTkLabel(p, text=atajo.comando_decir(), anchor="w",
                     font=ctk.CTkFont(family=pu.TEXT_FONT, size=12),
                     text_color=self._col("--text")).pack(fill="x", padx=24)
        if not atajo.es_gnome():
            return
        fila = ctk.CTkFrame(p, fg_color="transparent")
        fila.pack(fill="x", padx=24, pady=8)
        aviso = ctk.CTkLabel(p, text="", anchor="w", justify="left",
                             wraplength=420, font=self.font(),
                             text_color=self._col("--text-2"))

        def crear():
            txt = self.cfg.get("atajo_global", atajo.ATAJO_POR_DEFECTO)
            try:
                tecla = atajo.crear_atajo_gnome(txt)
                aviso.configure(text=t("Created in GNOME: {key}", key=tecla))
            except RuntimeError as exc:
                aviso.configure(text=t("Could not create it: {error}", error=exc))

        b = ctk.CTkButton(fila, text=t("Create shortcut in GNOME"), command=crear,
                          height=self._px("--control-h", 36),
                          font=self.font())
        self._paint_button(b, True)
        b.pack(side="left")
        ctk.CTkLabel(fila, text=f"({self.cfg.get('atajo_global', atajo.ATAJO_POR_DEFECTO)})",
                     font=self.font(), text_color=self._col("--text-3")
                     ).pack(side="left", padx=8)
        aviso.pack(fill="x", padx=24)
