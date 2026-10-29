#!/usr/bin/env python3
# MultiVoice - interfaz CustomTkinter con pestañas, voces neuronales y sonido robot
# Uso: python3 multivoice.py

import json
import os
import queue
import re
import shutil
import sys
import tempfile
import threading
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog
from types import SimpleNamespace

import customtkinter as ctk

import atajo
import instancia
import medidor
import temas
import tts_engine
from ajustes import ENGINES, AjustesMixin
from biblioteca import LIB_TAB, BibliotecaMixin
from cola import ColaVoz
from decir_rapido import DecirRapidoMixin
from panel_cola import ColaMixin
from perfiles import PerfilesMixin
import perfiles
import frases
from frases import FrasesMixin
import pronunciacion
from pronunciacion import PronunciacionMixin
import soundboard
from soundboard import SoundboardMixin
import platform_utils as pu
from virtualmic import setup_virtual_mic, teardown_virtual_mic

CONFIG_DIR = pu.config_dir()
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")
ROBOT_VOICE = tts_engine.ROBOT_VOICE
PROBE_TEXTS = [
    "Hola, esta es tu nueva voz de prueba. ¿Cómo me escucho?",
    "El otro día vi una luz extraña en el pasillo de la Fundación.",
    "Todas las amenazas han sido neutralizadas. Todo está bajo control.",
]

_HEX6 = re.compile(r"^#[0-9a-fA-F]{6}$")
_HEX8 = re.compile(r"^#[0-9a-fA-F]{8}$")

DEFAULT_CONFIG = {
    "theme": temas.TEMA_POR_DEFECTO,
    "theme_mode": None,
    "voice": "es-MX-JorgeNeural",
    "rate": 0, "pitch": 0, "volume": 0,
    "robot_metal": 70,
    "auto_clear": True,
    "queue_enabled": True,
    "max_tabs": 5,
    "auto_save": False,
    "library_path": pu.default_library_dir(),
    "atajo_global": atajo.ATAJO_POR_DEFECTO,
}


def _mezclar(color, fondo):
    """Mezcla un #rrggbbaa sobre un #rrggbb y devuelve #rrggbb."""
    a = int(color[7:9], 16) / 255
    out = "#"
    for i in (1, 3, 5):
        f, b = int(color[i:i + 2], 16), int(fondo[i:i + 2], 16)
        out += f"{round(f * a + b * (1 - a)):02x}"
    return out


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as exc:
        print(f"MultiVoice: se ignora config.json ilegible ({exc})",
              file=sys.stderr)
    perfiles.asegurar(cfg)
    frases.asegurar(cfg)
    pronunciacion.asegurar(cfg)
    soundboard.asegurar(cfg)
    return cfg


def save_config(cfg):
    tmp = CONFIG_PATH + ".tmp"
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        os.replace(tmp, CONFIG_PATH)
    except OSError as exc:
        print(f"MultiVoice: no se pudo guardar config.json ({exc})",
              file=sys.stderr)


