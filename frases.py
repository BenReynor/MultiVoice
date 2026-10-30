"""Frases rápidas: botones agrupados por categorías que se dicen con un clic.

La lógica (crear, editar, borrar, mover, numerar) trabaja sobre el dict de
configuración (`cfg["phrases"]`, categoría -> lista de frases) y no usa la
interfaz, así se prueba sin pantalla. `FrasesMixin` dibuja la vista.
Cada frase es {"text": ..., "profile": ...}; con perfil vacío se dice con el
perfil activo (la voz que haya en la barra).
"""
import copy

import customtkinter as ctk

import tts_engine
from idioma import t


def tab_frases():
    return t("⚡ Phrases")


MAX_ATAJOS = 9
CATEGORIA_NUEVA = "General"

FRASES_EJEMPLO = {
    "Saludos": [
        {"text": "Hola a todos", "profile": ""},
        {"text": "Buenas noches, ¿qué tal?", "profile": ""},
        {"text": "Hasta luego, nos vemos", "profile": ""},
    ],
    "Reacciones": [
        {"text": "Jajaja, muy bueno", "profile": ""},
        {"text": "Gracias por la ayuda", "profile": ""},
    ],
}


def ejemplos():
    return copy.deepcopy(FRASES_EJEMPLO)


def _frase(datos):
    datos = datos if isinstance(datos, dict) else {"text": datos}
    return {"text": str(datos.get("text") or "").strip(),
            "profile": str(datos.get("profile") or "")}


def asegurar(cfg):
    """Garantiza cfg["phrases"]. Un config.json sin la clave recibe las de
    ejemplo; si existe (aunque vacía) se respeta."""
    datos = cfg.get("phrases")
    if not isinstance(datos, dict):
        cfg["phrases"] = ejemplos()
    else:
        limpio = {}
        for cat, lista in datos.items():
            cat = str(cat).strip()
            if cat and isinstance(lista, list):
                limpio[cat] = [f for f in map(_frase, lista) if f["text"]]
        cfg["phrases"] = limpio
    return cfg["phrases"]


def categorias(cfg):
    return list(asegurar(cfg))


def frases(cfg, categoria):
    return list(asegurar(cfg).get(categoria, []))


def crear_categoria(cfg, nombre):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("La categoría necesita un nombre")
    cats = asegurar(cfg)
    if nombre in cats:
        raise ValueError(f"Ya existe la categoría «{nombre}»")
    cats[nombre] = []
    return nombre


def renombrar_categoria(cfg, viejo, nuevo):
    nuevo = (nuevo or "").strip()
    cats = asegurar(cfg)
    if viejo not in cats:
        raise KeyError(viejo)
    if not nuevo:
        raise ValueError("La categoría necesita un nombre")
    if nuevo != viejo and nuevo in cats:
        raise ValueError(f"Ya existe la categoría «{nuevo}»")
    cfg["phrases"] = {(nuevo if c == viejo else c): f for c, f in cats.items()}
    return nuevo


def borrar_categoria(cfg, categoria):
    """Quita la categoría con sus frases; True si existía."""
    return asegurar(cfg).pop(categoria, None) is not None


def agregar(cfg, categoria, texto, perfil=""):
    """Añade una frase al final (crea la categoría si no existe)."""
    f = _frase({"text": texto, "profile": perfil})
    if not f["text"]:
        raise ValueError("La frase no puede estar vacía")
    categoria = (categoria or "").strip() or CATEGORIA_NUEVA
    asegurar(cfg).setdefault(categoria, []).append(f)
    return f


def editar(cfg, categoria, indice, texto=None, perfil=None):
    lista = asegurar(cfg).get(categoria)
    if lista is None or not 0 <= indice < len(lista):
        raise KeyError((categoria, indice))
    if texto is not None:
        texto = texto.strip()
        if not texto:
            raise ValueError("La frase no puede estar vacía")
        lista[indice]["text"] = texto
    if perfil is not None:
        lista[indice]["profile"] = perfil
    return lista[indice]


