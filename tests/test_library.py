import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import library  # noqa: E402


def _audio(d, name, text, voice):
    (d / name).write_bytes(b"x" * 1536)
    (d / (name + ".json")).write_text(
        json.dumps({"text": text, "voice": voice}), encoding="utf-8")


def test_list_entries_busca_en_texto_y_voz(tmp_path):
    _audio(tmp_path, "voz_a.mp3", "Hola mundo", "Jorge")
    _audio(tmp_path, "voz_b.wav", "Adiós", "Sonido robot")
    (tmp_path / "notas.txt").write_text("no es audio")
    assert len(library.list_entries(str(tmp_path))) == 2
    assert [e["name"] for e in library.list_entries(str(tmp_path), "ROBOT")] == ["voz_b.wav"]
    assert library.list_entries(str(tmp_path), "hola")[0]["voice"] == "Jorge"
    assert library.list_entries(str(tmp_path / "no_existe")) == []


def test_delete_entry_borra_audio_y_sidecar(tmp_path):
    _audio(tmp_path, "voz_a.mp3", "x", "y")
    assert library.delete_entry(str(tmp_path / "voz_a.mp3"))
    assert os.listdir(tmp_path) == []
    (tmp_path / "otro.txt").write_text("a")
    assert not library.delete_entry(str(tmp_path / "otro.txt"))
    assert (tmp_path / "otro.txt").exists()


def test_fmt_size():
    assert library.fmt_size(512) == "512 B"
    assert library.fmt_size(1536) == "1.5 KB"
