import math
import os
import struct
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cola  # noqa: E402
import medidor  # noqa: E402


def job(texto, voz="Jorge"):
    return {"text": texto, "voice_label": voz, "widget": object(),
            "clear_after": True, "queue": True}


class Reloj:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def test_encolar_y_avanzar_en_orden():
    c = cola.ColaVoz()
    a, b = c.encolar(job("uno")), c.encolar(job("dos"))
    assert a.id != b.id
    sonando, pendientes, _ = c.instantanea()
    assert sonando is None and [e.texto for e in pendientes] == ["uno", "dos"]
    assert c.avanzar() is a
    sonando, pendientes, _ = c.instantanea()
    assert sonando is a and [e.texto for e in pendientes] == ["dos"]
    assert c.hay_actividad()


def test_avanzar_con_cola_vacia():
    assert cola.ColaVoz().avanzar() is None


def test_quitar_elemento_de_la_cola():
    c = cola.ColaVoz()
    a, b = c.encolar(job("uno")), c.encolar(job("dos"))
    assert c.quitar(a.id) is True
    assert c.quitar(a.id) is False
    assert c.avanzar() is b


def test_no_se_puede_quitar_lo_que_suena():
    c = cola.ColaVoz()
    a = c.encolar(job("uno"))
    c.avanzar()
    assert c.quitar(a.id) is False


def test_terminar_pasa_al_historial_y_stop_no():
    c = cola.ColaVoz()
    c.encolar(job("uno"))
    c.encolar(job("dos"))
    c.avanzar()
    c.terminar(completado=True)
    c.avanzar()
    c.terminar(completado=False)
    sonando, _, historial = c.instantanea()
    assert sonando is None
    assert [e.texto for e in historial] == ["uno"]
    assert not c.hay_actividad()


def test_historial_con_tope_y_mas_reciente_primero():
    c = cola.ColaVoz(tope=3)
    for i in range(5):
        c.encolar(job(f"t{i}"))
        c.avanzar()
        c.terminar()
    _, _, historial = c.instantanea()
    assert [e.texto for e in historial] == ["t4", "t3", "t2"]


def test_repetir_devuelve_copia_sin_widget():
    c = cola.ColaVoz()
    original = job("hola")
    el = c.encolar(original)
    c.avanzar()
    c.terminar()
    copia = c.repetir(el.id)
    assert copia["text"] == "hola" and copia["widget"] is None
    assert copia["clear_after"] is None
    assert original["widget"] is not None      # el original no cambia
    assert c.repetir(9999) is None
    c.limpiar_historial()
    assert c.repetir(el.id) is None


def test_vaciar_descarta_pendientes_pero_no_lo_que_suena():
    c = cola.ColaVoz()
    for t in "abc":
        c.encolar(job(t))
    c.avanzar()
    assert c.vaciar() == 2
    sonando, pendientes, _ = c.instantanea()
    assert sonando.texto == "a" and pendientes == []


def test_progreso_y_nivel_siguen_al_reloj():
    reloj = Reloj()
    c = cola.ColaVoz(reloj=reloj)
    c.encolar(job("hola"))
    c.avanzar()
    assert c.progreso() == 0.0 and c.nivel() == 0.0
    c.iniciar_audio(2.0, [0.1, 0.5, 0.9] + [0.0] * 37)
    reloj.t = 0.5
    assert c.progreso() == 0.25
    assert c.nivel() == 0.0                  # ventana 10 del medidor
    reloj.t = 0.06
    assert c.nivel() == 0.5
    reloj.t = 5.0
    assert c.progreso() == 1.0 and c.nivel() == 0.0
    c.terminar()
    assert c.progreso() == 0.0


def test_recortar_texto():
    assert cola.recortar("  hola \n  mundo ") == "hola mundo"
    largo = cola.recortar("a" * 100, 20)
    assert len(largo) == 20 and largo.endswith("…")


def _wav(ruta, amplitud, segundos=0.2, tasa=8000):
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(tasa)
        n = int(segundos * tasa)
        w.writeframes(b"".join(
            struct.pack("<h", int(amplitud * math.sin(i / 5))) for i in range(n)))


def test_envolvente_distingue_silencio_y_sonido(tmp_path):
    fuerte, callado = str(tmp_path / "f.wav"), str(tmp_path / "c.wav")
    _wav(fuerte, 20000)
    _wav(callado, 0)
    dur, niv = medidor.envolvente(fuerte)
    assert abs(dur - 0.2) < 0.01 and len(niv) == 4
    assert all(0.5 < n <= 1 for n in niv)
    assert medidor.envolvente(callado)[1] == [0.0] * 4


def test_envolvente_de_archivo_roto(tmp_path):
    ruta = tmp_path / "x.wav"
    ruta.write_bytes(b"no es un wav")
    assert medidor.envolvente(str(ruta)) == (0.0, [])
    assert medidor.envolvente(str(tmp_path / "no_existe.wav")) == (0.0, [])