def borrar(cfg, categoria, indice):
    lista = asegurar(cfg).get(categoria)
    if lista is None or not 0 <= indice < len(lista):
        return False
    del lista[indice]
    return True


def mover(cfg, origen, indice, destino):
    """Mueve una frase a otra categoría (al final; la crea si no existe)."""
    cats = asegurar(cfg)
    lista = cats.get(origen)
    if lista is None or not 0 <= indice < len(lista):
        raise KeyError((origen, indice))
    destino = (destino or "").strip()
    if not destino:
        raise ValueError("La categoría necesita un nombre")
    f = lista.pop(indice)
    cats.setdefault(destino, []).append(f)
    return f


def numeradas(cfg, maximo=MAX_ATAJOS):
    """Las primeras frases en el orden de la vista: [(n, categoría, índice, frase)].
    n va de 1 a `maximo` y es el número del atajo Ctrl+n."""
    out = []
    for cat, lista in asegurar(cfg).items():
        for i, f in enumerate(lista):
            if len(out) >= maximo:
                return out
            out.append((len(out) + 1, cat, i, f))
    return out


def frase_numero(cfg, n):
    for num, _cat, _i, f in numeradas(cfg):
        if num == n:
            return f
    return None


def job_desde_perfil(texto, perfil):
    """Trabajo de síntesis con los ajustes de un perfil, sin tocar la interfaz."""
    from multivoice import ROBOT_VOICE  # import tardío: evita el ciclo
    engine = perfil["engine"]
    voces = tts_engine.list_voices(engine)
    voz = next((v for v in voces if v["label"] == perfil["voice"]), None)
    if perfil["voice"] == ROBOT_VOICE:
        engine = "robot"
    elif voz is None and voces:
        voz = voces[0]
    rate, pitch, volume = perfil["rate"], perfil["pitch"], perfil["volume"]
    if engine == "robot":
        opts = {"robot_speed": max(40, min(450, round(80 + (rate + 50) * 1.1))),
                "robot_pitch": max(1, min(99, round(30 + pitch * 0.6))),
                "volume": volume, "robot_metal": perfil["metal"] / 100.0}
        label = ROBOT_VOICE
    elif engine == "gtts":
        opts = {"lang": voz["id"], "slow": False}
        label = voz["label"]
    else:
        engine = "edge"
        opts = {"voice": voz["id"], "rate": rate, "pitch": pitch,
                "volume": volume}
        label = voz["label"]
    return {"text": texto, "engine": engine, "opts": opts, "widget": None,
            "clear_after": None, "voice_label": label}


