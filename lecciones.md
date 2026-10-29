# Lecciones aprendidas — memoria del proyecto

Cada lección evita repetir un error ya corregido (corrección única de errores).
El agente lee este archivo antes de cada tarea, así que escribe aquí TODO lo que
no quieras que vuelva a pasar. El dedalo añade una entrada automática cuando
una tarea queda bloqueada ([B]).

Formato recomendado:
- Síntoma: qué falló.
- Causa: por qué falló.
- Prevención: qué hacer para no repetirlo (o qué cambiar en plan.md).
- Prueba: cómo verificar que está resuelto (test/check).

Añade las tuyas con el botón "+ Nueva lección" de la pestaña Memoria, o a mano.
## 2026-10-29 00:40 — Tarea bloqueada: Ventana principal con CustomTkinter
- Síntoma: El agente no cumplió el criterio tras 2 intentos.
- Causa: revisor_fail en la iteración 2: El criterio de la tarea se cumple: CustomTkinter está en `requirements.txt`, la ventana usa la paleta de `temas.py` con cabecera, Probar, metal condicional, pestañas, Hablar/Detener/Guardar y atajos, y los tests usan rutas temporales. Hay un fallo de empaquetado: `temas.py` lee `assets/temas/*.css` en tiempo de ejecución (`carpeta_temas()` usa `sys._MEIPASS` en el build), pero `build.yml` solo añade `--add-data "bundle/bin"` y no incluye `assets/temas`. El ejecutable de PyInstaller arrancaría sin los temas y `temas.paleta()` en `TTSApp.__init__` fallaría al abrir el CSS. El smoke test corre desde el código fuente, así que no lo detecta. Hay que añadir `assets/temas` al `--add-data` del build.
- Prevención: Reformular la tarea en plan.md, dividirla en pasos más pequeños o revisar los criterios.
