"""Vista de la Biblioteca de audios (mezcla para TTSApp).

Lista con texto, voz, fecha y tamaño; búsqueda; reproducir; abrir carpeta y
borrar con confirmación. La lógica de datos vive en library.py.
"""
import os
import subprocess
import sys
import tkinter as tk
from datetime import datetime

import customtkinter as ctk

import platform_utils as pu
from library import cleanup_library, delete_entry, fmt_size, list_entries

LIB_TAB = "📁 Biblioteca"
MAX_FILAS = 200


class BibliotecaMixin:
    def _get_library_dir(self):
        return self.cfg.get("library_path", pu.default_library_dir())

    def _build_library_tab(self):
        self.lib_tab = self.tabview.add(LIB_TAB)
        barra = ctk.CTkFrame(self.lib_tab, fg_color="transparent")
        barra.pack(fill="x", padx=4, pady=(2, 6))
        self.lib_search_var = tk.StringVar()
        self.lib_search = ctk.CTkEntry(
            barra, textvariable=self.lib_search_var, height=self._px(
                "--control-h", 36), font=self.font(),
            placeholder_text="🔍 Buscar por texto o voz…")
        self.lib_search.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.lib_search_var.trace_add("write", lambda *a: self._refresh_library())
        self._reg(self.lib_search, self._paint_entry)
        self._btn(barra, "🔄 Actualizar", self._refresh_library).pack(
            side="left", padx=(0, 6))
        self._btn(barra, "📂 Abrir carpeta", self._open_library_folder).pack(
            side="left")

        self.lib_count = ctk.CTkLabel(self.lib_tab, text="", anchor="w",
                                      font=self.font())
        self.lib_count.pack(fill="x", padx=8)
        self._reg(self.lib_count, lambda w: w.configure(
            text_color=self._col("--text-3")))
        self.lib_list = ctk.CTkScrollableFrame(self.lib_tab, corner_radius=8)
        self.lib_list.pack(fill="both", expand=True, padx=4, pady=(4, 4))
        self._reg(self.lib_list, lambda w: w.configure(
            fg_color=self._col("--surface-2")))
        self.lib_rows = []
        self._refresh_library()

    def _paint_entry(self, w):
        w.configure(fg_color=self._col("--surface-2"),
                    text_color=self._col("--text"),
                    border_color=self._col("--border-strong"),
                    placeholder_text_color=self._col("--text-3"),
                    corner_radius=self._px("--radius", 8))

    def _style_library(self):
        """Repinta la lista con la paleta actual (se vuelve a dibujar)."""
        self._refresh_library()

    def _refresh_library(self):
        """Lee la carpeta y dibuja las filas (o el estado vacío)."""
        if not hasattr(self, "lib_list"):
            return
        c = self._col
        for w in self.lib_list.winfo_children():
            w.destroy()
        lib_dir = self._get_library_dir()
        query = self.lib_search_var.get()
        entries = list_entries(lib_dir, query)
        self.lib_entries = entries
        total = len(entries)
        self.lib_count.configure(
            text=f"{total} audio{'s' if total != 1 else ''}"
                 + (f" para «{query.strip()}»" if query.strip() else ""))
        if not entries:
            msg = ("Nada coincide con la búsqueda." if query.strip() else
                   "Aún no hay audios. Activa «Guardado automático» o pulsa "
                   "Guardar para llenar la biblioteca.")
            if not os.path.isdir(lib_dir) and not query.strip():
                msg = "La carpeta de la biblioteca todavía no existe. " + msg
            ctk.CTkLabel(self.lib_list, text=msg, wraplength=560,
                         font=self.font(), text_color=c("--text-2"),
                         justify="center").pack(pady=40, padx=20)
            return
        for e in entries[:MAX_FILAS]:
            self._lib_row(e)
        if total > MAX_FILAS:
            ctk.CTkLabel(self.lib_list, font=self.font(),
                         text=f"Se muestran los {MAX_FILAS} más recientes; "
                              "usa la búsqueda para afinar.",
                         text_color=c("--text-3")).pack(pady=8)

    def _lib_row(self, e):
        c = self._col
        fila = ctk.CTkFrame(self.lib_list, fg_color=c("--surface"),
                            corner_radius=self._px("--radius", 8))
        fila.pack(fill="x", padx=2, pady=2)
        izq = ctk.CTkFrame(fila, fg_color="transparent")
        izq.pack(side="left", fill="x", expand=True, padx=10, pady=6)
        texto = " ".join(e["text"].split()) or e["name"]
        if len(texto) > 90:
            texto = texto[:89] + "…"
        ctk.CTkLabel(izq, text=texto, anchor="w", font=self.font(),
                     text_color=c("--text")).pack(fill="x")
        fecha = datetime.fromtimestamp(e["mtime"]).strftime("%d/%m/%Y %H:%M")
        voz = e["voice"] or e["engine"] or "voz desconocida"
        ctk.CTkLabel(izq, anchor="w", text=f"{voz}  ·  {fecha}  ·  "
                     f"{fmt_size(e['size'])}",
                     font=self.font(self._px("--fs-sm", 12)),
                     text_color=c("--text-3")).pack(fill="x")
        borrar = ctk.CTkButton(fila, text="🗑 Borrar", width=84,
                               height=self._px("--control-h", 36) - 4,
                               font=self.font(),
                               command=lambda p=e["path"]: self._delete_library_entry(p))
        self._paint_button(borrar, False)
        borrar.pack(side="right", padx=(0, 10))
        play = ctk.CTkButton(fila, text="▶ Reproducir", width=104,
                             height=self._px("--control-h", 36) - 4,
                             font=self.font(),
                             command=lambda p=e["path"]: self._play_library_path(p))
        self._paint_button(play, True)
        play.pack(side="right", padx=(0, 6))

    def _open_path(self, path):
        if sys.platform.startswith("win"):
            os.startfile(path)  # noqa: S606 - solo rutas de la biblioteca
        else:
            subprocess.Popen(["xdg-open", path])

    def _play_library_path(self, path):
        """Abre el audio con el reproductor del sistema."""
        try:
            self._open_path(path)
            self.set_status(f"▶ Reproduciendo {os.path.basename(path)}")
        except Exception as exc:
            self.set_status(f"⚠️ No se pudo reproducir: {exc}")

    def _delete_library_entry(self, path):
        """Borra un audio tras pedir confirmación."""
        nombre = os.path.basename(path)
        if not self.confirmar(
                "¿Borrar este audio?",
                f"Se borrará «{nombre}» de la biblioteca. "
                "No se puede deshacer."):
            return False
        try:
            delete_entry(path)
        except OSError as exc:
            self.set_status(f"⚠️ No se pudo borrar: {exc}")
            return False
        self._refresh_library()
        self.set_status(f"🗑️ Borrado {nombre}")
        return True

    def _open_library_folder(self):
        lib_dir = self._get_library_dir()
        try:
            os.makedirs(lib_dir, exist_ok=True)
            self._open_path(lib_dir)
        except Exception as exc:
            self.set_status(f"⚠️ No se pudo abrir la carpeta: {exc}")

    def _cleanup_library(self):
        """Borra los audios de la app con más de 30 días (nada más)."""
        deleted = cleanup_library(self._get_library_dir(), days=30)
        if deleted:
            self.set_status(
                f"🧹 Limpieza automática: {deleted} archivo(s) antiguos eliminados")
