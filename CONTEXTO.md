# CONTEXTO.md — MultiVoice

## Qué es

App de escritorio en Python para **convertir texto en voz y hablar por un
micrófono virtual** en Discord y otras apps. Se escribe en la ventana, se pulsa
Hablar y la gente escucha la voz elegida.

- Motores: Microsoft Edge (voces neuronales, 14 en español, con internet),
  Google TTS (gTTS, con internet) y el **sonido robot** local (espeak-ng +
  ffmpeg: velocidad, tono, volumen y «metal»).
- Micrófono virtual: en Linux un sink/source de PipeWire creado con `pactl`
  (`virtualmic.py`); en Windows el cable VB-CABLE si está instalado
  (`tts_engine.find_virtual_output`), si no, los altavoces.
- Pestañas de texto, cola de reproducción, guardar MP3/WAV y una biblioteca de
  audios (`~/MultiVoice_Audio`, `library.py`).
- Sistemas: **Linux** (desarrollo y uso real) y **Windows** (experimental,
  sin probar en un PC real). macOS no se soporta.

## Estructura

| Archivo | Qué hace |
|---|---|
| `multivoice.py` | Interfaz (clase `TTSApp`), configuración (`config.json`), hilo de reproducción con cola |
| `tts_engine.py` | Síntesis (edge/gtts/robot), conversión con ffmpeg, reproducción y búsqueda del dispositivo virtual |
| `virtualmic.py` | Crear y quitar el micrófono virtual en Linux |
| `library.py` | Limpieza de la biblioteca (solo archivos `voz_*` de más de 30 días) |
| `platform_utils.py` | Rutas de configuración y biblioteca por sistema, fuentes, tecla modificadora |
| `tests/` | `test_safety.py` (pytest), `smoke_test.py` (motor), `gui_smoke.py` (ventana real en Xvfb) |

## Decisiones (2026-10-29)

- **Interfaz con CustomTkinter** (sigue siendo Python/Tk, empaquetado con
  PyInstaller en un solo archivo para Linux y Windows). Los motores TTS, la cola
  y el micrófono virtual **no se reescriben**: solo la capa visual y lo nuevo.
- **Estilos con las skills de diseño** (`ui-tokens` + `estilo-*`, en
  `~/.claude/skills`): el tema por defecto es **estilo-discord**; los 10 estilos
  de las skills se ofrecen como temas elegibles.
- **Interfaz en español**, coherente en toda la app (hoy mezcla inglés y español).
- Funciones nuevas pedidas por el dueño: cola e historial visibles, perfiles de
  voz, frases rápidas, diccionario de pronunciación, escucharse a uno mismo,
  soundboard de archivos y un atajo global para hablar desde cualquier app.

## Reglas para el agente

- El agente no puede leer archivos fuera del repositorio (las skills viven en
  `~/.claude/skills`): lo que haga falta de ellas ya está copiado en el repo
  (`assets/temas/*.css`). Las reglas de cada skill se leen cargando la skill.

- Entorno: `.venv` creado con **uv** (ya está en el PATH del loop). Para
  dependencias nuevas: añadirlas a `requirements.txt` y usar `uv pip install`.
- **Nunca** llamar de verdad a `setup_virtual_mic`/`pactl` ni reproducir audio en
  los tests: usar los dobles que ya usa `tests/gui_smoke.py`.
- **Nunca** escribir en la configuración ni en la biblioteca reales del usuario
  en los tests: rutas temporales como en `gui_smoke.py`.
- Los tests de la interfaz se ejecutan sin pantalla con `xvfb-run -a`.
- Toda función nueva debe funcionar en Linux y Windows o degradar con un aviso
  claro (p. ej. el atajo global en Wayland).
- Empaquetado: si una dependencia trae archivos de datos (customtkinter los
  trae), el paso de PyInstaller de `.github/workflows/build.yml` debe incluirlos.
