"""Virtual microphone (PulseAudio/PipeWire, Linux only)."""
import subprocess
import sys

MIC_SINK = "virtual-sink"
MIC_SOURCE = "virtual-mic"
MIC_DESCRIPTION = "🎤"


def _pactl(*args):
    return subprocess.run(["pactl", *args], stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL, text=True)


def find_module_ids(listing, needles):
    """Ids from `pactl list short modules` whose arguments contain a needle."""
    ids = []
    for line in listing.splitlines():
        parts = line.split("\t")
        if len(parts) >= 3 and parts[0].isdigit() \
                and any(n in parts[2] for n in needles):
            ids.append(parts[0])
    return ids


def setup_virtual_mic():
    """Load the virtual microphone. Returns the loaded module ids.

    Linux only. Only removes leftovers of its own sink/source (from a crashed
    previous run), never modules that belong to other applications.
    """
    if not sys.platform.startswith("linux"):
        return []
    try:
        stale = find_module_ids(
            _pactl("list", "short", "modules").stdout or "",
            (f"sink_name={MIC_SINK}", f"source_name={MIC_SOURCE}"))
        for i in stale:
            _pactl("unload-module", i)
        ids = []
        r = _pactl("load-module", "module-null-sink",
                   f"sink_name={MIC_SINK}",
                   "sink_properties=device.master_volume=1.0,sink_dont_move=yes",
                   "sample_spec=s16le=2ch=48000Hz")
        if r.returncode == 0:
            ids.append(r.stdout.strip())
        r = _pactl("load-module", "module-remap-source",
                   f"source_name={MIC_SOURCE}",
                   f"master={MIC_SINK}.monitor",
                   f"source_properties=device.description={MIC_DESCRIPTION}")
        if r.returncode == 0:
            ids.append(r.stdout.strip())
        return ids
    except FileNotFoundError:  # pactl not installed
        return []


def teardown_virtual_mic(ids):
    """Unload the modules the app loaded (the source first, then the sink)."""
    try:
        for i in reversed(ids):
            _pactl("unload-module", str(i))
    except FileNotFoundError:
        pass
