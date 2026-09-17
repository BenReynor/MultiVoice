#!/bin/bash
# Launcher - Iniciar TTS Multitud (la app crea y elimina el mic virtual)
cd "$(dirname "$0")"

echo "🔊 Iniciando TTS Multitud..."
python3 tts_multitud.py
