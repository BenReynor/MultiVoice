#!/bin/bash
# Hablar por micrófono virtual + audífonos (Motor edge-tts / robot)
# Uso: ./hablar.sh "texto a decir" [--engine robot] [--voice ID] [--rate N]
#                          [--pitch N] [--volume N] [--save archivo]
cd "$(dirname "$0")"

texto="$1"
shift
if [ -z "$texto" ]; then
    echo "Uso: ./hablar.sh \"texto a decir\" [opciones del motor]"
    exit 1
fi

python3 tts_engine.py "$texto" "$@"