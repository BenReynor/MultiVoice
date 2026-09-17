#!/usr/bin/env python3
# Motor TTS: edge-tts, gTTS, robot (espeak-ng)
# Uso:
#   python3 tts_engine.py "texto" [--engine edge|gtts|robot] [--voice ID]
#       [--rate N] [--pitch N] [--volume N] [--lang CODE]
#       [--robot-speed N] [--robot-pitch N] [--robot-metal N]
#       [--save FILE] [--no-play]
import argparse
import asyncio
import os
import subprocess

import edge_tts
from gtts import gTTS

ROBOT_VOICE = "🤖 Sonido Robot"
SAMPLE_RATE = 48000

# Voces en español conocidas de edge-tts (nombre amigable, id, género)
# Subconjunto reducido: países principales
SPANISH_VOICES = [
    ("Alvaro — España (M)", "es-ES-AlvaroNeural", "Male"),
    ("Elvira — España (F)", "es-ES-ElviraNeural", "Female"),
    ("Elena — Argentina (F)", "es-AR-ElenaNeural", "Female"),
    ("Tomas — Argentina (M)", "es-AR-TomasNeural", "Male"),
    ("Catalina — Chile (F)", "es-CL-CatalinaNeural", "Female"),
    ("Lorenzo — Chile (M)", "es-CL-LorenzoNeural", "Male"),
    ("Gonzalo — Colombia (M)", "es-CO-GonzaloNeural", "Male"),
    ("Salome — Colombia (F)", "es-CO-SalomeNeural", "Female"),
    ("Dalia — México (F)", "es-MX-DaliaNeural", "Female"),
    ("Jorge — México (M)", "es-MX-JorgeNeural", "Male"),
    ("Alex — Perú (M)", "es-PE-AlexNeural", "Male"),
    ("Camila — Perú (F)", "es-PE-CamilaNeural", "Female"),
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


def _pipe_to_devnull(r):
    return "" if r is None else (r.stdout or "")


def list_voices(engine="edge"):
    """Devuelve lista de voces disponibles para el motor especificado."""
    if engine == "edge":
        return [{"label": name, "id": vid, "gender": g, "engine": "edge"}
                for name, vid, g in SPANISH_VOICES]
    elif engine == "gtts":
        # gTTS usa códigos de idioma, no voces específicas
        return [
            {"label": "🌐 Google TTS — Español (es)", "id": "es", "gender": "—", "engine": "gtts"},
            {"label": "🌐 Google TTS — Español México (es-mx)", "id": "es-mx", "gender": "—", "engine": "gtts"},
            {"label": "🌐 Google TTS — Español España (es-es)", "id": "es-es", "gender": "—", "engine": "gtts"},
            {"label": "🌐 Google TTS — Inglés US (en)", "id": "en", "gender": "—", "engine": "gtts"},
            {"label": "🌐 Google TTS — Inglés UK (en-uk)", "id": "en-uk", "gender": "—", "engine": "gtts"},
        ]
    elif engine == "robot":
        return [{"label": ROBOT_VOICE, "id": ROBOT_VOICE, "gender": "Robot", "engine": "robot"}]
    return []


def edge_synth(text, voice, rate, pitch, volume, out_path):
    """Sintetiza con edge-tts. Devuelve la ruta del WAV final."""
    ext = os.path.splitext(out_path)[1].lower()
    save_mp3 = ext == ".mp3"
    if not save_mp3:
        # trabajo en temporal y convierto a la ruta pedida
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
        # el usuario pidió MP3: queda tal cual
        if os.path.exists(out_path + ".raw.wav"):
            os.remove(out_path + ".raw.wav")
        return out_path

    wav = os.path.splitext(out_path)[0] + ".wav"
    _run(["ffmpeg", "-y", "-i", tmp_mp3,
          "-ar", str(SAMPLE_RATE), "-ac", "2", wav])
    if os.path.exists(tmp_mp3):
        os.remove(tmp_mp3)
    return wav


def gtts_synth(text, lang, slow, out_path):
    """Sintetiza con gTTS (Google TTS). Devuelve la ruta del WAV final."""
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
    _run(["ffmpeg", "-y", "-i", tmp_mp3,
          "-ar", str(SAMPLE_RATE), "-ac", "2", wav])
    if os.path.exists(tmp_mp3):
        os.remove(tmp_mp3)
    return wav


def robot_synth(text, speed, pitch, volume, metal, out_path):
    """Sintetiza con espeak-ng + efectos ffmpeg estilo SCP-079."""
    ext = os.path.splitext(out_path)[1].lower()
    final = out_path if ext == ".wav" else out_path + ".wav"
    raw = final + ".raw.wav"
    speed = max(40, min(450, int(speed)))
    pitch = max(1, min(99, int(pitch)))
    metal = max(0.0, min(1.0, float(metal)))

    _run(["espeak-ng", "-v", "es+m1", "-p", str(pitch), "-s", str(speed),
          "-a", "150", "-g", "12", "-w", raw, text])

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
    _run(["ffmpeg", "-y", "-i", raw, "-af", af,
          "-ar", str(SAMPLE_RATE), "-ac", "2", out_path])
    if os.path.exists(raw):
        os.remove(raw)
    return out_path


def get_default_sink():
    r = _run(["pactl", "get-default-sink"])
    return (r.stdout or "").strip() if r.returncode == 0 else ""


def play_wav(wav_path):
    """Reproduce en el micrófono virtual y en los audífonos."""
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


def synthesize(text, engine, args, out_path):
    if engine == "robot":
        return robot_synth(text, args.robot_speed, args.robot_pitch,
                           args.volume, args.robot_metal, out_path)
    elif engine == "gtts":
        return gtts_synth(text, args.lang, args.slow, out_path)
    return edge_synth(text, args.voice, args.rate, args.pitch, args.volume,
                      out_path)


def main():
    ap = argparse.ArgumentParser(description="Motor TTS multitud")
    ap.add_argument("text", help="Texto a decir")
    ap.add_argument("--engine", choices=["edge", "gtts", "robot"], default="edge")
    ap.add_argument("--voice", default="es-MX-JorgeNeural")
    ap.add_argument("--lang", default="es", help="Código de idioma para gTTS (es, en, etc.)")
    ap.add_argument("--slow", action="store_true", help="Voz lenta para gTTS")
    ap.add_argument("--rate", type=int, default=0)
    ap.add_argument("--pitch", type=int, default=0)
    ap.add_argument("--volume", type=int, default=0)
    ap.add_argument("--robot-speed", type=int, default=110)
    ap.add_argument("--robot-pitch", type=int, default=15)
    ap.add_argument("--robot-metal", type=float, default=0.7)
    ap.add_argument("--save", default=None, help="Guardar a archivo y salir")
    ap.add_argument("--no-play", action="store_true", help="No reproducir")
    args = ap.parse_args()

    out = args.save or os.path.join(os.environ.get("TMPDIR", "/tmp"),
                                    "tts_speech.wav")
    wav = synthesize(args.text, args.engine, args, out)
    if not args.no_play and not args.save:
        procs = play_wav(wav)
        for p in procs:
            p.wait()


if __name__ == "__main__":
    main()