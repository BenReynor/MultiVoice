"""Panel lateral: lo que suena, la cola y el historial (mezcla para TTSApp).

Solo dibuja; la lógica vive en cola.py (`ColaVoz`) y medidor.py.
"""
import tkinter as tk

import customtkinter as ctk

from cola import recortar

REFRESCO_MS = 80
CARACTERES_FILA = 46
CARACTERES_AHORA = 90


class ColaMixin:
    def _build_cola_panel(self):
        ancho = max(250, min(self._px("--sidebar-w", 260), 300))
        fs = self._px("--fs-md", 13)
        self._cola_claves = None
        self._nivel_visible = 0.0
        self._cola_timer = None
        self.cola_panel = ctk.CTkFrame(self.root, width=ancho)
        self.cola_panel.pack(side="right", fill="y", padx=(0, 12), pady=(10, 8))
        self.cola_panel.pack_propagate(False)
        self._reg(self.cola_panel, self._paint_card)
        caja = ctk.CTkFrame(self.cola_panel, fg_color="transparent")
        caja.pack(fill="both", expand=True, padx=12, pady=10)

        # ---- Ahora suena ----
        self.lbl_ahora = self._titulo_panel(caja, "Ahora suena")
        self.now_text = ctk.CTkLabel(caja, text="", anchor="w", justify="left",
                                     wraplength=ancho - 50, font=self.font(fs))
        self.now_text.pack(fill="x", pady=(4, 0))
        self.now_voice = ctk.CTkLabel(caja, text="", anchor="w",
                                      font=self.font(fs - 1))
        self.now_voice.pack(fill="x")
        self.now_bar = ctk.CTkProgressBar(caja, height=8)
        self.now_bar.set(0)
        self.now_bar.pack(fill="x", pady=(6, 0))
        fila_nivel = ctk.CTkFrame(caja, fg_color="transparent")
        fila_nivel.pack(fill="x", pady=(6, 0))
        self.lbl_nivel = ctk.CTkLabel(fila_nivel, text="Nivel", width=44,
                                      anchor="w", font=self.font(fs - 1))
        self.lbl_nivel.pack(side="left")
        self.level_bar = ctk.CTkProgressBar(fila_nivel, height=8)
        self.level_bar.set(0)
        self.level_bar.pack(side="left", fill="x", expand=True)
        for w, color in ((self.now_text, "--text"), (self.now_voice, "--text-2"),
                         (self.lbl_nivel, "--text-2")):
            self._reg(w, lambda x, c=color: x.configure(text_color=self._col(c)))
        self._reg(self.now_bar, self._paint_barra)
        self._reg(self.level_bar, self._paint_barra)

        # ---- En cola ----
        self.lbl_cola = self._titulo_panel(caja, "En cola", pady=(14, 0))
        self.cola_list = self._lista_panel(caja, 118)

        # ---- Historial ----
        cab = ctk.CTkFrame(caja, fg_color="transparent")
        cab.pack(fill="x", pady=(14, 0))
        self.lbl_hist = ctk.CTkLabel(cab, text="Historial", anchor="w",
                                     font=self.font(fs, True))
        self.lbl_hist.pack(side="left")
        self._reg(self.lbl_hist, lambda w: w.configure(
            text_color=self._col("--text")))
        self.btn_hist_clear = self._btn(cab, "Limpiar", self._limpiar_historial,
                                        height=28)
        self.btn_hist_clear.pack(side="right")
        self.hist_list = self._lista_panel(caja, 0, expand=True)

        self._tick_cola()

    def _titulo_panel(self, parent, texto, pady=0):
        lbl = ctk.CTkLabel(parent, text=texto, anchor="w",
                           font=self.font(self._px("--fs-md", 13), True))
        lbl.pack(fill="x", pady=pady)
        self._reg(lbl, lambda w: w.configure(text_color=self._col("--text")))
        return lbl

    def _lista_panel(self, parent, alto, expand=False):
        lista = ctk.CTkScrollableFrame(parent, height=alto, corner_radius=8)
        lista.pack(fill="both" if expand else "x", expand=expand, pady=(4, 0))
        self._reg(lista, lambda w: w.configure(
            fg_color=self._col("--surface-2"),
            scrollbar_button_color=self._col("--border-strong")))
        return lista

    def _paint_barra(self, w):
        w.configure(fg_color=self._col("--border-strong"),
                    progress_color=self._col("--accent"))

    # ---------- Refresco ----------
    def _refresh_cola(self, forzar=False):
        """Redibuja el panel con el estado actual de la cola."""
        if not hasattr(self, "hist_list"):
            return
        sonando, pendientes, historial = self.worker.cola.instantanea()
        if sonando is None:
            self.now_text.configure(text="Nada suena ahora")
            self.now_voice.configure(text="")
            self.now_bar.set(0)
        else:
            self.now_text.configure(
                text=recortar(sonando.texto, CARACTERES_AHORA))
            self.now_voice.configure(text="🎤 " + sonando.voz)
        claves = (tuple(e.id for e in pendientes), tuple(e.id for e in historial))
        if claves == self._cola_claves and not forzar:
            return
        self._cola_claves = claves
        self.lbl_cola.configure(text=f"En cola ({len(pendientes)})")
        self.lbl_hist.configure(text=f"Historial ({len(historial)})")
        self.btn_hist_clear.configure(
            state="normal" if historial else "disabled")
        self._llenar_lista(self.cola_list, pendientes, "✕", self._quitar_de_cola,
                           "La cola está vacía")
        self._llenar_lista(self.hist_list, historial, "↻", self._repetir,
                           "Aún no has dicho nada en esta sesión")

    def _llenar_lista(self, lista, elementos, icono, comando, vacio):
        for w in lista.winfo_children():
            w.destroy()
        if not elementos:
            ctk.CTkLabel(lista, text=vacio, anchor="w", justify="left",
                         wraplength=200, font=self.font(),
                         text_color=self._col("--text-3")).pack(
                fill="x", padx=6, pady=6)
            return
        for el in elementos:
            fila = ctk.CTkFrame(lista, fg_color=self._col("--surface"),
                                corner_radius=self._px("--radius", 8))
            fila.pack(fill="x", pady=2)
            btn = ctk.CTkButton(
                fila, text=icono, width=32, height=32, cursor="hand2",
                command=lambda i=el.id: comando(i),
                font=self.font(self._px("--fs-md", 13) + 1, True),
                fg_color=self._col("--surface-2"),
                hover_color=self._col("--danger" if icono == "✕" else "--accent"),
                text_color=self._col("--text"),
                border_width=1, border_color=self._col("--border-strong"),
                corner_radius=self._px("--radius", 8))
            btn.pack(side="right", padx=4, pady=4)
            textos = ctk.CTkFrame(fila, fg_color="transparent")
            textos.pack(side="left", fill="x", expand=True, padx=(8, 0), pady=4)
            ctk.CTkLabel(textos, text=recortar(el.texto, CARACTERES_FILA),
                         anchor="w", justify="left", wraplength=170,
                         font=self.font(), text_color=self._col("--text")
                         ).pack(fill="x")
            ctk.CTkLabel(textos, text=el.voz, anchor="w",
                         font=self.font(self._px("--fs-sm", 12)),
                         text_color=self._col("--text-3")).pack(fill="x")

    def _tick_cola(self):
        """Mueve la barra de progreso y el medidor mientras suena."""
        cola = self.worker.cola
        sonando = cola.instantanea()[0]
        if sonando is None:
            self._nivel_visible = 0.0
            self.now_bar.set(0)
        else:
            self.now_bar.set(cola.progreso())
            # sube de golpe y baja poco a poco, como un vúmetro
            self._nivel_visible = max(cola.nivel(), self._nivel_visible * 0.8)
        self.level_bar.set(self._nivel_visible)
        n = self._nivel_visible
        self.level_bar.configure(progress_color=self._col(
            "--danger" if n > 0.9 else "--warning" if n > 0.75 else "--success"))
        self._cola_timer = self.root.after(REFRESCO_MS, self._tick_cola)

    def _stop_cola_timer(self):
        if self._cola_timer is not None:
            try:
                self.root.after_cancel(self._cola_timer)
            except tk.TclError:
                pass
            self._cola_timer = None

    # ---------- Acciones ----------
    def _quitar_de_cola(self, id_):
        if self.worker.cola.quitar(id_):
            self.set_status("🗑 Quitado de la cola")
        self._refresh_cola()

    def _repetir(self, id_):
        job = self.worker.cola.repetir(id_)
        if job is None:
            return
        job["queue"] = self.queue_var.get()
        self.worker.enqueue(job)
        self.set_status("🔁 Repitiendo: " + recortar(job["text"], 40))

    def _limpiar_historial(self):
        self.worker.cola.limpiar_historial()
        self._refresh_cola()
