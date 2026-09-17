#!/bin/bash
# Iniciar TTS Multitud (sin terminal)
cd "$(dirname "$0")"
./iniciar_mic.sh
python3 tts_multitud.py
