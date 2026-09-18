#!/bin/bash
# Crea el acceso directo "TTS Multitud" en el menú de aplicaciones y en el escritorio.
# Este script genera el .desktop con las rutas de tu copia del repositorio.
set -e

REPO="$(cd "$(dirname "$0")" && pwd)"
APP="tts-multitud"

ICON_DIR="$HOME/.local/share/icons"
APP_DIR="$HOME/.local/share/applications"
mkdir -p "$ICON_DIR" "$APP_DIR"
cp "$REPO/assets/icon.png" "$ICON_DIR/$APP.png"

cat > "$APP_DIR/$APP.desktop" <<EOF
[Desktop Entry]
Name=TTS Multitud
Comment=Hablar por micrófono virtual
Exec=bash -c "$REPO/iniciar.sh"
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
    echo "✅ Acceso directo creado en el escritorio: $DESK/$APP.desktop"
    break
  fi
done

update-desktop-database "$APP_DIR" 2>/dev/null || true
echo "✅ TTS Multitud accesible desde el buscador de aplicaciones."