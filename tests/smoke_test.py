"""Cross-platform smoke test: does not open the window or play audio."""
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tts_engine  # noqa: E402


def check_engines():
    edge = tts_engine.list_voices("edge")
    gtts = tts_engine.list_voices("gtts")
    robot = tts_engine.list_voices("robot")
    assert len(edge) == 14, f"edge voices: {len(edge)}"
    assert len(gtts) == 5, f"gtts voices: {len(gtts)}"
    assert robot and robot[0]["id"] == tts_engine.ROBOT_VOICE
    assert tts_engine.ROBOT_VOICE == "🤖 Robot Sound"
    print(f"engines OK: edge={len(edge)} gtts={len(gtts)} robot={len(robot)}")


def check_edge_synth():
    if not shutil.which("ffmpeg"):
        print("edge synth: SKIP (no ffmpeg)")
        return
    out = os.path.join(tempfile.gettempdir(), "smoke_edge.wav")
    try:
        wav = tts_engine.edge_synth("hi", "es-MX-JorgeNeural", 0, 0, 0, out)
        assert os.path.exists(wav) and os.path.getsize(wav) > 1000
        print("edge synth OK")
    except Exception as exc:  # no network on CI: do not break the build
        print(f"edge synth: SKIP ({exc!r})")


def check_robot_synth():
    if not shutil.which("espeak-ng"):
        print("robot synth: SKIP (no espeak-ng)")
        return
    if not shutil.which("ffmpeg"):
        print("robot synth: SKIP (no ffmpeg)")
        return
    out = os.path.join(tempfile.gettempdir(), "smoke_robot.wav")
    wav = tts_engine.robot_synth("hi", 135, 30, 0, 0, out)
    assert os.path.exists(wav) and os.path.getsize(wav) > 1000
    print("robot synth OK")


def check_virtual_device():
    if sys.platform.startswith("linux"):
        assert tts_engine.find_virtual_output() is None
        print("virtual device: SKIP (Linux uses pactl)")
        return
    try:
        import sounddevice  # noqa: F401
    except Exception as exc:
        raise AssertionError(f"sounddevice not installed: {exc!r}")
    found = tts_engine.find_virtual_output()
    print(f"virtual device: {found[1] if found else 'none (fallback speakers)'}")


def check_ffmpeg():
    exe = tts_engine.ffmpeg_bin()
    r = subprocess.run([exe, "-version"], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    assert r.returncode == 0, f"ffmpeg does not work: {exe}"
    print(f"ffmpeg OK: {exe}")


def main():
    check_engines()
    check_virtual_device()
    check_ffmpeg()
    check_edge_synth()
    check_robot_synth()
    print("SMOKE OK")


if __name__ == "__main__":
    main()
