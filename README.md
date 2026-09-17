<div align="center">

# TTS Multitud

**Convierte texto en voz y habla por un micrófono virtual en Discord y otras apps**

Escríbelo en la ventana, pulsa Hablar y tu audiencia te oye con la voz elegida.

</div>

## Instalación

### Opción 1: binario ya compilado (Windows, macOS y Linux)

Descarga el archivo de tu sistema desde [Releases](https://github.com/BenReynor/tts-multitud/releases), descomprímelo y ábrelo.

### Opción 2: desde el código

Requiere Python 3.8+ y los paquetes del sistema `ffmpeg`, `espeak-ng` y `python3-tk`.

```bash
python3 -m pip install -r requirements.txt
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

En Linux la app crea el micrófono virtual `🎤` al abrirse y lo elimina al cerrarla. En la app donde quieras hablar, selecciónalo como dispositivo de entrada:

- Discord: Ajustes → Voz y vídeo → Dispositivo de entrada → `🎤`
- Cualquier otra aplicación que permita elegir micrófono funciona igual.

Escribe un texto, pulsa **🔊 Hablar** y la voz se escucha en tu auricular y a través del mic virtual.

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

- El mic virtual `🎤` solo existe en Linux y mientras la app está abierta; si quieres elegirlo en Discord, ten la app abierta.
- En Windows y macOS la voz suena por el altavoz predeterminado (no crea micrófono virtual); para meterla en Discord ahí necesitas un cable virtual de audio del sistema.
- Edge TTS y Google TTS necesitan internet. El robot funciona sin conexión y necesita `espeak-ng` y `ffmpeg` instalados.

## Licencia

Uso personal. Sin licencia pública.