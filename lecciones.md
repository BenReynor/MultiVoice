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

- Síntoma: el revisor rechazó la ventana nueva porque el ejecutable de PyInstaller no incluía los datos de customtkinter ni assets/temas.
  Causa: temas.py lee assets/temas/*.css en tiempo de ejecución y customtkinter trae archivos propios.
  Prevención: build.yml ya tiene `--collect-all customtkinter` y `--add-data assets/temas`; si añades otra dependencia con datos o una carpeta que se lea en ejecución, añádela también a ese paso de build.yml en la misma tarea.
  Prueba: buscar la dependencia/carpeta en el paso «Build executable» de .github/workflows/build.yml.
