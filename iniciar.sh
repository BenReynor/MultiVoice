#!/bin/bash
# Launcher - Iniciar Multivoz (la app crea y elimina el mic virtual)
cd "$(dirname "$0")"

echo "🔊 Iniciando Multivoz..."
python3 tts_multitud.py