class SpeechWorker:
    """Cola de síntesis y reproducción, con posibilidad de detener."""

    def __init__(self, status_cb, on_clear=None, on_save=None, on_change=None,
                 pronunciar=None, salidas=None):
        # status_cb, on_clear, on_save, on_change must be scheduled via root.after
        self.cola = ColaVoz()
        self.on_change = on_change
        self.pronunciar = pronunciar or (lambda t: t)
        # () -> (escuchar, hay_virtual) en el momento de reproducir
        self.salidas = salidas or (lambda: (True, True))
        # cada trabajo encolado deja una ficha aquí; el trabajo real vive en
        # self.cola (así se puede quitar un elemento que aún espera)
        self.q = queue.Queue()
        self.lock = threading.Lock()
        self.procs = []
        self.running = True
        self.stop_requested = False
        self.busy = False
        self.status_cb = status_cb
        self.on_clear = on_clear
        self.on_save = on_save
        self.cancel_event = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while self.running:
            job = self.q.get()
            if job is None:
                break
            if self.stop_requested:
                self.stop_requested = False
                self.cola.vaciar()
                self._changed()
                continue
            item = self.cola.avanzar()
            if item is None:           # lo quitaron de la cola antes de tocarle
                continue
            job = item.job
            completado = False
            self._changed()
            self.busy = True
            self.status_cb("🔊 Hablando...")
            self.cancel_event.clear()
            tmp_dir = tempfile.mkdtemp(prefix="multivoice_")
            tmp = os.path.join(tmp_dir, "speech.wav")
            try:
                if job["engine"] == soundboard.MOTOR:
                    wav = job["opts"]["file"]    # ya convertido: no se borra
                else:
                    args = SimpleNamespace(**job["opts"])
                    wav = tts_engine.synthesize(
                        self.pronunciar(job["text"]), job["engine"], args, tmp)
                if self.stop_requested:
                    continue
                duracion, niveles = medidor.envolvente(wav)
                escuchar, hay_virtual = self.salidas()
                procs = tts_engine.play_wav(wav, escuchar, hay_virtual)
                self.cola.iniciar_audio(duracion, niveles)
                with self.lock:
                    self.procs = procs
                self._wait_procs(procs)
                with self.lock:
                    self.procs = []
                if not self.stop_requested:
                    completado = True
                    if job.get("clear_after") and self.on_clear:
                        self.on_clear(job.get("widget"))
                    if job.get("widget") is not None and self.on_save:
                        self.on_save(job)
                    self.status_cb("✅ Listo")
            except Exception as e:
                if not self.stop_requested:
                    self.status_cb(f"⚠️ Error: {e}")
            finally:
                shutil.rmtree(tmp_dir, ignore_errors=True)
                self.cola.terminar(completado)
                self.busy = False
                self._changed()

    def _changed(self):
        if self.on_change:
            self.on_change()

    def _wait_procs(self, procs):
        while any(p.poll() is None for p in procs):
            if self.cancel_event.wait(0.1):
                for p in procs:
                    try:
                        p.terminate()
                    except Exception:
                        pass
                return

    def enqueue(self, job):
        with self.lock:
            active = self.busy or bool(self.procs) or self.cola.hay_actividad()
        if active and not job.get("queue"):
            self.stop()
        self.stop_requested = False
        self.cola.encolar(job)
        self.q.put(True)
        self._changed()

    def stop(self):
        self.status_cb("⏹ Detenido")
        with self.lock:
            for p in self.procs:
                try:
                    p.terminate()
                except Exception:
                    pass
            self.procs = []
        self.cancel_event.set()
        self.stop_requested = True
        while True:
            try:
                self.q.get_nowait()
            except queue.Empty:
                break
        self.cola.vaciar()
        self._changed()


