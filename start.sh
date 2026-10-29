#!/bin/bash
# Launcher - Start MultiVoice (the app creates and removes the virtual mic).
#
# Runs from source with the project's own .venv, so the shortcut always opens
# the current version. The .venv is created when missing and its dependencies
# are re-synced whenever requirements.txt changes (uv if available, else pip),
# with a waiting window meanwhile. The system python3 is not used directly: it
# lacks the app's dependencies (customtkinter…).
cd "$(dirname "$0")" || exit 1
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"

VENV=".venv"
PY="$VENV/bin/python"
STAMP="$VENV/.requirements.sha1"
LOG="${XDG_CACHE_HOME:-$HOME/.cache}/multivoice/instalar.log"
mkdir -p "$(dirname "$LOG")"
QUIERO="$(sha1sum requirements.txt | cut -d' ' -f1)"

# Progress for the waiting window, on fd 3: a percentage and "# step" lines
# (zenity --progress format); the commands' own output goes to the log.
avance() { printf '%s\n# %s\n' "$1" "$2" >&3; }

preparar() {
    echo "== $(date '+%F %T') preparando el entorno"
    avance 5 "Comprobando el entorno…"
    if command -v uv >/dev/null 2>&1; then
        if [ ! -x "$PY" ]; then
            avance 10 "Creando el entorno de Python…"
            # The system Python ships Tk (python3-tk); uv's own builds may not.
            if [ -x /usr/bin/python3 ]; then
                uv venv --python /usr/bin/python3 "$VENV" || return 1
            else
                uv venv "$VENV" || return 1
            fi
        fi
        avance 30 "Instalando dependencias (voces, interfaz)…"
        uv pip install --python "$PY" -r requirements.txt || return 1
    else
        avance 10 "Creando el entorno de Python…"
        [ -x "$PY" ] || python3 -m venv "$VENV" || return 1
        avance 30 "Instalando dependencias (voces, interfaz)…"
        "$PY" -m pip install -r requirements.txt || return 1
    fi
    avance 95 "Terminando…"
    echo "$QUIERO" > "$STAMP"
    echo "== listo"
}

hay_pantalla() {
    command -v zenity >/dev/null 2>&1 && [ -n "${DISPLAY:-}${WAYLAND_DISPLAY:-}" ]
}

if [ ! -x "$PY" ] || [ "$(cat "$STAMP" 2>/dev/null)" != "$QUIERO" ]; then
    RC_FILE="$(mktemp)"
    if hay_pantalla; then
        { preparar 3>&1 >>"$LOG" 2>&1; echo $? > "$RC_FILE"; echo 100; } |
            zenity --progress --auto-close --no-cancel --title="MultiVoice — actualizando" \
                --width=420 --text="Preparando MultiVoice (solo la primera vez o tras una actualización)…" 2>/dev/null
    else
        echo "🔧 Preparando el entorno de MultiVoice…"
        preparar 3>/dev/null >>"$LOG" 2>&1; echo $? > "$RC_FILE"
    fi
    rc="$(cat "$RC_FILE")"; rm -f "$RC_FILE"
    if [ "$rc" != "0" ]; then
        msg="No se pudieron instalar las dependencias de MultiVoice. Detalle en $LOG"
        if hay_pantalla; then
            zenity --error --title=MultiVoice --text="$msg" 2>/dev/null
        else
            echo "$msg"
        fi
        exit 1
    fi
fi

# Keep the shortcut's icon in step with the program (installed by install.sh).
ICONO="$HOME/.local/share/icons/hicolor/512x512/apps/multivoice.png"
if [ -f "$ICONO" ] && ! cmp -s assets/icon.png "$ICONO"; then
    cp assets/icon.png "$ICONO"
    gtk-update-icon-cache -q -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo "🔊 Starting MultiVoice..."
exec "$PY" multivoice.py "$@"
