<div align="center">

<img src="assets/icon.png" width="96" alt="MultiVoice icon">

# MultiVoice

**Turn text into speech and speak through a virtual microphone in Discord and other apps**

Type in the window, press **Speak** and your audience hears you with the voice you chose.

**[⬇ Download the latest version](https://github.com/BenReynor/MultiVoice/releases/latest)** · Linux and Windows · no installation needed

</div>

> [!WARNING]
> **Windows is experimental and untested on a real PC.** MultiVoice is developed
> and used on Linux. On Windows the app builds and its window opens in automated
> tests, but the main feature, speaking into Discord through the **VB-CABLE**
> virtual cable, has never been tried on real hardware. On Windows you must
> install VB-CABLE yourself (see [Virtual microphone on Windows](#virtual-microphone-on-windows)).
> If it fails, please [open an issue](https://github.com/BenReynor/MultiVoice/issues).

## Screenshots

| Main window (Discord theme) | Quick phrases |
|---|---|
| ![Main window](docs/capturas/principal.png) | ![Quick phrases](docs/capturas/frases.png) |
| **Audio library** | **Retro theme** (one of 10) |
| ![Library](docs/capturas/biblioteca.png) | ![Retro theme](docs/capturas/tema_retro.png) |

<p align="center"><img src="docs/capturas/ajustes.png" width="520" alt="Settings → Shortcuts"><br><em>Settings → Shortcuts, with the global “speak” shortcut</em></p>

The interface is in Spanish.

## What you can do

- **Three TTS engines:** Microsoft Edge neural voices (14 Spanish voices, online), Google TTS (gTTS, online) and the local **robot sound** (espeak-ng, offline) that imitates SCP-079, with metal (distortion), speed, pitch and volume controls.
- **Voice profiles:** save engine, voice, speed, pitch, volume and metal under a name (e.g. “SCP-079”, “Narrator”) and switch between them from the voice bar. Two sample profiles are included.
- **Quick phrases:** buttons grouped in categories that speak a phrase with one click, with the active profile or their own. The first nine are on **Ctrl+1 … Ctrl+9**.
- **Queue and history:** a side panel shows what is playing (with a progress bar and level meter), what is waiting in the queue (each item can be removed) and what you said this session (repeat with one click).
- **Pronunciation dictionary:** replacements applied before speaking with any engine (e.g. `xd` → “equis de”), whole word or not, case-insensitive; can be turned off.
- **Soundboard:** add your own audio files (mp3/wav/ogg), name them and play them through the virtual microphone, respecting the queue.
- **Hear yourself:** the **Escucharme** switch also plays through your speakers what goes out through the virtual mic.
- **Global shortcut to speak from any app:** `multivoice --decir` opens a small always-on-top box in the running app; type and press Enter. See [Global shortcut](#global-shortcut).
- **Several text tabs**, optional auto-clear after speaking, and **save audio** to MP3 or WAV.
- **Audio library:** with *Auto-save* on, every spoken text is saved with its text and voice; search, play, open the folder or delete. Files created by the app (`voz_*`) older than 30 days are deleted automatically; any other file in the folder is never touched.
- **10 themes** (Discord by default, minimal, cyberpunk, warm, data, anime, manga, glass, retro, brutalist), with light/dark variants where available.
- **Single instance:** opening it again brings the open window to the front instead of starting a second copy.

## Installation

### Platform status

| System | Status |
|--------|--------|
| **Linux** | ✅ Developed and tested here, including real audio through the virtual microphone. |
| **Windows** | 🧪 **Experimental, untested on a real PC.** It builds and the window opens in automated tests, but playback through VB-CABLE has not been tested on real hardware. `install.sh` and `start.sh` are Linux-only: on Windows use `multivoice.exe` or `python multivoice.py`. |

Windows builds are provided on a best-effort basis. If something fails there, please [open an issue](https://github.com/BenReynor/MultiVoice/issues) with your system version and what you saw.

### Option 1: pre-built binary (Linux and Windows)

Download the file for your system from [Releases](https://github.com/BenReynor/MultiVoice/releases), unzip it and open it. There is one `.zip` per system:

- `multivoice-linux-x86_64.zip` → Linux on Intel/AMD processors (most common)
- `multivoice-linux-arm64.zip` → Linux on ARM (Raspberry Pi, many ARM boards)
- `multivoice-windows-x64.zip` → Windows

Nothing is installed and no shortcuts are created: the executable runs from wherever you unzip it.

- **Linux:** make it executable and run it. It only needs `pactl`/`pw-play` (PipeWire) to create the virtual microphone; `ffmpeg` and `espeak-ng` are already bundled.
  ```bash
  chmod +x multivoice && ./multivoice
  ```
- **Windows:** run it; if SmartScreen shows “Windows protected your PC”, choose *More info → Run anyway* (the executable is not signed).

The binary includes Python, the speech libraries, `ffmpeg` and `espeak-ng`. It does not include the virtual audio cable for Windows, which must be installed separately (see below).

Every push to `main` also builds fresh binaries in GitHub Actions (workflow **Build**, artifacts per system), if you want the latest version before a release.

### Option 2: from source (Linux)

Requires Python 3.8+ with Tk and the system packages `ffmpeg` and `espeak-ng`. On Debian/Ubuntu:

```bash
sudo apt install ffmpeg espeak-ng python3-tk
git clone https://github.com/BenReynor/MultiVoice.git
cd MultiVoice
./install.sh     # launcher in the applications menu and on the desktop
./start.sh       # or open it from the launcher
```

`start.sh` creates the project's own `.venv` the first time (with [uv](https://docs.astral.sh/uv/) if installed, otherwise `venv` + `pip`) and installs `requirements.txt`; it re-syncs it whenever `requirements.txt` changes, showing a progress window meanwhile. The launcher created by `install.sh` finds the folder even if you move it within your home, and its icon updates together with the app.

On Windows from source: `python -m pip install -r requirements.txt` and `python multivoice.py`.

## Quick start

On Linux the app creates the `🎤` virtual microphone when it opens and removes it when it closes. In the app where you want to speak, select it as the input device:

- Discord: Settings → Voice & Video → Input device → `🎤`
- Any other app that lets you choose a microphone works the same way.

Type some text, press **🔊 Hablar** (or Enter) and the voice goes out through the virtual mic.

## Global shortcut

`multivoice --decir` asks the open MultiVoice to show a small always-on-top box: type, press Enter and it is spoken. To use it from any app, bind it to a key:

- **Linux:** Wayland does not let apps register global shortcuts, so the system does it. *Ajustes → Atajos* shows the exact command and, on GNOME, a button that creates the shortcut for you (default `Ctrl+Alt+H`). On other desktops, add a custom shortcut that runs that command.
- **Windows:** the app registers the shortcut itself (configurable in *Ajustes → Atajos*, default `Ctrl+Alt+H`).

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| Enter / Ctrl+Enter | Speak the current tab |
| Ctrl+T | New tab |
| Ctrl+W | Close tab |
| Ctrl+1 … Ctrl+9 | Say quick phrase 1–9 |
| F5 | Test the selected voice |
| Esc | Close Settings and dialogs |

## Virtual microphone on Windows

There the app cannot create the microphone on its own: it needs a virtual audio cable from the system. The app detects it and plays through it automatically; you only have to select the input in Discord.

1. **Install the cable (once):** [VB-CABLE](https://vb-audio.com/Cable/) (installer, requires administrator permissions).
2. **Choose the input in Discord:** Settings → Voice & Video → Input device → `CABLE Output`.

To hear yourself, turn on **Escucharme** in the app (it also plays through your normal output).

### If something doesn't sound right

- Leave the app open; it only plays while running.
- If Discord sounds too low, try *Discord → Settings → Voice & Video → Disable audio processing* and adjust the input volume.
- If it doesn't detect the cable, the app plays through the speakers and warns you when it opens.

## Notes

- The `🎤` virtual mic only exists on Linux and while the app is open.
- Edge TTS and Google TTS need internet. The robot works offline and uses `espeak-ng`; it is bundled in the binaries (from source you need it installed).
- **Privacy:** with Edge TTS and Google TTS the text you type is sent to Microsoft and Google respectively. The robot sound is fully local. With Auto-save, the text is also stored in plain text next to each audio file.
- **Where things are saved:** the audio library goes to `~/MultiVoice_Audio` (Linux) or `Documents/MultiVoice_Audio` (Windows). Settings, profiles, quick phrases, the dictionary and the soundboard list are stored in `config.json`: in your user config folder for the packaged app (`~/.config/MultiVoice` or `%APPDATA%\MultiVoice`), next to `multivoice.py` when running from source.

## Development

```bash
.venv/bin/ruff check .
.venv/bin/python -m pytest -q
.venv/bin/python tests/smoke_test.py            # TTS engines (no network)
xvfb-run -a .venv/bin/python tests/gui_smoke.py # opens the real window headless
```

CI runs the same checks on Linux and Windows and builds the binaries (`.github/workflows/build.yml`). Packaged builds bundle CustomTkinter's data files (`--collect-all customtkinter`), the themes (`--add-data assets/temas`) and the icon; if you add a dependency with data files or a folder read at run time, add it to the “Build executable” step too. `CONTEXTO.md` explains the structure and the design decisions.

## Contributing

Contributions are welcome: open an [issue](https://github.com/BenReynor/MultiVoice/issues)
to report a bug or suggest an idea, or send a pull request. Run the checks in
[Development](#development) first (CI runs them on Linux and Windows). Testing on
a real Windows PC with VB-CABLE is especially helpful. The interface is in Spanish.

## License

[MIT](LICENSE): you may use, copy, modify and distribute MultiVoice freely, including
in your own projects, as long as you keep the copyright notice.
