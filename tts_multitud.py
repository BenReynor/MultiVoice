#!/usr/bin/env python3
# TTS Multitud - UI con pestañas, voces neuronales y robot SCP-079
# Uso: python3 tts_multitud.py

import json
import os
import queue
import threading
import tkinter as tk
from tkinter import ttk, filedialog
from types import SimpleNamespace

import tts_engine

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
ROBOT_VOICE = tts_engine.ROBOT_VOICE
PROBE_TEXTS = [
    "Hola, esta es tu nueva voz de prueba. ¿Cómo me escuchas?",
    "El otro día vi una luz extraña en el pasillo de la fundación.",
    "Todas las amenazas han sido neutralizadas. Todo está bajo control.",
]

THEMES = {
    "dark": {
        "bg": "#0d1117", "panel": "#161b22", "panel2": "#21262d",
        "fg": "#e6edf3", "fg_dim": "#8b949e", "accent": "#3fb950",
        "accent_hover": "#56d364", "btn": "#21262d", "active": "#30363d",
        "input": "#0d1117", "tab": "#161b22", "select": "#21262d",
        "status": "#0d1117", "border": "#30363d", "danger": "#f85149",
        "title": "#f0f6fc", "slider_bg": "#21262d", "slider_fg": "#e6edf3",
    },
    "light": {
        "bg": "#ffffff", "panel": "#f6f8fa", "panel2": "#e1e4e8",
        "fg": "#24292f", "fg_dim": "#656d76", "accent": "#2da44e",
        "accent_hover": "#2ea043", "btn": "#f3f4f6", "active": "#d0d7de",
        "input": "#ffffff", "tab": "#f6f8fa", "select": "#e1e4e8",
        "status": "#f6f8fa", "border": "#d0d7de", "danger": "#cf222e",
        "title": "#24292f", "slider_bg": "#e1e4e8", "slider_fg": "#24292f",
    },
    "hacker": {
        "bg": "#000000", "panel": "#0d1117", "panel2": "#161b22",
        "fg": "#00ff00", "fg_dim": "#00aa00", "accent": "#00ff00",
        "accent_hover": "#00cc00", "btn": "#001100", "active": "#002200",
        "input": "#000000", "tab": "#0d1117", "select": "#161b22",
        "status": "#000000", "border": "#004400", "danger": "#ff3333",
        "title": "#00ff00", "slider_bg": "#001100", "slider_fg": "#00ff00",
    },
    "dracula": {
        "bg": "#282a36", "panel": "#1e1f29", "panel2": "#44475a",
        "fg": "#f8f8f2", "fg_dim": "#6272a4", "accent": "#bd93f9",
        "accent_hover": "#caa9fa", "btn": "#44475a", "active": "#6272a4",
        "input": "#282a36", "tab": "#1e1f29", "select": "#44475a",
        "status": "#191a21", "border": "#6272a4", "danger": "#ff5555",
        "title": "#f8f8f2", "slider_bg": "#44475a", "slider_fg": "#f8f8f2",
    },
    "gruvbox": {
        "bg": "#282828", "panel": "#1d2021", "panel2": "#3c3836",
        "fg": "#ebdbb2", "fg_dim": "#928374", "accent": "#b8bb26",
        "accent_hover": "#d8d02a", "btn": "#3c3836", "active": "#504945",
        "input": "#282828", "tab": "#1d2021", "select": "#3c3836",
        "status": "#1d2021", "border": "#504945", "danger": "#fb4934",
        "title": "#fbf1c7", "slider_bg": "#3c3836", "slider_fg": "#ebdbb2",
    },
}

DEFAULT_CONFIG = {
    "theme": "dark",
    "voice": "es-MX-JorgeNeural",
    "rate": 0, "pitch": 0, "volume": 0,
    "robot_metal": 70,
    "auto_clear": True,
    "queue_enabled": True,
    "max_tabs": 5,
}

