"""Instancia única y paso de mensajes entre ejecuciones (sin GUI, testable).

La primera ejecución escucha en un socket local (127.0.0.1); si el puerto ya
está ocupado, ya hay una instancia abierta: se le manda el mensaje y se sale.
El mensaje es una línea JSON {"cmd": ...}; solo se aceptan órdenes conocidas.
"""
import json
import socket
import threading

PUERTO = 47653
CMD_DECIR = "decir"      # abrir el cuadro para escribir y decir
CMD_MOSTRAR = "mostrar"  # traer la ventana principal al frente
COMANDOS = (CMD_DECIR, CMD_MOSTRAR)
_MAX = 4096


def comando_de_args(argv):
    """Orden que pide la línea de comandos: --decir, o mostrar la ventana."""
    return CMD_DECIR if "--decir" in argv else CMD_MOSTRAR


def enviar(cmd, puerto=PUERTO, timeout=2.0):
    """Manda una orden a la instancia abierta. True si la recibió."""
    try:
        with socket.create_connection(("127.0.0.1", puerto), timeout) as s:
            s.sendall((json.dumps({"cmd": cmd}) + "\n").encode("utf-8"))
            return s.recv(8) == b"ok\n"
    except OSError:
        return False


class Servidor:
    """Escucha órdenes de otras ejecuciones y llama a `al_mensaje(cmd)`
    (desde un hilo propio: la interfaz debe replanificarlo con root.after)."""

    def __init__(self, al_mensaje, puerto=PUERTO):
        self.al_mensaje = al_mensaje
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # en Windows SO_REUSEADDR permitiría un segundo bind: no se usa
            self.sock.bind(("127.0.0.1", puerto))
            self.sock.listen(4)
        except OSError:
            self.sock.close()
            raise
        self.puerto = self.sock.getsockname()[1]
        self._hilo = threading.Thread(target=self._servir, daemon=True)
        self._hilo.start()

    def _servir(self):
        while True:
            try:
                con, _ = self.sock.accept()
            except OSError:
                return  # cerrado
            with con:
                con.settimeout(2.0)
                try:
                    datos = b""
                    while not datos.endswith(b"\n") and len(datos) < _MAX:
                        trozo = con.recv(1024)
                        if not trozo:
                            break
                        datos += trozo
                    cmd = json.loads(datos.decode("utf-8")).get("cmd")
                except (OSError, ValueError, AttributeError):
                    continue
                if cmd in COMANDOS:
                    try:
                        con.sendall(b"ok\n")
                    except OSError:
                        pass
                    self.al_mensaje(cmd)

    def cerrar(self):
        try:
            self.sock.close()
        except OSError:
            pass


def arrancar(argv, al_mensaje, puerto=PUERTO):
    """Devuelve (servidor, None) si esta es la primera instancia, o
    (None, avisada) si ya había una: avisada dice si pudo entregarle la orden."""
    try:
        return Servidor(al_mensaje, puerto), None
    except OSError:
        return None, enviar(comando_de_args(argv), puerto)
