<div align="center">

# TTS Multitud

**Convierte texto en voz y habla por un micrófono virtual en Discord y otras apps**

Escríbelo en la ventana, pulsa Hablar y tu audiencia te oye con la voz elegida.

</div>

## Instalación

### Opción 1: binario ya compilado (Windows, macOS y Linux)

Descarga el archivo de tu sistema desde [Releases](https://github.com/BenReynor/tts-multitud/releases) (la última versión: `v1.1.0`), descomprímelo y ábrelo. Hay un `.zip` por sistema:

- `tts-multitud-linux-x86_64.zip` → Linux en procesador Intel/AMD (la mayoría)
- `tts-multitud-linux-arm64.zip` → Linux en ARM (Raspberry Pi, muchos ARM)
- `tts-multitud-windows-x64.zip` → Windows
- `tts-multitud-macos-arm64.zip` → macOS en Apple Silicon (M1/M2/M3/M4)
- `tts-multitud-macos-intel.zip` → macOS en procesador Intel

Si no sabes cuál es tu macOS, *Apple  →  Acerca de este Mac*; si no pone "Apple", es Intel.

El `.zip` se descarga en la carpeta **Descargas** del navegador y, al descomprimirlo, se crea la carpeta `tts-multitud-<SO>` donde elijas. No se instala nada ni se crean accesos directos: el ejecutable corre desde donde lo descomprimas y lo puedes mover a donde quieras.

- **Linux:** dale permisos y ejecútalo. Solo necesita `pactl`/`pw-play` (PipeWire) para crear el micrófono virtual; `ffmpeg` y `espeak-ng` ya van incluidos.
  ```bash
  chmod +x tts-multitud && ./tts-multitud
  ```
- **Windows:** ejecútalo; si sale SmartScreen, *Más información → Ejecutar de todas formas*.
- **macOS:** ábrelo; si Gatekeeper lo bloquea, clic derecho → *Abrir*, o `xattr -dr com.apple.quarantine tts-multitud.app`.

El binario incluye Python, las librerías de voz, `ffmpeg` y `espeak-ng`. No incluye el cable de audio virtual de Windows/macOS, que debe instalarse aparte (ver abajo).

### Opción 2: desde el código

Requiere Python 3.8+ y los paquetes del sistema `ffmpeg`, `espeak-ng` y `python3-tk`.

```bash
git clone https://github.com/BenReynor/tts-multitud.git
cd tts-multitud
python3 -m pip install -r requirements.txt
```

Para crear el acceso directo (con el icono de la app) en el menú de aplicaciones y en el escritorio:

```bash
./instalar_acceso.sh
```

En Debian/Ubuntu, para las dependencias del sistema:

```bash
sudo apt install ffmpeg espeak-ng python3-tk
```

## Inicio rápido

- **Binario descargado:** abre `tts-multitud` (Linux/macOS) o `tts-multitud.exe` (Windows).
- **Desde el código:**

```bash
./iniciar.sh
```

En Linux la app crea el micrófono virtual `🎤` al abrirse y lo elimina al cerrarla. En la app donde quieras hablar, selecciónalo como dispositivo de entrada:

- Discord: Ajustes → Voz y vídeo → Dispositivo de entrada → `🎤`
- Cualquier otra aplicación que permita elegir micrófono funciona igual.

Escribe un texto, pulsa **🔊 Hablar** y la voz se escucha en tu auricular y a través del mic virtual.

## Micrófono virtual en Windows y macOS

Ahí la app no puede crear el micrófono sola: necesita un cable de audio virtual del sistema. La app lo detecta y reproduce en él automáticamente; solo tienes que seleccionar la entrada en Discord.

1. **Instala el cable (una vez):**
   - **macOS:** [BlackHole](https://existential.audio/blackhole/) (`brew install --cask blackhole-2ch`).
   - **Windows:** [VB-CABLE](https://vb-audio.com/Cable/) (instalador, requiere permisos de administrador).
2. **Elige la entrada en Discord:** Ajustes → Voz y vídeo → Dispositivo de entrada → `BlackHole 2ch` (macOS) o `CABLE Output` (Windows).

### Escucharte a ti mismo

El cable virtual manda el audio a Discord, pero no a tus altavoces; para oírte necesitas duplicar la salida:

- **macOS:** en *Audio MIDI Setup* crea un **dispositivo de salida múltiple** con tus altavoces + BlackHole y selecciónalo como salida del sistema.
- **Windows:** en *Sonido → Grabación → CABLE Output → Propiedades → Escuchar* marca **Escuchar este dispositivo** y elige tus altavoces.

### Si algo no suena

- Deja la app abierta; en Windows/macOS solo reproduce mientras se ejecuta.
- En Windows, si en Discord se oye muy bajo, prueba a `Discord → Ajustes → Voz y vídeo → Desactivar el procesamiento de audio` y ajusta el volumen de entrada.
- Si no detecta el cable, la app reproduce por el altavoz y lo avisa al abrirse.

> Verificado en Linux; el ruteo a BlackHole/VB-CABLE está probado en la integración automática, pero no en hardware real de Windows/macOS.

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
- En Windows y macOS la app usa el cable virtual del sistema (BlackHole o VB-CABLE) si lo tienes instalado; si no, reproduce por el altavoz.
- Edge TTS y Google TTS necesitan internet. El robot funciona sin conexión y usa `espeak-ng`; en los binarios ya va incluido (desde el código necesitas tenerlo instalado).

## Licencia

Uso personal. Sin licencia pública.