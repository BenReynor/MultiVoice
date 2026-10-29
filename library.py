"""Audio library helpers (no GUI imports, so they can be tested headless)."""
import json
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


AUDIO_SUFFIXES = (".mp3", ".wav")


def fmt_size(n):
    """Tamaño legible: 512 B, 1.5 KB, 2.0 MB…"""
    n = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} B" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def list_entries(lib_dir, query=""):
    """Audios de la biblioteca, del más nuevo al más viejo.

    Cada entrada: path, name, text, voice, engine, mtime, size. `query` filtra
    (sin distinguir mayúsculas) por texto, voz o nombre de archivo.
    """
    if not os.path.isdir(lib_dir):
        return []
    q = query.strip().lower()
    out = []
    with os.scandir(lib_dir) as it:
        for e in it:
            try:
                if (not e.name.lower().endswith(AUDIO_SUFFIXES)
                        or not e.is_file(follow_symlinks=False)):
                    continue
                st = e.stat(follow_symlinks=False)
            except OSError:
                continue
            meta = {}
            try:
                with open(e.path + ".json", encoding="utf-8") as f:
                    meta = json.load(f)
            except (OSError, ValueError):
                pass
            if not isinstance(meta, dict):
                meta = {}
            item = {"path": e.path, "name": e.name,
                    "text": str(meta.get("text", "")),
                    "voice": str(meta.get("voice", "")),
                    "engine": str(meta.get("engine", "")),
                    "mtime": st.st_mtime, "size": st.st_size}
            hay = f"{item['text']} {item['voice']} {item['name']}".lower()
            if q and q not in hay:
                continue
            out.append(item)
    out.sort(key=lambda x: x["mtime"], reverse=True)
    return out


def delete_entry(path):
    """Borra un audio y su .json. Devuelve True si se borró el audio."""
    if not path.lower().endswith(AUDIO_SUFFIXES):
        return False
    os.remove(path)
    if os.path.isfile(path + ".json"):
        os.remove(path + ".json")
    return True
