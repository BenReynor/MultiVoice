"""Pantalla de carga: mientras se construye la ventana principal (oculta) se
muestra el icono, el paso actual y una barra de progreso, en vez de ver cómo
aparecen los controles uno a uno."""
import os
import tkinter as tk

import customtkinter as ctk

import platform_utils as pu

FONDO = "#0f172a"
TEXTO = "#e2e8f0"
TENUE = "#94a3b8"
ACENTO = "#f9a8d4"
PISTA = "#1e293b"
ICONO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.png")


class PantallaCarga:
    def __init__(self, root):
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.configure(bg=FONDO)
        self.win.attributes("-topmost", True)
        ancho, alto = 360, 240
        x = (self.win.winfo_screenwidth() - ancho) // 2
        y = (self.win.winfo_screenheight() - alto) // 2
        self.win.geometry(f"{ancho}x{alto}+{x}+{y}")

        self._img = None
        try:
            self._img = tk.PhotoImage(file=ICONO).subsample(6)   # 512 → ~85 px
        except tk.TclError:
            pass
        if self._img is not None:
            tk.Label(self.win, image=self._img, bg=FONDO).pack(pady=(24, 6))
        ctk.CTkLabel(self.win, text="MultiVoice", text_color=TEXTO, fg_color=FONDO,
                     font=ctk.CTkFont(family=pu.UI_FONT, size=20, weight="bold")
                     ).pack()
        self.lbl = ctk.CTkLabel(self.win, text="", text_color=TENUE, fg_color=FONDO,
                                font=ctk.CTkFont(family=pu.UI_FONT, size=12))
        self.lbl.pack(side="bottom", pady=(4, 20))
        self.barra = ctk.CTkProgressBar(self.win, width=300, height=10,
                                        progress_color=ACENTO, fg_color=PISTA,
                                        bg_color=FONDO)
        self.barra.pack(side="bottom")
        self.barra.set(0)
        self.valor = 0.0
        self.win.update()

    def paso(self, texto, fraccion):
        """Muestra un paso y su avance (0–1); la barra nunca retrocede."""
        self.valor = max(self.valor, min(1.0, float(fraccion)))
        self.lbl.configure(text=texto)
        self.barra.set(self.valor)
        self.win.update()

    def cerrar(self):
        self.win.destroy()
