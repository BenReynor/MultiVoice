#!/usr/bin/env python3
# TTS engine: edge-tts, gTTS, robot (espeak-ng)
# Usage:
#   python3 tts_engine.py "text" [--engine edge|gtts|robot] [--voice ID]
#       [--rate N] [--pitch N] [--volume N] [--lang CODE]
#       [--robot-speed N] [--robot-pitch N] [--robot-metal N]
#       [--save FILE] [--no-play]
import argparse
import asyncio
import os
import shutil
import subprocess
import sys
import threading

import edge_tts
from gtts import gTTS

ROBOT_VOICE = "🤖 Robot Sound"
SAMPLE_RATE = 48000

# Known Spanish voices from edge-tts (friendly name, id, gender)
# Reduced subset: main countries
SPANISH_VOICES = [
    ("Alvaro — Spain (M)", "es-ES-AlvaroNeural", "Male"),
    ("Elvira — Spain (F)", "es-ES-ElviraNeural", "Female"),
    ("Elena — Argentina (F)", "es-AR-ElenaNeural", "Female"),
    ("Tomas — Argentina (M)", "es-AR-TomasNeural", "Male"),
    ("Catalina — Chile (F)", "es-CL-CatalinaNeural", "Female"),
    ("Lorenzo — Chile (M)", "es-CL-LorenzoNeural", "Male"),
    ("Gonzalo — Colombia (M)", "es-CO-GonzaloNeural", "Male"),
    ("Salome — Colombia (F)", "es-CO-SalomeNeural", "Female"),
    ("Dalia — Mexico (F)", "es-MX-DaliaNeural", "Female"),
    ("Jorge — Mexico (M)", "es-MX-JorgeNeural", "Male"),
    ("Alex — Peru (M)", "es-PE-AlexNeural", "Male"),
    ("Camila — Peru (F)", "es-PE-CamilaNeural", "Female"),
    ("Paola — Venezuela (F)", "es-VE-PaolaNeural", "Female"),
    ("Sebastian — Venezuela (M)", "es-VE-SebastianNeural", "Male"),
]


def _run(cmd, **kw):
    kw.pop("capture_output", None)
    kw.pop("stderr", None)
    kw.pop("stdout", None)
    return subprocess.run(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, **kw)


def _resource_dir():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def _find_bin(name):
    """Find an executable bundled with the app (bin/) or fall back to PATH."""
    exe = name + ".exe" if sys.platform.startswith("win") else name
    base = _resource_dir()
    for cand in (os.path.join(base, "bin", exe), os.path.join(base, exe)):
        if os.path.exists(cand):
            try:
                os.chmod(cand, 0o755)
            except OSError:
                pass
            return cand
    return shutil.which(name) or name


def ffmpeg_bin():
    """Path to ffmpeg: bundled with the app, imageio-ffmpeg or the system."""
    path = _find_bin("ffmpeg")
    if path != "ffmpeg":
        return path
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"


def espeak_bin():
    """Path to espeak-ng: bundled with the app or the system."""
    return _find_bin("espeak-ng")


def _espeak_env():
    """Prepare the environment if the app bundles espeak-ng and its data."""
    base = _resource_dir()
    bin_dir = os.path.join(base, "bin")
    data_parent = None
    for parent in (bin_dir, base):
        if os.path.isdir(os.path.join(parent, "espeak-ng-data")):
            data_parent = parent
            break
    if not data_parent and not os.path.isdir(bin_dir):
        return None
    env = dict(os.environ)
    env["ESPEAK_DATA_PATH"] = data_parent or base
    ld = os.environ.get("LD_LIBRARY_PATH", "")
    env["LD_LIBRARY_PATH"] = bin_dir + (":" + ld if ld else "")
    dy = os.environ.get("DYLD_LIBRARY_PATH", "")
    env["DYLD_LIBRARY_PATH"] = bin_dir + (":" + dy if dy else "")
    return env


def _pipe_to_devnull(r):
    return "" if r is None else (r.stdout or "")


def list_voices(engine="edge"):
    """Return the list of available voices for the given engine."""
    if engine == "edge":
        return [{"label": name, "id": vid, "gender": g, "engine": "edge"}
                for name, vid, g in SPANISH_VOICES]
    elif engine == "gtts":
        # gTTS uses language codes, not specific voices
        return [
            {"label": "🌐 Google TTS — Spanish (es)", "id": "es", "gender": "—", "engine": "gtts"},
            {"label": "🌐 Google TTS — Spanish Mexico (es-mx)", "id": "es-mx", "gender": "—", "engine": "gtts"},
            {"label": "🌐 Google TTS — Spanish Spain (es-es)", "id": "es-es", "gender": "—", "engine": "gtts"},
            {"label": "🌐 Google TTS — English US (en)", "id": "en", "gender": "—", "engine": "gtts"},
            {"label": "🌐 Google TTS — English UK (en-uk)", "id": "en-uk", "gender": "—", "engine": "gtts"},
        ]
    elif engine == "robot":
        return [{"label": ROBOT_VOICE, "id": ROBOT_VOICE, "gender": "Robot", "engine": "robot"}]
    return []


