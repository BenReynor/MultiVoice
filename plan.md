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
- [ ] Escucharse a uno mismo y soundboard
  criterio: un interruptor «Escucharme» reproduce también por la salida normal lo que suena por el micrófono virtual (en Linux y en Windows; si no hay micrófono virtual no duplica); una vista Soundboard permite añadir archivos de audio propios (mp3/wav/ogg), ponerles nombre y reproducirlos por el micrófono virtual con un botón, respetando la cola; los archivos se convierten con el ffmpeg de la app; tests de pytest de la conversión y de la lista del soundboard (sin reproducir audio de verdad)
- [ ] Atajo global para hablar
  criterio: la app es de instancia única (una segunda ejecución con `--decir` avisa a la primera por un socket local y sale); `multivoice --decir` abre en la instancia abierta un cuadro pequeño siempre encima donde se escribe y Enter lo dice; en Windows se registra un atajo global configurable (pynput) que abre ese cuadro; en Linux, como Wayland no permite atajos globales a las apps, Ajustes → Atajos explica cómo asignar `multivoice --decir` a una tecla en el sistema y, en GNOME, ofrece crearlo automáticamente con gsettings; tests de pytest de la instancia única y del paso de mensajes

Verificación manual (el dueño, en Linux con Discord):
- Recorrer los temas; hablar con cada motor; guardar y abrir la biblioteca.
- Crear un perfil y una frase rápida y decirlas en Discord por el micrófono virtual.
- Probar el diccionario, «Escucharme», un sonido del soundboard y el atajo global con Discord delante.
