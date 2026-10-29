"""Soundboard y «Escucharme»: conversión y lista, sin reproducir audio."""
import json
import os
import sys
import types

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import soundboard  # noqa: E402
import tts_engine  # noqa: E402


def _ffmpeg_falso(creados=None, codigo=0):
    """Doble de ffmpeg: crea el archivo de salida (último argumento)."""
    def run(cmd, **kw):
        if codigo == 0:
            with open(cmd[-1], "wb") as f:
                f.write(b"RIFF")
        if creados is not None:
            creados.append(cmd)
        return types.SimpleNamespace(returncode=codigo)
    return run


def test_convertir_usa_ffmpeg_a_wav_48k_estereo(tmp_path):
    origen = tmp_path / "risa.mp3"
    origen.write_bytes(b"x")
    cmds = []
    nombre = soundboard.convertir(str(origen), str(tmp_path / "sb"),
                                  run=_ffmpeg_falso(cmds), ffmpeg="FFMPEG")
    assert nombre.endswith(".wav")
    assert os.path.isfile(tmp_path / "sb" / nombre)
    cmd = cmds[0]
    assert cmd[0] == "FFMPEG" and str(origen) in cmd
    assert cmd[cmd.index("-ar") + 1] == "48000"
    assert cmd[cmd.index("-ac") + 1] == "2"


def test_convertir_usa_el_ffmpeg_de_la_app(tmp_path, monkeypatch):
    origen = tmp_path / "a.ogg"
    origen.write_bytes(b"x")
    monkeypatch.setattr(tts_engine, "ffmpeg_bin", lambda: "/app/ffmpeg")
    cmds = []
    soundboard.convertir(str(origen), str(tmp_path), run=_ffmpeg_falso(cmds))
    assert cmds[0][0] == "/app/ffmpeg"


@pytest.mark.parametrize("ext", [".mp3", ".wav", ".ogg", ".MP3"])
def test_acepta_mp3_wav_ogg(tmp_path, ext):
    origen = tmp_path / ("s" + ext)
    origen.write_bytes(b"x")
    assert soundboard.convertir(str(origen), str(tmp_path),
                                run=_ffmpeg_falso())


def test_rechaza_formato_y_archivo_inexistente(tmp_path):
    otro = tmp_path / "a.txt"
    otro.write_text("x")
    with pytest.raises(ValueError):
        soundboard.convertir(str(otro), str(tmp_path), run=_ffmpeg_falso())
    with pytest.raises(FileNotFoundError):
        soundboard.convertir(str(tmp_path / "no.mp3"), str(tmp_path),
                             run=_ffmpeg_falso())


def test_ffmpeg_que_falla_da_error(tmp_path):
    origen = tmp_path / "a.mp3"
    origen.write_bytes(b"x")
    with pytest.raises(RuntimeError):
        soundboard.convertir(str(origen), str(tmp_path),
                             run=_ffmpeg_falso(codigo=1))


def test_nombre_por_defecto():
    assert soundboard.nombre_por_defecto("/x/risa_malvada-1.mp3") == "risa malvada 1"


def test_agregar_renombrar_borrar():
    cfg = {}
    assert soundboard.sonidos(cfg) == []
    soundboard.agregar(cfg, " Risa ", "snd_1.wav")
    soundboard.agregar(cfg, "Aplausos", "snd_2.wav")
    assert [s["name"] for s in soundboard.sonidos(cfg)] == ["Risa", "Aplausos"]
    soundboard.renombrar(cfg, 0, "Risa 2")
    assert cfg["soundboard"][0]["name"] == "Risa 2"
    assert soundboard.borrar(cfg, 0)
    assert not soundboard.borrar(cfg, 5)
    assert cfg["soundboard"] == [{"name": "Aplausos", "file": "snd_2.wav"}]


def test_nombre_vacio_falla():
    with pytest.raises(ValueError):
        soundboard.agregar({}, "  ", "a.wav")
    cfg = {}
    soundboard.agregar(cfg, "a", "a.wav")
    with pytest.raises(ValueError):
        soundboard.renombrar(cfg, 0, " ")
    with pytest.raises(KeyError):
        soundboard.renombrar(cfg, 3, "x")


def test_borrar_quita_el_wav_pero_no_sale_de_la_carpeta(tmp_path):
    dentro = tmp_path / "snd_1.wav"
    dentro.write_bytes(b"x")
    fuera = tmp_path.parent / "fuera_sb.wav"
    fuera.write_bytes(b"x")
    cfg = {"soundboard": [{"name": "a", "file": "snd_1.wav"},
                          {"name": "b", "file": "../fuera_sb.wav"}]}
    assert soundboard.borrar(cfg, 0, str(tmp_path))
    assert not dentro.exists()
    assert soundboard.borrar(cfg, 0, str(tmp_path))
    assert fuera.exists()


def test_config_viejo_o_roto_se_normaliza():
    cfg = {"soundboard": [{"name": "ok", "file": "a.wav"}, {"name": ""}, 5]}
    assert soundboard.asegurar(cfg) == [{"name": "ok", "file": "a.wav"}]
    cfg = {"soundboard": "roto"}
    assert soundboard.asegurar(cfg) == []


def test_viaja_por_config_json(tmp_path):
    cfg = {}
    soundboard.agregar(cfg, "Risa", "snd_1.wav")
    ruta = tmp_path / "config.json"
    ruta.write_text(json.dumps(cfg), encoding="utf-8")
    nuevo = json.loads(ruta.read_text(encoding="utf-8"))
    assert soundboard.sonidos(nuevo) == [{"name": "Risa", "file": "snd_1.wav"}]


def test_job_sonido_va_a_la_cola_sin_sintetizar():
    job = soundboard.job_sonido({"name": "Risa", "file": "a.wav"}, "/t/a.wav")
    assert job["engine"] == soundboard.MOTOR
    assert job["opts"]["file"] == "/t/a.wav"
    assert job["text"].endswith("Risa") and job["widget"] is None


def test_ruta_sonido_rechaza_rutas_con_directorios():
    assert soundboard.ruta_sonido("/d", {"file": "a.wav"}) == os.path.join("/d", "a.wav")
    assert soundboard.ruta_sonido("/d", {"file": "../a.wav"}) is None


@pytest.mark.parametrize("hay_virtual,escuchar,esperado", [
    (True, False, ["virtual"]),
    (True, True, ["virtual", "normal"]),
    (False, False, ["normal"]),     # sin micrófono virtual: no queda mudo
    (False, True, ["normal"]),      # y nunca se duplica
])
def test_plan_salidas_escucharme(hay_virtual, escuchar, esperado):
    for linux in (True, False):
        assert tts_engine.plan_salidas(linux, hay_virtual, escuchar) == esperado
