"""Abre la ventana real un momento (necesita pantalla: Xvfb en Linux/CI)."""
import os
import sys
import tempfile

import customtkinter as ctk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import multivoice as mv  # noqa: E402
import temas  # noqa: E402

tmp = tempfile.mkdtemp(prefix="mv_gui_")
mv.CONFIG_DIR = tmp
mv.CONFIG_PATH = os.path.join(tmp, "nested", "config.json")  # se debe crear
mv.DEFAULT_CONFIG["library_path"] = os.path.join(tmp, "lib")
mv.setup_virtual_mic = lambda: []          # no tocar el servidor de audio
mv.teardown_virtual_mic = lambda ids: None

# El tema guardado debe aplicarse al arrancar, no solo al cambiarlo.
# «hacker» es un nombre antiguo que pasa a Cyberpunk.
os.makedirs(os.path.dirname(mv.CONFIG_PATH), exist_ok=True)
with open(mv.CONFIG_PATH, "w", encoding="utf-8") as f:
    f.write('{"theme": "hacker"}')

root = ctk.CTk()
app = mv.TTSApp(root)
pal = temas.paleta("cyberpunk")
assert app.theme == "cyberpunk", "el tema guardado no se leyó"
assert app.btn_speak.cget("fg_color") == pal["--accent"], "tema no aplicado al arrancar"
assert app.btn_speak.cget("text_color") == pal["--accent-text"]
assert app.btn_stop.cget("fg_color") == pal["--surface-2"], "tema no aplicado al arrancar"
assert app.status.cget("text_color") == pal["--text-2"], "estado sin colorear"
assert app.status.cget("text").strip(), "la barra de estado está vacía"

# Cada tema (y cada modo) se aplica sin error y cambia los colores
for tema, _nombre in temas.lista_temas():
    for modo in temas.modos(tema) or (None,):
        app.set_theme(tema, modo)
        root.update()
        p = temas.paleta(tema, modo)
        assert app.btn_speak.cget("fg_color") == app._col("--accent"), (tema, modo)
        assert app.cfg["theme"] == tema, (tema, modo)
        assert app.theme_menu.get() == app._theme_label(), (tema, modo)
        assert "--bg" in p
app.set_theme("discord")
assert app.btn_speak.cget("fg_color") == temas.paleta("discord")["--accent"]

# El panel de voz solo muestra los controles del motor elegido
def visibles():
    rows = {k: r.winfo_manager() == "pack" for k, r in app.slider_rows.items()}
    rows["metal"] = app.robot_row.winfo_manager() == "pack"
    return rows


app._on_engine_changed("edge")
app.voice_combo.set(app.voices[0]["label"])
app._on_voice_changed()
assert visibles() == {"rate": True, "pitch": True, "volume": True, "metal": False}
app.voice_combo.set(mv.ROBOT_VOICE)
app._on_voice_changed()
assert visibles() == {"rate": True, "pitch": True, "volume": True, "metal": True}
app._on_engine_changed("gtts")
app.voice_combo.set(app.voices[0]["label"])
app._on_voice_changed()
assert visibles() == {"rate": False, "pitch": False, "volume": False, "metal": False}
app._on_engine_changed("edge")

# Pestañas, atajos y ajustes
app.add_tab()
assert len(app.tab_texts) == 2
app.root.event_generate("<Control-w>")
app.open_settings()
root.update()
app.settings_win.destroy()
app._save_soon()
app.on_close()
assert os.path.isfile(mv.CONFIG_PATH), "config.json no se escribió"
print(f"GUI SMOKE OK ({sys.platform}, tema={app.theme})")