class FrasesMixin:
    """Pestaña «Frases»: botones por categoría y atajos Ctrl+1…Ctrl+9."""

    def _build_frases_tab(self):
        self.frases_tab = self.tabview.add(tab_frases())
        barra = ctk.CTkFrame(self.frases_tab, fg_color="transparent")
        barra.pack(fill="x", padx=4, pady=(2, 6))
        self._btn(barra, "＋ Frase", lambda: self.frase_dialogo()).pack(
            side="left", padx=(0, 6))
        self._btn(barra, "＋ Categoría", self.categoria_nueva).pack(side="left")
        self.frases_hint = ctk.CTkLabel(
            barra, text="Ctrl+1…9 dicen las nueve primeras", anchor="e",
            font=self.font())
        self.frases_hint.pack(side="right", padx=8)
        self._reg(self.frases_hint, lambda w: w.configure(
            text_color=self._col("--text-3")))
        self.frases_list = ctk.CTkScrollableFrame(self.frases_tab,
                                                  corner_radius=8)
        self.frases_list.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self._reg(self.frases_list, lambda w: w.configure(
            fg_color=self._col("--surface-2")))
        self._refresh_frases()

    def _refresh_frases(self):
        if not hasattr(self, "frases_list"):
            return
        c = self._col
        for w in self.frases_list.winfo_children():
            w.destroy()
        cats = asegurar(self.cfg)
        if not cats:
            ctk.CTkLabel(
                self.frases_list, font=self.font(), text_color=c("--text-3"),
                text="No hay frases. Crea una categoría o pulsa «＋ Frase»."
            ).pack(pady=24)
            return
        numero = {(cat, i): n for n, cat, i, _ in numeradas(self.cfg)}
        h = self._px("--control-h", 36)
        for cat, lista in cats.items():
            cab = ctk.CTkFrame(self.frases_list, fg_color="transparent")
            cab.pack(fill="x", pady=(8, 2))
            ctk.CTkLabel(cab, text=cat, font=self.font(None, True),
                         text_color=c("--text")).pack(side="left", padx=4)
            for texto, cmd in (("🗑", lambda k=cat: self.categoria_borrar(k)),
                               ("✎", lambda k=cat: self.categoria_renombrar(k))):
                b = self._btn(cab, texto, cmd, height=h - 8)
                b.configure(width=h - 4)
                b.pack(side="right", padx=(4, 0))
            if not lista:
                ctk.CTkLabel(self.frases_list, text="Categoría vacía",
                             font=self.font(), text_color=c("--text-3"),
                             anchor="w").pack(fill="x", padx=8)
            for i, f in enumerate(lista):
                fila = ctk.CTkFrame(self.frases_list, fg_color="transparent")
                fila.pack(fill="x", pady=2)
                n = numero.get((cat, i))
                marca = f"Ctrl+{n}  " if n else ""
                extra = f"  · 🎭 {f['profile']}" if f["profile"] else ""
                b = self._btn(fila, f"{marca}{f['text']}{extra}",
                              lambda k=cat, j=i: self.decir_frase(k, j))
                b.configure(anchor="w")
                b.pack(side="left", fill="x", expand=True)
                for texto, cmd in (
                        ("✕", lambda k=cat, j=i: self.frase_borrar(k, j)),
                        ("✎", lambda k=cat, j=i: self.frase_dialogo(k, j))):
                    bb = self._btn(fila, texto, cmd)
                    bb.configure(width=h)
                    bb.pack(side="right", padx=(4, 0))

    # ---------- Decir ----------
    def decir_frase(self, categoria, indice):
        lista = frases(self.cfg, categoria)
        if not 0 <= indice < len(lista):
            return False
        return self._decir(lista[indice])

    def decir_numero(self, n):
        f = frase_numero(self.cfg, n)
        if f is None:
            self.set_status(f"⚠️ No hay frase para Ctrl+{n}")
            return False
        return self._decir(f)

    def _decir(self, f):
        import perfiles
        perfil = perfiles.cargar(self.cfg, f["profile"]) if f["profile"] else None
        if perfil is not None:
            job = job_desde_perfil(f["text"], perfil)
        else:
            job = self.build_job(f["text"])
        job["queue"] = self.queue_var.get()
        self.worker.enqueue(job)
        return True

    # ---------- Edición ----------
    def _frases_guardar(self, msg):
        self._save_soon()
        self._refresh_frases()
        self.set_status(msg)

    def frase_borrar(self, categoria, indice):
        if borrar(self.cfg, categoria, indice):
            self._frases_guardar("⚡ Frase borrada")

    def categoria_nueva(self):
        nombre = self._pedir_nombre("Nueva categoría", "Nombre de la categoría:")
        if not nombre:
            return
        try:
            crear_categoria(self.cfg, nombre)
        except ValueError as exc:
            self.set_status(f"⚠ {exc}")
            return
        self._frases_guardar(f"⚡ Categoría «{nombre}» creada")

    def categoria_renombrar(self, viejo):
        nuevo = self._pedir_nombre("Renombrar categoría", "Nuevo nombre:", viejo)
        if not nuevo or nuevo == viejo:
            return
        try:
            renombrar_categoria(self.cfg, viejo, nuevo)
        except ValueError as exc:
            self.set_status(f"⚠ {exc}")
            return
        self._frases_guardar(f"⚡ Categoría renombrada a «{nuevo}»")

    def categoria_borrar(self, categoria):
        n = len(frases(self.cfg, categoria))
        if n and not self.confirmar(
                "Borrar categoría",
                f"¿Borrar «{categoria}» y sus {n} frases?"):
            return
        if borrar_categoria(self.cfg, categoria):
            self._frases_guardar(f"⚡ Categoría «{categoria}» borrada")

    def frase_dialogo(self, categoria=None, indice=None):
        """Ventana para crear (indice None) o editar una frase: texto,
        categoría (mover) y perfil propio."""
        import perfiles
        editando = indice is not None
        actual = frases(self.cfg, categoria)[indice] if editando else \
            {"text": "", "profile": ""}
        cats = categorias(self.cfg) or [CATEGORIA_NUEVA]
        dlg = ctk.CTkToplevel(self.root)
        dlg.title("Editar frase" if editando else "Nueva frase")
        dlg.transient(self.root)
        dlg.configure(fg_color=self._col("--bg"))
        marco = ctk.CTkFrame(dlg, fg_color="transparent")
        marco.pack(fill="both", expand=True, padx=16, pady=14)
        h = self._px("--control-h", 36)

        def campo(titulo):
            ctk.CTkLabel(marco, text=titulo, anchor="w", font=self.font(),
                         text_color=self._col("--text")).pack(fill="x",
                                                              pady=(8, 2))

        campo("Frase")
        texto = ctk.CTkEntry(marco, width=360, height=h, font=self.font())
        texto.insert(0, actual["text"])
        texto.pack(fill="x")
        self._paint_entry(texto)
        campo("Categoría")
        cat = ctk.CTkComboBox(marco, values=cats, height=h, font=self.font(),
                              dropdown_font=self.font())
        cat.set(categoria or cats[0])
        cat.pack(fill="x")
        self._paint_menu(cat)
        campo("Voz de la frase")
        sin = "— Perfil activo —"
        perf = ctk.CTkOptionMenu(
            marco, values=[sin] + perfiles.nombres(self.cfg), height=h,
            font=self.font(), dropdown_font=self.font())
        perf.set(actual["profile"] if actual["profile"] in
                 perfiles.nombres(self.cfg) else sin)
        perf.pack(fill="x")
        self._paint_menu(perf)
        error = ctk.CTkLabel(marco, text="", anchor="w", font=self.font(),
                             text_color=self._col("--danger"))
        error.pack(fill="x", pady=(8, 0))

        def aceptar():
            pf = "" if perf.get() == sin else perf.get()
            destino = cat.get().strip() or CATEGORIA_NUEVA
            try:
                if editando:
                    editar(self.cfg, categoria, indice, texto.get(), pf)
                    if destino != categoria:
                        mover(self.cfg, categoria, indice, destino)
                else:
                    agregar(self.cfg, destino, texto.get(), pf)
            except ValueError as exc:
                error.configure(text=str(exc))
                return
            dlg.destroy()
            self._frases_guardar("⚡ Frase guardada")

        botones = ctk.CTkFrame(marco, fg_color="transparent")
        botones.pack(fill="x", pady=(10, 0))
        self._btn(botones, "Guardar", aceptar, accent=True).pack(side="right")
        self._btn(botones, "Cancelar", dlg.destroy).pack(side="right",
                                                         padx=(0, 6))
        dlg.bind("<Escape>", lambda e: dlg.destroy())
        dlg.bind("<Return>", lambda e: aceptar())
        self._frase_dialogo_actual = dlg
        self._frase_dialogo_aceptar = aceptar
        self._frase_dialogo_campos = (texto, cat, perf, sin)
        texto.focus_set()
        return dlg