THEME_ORDER = ["dark", "light", "hacker", "dracula", "gruvbox"]


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class SpeechWorker:
    """Cola de síntesis + reproducción con capacidad de detener."""

    def __init__(self, status_cb, on_clear=None):
        # status_cb y on_clear deben programarse via root.after
        self.q = queue.Queue()
        self.lock = threading.Lock()
        self.procs = []
        self.running = True
        self.stop_requested = False
        self.busy = False
        self.status_cb = status_cb
        self.on_clear = on_clear
        self.cancel_current = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while self.running:
            job = self.q.get()
            if job is None:
                break
            if self.stop_requested:
                self.stop_requested = False
                continue
            self.busy = True
            self.status_cb("🔊 Hablando...")
            tmp = os.path.join(os.environ.get("TMPDIR", "/tmp"),
                               f"tts_multitud_{threading.get_ident()}_{id(job)}.wav")
            try:
                args = SimpleNamespace(**job["opts"])
                wav = tts_engine.synthesize(job["text"], job["engine"], args,
                                            tmp)
                if self.stop_requested:
                    continue
                procs = tts_engine.play_wav(wav)
                with self.lock:
                    self.procs = procs
                self._wait_procs(procs)
                with self.lock:
                    self.procs = []
                if not self.stop_requested:
                    if job.get("clear_after") and self.on_clear:
                        self.on_clear(job.get("widget"))
                    self.status_cb("✅ Listo")
            except Exception as e:
                if not self.stop_requested:
                    self.status_cb(f"⚠️ Error: {e}")
            finally:
                for suffix in ("", ".raw.wav", ".mp3"):
                    try:
                        os.remove(tmp + suffix)
                    except OSError:
                        pass
                self.busy = False
                self.cancel_event = None

    def _wait_procs(self, procs):
        self.cancel_event = threading.Event()
        while any(p.poll() is None for p in procs):
            if self.cancel_event.is_set():
                for p in procs:
                    try:
                        p.terminate()
                    except Exception:
                        pass
                return
            threading.Event().wait(0.1)

    def enqueue(self, job):
        with self.lock:
            active = self.busy or bool(self.procs) or not self.q.empty()
        if active and not job.get("queue"):
            self.stop()
        self.stop_requested = False
        self.q.put(job)

    def stop(self):
        self.status_cb("⏹ Detenido")
        with self.lock:
            for p in self.procs:
                try:
                    p.terminate()
                except Exception:
                    pass
            self.procs = []
        if getattr(self, "cancel_event", None):
            self.cancel_event.set()
        self.stop_requested = True
        while True:
            try:
                self.q.get_nowait()
            except queue.Empty:
                break


