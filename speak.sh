#!/bin/bash
# Speak through the virtual microphone + headphones (edge-tts / robot engine)
# Usage: ./speak.sh "text to speak" [--engine robot] [--voice ID] [--rate N]
#                       [--pitch N] [--volume N] [--save file]
cd "$(dirname "$0")"

text="$1"
shift
if [ -z "$text" ]; then
    echo "Usage: ./speak.sh \"text to speak\" [engine options]"
    exit 1
fi

python3 tts_engine.py "$text" "$@"