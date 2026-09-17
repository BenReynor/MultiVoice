#!/bin/bash
# Launcher - Iniciar TTS Multitud
cd "$(dirname "$0")"

echo "🎤 Iniciando micrófono virtual..."
./iniciar_mic.sh

echo "🔊 Iniciando TTS Multitud..."
python3 tts_multitud.py &