class TTSApp:
    def __init__(self, root):
        self.root = root
        self.cfg = load_config()
        self.theme = self.cfg.get("theme", "dark")
        if self.theme not in THEMES:
            self.theme = "dark"
        self.pal = THEMES[self.theme]

        self.current_engine = self.cfg.get("engine", "edge")
        self._reload_voices()

        self.tab_texts = {}
        self.tab_counter = 0
        self.buttons = []

        self.worker = SpeechWorker(
            lambda msg: self.root.after(0, self.set_status, msg),
            on_clear=lambda w: self.root.after(0, self._safe_clear, w))

        self._build_style()
        self._build_ui()
        self.apply_theme()
        self.add_tab()

        self.bind_shortcuts()
        labels = [v["label"] for v in self.voices]
        saved_voice = self.cfg.get("voice", "")
        self.voice_combo.set(saved_voice if saved_voice in labels
                             else self.voices[0]["label"])
        self.engine_combo.set(self.current_engine)
        self._on_voice_changed()
        self._set_slider("rate", self.cfg.get("rate", 0))
        self._set_slider("pitch", self.cfg.get("pitch", 0))
        self._set_slider("volume", self.cfg.get("volume", 0))
        self.metal_slider.set(self.cfg.get("robot_metal", 70))
        self.set_status("✅ Listo — elige motor y voz")

    def _reload_voices(self):
        """Recarga la lista de voces según el motor actual."""
        self.voices = tts_engine.list_voices(self.current_engine)
        if self.current_engine == "robot":
            # Para robot, asegurar que esté en la lista
            labels = [v["label"] for v in self.voices]
            if ROBOT_VOICE not in labels:
                self.voices.insert(0, {"label": ROBOT_VOICE, "id": ROBOT_VOICE, "gender": "Robot", "engine": "robot"})
        else:
            # Añadir robot como opción al final para otros motores
            self.voices.append({"label": ROBOT_VOICE, "id": ROBOT_VOICE, "gender": "Robot", "engine": "robot"})

    # ---------- Estilos ----------
    def _build_style(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

    # ---------- UI ----------
    def _build_ui(self):
        self.root.title("TTS Multitud")
        self.root.geometry("760x640")
        self.root.minsize(680, 560)

        # ---- Cabecera ----
        self.top = tk.Frame(self.root)
        self.top.pack(fill=tk.X, padx=16, pady=(12, 0))
        tk.Label(self.top, text="🎙 TTS Multitud",
                 font=("Ubuntu", 15, "bold")).pack(side=tk.LEFT)
        self.btn_settings = self._btn(self.top, "⚙ Ajustes", self.open_settings)
        self.btn_settings.pack(side=tk.RIGHT, padx=(6, 0))
        self.btn_theme = self._btn(self.top, "🌓 Tema", self.toggle_theme)
        self.btn_theme.pack(side=tk.RIGHT)

        # ---- Tarjeta: voz ----
        self.voice_card = tk.Frame(self.root, bd=0, highlightthickness=1,
                                   highlightbackground=self.pal["border"])
        self.voice_card.pack(fill=tk.X, padx=12, pady=(10, 0))
        self.inner = tk.Frame(self.voice_card)
        self.inner.pack(fill=tk.X, padx=14, pady=12)
        # Motor
        tk.Label(self.inner, text="Motor", font=("Ubuntu", 10, "bold")).pack(
            side=tk.LEFT, padx=(0, 10))
        self.engine_combo = ttk.Combobox(
            self.inner, state="readonly", width=14,
            values=["edge", "gtts", "pyttsx3", "robot"])
        self.engine_combo.pack(side=tk.LEFT, padx=(0, 12))
        self.engine_combo.bind("<<ComboboxSelected>>", self._on_engine_changed)
        # Voz
        tk.Label(self.inner, text="Voz", font=("Ubuntu", 10, "bold")).pack(
            side=tk.LEFT, padx=(12, 10))
        self.voice_combo = ttk.Combobox(
            self.inner, state="readonly",
            values=[v["label"] for v in self.voices])
        self.voice_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.voice_combo.bind("<<ComboboxSelected>>", self._on_voice_changed)
        self.btn_probe = self._btn(self.inner, "👂 Probar", self.probe_voice)
        self.btn_probe.pack(side=tk.LEFT, padx=(10, 0))

        # ---- Tarjeta: ajustes de voz ----
        self.cfg_frame = tk.Frame(self.root, bd=0, highlightthickness=1,
                                  highlightbackground=self.pal["border"])
        self.cfg_frame.pack(fill=tk.X, padx=12, pady=(8, 0))
        self.cfg_inner = tk.Frame(self.cfg_frame)
        self.cfg_inner.pack(fill=tk.X, padx=14, pady=10)

        self.sliders = {}
        self.slider_labels = {}
        # (clave, título, mínimo, máximo, columna)
        sliders = [
            ("rate", "⏩ Velocidad", -50, 100, 0),
            ("pitch", "🎚 Tono", -50, 50, 0),
            ("volume", "🔊 Volumen", -50, 50, 1),
        ]
        cols = [tk.Frame(self.cfg_inner) for _ in range(2)]
        for c in cols:
            c.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 14))
        for key, name, lo, hi, col in sliders:
            row = tk.Frame(cols[col])
            row.pack(fill=tk.X, pady=3)
            head = tk.Frame(row)
            head.pack(fill=tk.X)
            lab = tk.Label(head, text=name, anchor="w")
            lab.pack(side=tk.LEFT)
            val = tk.Label(head, text="+0", anchor="e", width=6)
            val.pack(side=tk.RIGHT)
            s = ttk.Scale(row, from_=lo, to=hi, value=0,
                          command=lambda v, k=key, val=val: self._on_slider(
                              k, v, val))
            s.pack(fill=tk.X)
            s.bind("<ButtonRelease-1>", lambda e: self._persist_sliders())
            self.sliders[key] = s
            self.slider_labels[key] = val

        # fila del robot (visible solo con SCP-079)
        self.robot_row = tk.Frame(self.cfg_inner)
        self.robot_row.pack(fill=tk.X, pady=(3, 0))
        head_r = tk.Frame(self.robot_row)
        head_r.pack(fill=tk.X)
        tk.Label(head_r, text="🤖 Metal", anchor="w").pack(side=tk.LEFT)
        self.metal_value = tk.Label(head_r, text="70%", anchor="e", width=6)
        self.metal_value.pack(side=tk.RIGHT)
        self.metal_slider = ttk.Scale(
            self.robot_row, from_=0, to=100, value=70,
            command=lambda v: self._on_metal(v))
        self.metal_slider.pack(fill=tk.X)
        self.metal_slider.bind("<ButtonRelease-1>",
                               lambda e: self._persist_sliders())

        self.hint = tk.Label(self.cfg_inner, text="", anchor="w")
        self.hint.pack(fill=tk.X, pady=(4, 0))

        # ---- Editor: pestañas ----
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=(10, 0))
        self.notebook.bind("<<NotebookTabChanged>>", self.on_tab_changed)

        # ---- Barra inferior ----
        self.bottom = tk.Frame(self.root)
        self.bottom.pack(fill=tk.X, padx=12, pady=(8, 4))

        self.btn_add = self._btn(self.bottom, "＋ Nueva", self.add_tab)
        self.btn_add.pack(side=tk.LEFT, padx=(0, 6))
        self.btn_del = self._btn(self.bottom, "✕ Eliminar",
                                 self.delete_current_tab)
        self.btn_del.pack(side=tk.LEFT)

        self.auto_clear_var = tk.BooleanVar(value=self.cfg.get("auto_clear", True))
        self.queue_var = tk.BooleanVar(value=self.cfg.get("queue_enabled", True))
        cb1 = tk.Checkbutton(self.bottom, text="Auto-limpiar",
                             variable=self.auto_clear_var,
                             command=self._persist_flags)
        cb1.pack(side=tk.LEFT, padx=(14, 2))
        cb2 = tk.Checkbutton(self.bottom, text="Encolar audios",
                             variable=self.queue_var,
                             command=self._persist_flags)
        cb2.pack(side=tk.LEFT, padx=2)

        self.btn_save = self._btn(self.bottom, "💾 Guardar", self.save_audio)
        self.btn_save.pack(side=tk.RIGHT, padx=(6, 0))
        self.btn_stop = self._btn(self.bottom, "⏹ Detener",
                                  lambda: self.worker.stop())
        self.btn_stop.pack(side=tk.RIGHT, padx=(6, 0))
        self.btn_speak = self._btn(self.bottom, "🔊 Hablar",
                                   self.speak_current, accent=True)
        self.btn_speak.pack(side=tk.RIGHT, padx=(6, 0))

        self.status = tk.Label(self.root, text="", anchor="w", padx=16,
                               pady=4)
        self.status.pack(fill=tk.X, side=tk.BOTTOM)

        self._apply_widget_palette()

    def _btn(self, parent, text, command, width=None, accent=False):
        btn = tk.Button(parent, text=text, command=command,
                        relief="flat", padx=12, pady=5, cursor="hand2",
                        font=("Ubuntu", 9), takefocus=False,
                        activeforeground="white")
        if width:
            btn.configure(width=width)
        self.buttons.append((btn, accent))
        return btn

    def _apply_widget_palette(self):
        self.root.configure(bg=self.pal["bg"])
        for w in (self.top, self.voice_card, self.cfg_frame, self.robot_row,
                  self.bottom):
            w.configure(bg=self.pal["bg"])
            self._paint_container(w)
        # inner frames de las tarjetas
        for attr in ("inner", "cfg_inner"):
            if hasattr(self, attr):
                getattr(self, attr).configure(bg=self.pal["bg"])
        # hint label
        if hasattr(self, "hint"):
            self.hint.configure(bg=self.pal["bg"])

    # ---------- Sliders ----------
    def _on_slider(self, key, value, label):
        v = int(round(float(value)))
        if key == "volume":
            label.configure(text=f"{v:+d}dB")
        else:
            label.configure(text=f"{v:+d}")

    def _set_slider(self, key, value):
        self.sliders[key].set(value)
        lab = self.slider_labels[key]
        if key == "volume":
            lab.configure(text=f"{value:+d}dB")
        else:
            lab.configure(text=f"{value:+d}")
        self.cfg[key] = value
        save_config(self.cfg)

    def _on_metal(self, value):
        v = int(round(float(value)))
        self.metal_value.configure(text=f"{v}%")
        self.cfg["robot_metal"] = v
        save_config(self.cfg)

    def _persist_sliders(self):
        for key in ("rate", "pitch", "volume"):
            self.cfg[key] = int(round(float(self.sliders[key].get())))
        self.cfg["robot_metal"] = int(round(float(self.metal_slider.get())))
        save_config(self.cfg)

    def _persist_flags(self):
        self.cfg["auto_clear"] = self.auto_clear_var.get()
        self.cfg["queue_enabled"] = self.queue_var.get()
        save_config(self.cfg)

    def _on_engine_changed(self, event=None):
        """Cambia el motor TTS y recarga las voces."""
        new_engine = self.engine_combo.get()
        if new_engine == self.current_engine:
            return
        self.current_engine = new_engine
        self.cfg["engine"] = new_engine
        save_config(self.cfg)
        self._reload_voices()
        self.voice_combo.configure(values=[v["label"] for v in self.voices])
        # Seleccionar primera voz disponible
        if self.voices:
            self.voice_combo.set(self.voices[0]["label"])
        self._on_voice_changed()

    # ---------- Voz ----------
    def _on_voice_changed(self, event=None):
        label = self.voice_combo.get()
        is_robot = label == ROBOT_VOICE
        self.robot_row.configure(bg=self.pal["bg"])
        self._paint_container(self.robot_row)
        self.metal_slider.configure(state="normal" if is_robot else "disabled")
        if is_robot:
            if self.sliders["rate"].get() == 0:
                self._set_slider("rate", -15)
            if self.sliders["pitch"].get() == 0:
                self._set_slider("pitch", -25)
            self.hint.configure(text="🤖 Sonido robot: voz robótica profunda. Ajusta Metal para más distorsión.",
                                fg=self.pal["accent"])
        else:
            # Detectar motor de la voz seleccionada
            voice_info = next((v for v in self.voices if v["label"] == label), {})
            engine = voice_info.get("engine", self.current_engine)
            if engine == "edge":
                self.hint.configure(text="✨ Voces neuronales (requieren internet). Edge TTS - 14 voces español.",
                                    fg=self.pal["fg_dim"])
            elif engine == "gtts":
                self.hint.configure(text="🌐 Google TTS (requiere internet). Múltiples idiomas disponibles.",
                                    fg=self.pal["fg_dim"])
            elif engine == "pyttsx3":
                self.hint.configure(text="🔧 pyttsx3 (local, offline). Usa voces del sistema (espeak/nsss/sapi5).",
                                    fg=self.pal["fg_dim"])
            else:
                self.hint.configure(text="✨ Voces disponibles.",
                                    fg=self.pal["fg_dim"])
        self.cfg["voice"] = label
        save_config(self.cfg)

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
        elif engine == "pyttsx3":
            opts = {"voice": voice["id"], "rate": max(50, min(400, 200 + rate)),
                    "volume": max(0.0, min(1.0, (volume + 50) / 100.0))}
            return {"text": text, "engine": "pyttsx3", "opts": opts,
                    "widget": widget, "clear_after": clear_after}
        # edge por defecto
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
        # la limpieza la hace el worker via on_clear al terminar

    def _safe_clear(self, widget):
        try:
            if widget and widget.winfo_exists():
                widget.delete("1.0", tk.END)
        except tk.TclError:
            pass

    def save_audio(self):
        text_widget = self.get_current_text()
        if not text_widget:
            return
        text = text_widget.get("1.0", tk.END).strip()
        if not text:
            self.set_status("⚠️ Nada que guardar")
            return
        voice = self.current_voice()
        ext = "mp3" if voice["id"] != ROBOT_VOICE else "wav"
        path = filedialog.asksaveasfilename(
            defaultextension=f".{ext}",
            filetypes=[(f"Audio ({ext})", f"*.{ext}")],
            initialfile=f"tts_{self.tab_counter}.{ext}")
        if not path:
            return

        def run():
            try:
                job = self.build_job(text)
                args = SimpleNamespace(**job["opts"])
                tts_engine.synthesize(text, job["engine"], args, path)
                self.root.after(0, lambda: self.set_status(
                    f"✅ Guardado: {os.path.basename(path)}"))
            except Exception as exc:
                msg = str(exc)

                def show_err():
                    self.set_status(f"⚠️ Error: {msg}")

                self.root.after(0, show_err)

        threading.Thread(target=run, daemon=True).start()
        self.set_status("💾 Guardando...")

    # ---------- Pestañas ----------
    def add_tab(self):
        if len(self.tab_texts) >= self.cfg.get("max_tabs", 5):
            self.set_status("⚠️ Límite de pestañas alcanzado")
            return
        self.tab_counter += 1
        name = f"Voz {self.tab_counter}"
        tab = tk.Frame(self.notebook)
        text = tk.Text(tab, height=12, width=50, relief="flat", wrap="word",
                       font=("Arial", 11), undo=True,
                       bg=self.pal["input"], fg=self.pal["fg"],
                       insertbackground=self.pal["fg"])
        text.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
        text.bind("<Return>", lambda e: (self.speak(text), "break"))
        text.bind("<Control-Return>", lambda e: (self.speak(text), "break"))
        self.tab_texts[name] = text
        self.notebook.add(tab, text=name)
        self.notebook.select(tab)
        text.focus_set()

    def delete_current_tab(self):
        if len(self.tab_texts) <= 1:
            return
        current = self.notebook.select()
        if not current:
            return
        tab = self.notebook.nametowidget(current)
        name = self.notebook.tab(current, "text")
        self.notebook.forget(current)
        self.tab_texts.pop(name, None)
        tab.destroy()

    def on_tab_changed(self, event=None):
        current = self.notebook.select()
        if not current:
            return
        tab = self.notebook.nametowidget(current)
        for child in tab.winfo_children():
            if isinstance(child, tk.Text):
                child.focus_set()
                break

    def get_current_text(self):
        current = self.notebook.select()
        if not current:
            return None
        name = self.notebook.tab(current, "text")
        return self.tab_texts.get(name)

    # ---------- Tema ----------
    def toggle_theme(self):
        idx = THEME_ORDER.index(self.theme)
        self.theme = THEME_ORDER[(idx + 1) % len(THEME_ORDER)]
        self.cfg["theme"] = self.theme
        save_config(self.cfg)
        self.apply_theme()

    def open_settings(self):
        """Diálogo de configuración completo."""
        win = tk.Toplevel(self.root)
        win.title("⚙ Configuración")
        win.geometry("460x560")
        win.resizable(False, False)
        win.transient(self.root)
        win.grab_set()
        win.configure(bg=self.pal["bg"])

        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- pestaña: General ---
        gen = tk.Frame(nb, bg=self.pal["bg"])
        nb.add(gen, text=" General ")

        # Motor TTS
        tk.Label(gen, text="Motor TTS", font=("Ubuntu", 10, "bold"),
                 bg=self.pal["bg"], fg=self.pal["fg"]).pack(anchor="w", padx=14, pady=(14, 4))
        frm_eng = tk.Frame(gen, bg=self.pal["bg"])
        frm_eng.pack(fill=tk.X, padx=14)
        eng_var = tk.StringVar(value=self.current_engine)
        cb_eng = ttk.Combobox(frm_eng, state="readonly", textvariable=eng_var,
                              values=["edge", "gtts", "pyttsx3", "robot"])
        cb_eng.pack(fill=tk.X)
        cb_eng.bind("<<ComboboxSelected>>", lambda e: self._on_engine_changed())

        # Tema
        tk.Label(gen, text="Tema", font=("Ubuntu", 10, "bold"),
                 bg=self.pal["bg"], fg=self.pal["fg"]).pack(anchor="w", padx=14, pady=(14, 4))
        frm = tk.Frame(gen, bg=self.pal["bg"])
        frm.pack(fill=tk.X, padx=14)
        theme_var = tk.StringVar(value=self.theme)
        cb = ttk.Combobox(frm, state="readonly", textvariable=theme_var,
                          values=[f"{i+1}. {t.title()}" for i, t in enumerate(THEME_ORDER)])
        cb.pack(fill=tk.X)

        def _on_theme_change():
            sel = theme_var.get().split(". ")[1].lower()
            self.theme = sel
            self.cfg["theme"] = sel
            save_config(self.cfg)
            self.apply_theme()

        cb.bind("<<ComboboxSelected>>", lambda e: _on_theme_change())

        # Pestañas máximas
        tk.Label(gen, text="Máx. pestañas", font=("Ubuntu", 10, "bold"),
                 bg=self.pal["bg"], fg=self.pal["fg"]).pack(anchor="w", padx=14, pady=(14, 4))
        frm2 = tk.Frame(gen, bg=self.pal["bg"])
        frm2.pack(fill=tk.X, padx=14)
        tabs_var = tk.IntVar(value=self.cfg.get("max_tabs", 5))
        ttk.Scale(frm2, from_=1, to=10, variable=tabs_var,
                  command=lambda v: tabs_var.set(int(float(v)))).pack(side=tk.LEFT, fill=tk.X, expand=True)
        tk.Label(frm2, textvariable=tabs_var, bg=self.pal["bg"], fg=self.pal["fg"],
                 width=4).pack(side=tk.LEFT, padx=(8, 0))

        # --- pestaña: Audio ---
        aud = tk.Frame(nb, bg=self.pal["bg"])
        nb.add(aud, text=" Audio ")

        tk.Label(aud, text="Auto-limpiar al hablar", font=("Ubuntu", 10, "bold"),
                 bg=self.pal["bg"], fg=self.pal["fg"]).pack(anchor="w", padx=14, pady=(14, 4))
        ac_var = tk.BooleanVar(value=self.cfg.get("auto_clear", True))
        tk.Checkbutton(aud, text="Activar", variable=ac_var, bg=self.pal["bg"],
                       fg=self.pal["fg"], selectcolor=self.pal["panel"],
                       activebackground=self.pal["bg"],
                       command=lambda: (self.auto_clear_var.set(ac_var.get()),
                                        self.cfg.update({"auto_clear": ac_var.get()}),
                                        save_config(self.cfg))).pack(anchor="w", padx=14)

        tk.Label(aud, text="Encolar audios (no interrumpir)", font=("Ubuntu", 10, "bold"),
                 bg=self.pal["bg"], fg=self.pal["fg"]).pack(anchor="w", padx=14, pady=(14, 4))
        q_var = tk.BooleanVar(value=self.cfg.get("queue_enabled", True))
        tk.Checkbutton(aud, text="Activar", variable=q_var, bg=self.pal["bg"],
                       fg=self.pal["fg"], selectcolor=self.pal["panel"],
                       activebackground=self.pal["bg"],
                       command=lambda: (self.queue_var.set(q_var.get()),
                                        self.cfg.update({"queue_enabled": q_var.get()}),
                                        save_config(self.cfg))).pack(anchor="w", padx=14)

        # --- pestaña: Voz Robot ---
        rob = tk.Frame(nb, bg=self.pal["bg"])
        nb.add(rob, text=" 🔊 Sonido Robot ")

        tk.Label(rob, text="Configuración del sonido robot", font=("Ubuntu", 10, "bold"),
                 bg=self.pal["bg"], fg=self.pal["fg"]).pack(anchor="w", padx=14, pady=(14, 4))

        def make_slider(parent, label, key, lo, hi, unit="", default=None):
            cur = self.cfg.get(key, default if default is not None else 0)
            fr = tk.Frame(parent, bg=self.pal["bg"])
            fr.pack(fill=tk.X, padx=14, pady=4)
            tk.Label(fr, text=label, bg=self.pal["bg"], fg=self.pal["fg"]).pack(side=tk.LEFT)
            val = tk.Label(fr, text=f"{cur}{unit}",
                           bg=self.pal["bg"], fg=self.pal["fg_dim"], width=6)
            val.pack(side=tk.RIGHT)
            s = ttk.Scale(fr, from_=lo, to=hi, value=cur,
                          command=lambda v, k=key, lbl=val: (
                              lbl.configure(text=f"{int(float(v))}{unit}"),
                              self.cfg.update({k: int(float(v))}),
                              save_config(self.cfg)
                          ))
            s.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 8))

        make_slider(rob, "Velocidad (wpm)", "robot_speed", 40, 450, default=135)
        make_slider(rob, "Pitch espeak", "robot_pitch", 1, 99, default=30)
        make_slider(rob, "Metal (distorsión %)", "robot_metal", 0, 100, "%", default=70)
        make_slider(rob, "Volumen (dB)", "robot_volume", -50, 50, "dB")

        # --- pestaña: Atajos ---
        kbd = tk.Frame(nb, bg=self.pal["bg"])
        nb.add(kbd, text=" ⌨ Atajos ")
        for k, v in [
            ("Ctrl+Enter", "Hablar pestaña actual"),
            ("Ctrl+T", "Nueva pestaña"),
            ("Ctrl+W", "Cerrar pestaña"),
            ("F5", "Probar voz seleccionada"),
        ]:
            row = tk.Frame(kbd, bg=self.pal["bg"])
            row.pack(fill=tk.X, padx=14, pady=4)
            tk.Label(row, text=k, font=("Ubuntu", 9, "bold"),
                     bg=self.pal["bg"], fg=self.pal["accent"], width=12).pack(side=tk.LEFT)
            tk.Label(row, text=v, bg=self.pal["bg"], fg=self.pal["fg_dim"]).pack(side=tk.LEFT)

        # Botón cerrar
        bf = tk.Frame(win, bg=self.pal["bg"])
        bf.pack(fill=tk.X, padx=10, pady=10)
        self._btn(bf, "Cerrar", win.destroy, accent=False).pack(side=tk.RIGHT)

    def _paint_container(self, parent):
        for child in parent.winfo_children():
            try:
                child.configure(bg=self.pal["bg"])
            except (tk.TclError, Exception):
                pass
            self._paint_container(child)

    def _recolor_fg(self, widget):
        for w in widget.winfo_children():
            try:
                if w.winfo_class() in ("Label", "Checkbutton") and \
                        w not in (self.status, self.hint):
                    w.configure(fg=self.pal["fg"])
            except tk.TclError:
                pass
            self._recolor_fg(w)

    def apply_theme(self):
        self.pal = THEMES[self.theme]
        root_colors = dict(bg=self.pal["bg"])
        self.root.configure(**root_colors)

        self.style.configure("TNotebook", background=self.pal["bg"],
                             borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.pal["tab"],
                             foreground=self.pal["fg"], padding=[12, 4])
        self.style.map("TNotebook.Tab",
                       background=[("selected", self.pal["select"])],
                       foreground=[("selected", self.pal["fg"])])
        self.style.configure("TCombobox", fieldbackground=self.pal["input"],
                             background=self.pal["input"],
                             foreground=self.pal["fg"],
                             arrowcolor=self.pal["fg"])
        self.style.map("TCombobox",
                       fieldbackground=[("readonly", self.pal["input"])],
                       foreground=[("readonly", self.pal["fg"])])
        self.style.configure("Horizontal.TScale", background=self.pal["bg"],
                             troughcolor=self.pal["panel"])

        self._paint_container(self.root)
        for button, accent in self.buttons:
            if not button.winfo_exists():
                continue
            if accent:
                button.configure(bg=self.pal["accent"], fg="white",
                                 activebackground=self.pal["accent"])
            else:
                button.configure(bg=self.pal["btn"], fg=self.pal["fg"],
                                 activebackground=self.pal["active"])
        self.status.configure(bg=self.pal["status"], fg=self.pal["fg_dim"])
        for cb in self.bottom.winfo_children():
            if isinstance(cb, tk.Checkbutton):
                cb.configure(bg=self.pal["bg"], fg=self.pal["fg"],
                             selectcolor=self.pal["panel"],
                             activebackground=self.pal["bg"],
                             activeforeground=self.pal["fg"],
                             highlightthickness=0)
        for name, text in self.tab_texts.items():
            text.configure(bg=self.pal["input"], fg=self.pal["fg"],
                           insertbackground=self.pal["fg"])
        for f in (self.cfg_frame, self.top):
            f.configure(bg=self.pal["bg"])
        self._recolor_fg(self.root)
        if hasattr(self, "hint"):
            self.hint.configure(
                fg=(self.pal["accent"]
                    if self.voice_combo.get() == ROBOT_VOICE
                    else self.pal["fg_dim"]))

    # ---------- Estado / atajos ----------
    def set_status(self, msg):
        self.status.configure(text=msg)

    def bind_shortcuts(self):
        self.root.bind("<Control-Return>", lambda e: self.speak_current())
        self.root.bind("<Control-t>", lambda e: (self.add_tab(), "break"))
        self.root.bind("<Control-w>",
                       lambda e: (self.delete_current_tab(), "break"))
        self.root.bind("<F5>", lambda e: self.probe_voice())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        self.worker.stop()
        self.worker.running = False
        self.worker.q.put(None)
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TTSApp(root)
    root.mainloop()