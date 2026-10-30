"""Abre la ventana real un momento (necesita pantalla: Xvfb en Linux/CI)."""
import json
import os
import queue
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
# Arranque como en main(): ventana oculta y pantalla de carga con el avance.
root.withdraw()
carga = mv.PantallaCarga(root)
pasos = []


def _avance(texto, fraccion):
    pasos.append((texto, fraccion))
    carga.paso(texto, fraccion)


app = mv.TTSApp(root, progreso=_avance)
assert len(pasos) >= 5 and pasos[-1][1] == 1.0, pasos
assert [f for _, f in pasos] == sorted(f for _, f in pasos), "la barra retrocede"
assert carga.barra.get() == 1.0
carga.cerrar()
root.deiconify()
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
# El desplegable de motor muestra el motor actual (también en Ajustes)
assert app.engine_menu.get() == mv.ENGINES["edge"], "motor vacío en la ventana"
app.open_settings()
root.update()
win = app.settings_win
assert win.winfo_exists() and isinstance(win, ctk.CTkToplevel), "Ajustes no es modal"
assert win.winfo_toplevel() is win and win is not root
assert list(app._sections) == ["General", "Audio", "Sonido robot", "Atajos"]
assert app.settings_engine_menu.get() == mv.ENGINES["edge"], "motor vacío en Ajustes"
for sec in app._sections:
    app._show_section(sec)
    root.update()
    assert app._sections[sec].winfo_manager() == "pack", sec
app._on_engine_changed("robot")
assert app.settings_engine_menu.get() == mv.ENGINES["robot"]
app._on_engine_changed("edge")
app.open_settings("Atajos")          # no abre una segunda ventana
assert app.settings_section == "Atajos"
win.destroy()
root.update()

# Biblioteca: lista, búsqueda, reproducir, abrir carpeta y borrar con confirmación
lib = app._get_library_dir()
os.makedirs(lib, exist_ok=True)
for nombre, texto, voz in (("voz_1.mp3", "Hola mundo", "Jorge"),
                           ("voz_2.wav", "Adiós robot", "Sonido robot")):
    with open(os.path.join(lib, nombre), "wb") as f:
        f.write(b"x" * 2048)
    with open(os.path.join(lib, nombre + ".json"), "w", encoding="utf-8") as f:
        json.dump({"text": texto, "voice": voz, "engine": "edge"}, f)
app.tabview.set(mv.lib_tab())
app.on_tab_changed()
root.update()
assert len(app.lib_entries) == 2
app.lib_search_var.set("robot")
root.update()
assert [e["name"] for e in app.lib_entries] == ["voz_2.wav"]
app.lib_search_var.set("zzz")
assert app.lib_entries == [] and "Nada coincide" in str(
    [w.cget("text") for w in app.lib_list.winfo_children()])
