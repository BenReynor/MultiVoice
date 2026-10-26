"""Headless tests: the library cleanup must never delete what it doesn't own."""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import library  # noqa: E402
import virtualmic  # noqa: E402

DAY = 86400


def touch(path, age_days):
    with open(path, "w") as f:
        f.write("x")
    t = time.time() - age_days * DAY
    os.utime(path, (t, t))


def test_cleanup_only_removes_old_app_files():
    with tempfile.TemporaryDirectory() as d:
        old_owned = ["voz_old.mp3", "voz_old.mp3.json", "voz_old2.wav",
                     "voz_old2.wav.json"]
        keep = ["voz_new.mp3", "voz_new.mp3.json",       # recent
                "musica.mp3", "old_song.wav", "notes.json",  # not ours
                "VOZ.txt", "voz_old.txt", "config.json"]
        for n in old_owned:
            touch(os.path.join(d, n), 90)
        for n in keep:
            touch(os.path.join(d, n), 90 if "new" not in n else 1)
        os.mkdir(os.path.join(d, "voz_dir.mp3"))
        outside = os.path.join(d, "outside_target.mp3")
        touch(outside, 90)
        os.symlink(outside, os.path.join(d, "voz_link.mp3"))

        removed = library.cleanup_library(d, days=30)

        assert removed == len(old_owned), removed
        left = set(os.listdir(d))
        for n in old_owned:
            assert n not in left, n
        for n in keep + ["voz_dir.mp3", "voz_link.mp3", "outside_target.mp3"]:
            assert n in left, f"{n} was deleted!"


def test_cleanup_missing_dir():
    assert library.cleanup_library("/nonexistent/multivoice") == 0


def test_find_module_ids_only_matches_own_modules():
    listing = (
        "5\tmodule-null-sink\tsink_name=virtual-sink sink_properties=x\n"
        "6\tmodule-remap-source\tsource_name=virtual-mic master=virtual-sink.monitor\n"
        "7\tmodule-null-sink\tsink_name=obs_sink\n"
        "8\tmodule-loopback\tsource=foo sink=bar\n"
        "9\tmodule-always-sink\t\n")
    ids = virtualmic.find_module_ids(
        listing, ("sink_name=virtual-sink", "source_name=virtual-mic"))
    assert ids == ["5", "6"], ids


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print(f"{name} OK")
