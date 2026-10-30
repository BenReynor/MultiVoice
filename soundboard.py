"""Soundboard: archivos de audio propios que suenan por el micrófono virtual.

La lógica (convertir con el ffmpeg de la app, lista en `cfg["soundboard"]`)
no usa la interfaz ni reproduce nada, así se prueba sin pantalla ni audio.
Cada sonido es {"name": ..., "file": <wav dentro de la carpeta del soundboard>}.
`SoundboardMixin` dibuja la vista y encola el sonido como un trabajo más de la
cola (motor «sound»). Los archivos se copian ya convertidos a WAV 48 kHz
estéreo, así el original puede moverse o borrarse.
"""
import os
import re
import uuid
from tkinter import filedialog

import customtkinter as ctk

import tts_engine
from idioma import t


def tab_soundboard():
    return t("🎵 Soundboard")


EXTENSIONES = (".mp3", ".wav", ".ogg")
MOTOR = "sound"


def carpeta(config_dir):
    return os.path.join(config_dir, "soundboard")


def es_soportado(ruta):
    return os.path.splitext(ruta)[1].lower() in EXTENSIONES


def nombre_por_defecto(ruta):
    base = os.path.splitext(os.path.basename(ruta))[0]
    return re.sub(r"[_\-]+", " ", base).strip() or "Sonido"


def convertir(origen, destino_dir, run=None, ffmpeg=None):
    """Convierte un mp3/wav/ogg a WAV 48 kHz estéreo con el ffmpeg de la app.

    Devuelve el nombre del WAV creado dentro de `destino_dir`. `run` y `ffmpeg`
    se pueden sustituir en los tests."""
    if not es_soportado(origen):
        raise ValueError("Formato no soportado (usa mp3, wav u ogg)")
    if not os.path.isfile(origen):
        raise FileNotFoundError(origen)
    os.makedirs(destino_dir, exist_ok=True)
    nombre = f"snd_{uuid.uuid4().hex[:10]}.wav"
    destino = os.path.join(destino_dir, nombre)
    run = run or tts_engine._run
    r = run([ffmpeg or tts_engine.ffmpeg_bin(), "-y", "-i", origen, "-vn",
             "-ar", str(tts_engine.SAMPLE_RATE), "-ac", "2", destino])
    if getattr(r, "returncode", 0) != 0 or not os.path.isfile(destino):
        raise RuntimeError("ffmpeg no pudo convertir el archivo")
    return nombre


def _sonido(datos):
    datos = datos if isinstance(datos, dict) else {}
    return {"name": str(datos.get("name") or "").strip(),
            "file": str(datos.get("file") or "").strip()}


def asegurar(cfg):
    """Garantiza cfg["soundboard"] como lista de sonidos válidos."""
    datos = cfg.get("soundboard")
    datos = datos if isinstance(datos, list) else []
    cfg["soundboard"] = [s for s in map(_sonido, datos)
                         if s["name"] and s["file"]]
    return cfg["soundboard"]


def sonidos(cfg):
    return asegurar(cfg)


def agregar(cfg, nombre, archivo):
    s = _sonido({"name": nombre, "file": archivo})
    if not s["name"]:
        raise ValueError("El sonido necesita un nombre")
    if not s["file"]:
        raise ValueError("Falta el archivo del sonido")
    sonidos(cfg).append(s)
    return s


def renombrar(cfg, indice, nombre):
    lista = sonidos(cfg)
    if not 0 <= indice < len(lista):
        raise KeyError(indice)
    if not nombre.strip():
        raise ValueError("El sonido necesita un nombre")
    lista[indice]["name"] = nombre.strip()
    return lista[indice]


def borrar(cfg, indice, destino_dir=None):
    """Quita el sonido de la lista y borra su WAV si está en `destino_dir`."""
    lista = sonidos(cfg)
    if not 0 <= indice < len(lista):
        return False
    s = lista.pop(indice)
    if destino_dir:
        ruta = ruta_sonido(destino_dir, s)
        if ruta and os.path.isfile(ruta):
            try:
                os.remove(ruta)
            except OSError:
                pass
    return True


def ruta_sonido(destino_dir, sonido):
    """Ruta del WAV del sonido, o None si el nombre intenta salir de la carpeta."""
    nombre = sonido.get("file", "")
    if not nombre or os.path.basename(nombre) != nombre:
        return None
    return os.path.join(destino_dir, nombre)


