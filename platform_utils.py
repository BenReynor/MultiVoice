"""Per-OS paths, fonts and key modifiers (no GUI imports, testable headless)."""
import os
import sys

APP_NAME = "MultiVoice"
IS_MAC = sys.platform == "darwin"
IS_WIN = sys.platform.startswith("win")


def config_dir(frozen=None, source_dir=None):
    """Where config.json lives.

    Running from source: next to the script (keeps existing setups working).
    Packaged (.exe/.app): the per-user config folder, because a PyInstaller
    --onefile app unpacks to a temp folder that is wiped on exit.
    """
    frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    if not frozen:
        return source_dir or os.path.dirname(os.path.abspath(__file__))
    home = os.path.expanduser("~")
    if IS_WIN:
        base = os.environ.get("APPDATA") or os.path.join(
            home, "AppData", "Roaming")
    elif IS_MAC:
        base = os.path.join(home, "Library", "Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
            home, ".config")
    return os.path.join(base, APP_NAME)


def default_library_dir(platform=None, home=None):
    """Default audio library: Documents on Windows/macOS, ~ on Linux."""
    platform = platform or sys.platform
    home = home or os.path.expanduser("~")
    name = "MultiVoice_Audio"
    if platform.startswith("win") or platform == "darwin":
        docs = os.path.join(home, "Documents")
        return os.path.join(docs if os.path.isdir(docs) else home, name)
    return os.path.join(home, name)


UI_FONT = "Segoe UI" if IS_WIN else "Helvetica Neue" if IS_MAC else "Ubuntu"
TEXT_FONT = "Arial"

# Tk key modifier and the label shown in the shortcuts list
MOD = "Command" if IS_MAC else "Control"
MOD_LABEL = "⌘" if IS_MAC else "Ctrl"
