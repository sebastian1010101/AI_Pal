# Step 7 — Voz: STT + TTS (M2)

## Objetivo
Agregar entrada y salida de voz al chat existente, sin avatar todavía.

## Prerrequisitos
- Step6 completado, con señal suficiente para seguir invirtiendo en el proyecto.

## Tareas
1. Elegir proveedor de STT y completar `STT_API_KEY` en `.env` (ver `PROJECT.md` sección 3 para opciones consideradas).
2. Implementar `transcribe_audio` en `main.py`, reemplazando el placeholder actual.
3. Elegir proveedor de TTS y completar `TTS_API_KEY`.
4. Implementar `synthesize_speech` en `main.py`, reemplazando el placeholder actual (`return None`).
5. En el frontend: agregar captura de audio del micrófono (grabación simple, sin necesidad de streaming en tiempo real todavía) y reproducción del audio de respuesta.
6. Medir la latencia extremo a extremo (desde que el usuario termina de hablar hasta que empieza a sonar la respuesta) — objetivo de referencia: menos de 2.5 segundos percibidos (ver `ARCHITECTURE.md`).
7. Si la latencia es alta, documentar en `DECISIONS.md` qué se probó y qué trade-off se tomó (ej. modelo de TTS más rápido vs. más natural).

## Definición de hecho
Se puede hablar por micrófono desde el navegador y recibir una respuesta hablada del personaje, con memoria y personalidad ya funcionando desde M1.

## Qué NO hacer en este step
- No implementar clonación de voz custom — usar una voz preset del proveedor elegido (ver `PROJECT.md`, no-goals).
- No tocar el avatar 3D todavía — eso es Step8, y depende de tener el audio de respuesta funcionando primero (el lip-sync necesita ese audio).

## Siguiente paso
`Step8.md` — avatar 3D y lip-sync.
