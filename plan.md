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
  criterio: un perfil guarda motor, voz, velocidad, tono, volumen y metal con un nombre (p. ej. «Robot», «Narrador»); se crean, renombran y borran desde la interfaz y se eligen con un desplegable en la barra de voz; se guardan en config.json; vienen dos perfiles de ejemplo; tests de pytest de guardar/cargar/borrar perfiles y de config.json antiguo sin perfiles
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

- [x] Documentación
  criterio: README.md (en inglés) dice que la interfaz está en inglés por defecto y se cambia a español en Settings → General, y enlaza «Español» a un README.es.md nuevo con la traducción completa (mismas capturas), que enlaza de vuelta «English»; CONTEXTO.md cambia «Interfaz en español» por «Interfaz en inglés por defecto con español opcional (idioma.py)»

Verificación manual:
- Abrir MultiVoice: todo en inglés. Settings → Language → Español, reiniciar: todo en español.
- Hablar, perfiles, frases y soundboard funcionan igual en los dos idiomas.

## FASE 4 — Cientos de voces y voces más fiables

MultiVoice pasa de 14 voces en español a cientos en todos los idiomas, añade voces
**sin internet** que se descargan solo si el usuario las elige (el programa no
pesa más) y deja de quedarse callado sin red. Reglas para toda la fase: los tests
nunca usan la red (listas de voces y descargas simuladas), los textos nuevos van
con `t()` y su entrada en `_ES`, y todo funciona igual en Linux y Windows.

- [ ] Todas las voces de Edge, en todos los idiomas
  criterio: la lista de voces de Edge sale de `edge_tts.list_voices()` (todas las locales, no solo español) y se guarda en caché en la carpeta de config (se refresca como mucho una vez al día; sin red se usa la caché y, si no hay, la lista española actual de respaldo); cada voz tiene idioma, país, género y nombre legible; el texto de ayuda del motor deja de decir «14 Spanish voices» y muestra el total real; perfiles y frases con voces antiguas siguen funcionando; tests con una lista simulada (agrupar por idioma, caché vigente/caducada, sin red)

- [ ] Selector de voces con idioma, buscador, escucha previa y favoritas
  criterio: siguiendo las skills ui-tokens y diseno-escritorio, el desplegable de voz se sustituye por un selector con filtro de idioma (por defecto el de la interfaz), filtro de motor, buscador (nombre, idioma, país), botón ▶ para escuchar una frase de prueba sin elegirla, estrella de favoritas (guardadas en config.json y mostradas arriba) y marcas «sin internet» / «requiere descarga»; se abre también con un atajo de teclado; gui_smoke abre el selector, filtra, marca una favorita y elige una voz

- [ ] Voces locales Piper descargables
  criterio: nuevo motor «Piper (offline)»; MultiVoice no incluye Piper: al elegirlo por primera vez ofrece descargar el ejecutable oficial de Piper para el sistema (Linux x86_64/arm64, Windows x64) y cada voz se descarga al elegirla (catálogo oficial de voces con idioma, calidad y tamaño), con barra de progreso, cancelar, comprobación SHA-256 y carpeta de datos del usuario; Ajustes → Voces lista las voces descargadas con su tamaño y permite borrarlas; la síntesis usa el mismo paso final de ffmpeg que los otros motores; tests con descargas simuladas (catálogo, suma correcta/incorrecta, cancelar) y un test que sintetiza con un ejecutable Piper falso

- [ ] Voces del sistema en Windows y más robots
  criterio: en Windows, nuevo motor «Windows voices» que lista y usa las voces instaladas del sistema mediante System.Speech (PowerShell, sin dependencias nuevas) y escribe un WAV que pasa por el paso final de ffmpeg; en Linux el motor no aparece; el robot (espeak-ng) ofrece variantes (voces e idiomas de espeak-ng y sus variantes como susurro o ronco) además del sonido robot actual; tests: comando de PowerShell generado (sin ejecutarlo fuera de Windows), lista de variantes de espeak-ng simulada

- [ ] Plan B sin conexión
  criterio: si Edge o Google fallan por falta de red o error del servicio, el texto se dice con una voz local (la elegida en Ajustes → Audio «Offline fallback voice»: una voz Piper descargada o el robot) y la barra de estado avisa una vez («Sin conexión: usando voz local»); se puede desactivar; el fallo no bloquea la cola ni la interfaz; tests con el motor online simulado fallando (usa la voz de respaldo, avisa una sola vez, desactivado = error como hoy)

- [ ] Hablar mientras se genera y caché de audio
  criterio: un texto largo se parte por frases y empieza a sonar en cuanto está la primera mientras se generan las siguientes (sin cortes audibles entre frases ni cambios de orden); una caché local guarda cada audio generado con clave (motor, voz, ajustes, efectos, texto), con tope de tamaño configurable (por defecto 200 MB, se borra lo más antiguo) y botón «Vaciar caché» en Ajustes; repetir una frase rápida o del historial suena al instante; las frases rápidas se pregeneran en segundo plano al elegir perfil; tests: partir frases (abreviaturas, signos ¿?¡!, números), orden de reproducción, acierto/fallo de caché, tope de tamaño