def edge_synth(text, voice, rate, pitch, volume, out_path):
    """Synthesize with edge-tts. Returns the path to the final WAV."""
    ext = os.path.splitext(out_path)[1].lower()
    save_mp3 = ext == ".mp3"
    if not save_mp3:
        # work in a temp file and convert to the requested path
        tmp_mp3 = out_path + ".mp3"
    else:
        tmp_mp3 = out_path

    async def _gen():
        com = edge_tts.Communicate(
            text,
            voice=voice,
            rate=f"{rate:+d}%",
            pitch=f"{pitch:+d}Hz",
            volume=f"{volume:+d}%",
        )
        await com.save(tmp_mp3)

    asyncio.run(_gen())

    if save_mp3:
        # the user asked for MP3: leave it as is
        if os.path.exists(out_path + ".raw.wav"):
            os.remove(out_path + ".raw.wav")
        return out_path

    wav = os.path.splitext(out_path)[0] + ".wav"
    _run([ffmpeg_bin(), "-y", "-i", tmp_mp3,
          "-ar", str(SAMPLE_RATE), "-ac", "2", wav])
    if os.path.exists(tmp_mp3):
        os.remove(tmp_mp3)
    return wav


def gtts_synth(text, lang, slow, out_path):
    """Synthesize with gTTS (Google TTS). Returns the path to the final WAV."""
    ext = os.path.splitext(out_path)[1].lower()
    save_mp3 = ext == ".mp3"
    if not save_mp3:
        tmp_mp3 = out_path + ".mp3"
    else:
        tmp_mp3 = out_path

    tts = gTTS(text=text, lang=lang, slow=slow)
    tts.save(tmp_mp3)

    if save_mp3:
        if os.path.exists(out_path + ".raw.wav"):
            os.remove(out_path + ".raw.wav")
        return out_path

    wav = os.path.splitext(out_path)[0] + ".wav"
    _run([ffmpeg_bin(), "-y", "-i", tmp_mp3,
          "-ar", str(SAMPLE_RATE), "-ac", "2", wav])
    if os.path.exists(tmp_mp3):
        os.remove(tmp_mp3)
    return wav


def robot_synth(text, speed, pitch, volume, metal, out_path):
    """Synthesize with espeak-ng + ffmpeg effects in an SCP-079 style."""
    ext = os.path.splitext(out_path)[1].lower()
    final = out_path if ext == ".wav" else out_path + ".wav"
    raw = final + ".raw.wav"
    speed = max(40, min(450, int(speed)))
    pitch = max(1, min(99, int(pitch)))
    metal = max(0.0, min(1.0, float(metal)))

    _run([espeak_bin(), "-v", "es+m1", "-p", str(pitch), "-s", str(speed),
          "-a", "150", "-g", "12", "-w", raw, text], env=_espeak_env())

    factor = 0.72 - 0.30 * metal
    atempo = 1.0 / factor
    chorus_in = 0.5 * (0.2 + 0.8 * metal)
    chorus_st = 0.8 + 0.2 * metal
    chorus_del = 40 + 140 * metal
    chorus_dep = 0.7 * metal
    chorus_fb = 0.4 + 0.5 * metal
    chorus_vol = 0.3 + 0.7 * metal
    acrusher_mix = max(0, 0.45 * metal - 0.15)

    af = (
        f"asetrate=22050*{factor:.4f},aresample=44100,atempo={atempo:.4f},"
        f"acompressor=threshold=-25dB:ratio=8:attack=5:release=140,"
        f"chorus={chorus_in:.3f}:{chorus_st:.3f}:{chorus_del:.1f}:"
        f"{chorus_dep:.3f}:{chorus_fb:.3f}:{chorus_vol:.3f},"
        f"acrusher=bits=10:mode=log:mix={acrusher_mix:.3f},"
        f"volume={volume:+d}dB"
    )
    _run([ffmpeg_bin(), "-y", "-i", raw, "-af", af,
          "-ar", str(SAMPLE_RATE), "-ac", "2", out_path])
    if os.path.exists(raw):
        os.remove(raw)
    return out_path


def get_default_sink():
    r = _run(["pactl", "get-default-sink"])
    return (r.stdout or "").strip() if r.returncode == 0 else ""


