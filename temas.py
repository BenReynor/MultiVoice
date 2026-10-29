"""Temas de la interfaz: lee assets/temas/<nombre>.css (contrato ui-tokens)."""
import os
import re
import sys

# nombre -> nombre en español
TEMAS = {
    "discord": "Discord",
    "minimal": "Minimal",
    "cyberpunk": "Cyberpunk",
    "calido": "Cálido",
    "datos": "Datos",
    "anime": "Anime",
    "manga": "Manga",
    "glass": "Cristal",
    "retro": "Retro",
    "brutalista": "Brutalista",
}

# variantes de modo que ofrece cada tema (la primera es la base)
MODOS = {
    "minimal": ("oscuro", "claro"),
    "datos": ("oscuro", "claro"),
    "glass": ("oscuro", "claro"),
    "anime": ("dia", "noche"),
    "manga": ("papel", "noir"),
}

TEMA_POR_DEFECTO = "discord"

# nombres de temas antiguos -> tema nuevo (y modo si aplica)
NOMBRES_ANTIGUOS = {
    "dark": ("discord", None),
    "light": ("minimal", "claro"),
    "hacker": ("cyberpunk", None),
    "dracula": ("anime", "noche"),
    "gruvbox": ("calido", None),
}

_BLOQUE = re.compile(r'\[data-tema="([^"]+)"\](?:\[data-modo="([^"]+)"\])?\s*\{([^}]*)\}')
_VAR = re.compile(r"(--[\w-]+)\s*:\s*([^;]+);")
_COLOR_SCHEME = re.compile(r"color-scheme\s*:\s*(\w+)\s*;")


def carpeta_temas():
    """Carpeta assets/temas, desde el código fuente o desde PyInstaller."""
    base = getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "assets", "temas")


def lista_temas():
    """Lista de (id, nombre en español) de los temas disponibles."""
    return [(t, n) for t, n in TEMAS.items()
            if os.path.isfile(os.path.join(carpeta_temas(), t + ".css"))]


def modos(tema):
    """Modos del tema (vacío si solo tiene uno)."""
    return MODOS.get(tema, ())


def traducir_nombre(nombre, modo=None):
    """Devuelve (tema, modo) válidos; traduce nombres antiguos o desconocidos."""
    nombre = (nombre or "").strip().lower()
    if nombre in TEMAS:
        return nombre, modo if modo in modos(nombre) else None
    if nombre in NOMBRES_ANTIGUOS:
        return NOMBRES_ANTIGUOS[nombre]
    return TEMA_POR_DEFECTO, None


def paleta(tema, modo=None):
    """Tokens del tema: base + variante de modo. Claves como '--bg'."""
    tema, modo = traducir_nombre(tema, modo)
    ruta = os.path.join(carpeta_temas(), tema + ".css")
    with open(ruta, encoding="utf-8") as f:
        css = re.sub(r"/\*.*?\*/", "", f.read(), flags=re.S)
    base, variante = {}, {}
    for t, m, cuerpo in _BLOQUE.findall(css):
        if t != tema:
            continue
        destino = base if not m else (variante if m == modo else None)
        if destino is None:
            continue
        destino.update(_VAR.findall(cuerpo))
        cs = _COLOR_SCHEME.search(cuerpo)
        if cs:
            destino["color-scheme"] = cs.group(1)
    res = {k: v.strip() for k, v in base.items()}
    res.update({k: v.strip() for k, v in variante.items()})
    return res