- [ ] Volumen igualado y botón Callar global
  criterio: el paso final de ffmpeg normaliza el volumen (loudnorm) para que todos los motores suenen parejos; opción en Ajustes → Audio (activada por defecto); «Detener» corta lo que suena y vacía la cola y tiene un atajo global: en Windows registrado por la app y en Linux mediante `multivoice --callar` (mismo mecanismo de instancia única que `--decir`), mostrado en Ajustes → Atajos con el botón de GNOME como el atajo de decir; tests de la orden `--callar` por instancia única y del filtro de normalización generado

Verificación manual:
- Elegir una voz en inglés y otra en japonés de Edge; marcar favoritas.
- Descargar una voz Piper en español y hablar con el Wi-Fi apagado; con una voz de Edge y sin red, comprobar el plan B.
- Pegar un texto de 10 frases: empieza a sonar enseguida. Repetir una frase rápida: suena al instante.
- Atajo de Callar en mitad de un texto largo.

## FASE 5 — Laboratorio de voces: efectos, etiquetas y paquetes

MultiVoice como un «Loquendo moderno»: cualquier voz se convierte en un personaje
con efectos encadenables, y el texto puede cambiar de voz, hacer pausas y meter
sonidos a mitad de frase. Todos los efectos se aplican con ffmpeg (ya incluido),
así que funcionan con todos los motores.

- [ ] Motor de efectos encadenables
  criterio: módulo `efectos.py` con un catálogo de efectos (id, nombre con `t()`, categoría, parámetro de intensidad 0–100) que genera la cadena de filtros de ffmpeg: tono y ritmo (tono, velocidad, vibrato, temblor), robots (robot/metal actual, alien, 8 bits, distorsión, radio militar), personajes (demonio, ardilla, gigante, fantasma, susurro, coro), lugares (eco, cueva, sala, catedral, baño, bajo el agua, exterior) y aparatos (teléfono, radio vieja, megáfono, walkie-talkie, estadio); un perfil guarda una lista ordenada de efectos con su intensidad (`efectos` en config.json); el «metal» actual del robot se migra a un efecto sin cambiar cómo suena; tests: cada efecto genera un filtro válido (ffmpeg lo acepta con un WAV corto de silencio generado en el test), el orden se respeta, migración del metal

- [ ] Vista «Voice lab»
  criterio: siguiendo las skills ui-tokens y diseno-escritorio, una vista nueva para editar el personaje del perfil activo: añadir efectos por categoría, reordenarlos, quitar, deslizador de intensidad, ▶ escuchar el resultado con una frase de prueba o el texto actual, y guardar en el perfil; ajustes listos incluidos (p. ej. «Robot», «Narrador de terror», «Locutor de radio», «Demonio», «Ardilla», «Fantasma», «Teléfono») que se aplican con un clic y luego se pueden retocar; gui_smoke abre la vista, añade dos efectos, cambia el orden y guarda

- [ ] Etiquetas dentro del texto
  criterio: módulo `etiquetas.py` que interpreta `[voz:Perfil]`, `[pausa:segundos]`, `[sonido:nombre del soundboard]` y `[efecto:id] … [/efecto]` (sin distinguir mayúsculas; acepta también `[voice:…]`, `[pause:…]`, `[sound:…]`, `[effect:…]`), divide el texto en tramos y los dice en orden en un solo audio continuo; una etiqueta desconocida o un perfil/sonido inexistente se muestra en la barra de estado y se dice el resto; opción «Interpretar etiquetas» en Ajustes (activada); el editor colorea las etiquetas y la ayuda (Ajustes → Atajos o un botón «?») las explica; tests del analizador (anidado no permitido, valores inválidos, texto sin etiquetas igual que hoy) y de la combinación de tramos

- [ ] Paquetes para compartir
  criterio: «Export pack» guarda en un archivo `.mvpack` (zip con JSON) los perfiles elegidos con sus efectos, las frases rápidas, el diccionario y, opcionalmente, los sonidos del soundboard; «Import pack» muestra lo que contiene, avisa de choques de nombres (renombrar, reemplazar u omitir) y lo añade; un paquete nunca incluye claves, rutas personales ni la biblioteca; se rechazan paquetes corruptos, con rutas fuera del paquete (zip slip) o de más de 50 MB; tests de exportar → importar, choques de nombres y paquetes maliciosos

Verificación manual:
- Crear un personaje «demonio + eco + radio» y usarlo en Discord.
- Escribir `[voz:Robot] Acceso denegado. [pausa:1] [voz:Narrador] Y entonces… [sonido:risa]` y escucharlo de corrido.
- Exportar un paquete, importarlo en otra instalación.

## FASE 6 — Diversión y comodidad para directos

