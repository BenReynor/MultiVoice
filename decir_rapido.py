"""Cuadro «Decir» siempre encima, instancia única y atajo global (mezcla para TTSApp)."""
import sys
import tkinter as tk

import customtkinter as ctk

import atajo
import instancia
from idioma import t


class DecirRapidoMixin:
    decir_win = None
    servidor = None
    atajo_win = None

    # ---------- Instancia única ----------
    def iniciar_instancia(self, servidor):
        """Recibe las órdenes de otras ejecuciones (`multivoice --decir`)."""
        self.servidor = servidor
        if servidor is not None:
            servidor.al_mensaje = lambda cmd: self.root.after(
                0, self.atender_orden, cmd)
        self.registrar_atajo_global()

    def atender_orden(self, cmd):
        if cmd == instancia.CMD_DECIR:
            self.abrir_decir()
        else:
            try:
                self.root.deiconify()
                self.root.lift()
                self.root.focus_force()
            except tk.TclError:
                pass

    # ---------- Atajo global (solo Windows) ----------
    def registrar_atajo_global(self):
        """Registra el atajo global; devuelve True si quedó activo."""
        if not sys.platform.startswith("win"):
            return False
        if self.atajo_win is None:
            self.atajo_win = atajo.GlobalWindows(
                lambda: self.root.after(0, self.abrir_decir))
        texto = self.cfg.get("atajo_global", atajo.ATAJO_POR_DEFECTO)
        ok = self.atajo_win.registrar(texto)
        if not ok:
            self.set_status(t("⚠️ Could not register the global shortcut "
                              "({shortcut})", shortcut=texto))
        return ok

    # ---------- Cuadro ----------
    def abrir_decir(self):
        """Cuadro pequeño siempre encima: escribe y Enter lo dice."""
        if self.decir_win is not None and self.decir_win.winfo_exists():
            self.decir_win.deiconify()
            self.decir_win.lift()
            self.decir_entry.focus_force()
            return
        c = self._col
        win = ctk.CTkToplevel(self.root)
        self.decir_win = win
        win.title(t("Say"))
        win.configure(fg_color=c("--surface"))
        win.attributes("-topmost", True)
        win.resizable(False, False)
        ancho, alto = 460, 64
        try:
            x = (win.winfo_screenwidth() - ancho) // 2
            y = win.winfo_screenheight() // 3
        except tk.TclError:
            x = y = 100
        win.geometry(f"{ancho}x{alto}+{x}+{y}")
        self.decir_entry = ctk.CTkEntry(
            win, placeholder_text=t("Type and press Enter to say it…"),
            height=self._px("--control-h", 36), font=self.font(),
            fg_color=c("--surface-2"), text_color=c("--text"),
            border_color=c("--accent"))
        self.decir_entry.pack(fill="x", padx=12, pady=14)
        self.decir_entry.bind("<Return>", lambda e: self.decir_enviar())
        win.bind("<Escape>", lambda e: win.destroy())
        self.decir_entry.bind("<Escape>", lambda e: win.destroy())
        win.after(100, self._decir_foco)

    def _decir_foco(self):
        try:
            if self.decir_win is not None and self.decir_win.winfo_exists():
                self.decir_win.lift()
                self.decir_win.focus_force()
                self.decir_entry.focus_force()
        except tk.TclError:
            pass

    def decir_enviar(self):
        """Dice el texto del cuadro y lo cierra. Devuelve el texto dicho."""
        texto = self.decir_entry.get().strip()
        if not texto:
            return ""
        self.decir_texto(texto)
        self.decir_win.destroy()
        return texto

    def decir_texto(self, texto):
        job = self.build_job(texto)
        job["queue"] = self.queue_var.get()
        self.worker.enqueue(job)
