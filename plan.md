# plan.md — MultiVoice

Rediseño de la interfaz con CustomTkinter y funciones nuevas. Contexto y reglas
en CONTEXTO.md. Cada tarea lleva su `criterio:`; el gate ejecuta ruff, pytest,
el smoke test del motor y el test de la ventana real (Xvfb).

## FASE 1 — Nueva interfaz con CustomTkinter

- [x] Temas desde las skills de diseño
  criterio: siguiendo la skill ui-tokens, los 10 temas de las skills estilo-* ya están copiados en assets/temas/<nombre>.css (minimal, discord, cyberpunk, calido, datos, anime, manga, glass, retro, brutalista; no los modifiques) y un módulo temas.py los lee (base + variante de modo) y devuelve una paleta con los tokens del contrato (`--bg`, `--surface`, `--text`, `--accent`, `--accent-text`, `--danger`, radios…) y la lista de temas disponibles con su nombre en español; un tema guardado con un nombre antiguo (dark, light, hacker, dracula, gruvbox) se traduce a uno nuevo; tests de pytest para leer un tema, la variante de modo y la traducción de nombres antiguos
- [x] Ventana principal con CustomTkinter
  criterio: usando las skills ui-tokens, estilo-discord y diseno-escritorio, `customtkinter` está en requirements.txt y la ventana se construye con widgets de CustomTkinter coloreados con la paleta de temas.py (tema por defecto «Discord»): cabecera con el nombre de la app, selector de tema y botón de ajustes; barra de motor y voz con «Probar»; panel de ajuste de voz que solo muestra los controles del motor elegido (el «metal» solo con el robot); editor de texto con pestañas; barra inferior con **Hablar** como botón principal grande, Detener y Guardar, y una barra de estado; toda la interfaz en español; se conservan todos los atajos de teclado y funciones actuales; tests/gui_smoke.py se adapta y comprueba que el tema guardado se aplica al arrancar y que cada tema se aplica sin error
- [x] Ajustes y Biblioteca con la nueva interfaz
  criterio: usando las skills ui-tokens, estilo-discord y diseno-escritorio, Ajustes es una ventana modal propia (no un panel encima de la principal) con secciones General, Audio, Sonido robot y Atajos, y el desplegable de motor muestra el motor actual (hoy aparece vacío); la Biblioteca es una vista con lista de audios (texto, voz, fecha, tamaño), buscar, reproducir, abrir carpeta y borrar con confirmación; todo en español; gui_smoke abre Ajustes y la Biblioteca
- [x] Empaquetado con CustomTkinter
  criterio: el paso de PyInstaller de .github/workflows/build.yml ya incluye `--collect-all customtkinter` y `--add-data assets/temas` (no lo cambies salvo que falte algo); existe un test de pytest que comprueba que temas.py encuentra los temas tanto desde el código fuente como con la ruta de recursos de PyInstaller (`sys._MEIPASS` simulado apuntando a una copia temporal de assets/temas); README actualizado con capturas pendientes marcadas como TODO

## FASE 2 — Funciones nuevas

- [x] Cola e historial visibles
  criterio: siguiendo las skills ui-tokens y diseno-escritorio, un panel lateral muestra lo que está sonando (texto recortado, voz y una barra de progreso), lo que espera en la cola (cada elemento se puede quitar) y el historial de lo dicho en esta sesión (repetir con un clic); un medidor de nivel muestra el volumen mientras suena; la lógica de cola/historial vive fuera de la interfaz (módulo propio) y tiene tests de pytest (encolar, quitar, avanzar, historial con tope)
- [x] Perfiles de voz
  criterio: un perfil guarda motor, voz, velocidad, tono, volumen y metal con un nombre (p. ej. «SCP-079», «Narrador»); se crean, renombran y borran desde la interfaz y se eligen con un desplegable en la barra de voz; se guardan en config.json; vienen dos perfiles de ejemplo; tests de pytest de guardar/cargar/borrar perfiles y de config.json antiguo sin perfiles
- [x] Frases rápidas
  criterio: siguiendo las skills ui-tokens y diseno-escritorio, una vista de frases rápidas con botones agrupados por categorías (crear, editar, borrar, mover entre categorías) dice la frase al pulsarla con el perfil activo o con uno propio de la frase; las nueve primeras se disparan con Ctrl+1…Ctrl+9; se guardan en config.json; tests de pytest de la lógica de frases y categorías
- [x] Diccionario de pronunciación
  criterio: una tabla editable de reemplazos (texto → cómo decirlo, palabra completa o no, sin distinguir mayúsculas) se aplica antes de sintetizar en todos los motores y se puede activar o desactivar; trae algunos de ejemplo (xd → equis de, etc.); la función de reemplazo es pura y tiene tests de pytest (palabra completa, mayúsculas, varios reemplazos, desactivado)
- [x] Escucharse a uno mismo y soundboard
  criterio: un interruptor «Escucharme» reproduce también por la salida normal lo que suena por el micrófono virtual (en Linux y en Windows; si no hay micrófono virtual no duplica); una vista Soundboard permite añadir archivos de audio propios (mp3/wav/ogg), ponerles nombre y reproducirlos por el micrófono virtual con un botón, respetando la cola; los archivos se convierten con el ffmpeg de la app; tests de pytest de la conversión y de la lista del soundboard (sin reproducir audio de verdad)