- [ ] Avatar PNGtuber
  criterio: ventana opcional «Avatar» que muestra una imagen con la boca cerrada y otra con la boca abierta (y opcional parpadeo) según el nivel del audio que suena (el mismo medidor del panel), con umbral y suavizado ajustables; fondo de color sólido configurable (verde por defecto) o transparente donde el sistema lo permita, para capturarla en OBS; las imágenes las elige el usuario (PNG/GIF) y se incluye un avatar sencillo de ejemplo propio; se puede asignar un avatar por perfil; tests de la lógica de boca abierta/cerrada con niveles simulados y gui_smoke abre la ventana

- [ ] Atajos de perfil y órdenes para Stream Deck
  criterio: Ctrl+Shift+1…9 eligen los perfiles 1–9; la línea de comandos acepta `--decir "texto"` (dice el texto sin abrir el cuadro), `--frase N`, `--perfil "Nombre"` y `--callar`, enviadas a la ventana abierta por instancia única (si no hay ninguna, se abre); Ajustes → Atajos lo explica con ejemplos para Stream Deck, atajos del sistema y scripts; tests de cada orden por instancia única

Verificación manual:
- Avatar en OBS que mueve la boca al hablar.
- Un botón de Stream Deck (o un atajo del sistema) que dice una frase rápida.

## FASE 7 — Fácil de empezar, accesible y siempre al día

- [ ] Asistente de primer uso y prueba del micrófono
  criterio: la primera vez (o desde Ajustes → «Run setup again») un asistente de 3–4 pasos: idioma, elegir y escuchar una voz, comprobar el micrófono virtual (en Linux reproduce un tono por el 🎤 y lo capta desde su monitor para confirmar que llega señal; en Windows comprueba que VB-CABLE existe) y una pantalla con cómo elegirlo en Discord; se puede saltar; tests de la lógica de pasos y de la comprobación con señal simulada; gui_smoke recorre el asistente

- [ ] Asistente de VB-CABLE en Windows
  criterio: si en Windows no se detecta VB-CABLE, en vez de solo avisar se muestra una guía paso a paso (qué es, botón que abre la página oficial de descarga, instalar como administrador, reiniciar) y un botón «Check again» que lo detecta sin reiniciar la app; tests de la detección con dispositivos simulados

- [ ] Accesibilidad
  criterio: toda la ventana principal, Ajustes, el selector de voces y el Voice lab se pueden usar solo con teclado (orden de tabulación lógico, foco visible en todos los temas, Enter/Espacio activan, Esc cierra); Ajustes → General tiene «Text size» (90–150 %) que escala toda la interfaz; los botones solo con icono tienen texto alternativo o tooltip; tests: gui_smoke recorre con Tab los controles principales y aplica el tamaño 150 % sin errores

- [ ] Aviso de versión nueva
  criterio: al arrancar (opción en Ajustes, activada por defecto) se consulta la última release de GitHub (`/repos/BenReynor/MultiVoice/releases/latest`) con tiempo límite corto y sin bloquear la ventana; si hay una versión mayor, un aviso discreto con las notas y el enlace de descarga para el sistema del usuario; «Ignorar esta versión»; sin red no molesta; la app conoce su propia versión (constante única usada también por el empaquetado); tests de comparación de versiones y con respuestas simuladas (más nueva, igual, error)

- [ ] AppImage para Linux
  criterio: el workflow de build genera además `MultiVoice-x86_64.AppImage` (con icono PNG y `.DirIcon`, lanzador y las dependencias incluidas como el binario actual) que crea el 🎤 igual; README (en y es) lo añade a la tabla de descargas con instrucciones (`chmod +x`); el zip se mantiene

- [ ] Documentación y capturas
  criterio: README.md y README.es.md describen las voces (cientos de voces, Piper sin internet, voces de Windows), el Voice lab con la lista de efectos, las etiquetas con un ejemplo, los paquetes, el avatar, las órdenes de línea de comandos y el asistente; las capturas de docs/capturas/en y docs/capturas/es se rehacen con la interfaz nueva y textos de ejemplo generales; CONTEXTO.md actualizado con los módulos nuevos

Verificación manual:
- Borrar config.json: aparece el asistente y en 1 minuto se habla en Discord.
- Navegar la app solo con teclado y con texto al 150 %.
- Simular una versión vieja y ver el aviso.

## Más adelante (ideas, sin criterios todavía)
- Cambiador de voz del micrófono en tiempo real (tu voz con los efectos del Voice lab), empezando por efectos simples y vigilando la latencia.
- Bajar la música y otros sonidos mientras habla (ducking): Linux primero.
- Control desde el móvil (WebUI en la red local: escribir en el móvil y que hable el PC).
- Voces Kokoro descargables.
- Servicios de voz de pago con la clave propia del usuario (ElevenLabs, OpenAI, Azure), siempre opcionales.
- Clonación de voz opcional como descarga aparte, con aviso y consentimiento (no imitar a personas reales sin permiso).
- Integración con ARGUS: que un bot lea en voz alta mensajes de un canal o del chat de un directo.
- Traducir antes de hablar (escribir en un idioma y hablar en otro).
