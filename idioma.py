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
