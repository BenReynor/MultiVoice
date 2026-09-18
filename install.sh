#!/bin/bash
# Create the "MultiVoice" launcher in the applications menu and on the desktop.
# This script generates the .desktop file with the paths of your repo copy.
set -e

REPO="$(cd "$(dirname "$0")" && pwd)"
APP="multivoice"

ICON_DIR="$HOME/.local/share/icons"
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$ICON_DIR" "$APP_DIR"
cp "$REPO/assets/icon.png" "$ICON_DIR/$APP.png"

cat > "$APP_DIR/$APP.desktop" <<EOF
[Desktop Entry]
Name=MultiVoice
Comment=Speak through a virtual microphone
Exec=bash -c "$REPO/start.sh"
Icon=$ICON_DIR/$APP.png
Terminal=false
Type=Application
Categories=AudioVideo;Audio;
EOF
chmod +x "$APP_DIR/$APP.desktop"

for DESK in "$(xdg-user-dir DESKTOP 2>/dev/null)" "$HOME/Escritorio" "$HOME/Desktop"; do
  if [ -n "$DESK" ] && [ -d "$DESK" ]; then
    cp "$APP_DIR/$APP.desktop" "$DESK/$APP.desktop"
    chmod +x "$DESK/$APP.desktop"
    echo "✅ Launcher created on the desktop: $DESK/$APP.desktop"
    break
  fi
done

update-desktop-database "$APP_DIR" 2>/dev/null || true
echo "✅ MultiVoice is reachable from the app launcher."