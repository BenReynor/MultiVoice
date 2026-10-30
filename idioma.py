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
    # Ajustes, atajos y cuadro «Decir»
    'General':
        'General',
    'Audio':
        'Audio',
    'Robot sound':
        'Sonido robot',
    'Shortcuts':
        'Atajos',
    'Delete':
        'Borrar',
    'Cancel':
        'Cancelar',
    'MultiVoice Settings':
        'Ajustes de MultiVoice',
    'SETTINGS':
        'AJUSTES',
    'Close':
        'Cerrar',
    'Esc to close':
        'Esc para cerrar',
    'Voice engine':
        'Motor de voz',
    'Edge and Google need internet; the robot sound works offline.':
        'Edge y Google necesitan internet; el sonido robot funciona sin conexión.',
    'Maximum number of text tabs':
        'Máximo de pestañas de texto',
    'Tabs':
        'Pestañas',
    'Library folder':
        'Carpeta de la biblioteca',
    'The theme is chosen in the main window.':
        'El tema se elige en la ventana principal.',
    'After speaking':
        'Después de hablar',
    'Clear the text after speaking':
        'Borrar el texto al hablar',
    'Playback':
        'Reproducción',
    'Queue audio (do not interrupt)':
        'Encolar audios (no interrumpir)',
    'Library':
        'Biblioteca',
    'Save every spoken audio':
        'Guardar cada audio hablado',
    'Speed (wpm)':
        'Velocidad (ppm)',
    'espeak pitch':
        'Tono espeak',
    'Metal (distortion)':
        'Metal (distorsión)',
    'Volume (dB)':
        'Volumen (dB)',
    'Speak the current tab':
        'Hablar la pestaña actual',
    'Speak from the editor':
        'Hablar desde el editor',
    'New tab':
        'Nueva pestaña',
    'Close tab':
        'Cerrar pestaña',
    'Test the chosen voice':
        'Probar la voz elegida',
    'Global shortcut to speak':
        'Atajo global para hablar',
    'Opens an always-on-top box where you type and Enter says it. Format: ctrl+alt+h.':
        'Abre un cuadro siempre encima donde escribes y Enter lo dice. Formato: ctrl+alt+h.',
    'Invalid shortcut':
        'Atajo no válido',
    'Saved':
        'Guardado',
    'Could not register':
        'No se pudo registrar',
    'Save':
        'Guardar',
    ("On Linux (Wayland) apps cannot register global shortcuts. Assign the "
     "command «multivoice --decir» to a key in your system settings "
     "(Keyboard → Custom shortcuts) and it will open an always-on-top box "
     "where you type and Enter says it."):
        ("En Linux (Wayland) las apps no pueden registrar atajos globales. "
         "Asigna el comando «multivoice --decir» a una tecla en los ajustes "
         "de tu sistema (Teclado → Atajos personalizados) y abrirá un cuadro "
         "siempre encima donde escribes y Enter lo dice."),
    'Created in GNOME: {key}':
        'Creado en GNOME: {key}',
    'Could not create it: {error}':
        'No se pudo crear: {error}',
    'Create shortcut in GNOME':
        'Crear atajo en GNOME',
    'gsettings failed':
        'gsettings falló',
    'Invalid shortcut: use e.g. ctrl+alt+h':
        'Atajo no válido: usa p. ej. ctrl+alt+h',
    '⚠️ Could not register the global shortcut ({shortcut})':
        '⚠️ No se pudo registrar el atajo global ({shortcut})',
    'Say':
        'Decir',
    'Type and press Enter to say it…':
        'Escribe y pulsa Enter para decirlo…',
    # Ajustes → General → idioma
    "Language / Idioma": "Idioma / Language",
    "The language changes when you restart MultiVoice.":
        "El idioma cambia al reiniciar MultiVoice.",
    # Frases, Pronunciación, Soundboard y Biblioteca
    'The category needs a name':
        'La categoría necesita un nombre',
    'A category «{name}» already exists':
        'Ya existe la categoría «{name}»',
    'The phrase cannot be empty':
        'La frase no puede estar vacía',
    '＋ Phrase':
        '＋ Frase',
    '＋ Category':
        '＋ Categoría',
    'Ctrl+1…9 say the first nine':
        'Ctrl+1…9 dicen las nueve primeras',
    'No phrases. Create a category or press «＋ Phrase».':
        'No hay frases. Crea una categoría o pulsa «＋ Frase».',
    'Empty category':
        'Categoría vacía',
    '⚠️ No phrase for Ctrl+{n}':
        '⚠️ No hay frase para Ctrl+{n}',
    '⚡ Phrase deleted':
        '⚡ Frase borrada',
    'New category':
        'Nueva categoría',
    'Category name:':
        'Nombre de la categoría:',
    '⚡ Category «{name}» created':
        '⚡ Categoría «{name}» creada',
    'Rename category':
        'Renombrar categoría',
    '⚡ Category renamed to «{name}»':
        '⚡ Categoría renombrada a «{name}»',
    'Delete category':
        'Borrar categoría',
    'Delete «{name}» and its {n} phrases?':
        '¿Borrar «{name}» y sus {n} frases?',
    '⚡ Category «{name}» deleted':
        '⚡ Categoría «{name}» borrada',
    'Edit phrase':
        'Editar frase',
    'New phrase':
        'Nueva frase',
    'Phrase':
        'Frase',
    'Category':
        'Categoría',
    'Phrase voice':
        'Voz de la frase',
    '— Active profile —':
        '— Perfil activo —',
    '⚡ Phrase saved':
        '⚡ Frase guardada',
    'The text to replace cannot be empty':
        'El texto a reemplazar no puede estar vacío',
    'Use dictionary':
        'Usar diccionario',
    '＋ Rule':
        '＋ Regla',
    'No rules. Press «＋ Rule».':
        'Sin reglas. Pulsa «＋ Regla».',
    'Whole word':
        'Palabra completa',
    '🗣 Dictionary on':
        '🗣 Diccionario activado',
    '🗣 Dictionary off':
        '🗣 Diccionario desactivado',
    'Unsupported format (use mp3, wav or ogg)':
        'Formato no soportado (usa mp3, wav u ogg)',
    'ffmpeg could not convert the file':
        'ffmpeg no pudo convertir el archivo',
    'The sound needs a name':
        'El sonido necesita un nombre',
    'The sound file is missing':
        'Falta el archivo del sonido',
    '＋ Add sound':
        '＋ Añadir sonido',
    'No sounds. Press «＋ Add sound» (mp3, wav or ogg).':
        'Sin sonidos. Pulsa «＋ Añadir sonido» (mp3, wav u ogg).',
    'Add sounds':
        'Añadir sonidos',
    'All files':
        'Todos los archivos',
    '🎵 Sound added':
        '🎵 Sonido añadido',
    'Rename sound':
        'Renombrar sonido',
    '⚠ The file for that sound is missing':
        '⚠ Falta el archivo de ese sonido',
    '🔍 Search by text or voice…':
        '🔍 Buscar por texto o voz…',
    '🔄 Refresh':
        '🔄 Actualizar',
    '📂 Open folder':
        '📂 Abrir carpeta',
    '{n} audios for «{query}»':
        '{n} audios para «{query}»',
    '{n} audio':
        '{n} audio',
    '{n} audios':
        '{n} audios',
    'Nothing matches the search.':
        'Nada coincide con la búsqueda.',
    'No audios yet. Turn on «Auto-save» or press Save to fill the library.':
        'Aún no hay audios. Activa «Guardado automático» o pulsa Guardar para llenar la biblioteca.',
    'The library folder does not exist yet.':
        'La carpeta de la biblioteca todavía no existe.',
    'Showing the {n} most recent; use search to narrow down.':
        'Se muestran los {n} más recientes; usa la búsqueda para afinar.',
    'unknown voice':
        'voz desconocida',
    '🗑 Delete':
        '🗑 Borrar',
    '▶ Play':
        '▶ Reproducir',
    '▶ Playing {name}':
        '▶ Reproduciendo {name}',
    '⚠️ Could not play: {error}':
        '⚠️ No se pudo reproducir: {error}',
    'Delete this audio?':
        '¿Borrar este audio?',
    '«{name}» will be deleted from the library. This cannot be undone.':
        'Se borrará «{name}» de la biblioteca. No se puede deshacer.',
    '⚠️ Could not delete: {error}':
        '⚠️ No se pudo borrar: {error}',
    '🗑️ Deleted {name}':
        '🗑️ Borrado {name}',
    '⚠️ Could not open the folder: {error}':
        '⚠️ No se pudo abrir la carpeta: {error}',
    '🧹 Automatic cleanup: {n} old file(s) removed':
        '🧹 Limpieza automática: {n} archivo(s) antiguos eliminados',
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