def job_sonido(sonido, ruta):
    """Trabajo para la cola: suena un archivo ya convertido, sin sintetizar."""
    return {"text": "🎵 " + sonido["name"], "engine": MOTOR,
            "opts": {"file": ruta}, "widget": None, "clear_after": None,
            "voice_label": "Soundboard"}


class SoundboardMixin:
    """Vista «Soundboard»: un botón por sonido."""

    def _build_soundboard_tab(self):
        self.sb_tab = self.tabview.add(tab_soundboard())
        barra = ctk.CTkFrame(self.sb_tab, fg_color="transparent")
        barra.pack(fill="x", padx=4, pady=(2, 6))
        self._btn(barra, "＋ Añadir sonido", self.sb_anadir).pack(side="left")
        self.sb_lista = ctk.CTkScrollableFrame(self.sb_tab, corner_radius=8)
        self.sb_lista.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self._reg(self.sb_lista, lambda w: w.configure(
            fg_color=self._col("--surface-2")))
        self._refresh_soundboard()

    def _sb_dir(self):
        import multivoice
        return carpeta(multivoice.CONFIG_DIR)

    def _refresh_soundboard(self):
        if not hasattr(self, "sb_lista"):
            return
        c = self._col
        for w in self.sb_lista.winfo_children():
            w.destroy()
        lista = sonidos(self.cfg)
        if not lista:
            ctk.CTkLabel(self.sb_lista, font=self.font(),
                         text_color=c("--text-3"),
                         text="Sin sonidos. Pulsa «＋ Añadir sonido» "
                              "(mp3, wav u ogg).").pack(pady=24)
            return
        h = self._px("--control-h", 36)
        for i, s in enumerate(lista):
            fila = ctk.CTkFrame(self.sb_lista, fg_color="transparent")
            fila.pack(fill="x", pady=2)
            b = self._btn(fila, "▶ " + s["name"],
                          lambda j=i: self.sb_reproducir(j))
            b.configure(anchor="w")
            b.pack(side="left", fill="x", expand=True)
            for texto, cmd in (("✕", lambda j=i: self.sb_borrar(j)),
                               ("✎", lambda j=i: self.sb_renombrar(j))):
                bb = self._btn(fila, texto, cmd)
                bb.configure(width=h)
                bb.pack(side="right", padx=(4, 0))

    def sb_anadir(self):
        rutas = filedialog.askopenfilenames(
            title="Añadir sonidos",
            filetypes=[("Audio", "*.mp3 *.wav *.ogg"), ("Todos", "*.*")])
        for ruta in rutas:
            self.sb_anadir_archivo(ruta)

    def sb_anadir_archivo(self, ruta, nombre=None):
        """Convierte y añade un archivo. Devuelve True si se añadió."""
        try:
            archivo = convertir(ruta, self._sb_dir())
            agregar(self.cfg, nombre or nombre_por_defecto(ruta), archivo)
        except (ValueError, OSError, RuntimeError) as exc:
            self.set_status(f"⚠ {exc}")
            return False
        self._save_soon()
        self._refresh_soundboard()
        self.set_status("🎵 Sonido añadido")
        return True

    def sb_renombrar(self, indice):
        dlg = ctk.CTkInputDialog(text="Nuevo nombre:", title="Renombrar sonido")
        nombre = dlg.get_input()
        if nombre is None:
            return
        try:
            renombrar(self.cfg, indice, nombre)
        except (ValueError, KeyError) as exc:
            self.set_status(f"⚠ {exc}")
            return
        self._save_soon()
        self._refresh_soundboard()

    def sb_borrar(self, indice):
        if borrar(self.cfg, indice, self._sb_dir()):
            self._save_soon()
            self._refresh_soundboard()

    def sb_reproducir(self, indice):
        lista = sonidos(self.cfg)
        if not 0 <= indice < len(lista):
            return False
        ruta = ruta_sonido(self._sb_dir(), lista[indice])
        if not ruta or not os.path.isfile(ruta):
            self.set_status("⚠ Falta el archivo de ese sonido")
            return False
        job = job_sonido(lista[indice], ruta)
        job["queue"] = self.queue_var.get()
        self.worker.enqueue(job)
        return True
