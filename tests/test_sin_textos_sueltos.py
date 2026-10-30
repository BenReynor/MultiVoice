"""Ningún texto visible en español suelto en el código: va por t() y _ES."""
import ast
import os
import re

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ES = re.compile("[áéíóúñ¿¡ÁÉÍÓÚÑ]")

# Literales permitidos (texto exacto) y por qué.
EXCEPCIONES = {
    # Voz: frases de prueba que se pronuncian con voces españolas.
    "Hola, esta es tu nueva voz de prueba. ¿Cómo me escucho?": "voz",
    "El otro día vi una luz extraña en el pasillo de la Fundación.": "voz",
    "Todas las amenazas han sido neutralizadas. Todo está bajo control.":
        "voz",
    # Ejemplos de datos del usuario (frases rápidas y diccionario).
    "Buenas noches, ¿qué tal?": "frase de ejemplo editable",
    "cómo se dice": "reemplazo de ejemplo editable",
    # Nombre propio del estilo (como Discord o Cyberpunk), no se traduce.
    "Cálido": "nombre del tema estilo-calido",
}


def _archivos_py():
    for base, dirs, files in os.walk(RAIZ):
        dirs[:] = [d for d in dirs if not d.startswith(".")
                   and d not in ("__pycache__", "venv", "tests")]
        for f in files:
            if f.endswith(".py") and not (base == RAIZ and f == "idioma.py"):
                yield os.path.join(base, f)


def _docstrings(arbol):
    ids = set()
    for n in ast.walk(arbol):
        if isinstance(n, (ast.Module, ast.FunctionDef,
                          ast.AsyncFunctionDef, ast.ClassDef)):
            b = n.body
            if (b and isinstance(b[0], ast.Expr)
                    and isinstance(b[0].value, ast.Constant)
                    and isinstance(b[0].value.value, str)):
                ids.add(id(b[0].value))
    return ids


def test_sin_textos_sueltos_en_espanol():
    sueltos = []
    for ruta in _archivos_py():
        with open(ruta, encoding="utf-8") as f:
            arbol = ast.parse(f.read(), ruta)
        docs = _docstrings(arbol)
        for n in ast.walk(arbol):
            if (isinstance(n, ast.Constant) and isinstance(n.value, str)
                    and id(n) not in docs and ES.search(n.value)
                    and n.value not in EXCEPCIONES):
                sueltos.append(f"{os.path.relpath(ruta, RAIZ)}:{n.lineno}: "
                               f"{n.value[:60]!r}")
    assert not sueltos, "Textos en español sin traducir:\n" + "\n".join(sueltos)
