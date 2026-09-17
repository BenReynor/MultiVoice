<div align="center">

# TTS Multitud

**Convierte texto en voz y habla por un micrófono virtual en Discord y otras apps**

Escríbelo en la ventana, pulsa Hablar y tu audiencia te oye con la voz elegida.

</div>

## Instalación

Requiere Linux con PipeWire/PulseAudio, Python 3.8+ y los paquetes del sistema `ffmpeg`, `espeak-ng` y `python3-tk`.

```bash
python3 -m pip install edge-tts gTTS
```

En Debian/Ubuntu, para las dependencias del sistema:

```bash
sudo apt install ffmpeg espeak-ng python3-tk
```

## Inicio rápido

Abre la app:

```bash
./iniciar.sh
```

La app crea el micrófono virtual `🎤` al abrirse y lo elimina al cerrarla. En la app donde quieras hablar, selecciónalo como dispositivo de entrada:

- Discord: Ajustes → Voz y vídeo → Dispositivo de entrada → `🎤`
- Cualquier otra aplicación que permita elegir micrófono funciona igual.

Escribe un texto, pulsa **🔊 Hablar** y la voz se escucha en tu audiífono y a través del mic virtual.

## Qué puedes hacer

- **Tres motores TTS:** voces neuronales de Microsoft Edge (14 voces en español, internet), Google TTS (gTTS, internet) y sonido robot local (espeak-ng, sin internet).
- **Sonido robot:** simula la voz robótica del SCP-079, con control de metal (distorsión), velocidad, tono y volumen.
- **Múltiples pestañas:** prepara varios textos y reprodúcelos en cola, con auto-limpieza opcional.
- **Guardar audio:** exporta la voz a MP3 o WAV desde el botón Guardar.

## Atajos de teclado

| Atajo | Acción |
|-------|--------|
| Ctrl+Enter | Hablar la pestaña actual |
| Ctrl+T | Nueva pestaña |
| Ctrl+W | Cerrar pestaña |
| F5 | Probar la voz seleccionada |

## Notas

- El mic virtual solo existe mientras la app está abierta; si quieres elegirlo en Discord, ten la app abierta.
- Edge TTS y Google TTS necesitan internet. El robot funciona sin conexión.
- Es un proyecto local de Linux; no funciona en Windows ni macOS.

## Licencia

Uso personal. Sin licencia pública.