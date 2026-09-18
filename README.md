<div align="center">

# MultiVoice

**Turn text into speech and speak through a virtual microphone in Discord and other apps**

Type in the window, press **Speak** and your audience hears you with the voice you chose.

</div>

## Installation

### Option 1: pre-built binary (Windows, macOS and Linux)

Download the file for your system from [Releases](https://github.com/BenReynor/tts-multitud/releases) (latest version: `v1.2.0`), unzip it and open it. There is one `.zip` per system:

- `multivoice-linux-x86_64.zip` → Linux on Intel/AMD processors (most common)
- `multivoice-linux-arm64.zip` → Linux on ARM (Raspberry Pi, many ARM boards)
- `multivoice-windows-x64.zip` → Windows
- `multivoice-macos-arm64.zip` → macOS on Apple Silicon (M1/M2/M3/M4)
- `multivoice-macos-intel.zip` → macOS on Intel processors

If you don't know your macOS, check *Apple  →  About This Mac*; if it doesn't say "Apple", it's Intel.

The `.zip` downloads to your browser's **Downloads** folder and, when unzipped, creates the `multivoice-<OS>` folder wherever you choose. Nothing is installed and no shortcuts are created: the executable runs from wherever you unzip it and you can move it anywhere.

- **Linux:** make it executable and run it. It only needs `pactl`/`pw-play` (PipeWire) to create the virtual microphone; `ffmpeg` and `espeak-ng` are already bundled.
  ```bash
  chmod +x multivoice && ./multivoice
  ```
- **Windows:** run it; if SmartScreen appears, *More info → Run anyway*.
- **macOS:** open it; if Gatekeeper blocks it, right-click → *Open*, or `xattr -dr com.apple.quarantine multivoice.app`.

The binary includes Python, the speech libraries, `ffmpeg` and `espeak-ng`. It does not include the virtual audio cable for Windows/macOS, which must be installed separately (see below).

### Option 2: from source

Requires Python 3.8+ and the system packages `ffmpeg`, `espeak-ng` and `python3-tk`.

```bash
git clone https://github.com/BenReynor/tts-multitud.git
cd tts-multitud
python3 -m pip install -r requirements.txt
```

To create the launcher (with the app icon) in the applications menu and on the desktop:

```bash
./install.sh
```

On Debian/Ubuntu, for the system dependencies:

```bash
sudo apt install ffmpeg espeak-ng python3-tk
```

## Quick start

- **Downloaded binary:** open `multivoice` (Linux/macOS) or `multivoice.exe` (Windows).
- **From source:**

```bash
./start.sh
```

On Linux the app creates the `🎤` virtual microphone when it opens and removes it when it closes. In the app where you want to speak, select it as the input device:

- Discord: Settings → Voice & Video → Input device → `🎤`
- Any other app that lets you choose a microphone works the same way.

Type some text, press **🔊 Speak** and the voice is heard in your headphones and through the virtual mic.

## Virtual microphone on Windows and macOS

There the app cannot create the microphone on its own: it needs a virtual audio cable from the system. The app detects it and plays through it automatically; you only have to select the input in Discord.

1. **Install the cable (once):**
   - **macOS:** [BlackHole](https://existential.audio/blackhole/) (`brew install --cask blackhole-2ch`).
   - **Windows:** [VB-CABLE](https://vb-audio.com/Cable/) (installer, requires administrator permissions).
2. **Choose the input in Discord:** Settings → Voice & Video → Input device → `BlackHole 2ch` (macOS) or `CABLE Output` (Windows).

### Hear yourself

The virtual cable sends audio to Discord but not to your speakers; to hear yourself you need to duplicate the output:

- **macOS:** in *Audio MIDI Setup* create a **multi-output device** with your speakers + BlackHole and select it as the system output.
- **Windows:** in *Sound → Recording → CABLE Output → Properties → Listen* check **Listen to this device** and choose your speakers.

### If something doesn't sound right

- Leave the app open; on Windows/macOS it only plays while running.
- On Windows, if Discord sounds too low, try `Discord → Settings → Voice & Video → Disable audio processing` and adjust the input volume.
- If it doesn't detect the cable, the app plays through the speakers and warns you when it opens.

> Verified on Linux; routing to BlackHole/VB-CABLE is tested in the automated integration, but not on real Windows/macOS hardware.

## What you can do

- **Three TTS engines:** Microsoft Edge neural voices (14 Spanish voices, online), Google TTS (gTTS, online) and the local robot sound (espeak-ng, offline).
- **Robot sound:** simulates the robotic voice of SCP-079, with metal (distortion), speed, pitch and volume controls.
- **Multiple tabs:** prepare several texts and play them in a queue, with optional auto-clear.
- **Save audio:** export the voice to MP3 or WAV from the Save button.

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+Enter | Speak the current tab |
| Ctrl+T | New tab |
| Ctrl+W | Close tab |
| F5 | Test the selected voice |

## Notes

- The `🎤` virtual mic only exists on Linux and while the app is open; if you want to choose it in Discord, keep the app open.
- On Windows and macOS the app uses the system virtual cable (BlackHole or VB-CABLE) if installed; otherwise it plays through the speakers.
- Edge TTS and Google TTS need internet. The robot works offline and uses `espeak-ng`; it is bundled in the binaries (from source you need to have it installed).

## License

Personal use. No public license.