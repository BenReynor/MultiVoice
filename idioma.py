"""Idiomas de la interfaz: texto fuente en inglés, catálogo español opcional.

`t("Speak")` devuelve el texto tal cual en inglés y su traducción en español
si el idioma es «es» y la entrada está en `_ES`. Si falta, se muestra el
inglés. Los placeholders `{nombre}` se rellenan con str.format.

El idioma se fija con `set_idioma` ANTES de construir cualquier widget; no
evalúes `t()` al importar un módulo.
"""
IDIOMAS = {"en": "English", "es": "Español"}
POR_DEFECTO = "en"

_idioma = POR_DEFECTO

# inglés → español
_ES = {
    # Pestañas
    "📁 Library": "📁 Biblioteca",
    "⚡ Phrases": "⚡ Frases",
    "🎵 Soundboard": "🎵 Soundboard",
    "🗣 Pronunciation": "🗣 Pronunciación",
    # Ventana principal: carga
    "Starting…": "Iniciando…",
    "Reading your settings…": "Leyendo tu configuración…",
    "Loading voices…": "Cargando voces…",
    "Creating the virtual microphone…": "Creando el micrófono virtual…",
    "Preparing the window…": "Preparando la ventana…",
    "Loading quick phrases…": "Cargando frases rápidas…",
    "Loading the dictionary…": "Cargando el diccionario…",
    "Loading the soundboard…": "Cargando el soundboard…",
    "Loading the library…": "Cargando la biblioteca…",
    "Applying the theme…": "Aplicando el tema…",
    "Ready": "Listo",
    # Ventana principal: cabecera, motor y voz, ajuste de voz
    "⚙ Settings": "⚙ Ajustes",
    "Theme": "Tema",
    "Engine": "Motor",
    "Voice": "Voz",
    "👂 Test": "👂 Probar",
    "Speed": "Velocidad",
    "Pitch": "Tono",
    "Volume": "Volumen",
    "Metal": "Metal",
    "🤖 Robot sound: deep, robotic voice. Raise «Metal» for more distortion.":
        "🤖 Sonido robot: voz grave y robótica. Sube «Metal» para más distorsión.",
    "✨ Neural voices (need internet). Microsoft Edge: 14 Spanish voices.":
        "✨ Voces neuronales (necesitan internet). Microsoft Edge: 14 voces en español.",
    "🌐 Google TTS (needs internet). Several languages; no voice settings.":
        "🌐 Google TTS (necesita internet). Varios idiomas; sin ajustes de voz.",
    "✨ Voices available.": "✨ Voces disponibles.",
    # Ventana principal: pestañas, barra inferior y casillas
    "Voice {n}": "Voz {n}",
    "＋ New": "＋ Nueva",
    "✕ Close": "✕ Cerrar",
    "Clear after speaking": "Borrar al hablar",
    "Queue audio": "Encolar audios",
    "Auto-save": "Guardado automático",
    "Hear myself": "Escucharme",
    "🔊 Speak": "🔊 Hablar",
    "⏹ Stop": "⏹ Detener",
    "💾 Save": "💾 Guardar",
    # Barra de estado
    "✅ Ready: pick an engine and a voice": "✅ Listo: elige motor y voz",
    "🔊 Speaking...": "🔊 Hablando...",
    "✅ Done": "✅ Listo",
    "⏹ Stopped": "⏹ Detenido",
    "⚠️ Error: {error}": "⚠️ Error: {error}",
    "🎤 Virtual cable: {name}": "🎤 Cable virtual: {name}",
    "No virtual cable: install VB-CABLE": "Sin cable virtual: instala VB-CABLE",
    "⚠️ Type something before speaking": "⚠️ Escribe algo antes de hablar",
    "⚠️ There is nothing to save": "⚠️ No hay nada que guardar",
    "✅ Saved: {name}": "✅ Guardado: {name}",
    "💾 Saving...": "💾 Guardando...",
    "⚠️ Maximum number of tabs reached": "⚠️ Máximo de pestañas alcanzado",
    # Panel de cola
    "Now playing": "Ahora suena",
    "Nothing is playing": "Nada suena ahora",
    "Level": "Nivel",
    "Queued": "En cola",
    "Queued ({n})": "En cola ({n})",
    "History": "Historial",
    "History ({n})": "Historial ({n})",
    "Clear": "Limpiar",
    "The queue is empty": "La cola está vacía",
    "You haven't said anything yet this session":
        "Aún no has dicho nada en esta sesión",
    "🗑 Removed from the queue": "🗑 Quitado de la cola",
    "🔁 Repeating: {text}": "🔁 Repitiendo: {text}",
    # Perfiles
    "Profile": "Perfil",
    "— No profile —": "— Sin perfil —",
    "New profile": "Nuevo perfil",
    "Profile name:": "Nombre del perfil:",
    "Rename profile": "Renombrar perfil",
    "New name:": "Nuevo nombre:",
    "The profile needs a name": "El perfil necesita un nombre",
    "A profile «{name}» already exists": "Ya existe un perfil «{name}»",
    "🎭 Profile «{name}» applied": "🎭 Perfil «{name}» aplicado",
    "🎭 Profile «{name}» saved": "🎭 Perfil «{name}» guardado",
    "🎭 Profile «{name}» updated": "🎭 Perfil «{name}» actualizado",
    "🎭 Profile renamed to «{name}»": "🎭 Perfil renombrado a «{name}»",
    "🎭 Profile «{name}» deleted": "🎭 Perfil «{name}» borrado",
    # Ajustes → General → idioma
    "Language / Idioma": "Idioma / Language",
    "The language changes when you restart MultiVoice.":
        "El idioma cambia al reiniciar MultiVoice.",
}


def set_idioma(codigo):
    """Fija el idioma activo; un código desconocido vuelve al inglés."""
    global _idioma
    _idioma = codigo if codigo in IDIOMAS else POR_DEFECTO


def idioma():
    return _idioma


def t(texto, **kwargs):
    """Traduce `texto` (inglés) al idioma activo y rellena los placeholders."""
    if _idioma == "es":
        texto = _ES.get(texto, texto)
    return texto.format(**kwargs) if kwargs else texto