# Virtual cable names per system (substring, case-insensitive)
VIRTUAL_DEVICE_HINTS = {
    "win32": ["cable input", "vb-audio", "voicemeeter"],
    "darwin": ["blackhole", "loopback", "soundflower"],
}


def find_virtual_output():
    """Find a virtual output device (VB-CABLE, BlackHole...).

    Returns (index, name) or None. Windows/macOS only; on Linux the virtual
    mic is managed with pactl/PipeWire.
    """
    if sys.platform.startswith("linux"):
        return None
    try:
        import sounddevice as sd
    except Exception:
        return None
    key = "win32" if sys.platform.startswith("win") else "darwin"
    hints = VIRTUAL_DEVICE_HINTS.get(key, [])
    try:
        devices = sd.query_devices()
    except Exception:
        return None
    for idx, dev in enumerate(devices):
        if dev.get("max_output_channels", 0) <= 0:
            continue
        name = str(dev.get("name", ""))
        if any(h in name.lower() for h in hints):
            return idx, name
    return None


class _SdPlayer:
    """sounddevice player with the same interface as subprocess.Popen."""

    def __init__(self, wav_path, device):
        self._stop = threading.Event()
        self._done = threading.Event()
        self.device = device
        self.thread = threading.Thread(target=self._run, args=(wav_path,),
                                       daemon=True)
        self.thread.start()

    def _run(self, wav_path):
        try:
            import sounddevice as sd
            import wave
            with wave.open(wav_path, "rb") as w:
                rate = w.getframerate()
                channels = w.getnchannels()
                width = w.getsampwidth()
                data = w.readframes(w.getnframes())
            dtype = {1: "int8", 2: "int16", 4: "int32"}.get(width, "int16")
            with sd.RawOutputStream(samplerate=rate, channels=channels,
                                    dtype=dtype, device=self.device) as stream:
                chunk = rate * channels * width  # ~1 second
                for i in range(0, len(data), chunk):
                    if self._stop.is_set():
                        break
                    stream.write(data[i:i + chunk])
        except Exception:
            pass
        finally:
            self._done.set()

    def poll(self):
        return 0 if self._done.is_set() else None

    def terminate(self):
        self._stop.set()
        self._done.wait(2)


def play_wav(wav_path):
    """Play the audio.

    Linux: to the virtual microphone and to the speakers, with pw-play.
    Windows/macOS: to the virtual cable (if installed) and to the speakers,
    with sounddevice.
    """
    if sys.platform.startswith("linux"):
        procs = []
        procs.append(subprocess.Popen(
            ["pw-play", "--target=virtual-sink", wav_path],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        sink = get_default_sink()
        if sink:
            procs.append(subprocess.Popen(
                ["pw-play", "--target=" + sink, wav_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        return procs

    players = []
    virtual = find_virtual_output()
    if virtual is not None:
        players.append(_SdPlayer(wav_path, virtual[0]))
    # To the default speakers (so you hear yourself) besides the virtual cable.
    players.append(_SdPlayer(wav_path, None))
    return players


def synthesize(text, engine, args, out_path):
    if engine == "robot":
        return robot_synth(text, args.robot_speed, args.robot_pitch,
                           args.volume, args.robot_metal, out_path)
    elif engine == "gtts":
        return gtts_synth(text, args.lang, args.slow, out_path)
    return edge_synth(text, args.voice, args.rate, args.pitch, args.volume,
                      out_path)


def main():
    ap = argparse.ArgumentParser(description="MultiVoice speech engine")
    ap.add_argument("text", help="Text to speak")
    ap.add_argument("--engine", choices=["edge", "gtts", "robot"], default="edge")
    ap.add_argument("--voice", default="es-MX-JorgeNeural")
    ap.add_argument("--lang", default="es", help="Language code for gTTS (es, en, etc.)")
    ap.add_argument("--slow", action="store_true", help="Slow speech for gTTS")
    ap.add_argument("--rate", type=int, default=0)
    ap.add_argument("--pitch", type=int, default=0)
    ap.add_argument("--volume", type=int, default=0)
    ap.add_argument("--robot-speed", type=int, default=110)
    ap.add_argument("--robot-pitch", type=int, default=15)
    ap.add_argument("--robot-metal", type=float, default=0.7)
    ap.add_argument("--save", default=None, help="Save to a file and exit")
    ap.add_argument("--no-play", action="store_true", help="Do not play")
    args = ap.parse_args()

    out = args.save or os.path.join(os.environ.get("TMPDIR", "/tmp"),
                                    "multivoice_speech.wav")
    wav = synthesize(args.text, args.engine, args, out)
    if not args.no_play and not args.save:
        procs = play_wav(wav)
        for p in procs:
            p.wait()


if __name__ == "__main__":
    main()