- [x] Atajo global para hablar
  criterio: la app es de instancia única (una segunda ejecución con `--decir` avisa a la primera por un socket local y sale); `multivoice --decir` abre en la instancia abierta un cuadro pequeño siempre encima donde se escribe y Enter lo dice; en Windows se registra un atajo global configurable (pynput) que abre ese cuadro; en Linux, como Wayland no permite atajos globales a las apps, Ajustes → Atajos explica cómo asignar `multivoice --decir` a una tecla en el sistema y, en GNOME, ofrece crearlo automáticamente con gsettings; tests de pytest de la instancia única y del paso de mensajes

Verificación manual (el dueño, en Linux con Discord):
- Recorrer los temas; hablar con cada motor; guardar y abrir la biblioteca.
- Crear un perfil y una frase rápida y decirlas en Discord por el micrófono virtual.
- Probar el diccionario, «Escucharme», un sonido del soundboard y el atajo global con Discord delante.

## FASE 3 — Idiomas: inglés por defecto, español opcional

MultiVoice se publica para cualquiera: la interfaz arranca en **inglés** y se
puede cambiar a **español** en Ajustes. Mismo enfoque que Dédalo: el texto fuente
del código está en inglés y `t()` lo traduce con un catálogo español; si falta
una entrada se muestra el inglés. No se traducen las voces, los nombres que el
usuario escribe (perfiles, frases, categorías, sonidos) ni los identificadores
guardados en config.json (por ejemplo `🤖 Robot Sound`, que perfiles y frases
usan como voz). El cambio de idioma se aplica al reiniciar la app.

- [x] Base de idiomas y selector
  criterio: existe `idioma.py` con `t(texto, **kwargs)` (texto fuente en inglés, placeholders `{nombre}` con str.format), `set_idioma()`/`idioma()` y el catálogo `_ES` (inglés → español); config.json guarda `"language"` con `"en"` por defecto (un config.json antiguo sin la clave carga como `"en"`); el idioma se fija con `set_idioma` ANTES de construir cualquier widget (nada de `t()` evaluado al importar un módulo: los nombres de pestañas como LIB_TAB, TAB_FRASES, TAB_SOUNDBOARD y TAB_PRONUNCIACION pasan a funciones o se calculan al construir la interfaz); Ajustes → General tiene un selector «Language / Idioma» (English, Español) que guarda la elección y avisa de que se aplica al reiniciar; tests de pytest: t() en inglés y español, entrada que falta → inglés, placeholders, config sin "language" → "en", y un test que recorre los .py del proyecto (con `ast`) y falla si algún literal pasado a `t()` no está en `_ES`

- [x] Traducir la ventana principal
  criterio: multivoice.py (cabecera, barra de motor y voz, perfiles, ajuste de voz, editor y pestañas, barra inferior, casillas, barra de estado y sus mensajes), panel_cola.py y pantalla_carga.py usan `t()`; en inglés por defecto y en español con `"language": "es"`; tests/gui_smoke.py comprueba que por defecto el botón principal dice «Speak» y que con `"language": "es"` dice «Hablar», y que el resto del smoke sigue pasando en los dos idiomas

- [x] Traducir Ajustes, atajos y el cuadro para decir
  criterio: ajustes.py (secciones General, Audio, Sonido robot y Atajos, con la tabla de atajos y la explicación del atajo global), atajo.py (mensajes visibles) y decir_rapido.py usan `t()`; los nombres de las secciones de Ajustes se muestran traducidos pero la lógica no depende del texto mostrado; gui_smoke abre Ajustes en los dos idiomas

- [x] Traducir Frases, Pronunciación, Soundboard y Biblioteca
  criterio: frases.py, pronunciacion.py, soundboard.py y biblioteca.py usan `t()` en pestañas, botones, cabeceras, diálogos, confirmaciones y mensajes; los datos del usuario y los de ejemplo guardados en config.json no cambian al cambiar de idioma; gui_smoke recorre esas vistas en los dos idiomas

- [x] Traducir mensajes y diálogos del sistema
  criterio: los mensajes que ve el usuario desde tts_engine.py, virtualmic.py, library.py, instancia.py y platform_utils.py (errores, avisos de micrófono virtual o de VB-CABLE, títulos de diálogos de archivos y messagebox) usan `t()`; tests/smoke_test.py sigue pasando

- [x] Sin textos sueltos en español
  criterio: un test de pytest recorre con `ast` todos los .py de la app (fuera de idioma.py y tests/) y falla si encuentra un literal de texto visible en español (con á, é, í, ó, ú, ñ, ¿ o ¡) que no sea un comentario, docstring, voz, nombre de ejemplo o identificador documentado en una lista de excepciones corta y justificada; el test pasa

- [ ] Documentación
  criterio: README.md (en inglés) dice que la interfaz está en inglés por defecto y se cambia a español en Settings → General, y enlaza «Español» a un README.es.md nuevo con la traducción completa (mismas capturas), que enlaza de vuelta «English»; CONTEXTO.md cambia «Interfaz en español» por «Interfaz en inglés por defecto con español opcional (idioma.py)»

Verificación manual:
- Abrir MultiVoice: todo en inglés. Settings → Language → Español, reiniciar: todo en español.
- Hablar, perfiles, frases y soundboard funcionan igual en los dos idiomas.
