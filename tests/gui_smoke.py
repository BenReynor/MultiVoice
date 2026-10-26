"""Opens the real window briefly (needs a display: Xvfb on Linux CI)."""
import os
import sys
import tempfile
import tkinter as tk

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import multivoice as mv  # noqa: E402

tmp = tempfile.mkdtemp(prefix="mv_gui_")
mv.CONFIG_DIR = tmp
mv.CONFIG_PATH = os.path.join(tmp, "nested", "config.json")  # must be created
mv.DEFAULT_CONFIG["library_path"] = os.path.join(tmp, "lib")
mv.setup_virtual_mic = lambda: []          # do not touch the audio server
mv.teardown_virtual_mic = lambda ids: None

root = tk.Tk()
app = mv.TTSApp(root)
for theme in mv.THEME_ORDER:                # every theme must apply cleanly
    app.theme = theme
    app.apply_theme()
app.add_tab()
app.open_settings()
root.update()
btn = app.btn_speak
btn.configure(bg="#123456", activebackground="#654321")  # FlatButton surface
app._save_soon()
app.on_close()
assert os.path.isfile(mv.CONFIG_PATH), "config.json not written"
print(f"GUI SMOKE OK ({sys.platform}, button={type(btn).__name__})")
