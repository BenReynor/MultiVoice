"""Cola, historial y progreso de lo que suena, sin interfaz.

El hilo de reproducción y la ventana comparten una `ColaVoz`; todos los
métodos son seguros entre hilos. Los trabajos (`job`) son los mismos
diccionarios que usa `SpeechWorker`.
"""
import threading
import time
from dataclasses import dataclass

import medidor

TOPE_HISTORIAL = 50


def recortar(texto, maximo=60):
    """Texto en una línea y como mucho `maximo` caracteres (con «…»)."""
    plano = " ".join(str(texto).split())
    if len(plano) <= maximo:
        return plano
    return plano[:max(maximo - 1, 0)].rstrip() + "…"


@dataclass
class Elemento:
    id: int
    texto: str
    voz: str
    job: dict


class ColaVoz:
    def __init__(self, tope=TOPE_HISTORIAL, reloj=time.monotonic):
        self._lock = threading.Lock()
        self._reloj = reloj
        self._tope = max(1, tope)
        self._siguiente_id = 1
        self._pendientes = []
        self._historial = []        # el más reciente primero
        self._sonando = None
        self._inicio = None
        self._duracion = 0.0
        self._niveles = []

    # ---- cola ----
    def encolar(self, job):
        with self._lock:
            el = Elemento(self._siguiente_id, job.get("text", ""),
                          job.get("voice_label", ""), job)
            self._siguiente_id += 1
            self._pendientes.append(el)
            return el

    def quitar(self, id_):
        """Quita un elemento que aún espera; False si ya no está."""
        with self._lock:
            for i, el in enumerate(self._pendientes):
                if el.id == id_:
                    del self._pendientes[i]
                    return True
            return False

    def vaciar(self):
        """Descarta todo lo que espera (no toca lo que suena); devuelve cuántos."""
        with self._lock:
            n = len(self._pendientes)
            self._pendientes.clear()
            return n

    def hay_actividad(self):
        with self._lock:
            return self._sonando is not None or bool(self._pendientes)

    # ---- reproducción ----
    def avanzar(self):
        """Pasa el primero de la cola a «sonando»; None si no hay nadie."""
        with self._lock:
            if not self._pendientes:
                return None
            self._sonando = self._pendientes.pop(0)
            self._inicio = None
            self._duracion = 0.0
            self._niveles = []
            return self._sonando

    def iniciar_audio(self, duracion=0.0, niveles=()):
        """Marca que el audio empieza ahora (para progreso y medidor)."""
        with self._lock:
            self._inicio = self._reloj()
            self._duracion = float(duracion)
            self._niveles = list(niveles)

    def terminar(self, completado=True):
        """Quita lo que sonaba; si se dijo entero pasa al historial."""
        with self._lock:
            el, self._sonando = self._sonando, None
            self._inicio, self._duracion, self._niveles = None, 0.0, []
            if el is not None and completado:
                self._historial.insert(0, el)
                del self._historial[self._tope:]
            return el

    def progreso(self):
        """Fracción 0..1 de lo que suena (0 si aún no hay audio)."""
        with self._lock:
            if self._inicio is None or self._duracion <= 0:
                return 0.0
            return max(0.0, min(1.0, (self._reloj() - self._inicio)
                                / self._duracion))

    def nivel(self):
        """Volumen 0..1 de lo que suena en este instante."""
        with self._lock:
            if self._inicio is None:
                return 0.0
            return medidor.nivel_en(self._niveles, self._reloj() - self._inicio)

    # ---- historial ----
    def repetir(self, id_):
        """Copia del trabajo de una entrada del historial, lista para encolar."""
        with self._lock:
            for el in self._historial:
                if el.id == id_:
                    return dict(el.job, widget=None, clear_after=None)
            return None

    def limpiar_historial(self):
        with self._lock:
            self._historial.clear()

    def instantanea(self):
        """(sonando, pendientes, historial) copiados para pintar la interfaz."""
        with self._lock:
            return (self._sonando, list(self._pendientes),
                    list(self._historial))
