"""Audio library helpers (no GUI imports, so they can be tested headless)."""
import os
import time

# Files created by the app's auto-save: voz_<timestamp>.mp3|wav + .json sidecar
OWNED_PREFIX = "voz_"
OWNED_SUFFIXES = (".mp3", ".wav", ".mp3.json", ".wav.json")


def is_app_file(name):
    """True only for files the app itself creates in the library folder."""
    low = name.lower()
    return low.startswith(OWNED_PREFIX) and low.endswith(OWNED_SUFFIXES)


def cleanup_library(lib_dir, days=30, now=None):
    """Delete app-created audio (and sidecars) older than `days`.

    Never touches files the app did not create, symlinks or subfolders.
    Returns the number of files removed.
    """
    if not os.path.isdir(lib_dir):
        return 0
    cutoff = (time.time() if now is None else now) - days * 86400
    deleted = 0
    with os.scandir(lib_dir) as it:
        for entry in it:
            try:
                if (not is_app_file(entry.name) or entry.is_symlink()
                        or not entry.is_file(follow_symlinks=False)):
                    continue
                if entry.stat(follow_symlinks=False).st_mtime < cutoff:
                    os.remove(entry.path)
                    deleted += 1
            except OSError:
                pass
    return deleted
