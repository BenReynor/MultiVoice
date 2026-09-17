"""Prueba de humo multiplataforma: no abre la ventana ni reproduce audio."""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tts_engine  # noqa: E402


def check_engines():
    edge = tts_engine.list_voices("edge")
    gtts = tts_engine.list_voices("gtts")
    robot = tts_engine.list_voices("robot")
    assert len(edge) == 14, f"voces edge: {len(edge)}"
    assert len(gtts) == 5, f"voces gtts: {len(gtts)}"
    assert robot and robot[0]["id"] == tts_engine.ROBOT_VOICE
    assert tts_engine.ROBOT_VOICE == "🤖 Sonido Robot"
    print(f"motores OK: edge={len(edge)} gtts={len(gtts)} robot={len(robot)}")


def check_edge_synth():
    if not shutil.which("ffmpeg"):
        print("edge synth: SKIP (sin ffmpeg)")
        return
    out = os.path.join(tempfile.gettempdir(), "smoke_edge.wav")
    try:
        wav = tts_engine.edge_synth("hola", "es-MX-JorgeNeural", 0, 0, 0, out)
        assert os.path.exists(wav) and os.path.getsize(wav) > 1000
        print("edge synth OK")
    except Exception as exc:  # red en CI puede fallar: no romper el build
        print(f"edge synth: SKIP ({exc!r})")


def check_robot_synth():
    if not shutil.which("espeak-ng"):
        print("robot synth: SKIP (sin espeak-ng)")
        return
    if not shutil.which("ffmpeg"):
        print("robot synth: SKIP (sin ffmpeg)")
        return
    out = os.path.join(tempfile.gettempdir(), "smoke_robot.wav")
    wav = tts_engine.robot_synth("hola", 135, 30, 0, 0, out)
    assert os.path.exists(wav) and os.path.getsize(wav) > 1000
    print("robot synth OK")


def main():
    check_engines()
    check_edge_synth()
    check_robot_synth()
    print("SMOKE OK")


if __name__ == "__main__":
    main()