app.lib_search_var.set("")
abiertos = []
app._open_path = abiertos.append
app._play_library_path(os.path.join(lib, "voz_1.mp3"))
app._open_library_folder()
assert abiertos == [os.path.join(lib, "voz_1.mp3"), lib]
app.confirmar = lambda *a, **k: False
assert not app._delete_library_entry(os.path.join(lib, "voz_1.mp3"))
assert os.path.exists(os.path.join(lib, "voz_1.mp3")), "borró sin confirmar"
app.confirmar = lambda *a, **k: True
assert app._delete_library_entry(os.path.join(lib, "voz_1.mp3"))
assert not os.path.exists(os.path.join(lib, "voz_1.mp3"))
assert not os.path.exists(os.path.join(lib, "voz_1.mp3.json"))
assert len(app.lib_entries) == 1
# Panel lateral: cola, historial y medidor (sin sintetizar ni reproducir)
cola = app.worker.cola
app.worker.q = queue.Queue()         # el hilo sigue esperando en la cola vieja
app.worker.enqueue(dict(app.build_job("Primer texto muy largo " * 10), queue=True))
app.worker.enqueue(dict(app.build_job("Segundo texto"), queue=True))
e2 = cola.instantanea()[1][-1]
root.update()
assert "En cola (2)" in app.lbl_cola.cget("text")
assert len(app.cola_list.winfo_children()) == 2
app._quitar_de_cola(e2.id)
root.update()
assert "En cola (1)" in app.lbl_cola.cget("text")
cola.avanzar()
cola.iniciar_audio(1.0, [0.8] * 30)
app._refresh_cola()
app._tick_cola()
assert app.now_text.cget("text").endswith("…") and app.now_voice.cget("text")
assert app._nivel_visible > 0, "el medidor no se mueve mientras suena"
cola.terminar()
app._refresh_cola()
root.update()
assert "Historial (1)" in app.lbl_hist.cget("text")
app._repetir(cola.instantanea()[2][0].id)
root.update()
assert "En cola (1)" in app.lbl_cola.cget("text"), "repetir no encola"
app.set_theme("minimal")             # el panel se repinta sin errores
root.update()
# perfiles: desplegable con los de ejemplo, aplicar, guardar, renombrar, borrar
assert {"SCP-079", "Narrador"} <= set(app.profile_menu.cget("values"))
assert app.apply_profile("SCP-079")
assert app.current_engine == "robot" and app.metal_slider.get() == 85
app.profile_menu.set("SCP-079")
app._pedir_nombre = lambda *a, **k: "Prueba"
app.profile_save_new()
assert "Prueba" in app.profile_menu.cget("values")
app._pedir_nombre = lambda *a, **k: "Prueba2"
app.profile_rename()
assert "Prueba2" in app.cfg["profiles"] and "Prueba" not in app.cfg["profiles"]
app.profile_delete()
assert "Prueba2" not in app.cfg["profiles"]
root.update()
# Frases rápidas: vista, decir con el perfil activo y con uno propio, Ctrl+1
import frases  # noqa: E402
dichas = []
app.worker.enqueue = dichas.append
app.tabview.set(frases.tab_frases())
app.on_tab_changed()
root.update()
assert frases.categorias(app.cfg) == ["Saludos", "Reacciones"]
assert app.decir_frase("Saludos", 0)
assert dichas[-1]["text"] == "Hola a todos"
frases.editar(app.cfg, "Saludos", 1, perfil="SCP-079")
assert app.decir_frase("Saludos", 1)
assert dichas[-1]["engine"] == "robot", dichas[-1]
assert app.root.bind("<Control-Key-9>"), "Ctrl+9 sin atajo"
app.decir_numero(1)
assert dichas[-1]["text"] == "Hola a todos" and len(dichas) == 3
app.frase_dialogo()
texto, cat, perf, sin = app._frase_dialogo_campos
texto.insert(0, "Frase nueva")
cat.set("Chistes")
app._frase_dialogo_aceptar()
assert frases.frases(app.cfg, "Chistes")[0]["text"] == "Frase nueva"
app.frase_dialogo("Chistes", 0)
texto, cat, perf, sin = app._frase_dialogo_campos
cat.set("Saludos")
app._frase_dialogo_aceptar()
assert frases.frases(app.cfg, "Chistes") == []
app.confirmar = lambda *a, **k: True
app.categoria_borrar("Chistes")
assert "Chistes" not in app.cfg["phrases"]
root.update()
# Soundboard: añadir (con ffmpeg falso), listar y encolar sin reproducir
import types  # noqa: E402
import soundboard  # noqa: E402
orig_run = soundboard.tts_engine._run


def _ffmpeg_falso(cmd, **kw):
    open(cmd[-1], "wb").close()
    return types.SimpleNamespace(returncode=0)


soundboard.tts_engine._run = _ffmpeg_falso
origen = os.path.join(tmp, "risa.mp3")
open(origen, "wb").close()
assert app.sb_anadir_archivo(origen)
soundboard.tts_engine._run = orig_run
assert [s["name"] for s in soundboard.sonidos(app.cfg)] == ["risa"]
visto = []
app.worker.enqueue = visto.append
assert app.sb_reproducir(0)
assert visto[0]["engine"] == "sound" and os.path.isfile(visto[0]["opts"]["file"])
assert app.listen_var.get() is False
app.listen_var.set(True)
app._persist_flags()
assert app.cfg["listen_self"] is True and app.worker.salidas()[0] is True
app.sb_borrar(0)
assert soundboard.sonidos(app.cfg) == []
# Cuadro «Decir»: siempre encima, Enter lo dice; la orden de otra ejecución lo abre
import instancia  # noqa: E402
visto.clear()
app.atender_orden(instancia.CMD_DECIR)
root.update()
assert app.decir_win.winfo_exists() and app.decir_win.attributes("-topmost")
app.decir_entry.insert(0, "hola desde el atajo")
assert app.decir_enviar() == "hola desde el atajo"
assert visto[0]["text"] == "hola desde el atajo"
root.update()
assert not app.decir_win.winfo_exists()
app.open_settings("Atajos")
root.update()
app.settings_win.destroy()
app._save_soon()
app.on_close()
assert os.path.isfile(mv.CONFIG_PATH), "config.json no se escribió"
print(f"GUI SMOKE OK ({sys.platform}, tema={app.theme})")