class TTSApp(AjustesMixin, BibliotecaMixin, ColaMixin, PerfilesMixin,
             FrasesMixin, PronunciacionMixin, SoundboardMixin,
             DecirRapidoMixin):
    def __init__(self, root):
        self.root = root
        self.cfg = load_config()
        self._save_job = None
        self.theme, self.mode = temas.traducir_nombre(
            self.cfg.get("theme"), self.cfg.get("theme_mode"))
        if self.mode is None and temas.modos(self.theme):
            self.mode = temas.modos(self.theme)[0]
        self.p = temas.paleta(self.theme, self.mode)

        self.current_engine = self.cfg.get("engine", "edge")
        if self.current_engine not in ENGINES:
            self.current_engine = "edge"
        self._reload_voices()

        self.tab_texts = {}
        self.tab_counter = 0
        self._paints = []

        self.mic_ids = setup_virtual_mic()

        self.worker = SpeechWorker(
            lambda msg: self.root.after(0, self.set_status, msg),
            on_clear=lambda w: self.root.after(0, self._safe_clear, w),
            on_save=lambda job: self.root.after(0, self.maybe_auto_save, job),
            on_change=lambda: self.root.after(0, self._refresh_cola),
            pronunciar=lambda t: pronunciacion.aplicar_cfg(t, self.cfg),
            salidas=lambda: (bool(self.cfg.get("listen_self", False)),
                             self._hay_virtual()))

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._build_ui()
        self.add_tab()
        self._build_frases_tab()
        self._build_pronunciacion_tab()
        self._build_soundboard_tab()
        self._build_library_tab()
        self.apply_theme()
        self._cleanup_library()

        self.bind_shortcuts()
        labels = [v["label"] for v in self.voices]
        saved_voice = self.cfg.get("voice", "")
        self.voice_combo.set(saved_voice if saved_voice in labels
                             else self.voices[0]["label"])
        self.engine_menu.set(ENGINES[self.current_engine])
        self._set_slider("rate", self.cfg.get("rate", 0))
        self._set_slider("pitch", self.cfg.get("pitch", 0))
        self._set_slider("volume", self.cfg.get("volume", 0))
        self.metal_slider.set(self.cfg.get("robot_metal", 70))
        self._on_metal(self.cfg.get("robot_metal", 70))
        self._on_voice_changed()
        self.set_status("✅ Listo: elige motor y voz")
        self._announce_virtual_device()

    def _save_soon(self):
        """Debounced config write: sliders fire dozens of events per drag."""
        if self._save_job is not None:
            self.root.after_cancel(self._save_job)
        self._save_job = self.root.after(400, self._flush_config)

    def _flush_config(self):
        if self._save_job is not None:
            self.root.after_cancel(self._save_job)
            self._save_job = None
        save_config(self.cfg)

    def _hay_virtual(self):
        """¿Hay micrófono virtual donde sonar? Linux: el que creó la app."""
        if sys.platform.startswith("linux"):
            return bool(self.mic_ids)
        return tts_engine.find_virtual_output() is not None

    def _announce_virtual_device(self):
        """Warn about the virtual mic status on Windows at startup."""
        if sys.platform.startswith("linux"):
            return
        found = tts_engine.find_virtual_output()
        if found:
            self.set_status(f"🎤 Cable virtual: {found[1]}")
        else:
            self.set_status("Sin cable virtual: instala VB-CABLE")

    def _reload_voices(self):
        """Reload the voice list for the current engine."""
        self.voices = tts_engine.list_voices(self.current_engine)
        if self.current_engine == "robot":
            # For the robot, make sure it is in the list
            labels = [v["label"] for v in self.voices]
            if ROBOT_VOICE not in labels:
                self.voices.insert(0, {"label": ROBOT_VOICE, "id": ROBOT_VOICE, "gender": "Robot", "engine": "robot"})
        else:
            # Add the robot as a final option for other engines
            self.voices.append({"label": ROBOT_VOICE, "id": ROBOT_VOICE, "gender": "Robot", "engine": "robot"})

    # ---------- Paleta ----------
    def _col(self, key, fallback="#808080"):
        """Color #rrggbb de un token; los #rrggbbaa se mezclan sobre --surface."""
        v = self.p.get(key, "")
        if _HEX6.match(v):
            return v
        if _HEX8.match(v):
            base = self.p.get("--surface", "")
            return _mezclar(v, base if _HEX6.match(base) else fallback)
        return fallback

    def _px(self, key, default):
        m = re.match(r"\s*(\d+)", self.p.get(key, ""))
        return int(m.group(1)) if m else default

    def font(self, size=None, bold=False):
        return ctk.CTkFont(family=pu.UI_FONT,
                           size=size or self._px("--fs-md", 13),
                           weight="bold" if bold else "normal")

    def _reg(self, widget, fn):
        """Registra cómo se pinta un widget con la paleta (ver apply_theme)."""
        self._paints.append((widget, fn))
        return widget

    # ---------- UI ----------
    def _build_ui(self):
        self.root.title("MultiVoice")
        self.root.geometry("1120x720")
        self.root.minsize(960, 620)
        r = self._px("--radius", 8)
        rl = self._px("--radius-lg", 12)
        h = self._px("--control-h", 36)
        fs = self._px("--fs-md", 13)

        # ---- Cabecera ----
        self.top = ctk.CTkFrame(self.root, corner_radius=0,
                                height=max(self._px("--header-h", 48), 48))
        self.top.pack(fill="x")
        self.top.pack_propagate(False)
        self.title_label = ctk.CTkLabel(self.top, text="🎙 MultiVoice",
                                        font=self.font(fs + 5, True))
        self.title_label.pack(side="left", padx=16)
        self.btn_settings = self._btn(self.top, "⚙ Ajustes", self.open_settings)
        self.btn_settings.pack(side="right", padx=(6, 16), pady=6)
        self.theme_entries = self._theme_entries()
        self.theme_menu = ctk.CTkOptionMenu(
            self.top, values=[e[0] for e in self.theme_entries], height=h,
            corner_radius=r, font=self.font(), dropdown_font=self.font(),
            command=self._on_theme_selected)
        self.theme_menu.pack(side="right", pady=6)
        self.lbl_theme = ctk.CTkLabel(self.top, text="Tema", font=self.font())
        self.lbl_theme.pack(side="right", padx=(0, 8))
        self._reg(self.top, lambda w: w.configure(fg_color=self._col("--surface")))
        self._reg(self.title_label, lambda w: w.configure(
            text_color=self._col("--text")))
        self._reg(self.lbl_theme, lambda w: w.configure(
            text_color=self._col("--text-2")))
        self._reg(self.theme_menu, self._paint_menu)

        # ---- Barra de estado ----
        self.status = ctk.CTkLabel(self.root, text="", anchor="w",
                                   corner_radius=0, height=26,
                                   font=self.font(fs - 1))
        self.status.pack(fill="x", side="bottom")
        self._reg(self.status, lambda w: w.configure(
            fg_color=self._col("--surface-2"), text_color=self._col("--text-2")))

        # ---- Panel lateral: suena / cola / historial ----
        self._build_cola_panel()

        # ---- Barra de motor y voz ----
        self.voice_card = ctk.CTkFrame(self.root, corner_radius=rl)
        self.voice_card.pack(fill="x", padx=12, pady=(10, 0))
        self._reg(self.voice_card, self._paint_card)
        inner = ctk.CTkFrame(self.voice_card, fg_color="transparent")
        inner.pack(fill="x", padx=14, pady=10)
        self.lbl_engine = ctk.CTkLabel(inner, text="Motor",
                                       font=self.font(fs, True))
        self.lbl_engine.pack(side="left", padx=(0, 8))
        self.engine_menu = ctk.CTkOptionMenu(
            inner, values=list(ENGINES.values()), width=150, height=h,
            corner_radius=r, font=self.font(), dropdown_font=self.font(),
            command=self._on_engine_selected)
        self.engine_menu.pack(side="left", padx=(0, 12))
        self.lbl_voice = ctk.CTkLabel(inner, text="Voz", font=self.font(fs, True))
        self.lbl_voice.pack(side="left", padx=(0, 8))
        self.btn_probe = self._btn(inner, "👂 Probar", self.probe_voice)
        self.btn_probe.pack(side="right", padx=(10, 0))
        self.voice_combo = ctk.CTkComboBox(
            inner, state="readonly", height=h, corner_radius=r,
            font=self.font(), dropdown_font=self.font(),
            values=[v["label"] for v in self.voices],
            command=self._on_voice_changed)
        self.voice_combo.pack(side="left", fill="x", expand=True)
        self._build_perfiles(inner)
        for lbl in (self.lbl_engine, self.lbl_voice):
            self._reg(lbl, lambda w: w.configure(text_color=self._col("--text")))
        self._reg(self.engine_menu, self._paint_menu)
        self._reg(self.voice_combo, self._paint_menu)

        # ---- Ajuste de voz (solo los controles del motor elegido) ----
        self.cfg_frame = ctk.CTkFrame(self.root, corner_radius=rl)
        self.cfg_frame.pack(fill="x", padx=12, pady=(8, 0))
        self._reg(self.cfg_frame, self._paint_card)
        self.cfg_inner = ctk.CTkFrame(self.cfg_frame, fg_color="transparent")
        self.cfg_inner.pack(fill="x", padx=14, pady=10)

        self.sliders = {}
        self.slider_labels = {}
        self.slider_rows = {}
        # (clave, título, mínimo, máximo)
        for key, name, lo, hi in (("rate", "Velocidad", -50, 100),
                                  ("pitch", "Tono", -50, 50),
                                  ("volume", "Volumen", -50, 50),
                                  ("metal", "Metal", 0, 100)):
            self._slider_row(key, name, lo, hi)
        self.metal_slider = self.sliders.pop("metal")
        self.metal_value = self.slider_labels.pop("metal")
        self.robot_row = self.slider_rows.pop("metal")

        self.hint = ctk.CTkLabel(self.cfg_inner, text="", anchor="w",
                                 font=self.font(fs - 1))
        self.hint.pack(fill="x", pady=(4, 0))

        # ---- Editor con pestañas ----
        self.tabview = ctk.CTkTabview(self.root, corner_radius=rl,
                                      command=self.on_tab_changed)
        self.tabview.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        self._reg(self.tabview, self._paint_tabview)

        # ---- Barra inferior ----
        self.bottom = ctk.CTkFrame(self.root, fg_color="transparent")
        self.bottom.pack(fill="x", padx=12, pady=(8, 4))
        opts = ctk.CTkFrame(self.bottom, fg_color="transparent")
        opts.pack(fill="x")
        self.btn_add = self._btn(opts, "＋ Nueva", self.add_tab)
        self.btn_add.pack(side="left", padx=(0, 6))
        self.btn_del = self._btn(opts, "✕ Cerrar", self.delete_current_tab)
        self.btn_del.pack(side="left")
        self.auto_clear_var = tk.BooleanVar(value=self.cfg.get("auto_clear", True))
        self.queue_var = tk.BooleanVar(value=self.cfg.get("queue_enabled", True))
        self.auto_save_var = tk.BooleanVar(value=self.cfg.get("auto_save", False))
        self.listen_var = tk.BooleanVar(value=self.cfg.get("listen_self", False))
        for text, var in (("Borrar al hablar", self.auto_clear_var),
                          ("Encolar audios", self.queue_var),
                          ("Guardado automático", self.auto_save_var),
                          ("Escucharme", self.listen_var)):
            cb = ctk.CTkCheckBox(opts, text=text, variable=var, font=self.font(),
                                 command=self._persist_flags)
            cb.pack(side="left", padx=(14, 0))
            self._reg(cb, self._paint_check)

        actions = ctk.CTkFrame(self.bottom, fg_color="transparent")
        actions.pack(fill="x", pady=(8, 0))
        self.btn_speak = self._btn(actions, "🔊 Hablar", self.speak_current,
                                   accent=True, height=h + 16, big=True)
        self.btn_speak.pack(side="left", fill="x", expand=True)
        self.btn_stop = self._btn(actions, "⏹ Detener",
                                  lambda: self.worker.stop(), height=h + 16)
        self.btn_stop.pack(side="left", padx=(8, 0))
        self.btn_save = self._btn(actions, "💾 Guardar", self.save_audio,
                                  height=h + 16)
        self.btn_save.pack(side="left", padx=(8, 0))
        self._reg(self.hint, lambda w: self._paint_hint())

    def _slider_row(self, key, name, lo, hi):
        fs = self._px("--fs-md", 13)
        row = ctk.CTkFrame(self.cfg_inner, fg_color="transparent")
        lab = ctk.CTkLabel(row, text=name, width=90, anchor="w",
                           font=self.font(fs))
        lab.pack(side="left")
        val = ctk.CTkLabel(row, text="+0", width=60, anchor="e",
                           font=self.font(fs))
        val.pack(side="right")
        s = ctk.CTkSlider(row, from_=lo, to=hi,
                          command=lambda v, k=key: self._on_slider(k, v))
        s.set(0)
        s.pack(side="left", fill="x", expand=True, padx=8)
        s.bind("<ButtonRelease-1>", lambda e: self._persist_sliders())
        self.sliders[key] = s
        self.slider_labels[key] = val
        self.slider_rows[key] = row
        self._reg(lab, lambda w: w.configure(text_color=self._col("--text")))
        self._reg(val, lambda w: w.configure(text_color=self._col("--text-2")))
        self._reg(s, self._paint_slider)

    def _btn(self, parent, text, command, accent=False, height=None, big=False):
        btn = ctk.CTkButton(
            parent, text=text, command=command, cursor="hand2",
            height=height or self._px("--control-h", 36),
            corner_radius=self._px("--radius", 8),
            font=self.font(self._px("--fs-md", 13) + (3 if big else 0), accent))
        self._reg(btn, lambda w, a=accent: self._paint_button(w, a))
        return btn

    # ---------- Pintado ----------
    def _paint_button(self, w, accent):
        if accent:
            w.configure(fg_color=self._col("--accent"),
                        hover_color=self._col("--accent-hover"),
                        text_color=self._col("--accent-text"),
                        border_width=0)
        else:
            w.configure(fg_color=self._col("--surface-2"),
                        hover_color=self._col("--surface-hover"),
                        text_color=self._col("--text"),
                        border_color=self._col("--border-strong"),
                        border_width=min(self._px("--border-w", 1), 3))
        w.configure(corner_radius=self._px("--radius", 8))

    def _paint_card(self, w):
        w.configure(fg_color=self._col("--surface"),
                    corner_radius=self._px("--radius-lg", 12))

    def _paint_menu(self, w):
        kw = dict(fg_color=self._col("--surface-2"),
                  text_color=self._col("--text"),
                  button_color=self._col("--surface-hover"),
                  button_hover_color=self._col("--accent"),
                  dropdown_fg_color=self._col("--surface"),
                  dropdown_hover_color=self._col("--surface-hover"),
                  dropdown_text_color=self._col("--text"),
                  corner_radius=self._px("--radius", 8))
        if isinstance(w, ctk.CTkComboBox):
            kw["border_color"] = self._col("--border-strong")
        w.configure(**kw)

    def _paint_slider(self, w):
        w.configure(fg_color=self._col("--border-strong"),
                    progress_color=self._col("--accent"),
                    button_color=self._col("--accent"),
                    button_hover_color=self._col("--accent-hover"))

    def _paint_check(self, w):
        w.configure(fg_color=self._col("--accent"),
                    hover_color=self._col("--accent-hover"),
                    border_color=self._col("--border-strong"),
                    checkmark_color=self._col("--accent-text"),
                    text_color=self._col("--text"))

    def _paint_tabview(self, w):
        w.configure(fg_color=self._col("--surface"),
                    corner_radius=self._px("--radius-lg", 12),
                    segmented_button_fg_color=self._col("--surface-2"),
                    segmented_button_selected_color=self._col("--accent"),
                    segmented_button_selected_hover_color=self._col("--accent-hover"),
                    segmented_button_unselected_color=self._col("--surface-2"),
                    segmented_button_unselected_hover_color=self._col("--surface-hover"),
                    text_color=self._col("--text"))
        # la pestaña activa lleva el texto del acento, el resto el texto normal
        try:
            actual = w.get()
            for name, btn in w._segmented_button._buttons_dict.items():
                btn.configure(text_color=self._col(
                    "--accent-text" if name == actual else "--text"))
        except (AttributeError, tk.TclError):
            pass

    def _paint_text(self, w):
        w.configure(fg_color=self._col("--surface-2"),
                    text_color=self._col("--text"),
                    border_color=self._col("--border-strong"),
                    scrollbar_button_color=self._col("--border-strong"),
                    corner_radius=self._px("--radius", 8))
        try:
            w._textbox.configure(insertbackground=self._col("--text"),
                                 selectbackground=self._col("--accent"),
                                 selectforeground=self._col("--accent-text"))
        except (AttributeError, tk.TclError):
            pass

    def _paint_hint(self):
        robot = self._effective_engine() == "robot"
        self.hint.configure(text_color=self._col(
            "--accent" if robot else "--text-2"))

    # ---------- Tema ----------
    def _theme_entries(self):
        """(etiqueta, tema, modo) de cada tema elegible."""
        out = []
        for t, nombre in temas.lista_temas():
            ms = temas.modos(t)
            if ms:
                out += [(f"{nombre} · {m}", t, m) for m in ms]
            else:
                out.append((nombre, t, None))
        return out

    def _theme_label(self):
        for label, t, m in self.theme_entries:
            if (t, m) == (self.theme, self.mode):
                return label
        return self.theme_entries[0][0]

    def _on_theme_selected(self, label):
        for lab, t, m in self.theme_entries:
            if lab == label:
                self.set_theme(t, m)
                return

    def set_theme(self, tema, modo=None):
        self.theme, self.mode = temas.traducir_nombre(tema, modo)
        if self.mode is None and temas.modos(self.theme):
            self.mode = temas.modos(self.theme)[0]
        self.cfg["theme"] = self.theme
        self.cfg["theme_mode"] = self.mode
        self._save_soon()
        self.apply_theme()

    def apply_theme(self):
        self.p = temas.paleta(self.theme, self.mode)
        ctk.set_appearance_mode("light" if self.p.get("color-scheme") == "light"
                                else "dark")
        self.root.configure(fg_color=self._col("--bg"))
        self.theme_menu.set(self._theme_label())
        for widget, fn in self._paints:
            try:
                if widget.winfo_exists():
                    fn(widget)
            except tk.TclError:
                pass
        for text in self.tab_texts.values():
            self._paint_text(text)
        self._style_library()
        self._refresh_frases()
        self._refresh_cola(forzar=True)

    # ---------- Sliders ----------
    def _on_slider(self, key, value):
        v = int(round(float(value)))
        self.slider_labels[key].configure(
            text=f"{v:+d}dB" if key == "volume" else f"{v:+d}")
        self.cfg[key] = v
        self._save_soon()

    def _set_slider(self, key, value):
        self.sliders[key].set(value)
        self._on_slider(key, value)

    def _on_metal(self, value):
        v = int(round(float(value)))
        self.metal_value.configure(text=f"{v}%")
        self.cfg["robot_metal"] = v
        self._save_soon()

    def _persist_sliders(self):
        for key in ("rate", "pitch", "volume"):
            self.cfg[key] = int(round(float(self.sliders[key].get())))
        self.cfg["robot_metal"] = int(round(float(self.metal_slider.get())))
        self._save_soon()

    def _persist_flags(self):
        self.cfg["auto_clear"] = self.auto_clear_var.get()
        self.cfg["queue_enabled"] = self.queue_var.get()
        self.cfg["auto_save"] = self.auto_save_var.get()
        self.cfg["listen_self"] = self.listen_var.get()
        self._save_soon()

    def _on_engine_selected(self, label):
        for eid, name in ENGINES.items():
            if name == label:
                self._on_engine_changed(eid)
                return

    def _on_engine_changed(self, new_engine=None):
        """Change the TTS engine and reload the voices."""
        if new_engine is None or new_engine == self.current_engine:
            return
        self.current_engine = new_engine
        self.cfg["engine"] = new_engine
        self._save_soon()
        self._reload_voices()
        self.voice_combo.configure(values=[v["label"] for v in self.voices])
        self.engine_menu.set(ENGINES[new_engine])
        menu = getattr(self, "settings_engine_menu", None)
        if menu is not None and menu.winfo_exists():
            menu.set(ENGINES[new_engine])
        # Select the first available voice
        if self.voices:
            self.voice_combo.set(self.voices[0]["label"])
        self._on_voice_changed()

    # ---------- Voz ----------
    def _effective_engine(self):
        label = self.voice_combo.get()
        if label == ROBOT_VOICE:
            return "robot"
        info = next((v for v in self.voices if v["label"] == label), {})
        return info.get("engine", self.current_engine)

    def _refresh_voice_panel(self):
        """Muestra solo los controles del motor de la voz elegida."""
        engine = self._effective_engine()
        for row in list(self.slider_rows.values()) + [self.robot_row]:
            row.pack_forget()
        self.hint.pack_forget()
        if engine in ("edge", "robot"):
            for key in ("rate", "pitch", "volume"):
                self.slider_rows[key].pack(fill="x", pady=3)
        if engine == "robot":
            self.robot_row.pack(fill="x", pady=3)
        self.hint.pack(fill="x", pady=(4, 0))
        return engine

    def _on_voice_changed(self, event=None):
        engine = self._refresh_voice_panel()
        if engine == "robot":
            if self.sliders["rate"].get() == 0:
                self._set_slider("rate", -15)
            if self.sliders["pitch"].get() == 0:
                self._set_slider("pitch", -25)
            self.hint.configure(text="🤖 Sonido robot: voz grave y robótica. "
                                     "Sube «Metal» para más distorsión.")
        elif engine == "edge":
            self.hint.configure(text="✨ Voces neuronales (necesitan internet). "
                                     "Microsoft Edge: 14 voces en español.")
        elif engine == "gtts":
            self.hint.configure(text="🌐 Google TTS (necesita internet). "
                                     "Varios idiomas; sin ajustes de voz.")
        else:
            self.hint.configure(text="✨ Voces disponibles.")
        self._paint_hint()
        self.cfg["voice"] = self.voice_combo.get()
        self._save_soon()

    def current_voice(self):
        label = self.voice_combo.get()
        for v in self.voices:
            if v["label"] == label:
                return v
        for v in self.voices:
            if v["engine"] != "robot":
                return v
        return self.voices[0]

    def build_job(self, text, widget=None, clear_after=None):
        job = self._build_job(text, widget, clear_after)
        job["voice_label"] = self.current_voice()["label"]
        return job

    def _build_job(self, text, widget=None, clear_after=None):
        voice = self.current_voice()
        rate = int(round(float(self.sliders["rate"].get())))
        pitch = int(round(float(self.sliders["pitch"].get())))
        volume = int(round(float(self.sliders["volume"].get())))
        engine = voice.get("engine", self.current_engine)
        if engine == "robot" or voice["id"] == ROBOT_VOICE:
            speed = max(40, min(450, int(self.cfg.get("robot_speed", 0))
                                or round(80 + (rate + 50) * 1.1)))
            rpitch = max(1, min(99, int(self.cfg.get("robot_pitch", 0))
                                or round(30 + pitch * 0.6)))
            rvol = int(self.cfg.get("robot_volume", 0))
            volume = rvol if rvol else volume
            metal = float(self.metal_slider.get()) / 100.0
            opts = {
                "robot_speed": speed, "robot_pitch": rpitch,
                "volume": volume, "robot_metal": metal,
            }
            return {"text": text, "engine": "robot", "opts": opts,
                    "widget": widget, "clear_after": clear_after}
        elif engine == "gtts":
            opts = {"lang": voice["id"], "slow": False}
            return {"text": text, "engine": "gtts", "opts": opts,
                    "widget": widget, "clear_after": clear_after}
        # edge by default
        opts = {"voice": voice["id"], "rate": rate, "pitch": pitch,
                "volume": volume}
        return {"text": text, "engine": "edge", "opts": opts,
                "widget": widget, "clear_after": clear_after}

    # ---------- Acciones ----------
    def probe_voice(self):
        phrase = PROBE_TEXTS[(self.tab_counter - 1) % len(PROBE_TEXTS)]
        job = self.build_job(phrase)
        job["queue"] = self.queue_var.get()
        self.worker.enqueue(job)

    def speak_current(self):
        text_widget = self.get_current_text()
        if not text_widget:
            return
        self.speak(text_widget)

    def speak(self, text_widget):
        text = text_widget.get("1.0", tk.END).strip()
        if not text:
            self.set_status("⚠️ Escribe algo antes de hablar")
            return
        clear = self.auto_clear_var.get()
        job = self.build_job(text, widget=text_widget, clear_after=clear)
        job["queue"] = self.queue_var.get()
        self.worker.enqueue(job)
        # the worker clears the widget via on_clear when it finishes

    def _safe_clear(self, widget):
        try:
            if widget and widget.winfo_exists():
                widget.delete("1.0", tk.END)
        except tk.TclError:
            pass

    def save_audio(self, auto=False, job=None):
        """Save the audio. `job` (auto-save) fixes text/voice at speak time."""
        if job is None:
            text_widget = self.get_current_text()
            if not text_widget:
                return
            text = text_widget.get("1.0", tk.END).strip()
            if not text:
                if not auto:
                    self.set_status("⚠️ No hay nada que guardar")
                return
            job = self.build_job(text)
        text = job["text"]
        ext = "wav" if job["engine"] == "robot" else "mp3"

        if auto:
            # Auto-save to library folder with timestamp
            lib_dir = self.cfg.get("library_path", DEFAULT_CONFIG["library_path"])
            os.makedirs(lib_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            path = os.path.join(lib_dir, f"voz_{ts}.{ext}")
        else:
            path = filedialog.asksaveasfilename(
                defaultextension=f".{ext}",
                filetypes=[(f"Audio ({ext})", f"*.{ext}")],
                initialfile=f"multivoice_{self.tab_counter}.{ext}")
            if not path:
                return

        def run():
            try:
                args = SimpleNamespace(**job["opts"])
                tts_engine.synthesize(pronunciacion.aplicar_cfg(text, self.cfg),
                                      job["engine"], args, path)
                # Save metadata sidecar
                meta = {
                    "text": text,
                    "engine": job["engine"],
                    "voice": job.get("voice_label", ""),
                    "opts": job["opts"],
                    "created": datetime.now().isoformat(),
                }
                with open(path + ".json", "w", encoding="utf-8") as f:
                    json.dump(meta, f, ensure_ascii=False, indent=2)
                self.root.after(0, lambda: self.set_status(
                    f"✅ Guardado: {os.path.basename(path)}"))
            except Exception as exc:
                msg = str(exc)
                self.root.after(0, lambda: self.set_status(f"⚠️ Error: {msg}"))

        threading.Thread(target=run, daemon=True).start()
        if not auto:
            self.set_status("💾 Guardando...")

    # Auto-save trigger (called after speak finishes)
    def maybe_auto_save(self, job):
        if self.cfg.get("auto_save", False):
            self.save_audio(auto=True, job=job)

    # ---------- Pestañas ----------
    def add_tab(self):
        if len(self.tab_texts) >= self.cfg.get("max_tabs", 5):
            self.set_status("⚠️ Máximo de pestañas alcanzado")
            return
        self.tab_counter += 1
        name = f"Voz {self.tab_counter}"
        tab = self.tabview.add(name)
        text = ctk.CTkTextbox(tab, wrap="word", border_width=1,
                              font=ctk.CTkFont(family=pu.TEXT_FONT, size=14),
                              undo=True)
        text.pack(fill="both", expand=True, padx=4, pady=4)
        text.bind("<Return>", lambda e: (self.speak(text), "break")[1])
        text.bind(f"<{pu.MOD}-Return>", lambda e: (self.speak(text), "break")[1])
        self.tab_texts[name] = text
        self._paint_text(text)
        self.tabview.set(name)
        self._paint_tabview(self.tabview)
        text.focus_set()

    def delete_current_tab(self):
        if len(self.tab_texts) <= 1:
            return
        name = self.tabview.get()
        if name not in self.tab_texts:
            return
        self.tab_texts.pop(name)
        self.tabview.delete(name)
        self.tabview.set(next(iter(self.tab_texts)))
        self.on_tab_changed()

    def on_tab_changed(self, event=None):
        name = self.tabview.get()
        self._paint_tabview(self.tabview)
        if name == LIB_TAB:
            self._refresh_library()
        elif name in self.tab_texts:
            self.tab_texts[name].focus_set()

    def get_current_text(self):
        return self.tab_texts.get(self.tabview.get())

    # ---------- Estado / atajos ----------
    def set_status(self, msg):
        self.status.configure(text="  " + msg)

    def bind_shortcuts(self):
        self.root.bind(f"<{pu.MOD}-Return>", lambda e: self.speak_current())
        self.root.bind(f"<{pu.MOD}-t>", lambda e: (self.add_tab(), "break")[1])
        self.root.bind(f"<{pu.MOD}-w>",
                       lambda e: (self.delete_current_tab(), "break")[1])
        self.root.bind("<F5>", lambda e: self.probe_voice())
        for n in range(1, frases.MAX_ATAJOS + 1):
            self.root.bind(f"<{pu.MOD}-Key-{n}>",
                           lambda e, n=n: (self.decir_numero(n), "break")[1])
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self._stop_cola_timer()
        self._flush_config()
        self.worker.stop()
        self.worker.running = False
        self.worker.q.put(None)
        teardown_virtual_mic(self.mic_ids)
        if self.servidor is not None:
            self.servidor.cerrar()
        if self.atajo_win is not None:
            self.atajo_win.detener()
        self.root.destroy()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    # Instancia única: si ya hay una abierta se le avisa y se sale
    servidor, avisada = instancia.arrancar(argv, lambda cmd: None)
    if servidor is None:
        if not avisada:
            print("MultiVoice: ya hay una instancia abierta, pero no responde.",
                  file=sys.stderr)
        return
    root = ctk.CTk()
    app = TTSApp(root)
    app.iniciar_instancia(servidor)
    if instancia.comando_de_args(argv) == instancia.CMD_DECIR:
        root.after(300, app.abrir_decir)
    root.mainloop()


if __name__ == "__main__":
    main()
