"""Medidor de nivel: envolvente de volumen de un WAV, sin interfaz.

`envolvente` lee el audio una vez y devuelve un nivel 0..1 por ventana; la
interfaz solo consulta `nivel_en` mientras suena.
"""
import array
import math
import sys
import wave

VENTANA = 0.05      # segundos por muestra del medidor
PISO_DB = -50.0     # por debajo de esto el medidor marca 0


def nivel_desde_rms(rms, maximo=32768.0):
    """RMS de muestras enteras -> nivel 0..1 en escala de decibelios."""
    if rms <= 0:
        return 0.0
    db = 20 * math.log10(min(rms, maximo) / maximo)
    return max(0.0, min(1.0, (db - PISO_DB) / -PISO_DB))


def envolvente(ruta, ventana=VENTANA):
    """(duración en s, [nivel por ventana]) de un WAV PCM de 16 bits.

    Con cualquier otro formato o un archivo ilegible devuelve (0.0, []).
    """
    try:
        with wave.open(ruta, "rb") as w:
            if w.getsampwidth() != 2:
                return 0.0, []
            tasa = w.getframerate()
            marcos = w.getnframes()
            por_ventana = max(1, int(tasa * ventana))
            niveles = []
            while True:
                datos = w.readframes(por_ventana)
                if not datos:
                    break
                muestras = array.array("h")
                muestras.frombytes(datos[:len(datos) // 2 * 2])
                if sys.byteorder == "big":
                    muestras.byteswap()
                n = len(muestras)
                rms = math.sqrt(sum(m * m for m in muestras) / n) if n else 0
                niveles.append(nivel_desde_rms(rms))
            return marcos / float(tasa), niveles
    except (wave.Error, EOFError, OSError, ZeroDivisionError):
        return 0.0, []


def nivel_en(niveles, segundos, ventana=VENTANA):
    """Nivel en un instante; 0 fuera del audio."""
    if segundos < 0:
        return 0.0
    i = int(segundos / ventana)
    return niveles[i] if 0 <= i < len(niveles) else 0.0
