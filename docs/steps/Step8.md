# Step 8 — Avatar 3D + lip-sync (M3)

## Objetivo
Reemplazar la interfaz de chat plano por un avatar 3D animado que hace lip-sync con el audio de la respuesta.

## Prerrequisitos
- Step7 completado: hay audio de respuesta real disponible en el frontend.

## Tareas
1. Elegir y descargar un modelo base con blend shapes estándar (ver ADR-003 — no modelar desde cero).
2. Configurar React Three Fiber en `apps/web` para cargar y renderizar el modelo.
3. Implementar el análisis de frecuencia del audio (Web Audio API) para generar visemas en tiempo real, siguiendo el enfoque de ADR-004 (no ML).
4. Mapear los visemas a los blend shapes del modelo para animar la boca mientras se reproduce el audio de respuesta.
5. Agregar animaciones básicas de idle (cuando no está hablando) — sin sistema emocional complejo todavía (ver `PROJECT.md`, no-goals).
6. Probar con distintas frases (cortas, largas, con pausas) para verificar que el lip-sync se ve razonable, sin esperar precisión fonética exacta (ver limitación conocida en `ARCHITECTURE.md` sección 6).

## Definición de hecho
El avatar se renderiza en el navegador, mueve la boca de forma reconocible como habla (no perfecta) mientras se reproduce el audio de respuesta, y tiene una animación de idle cuando no está hablando.

## Qué NO hacer en este step
- No perseguir realismo fotográfico ni animaciones faciales complejas de emoción — el scope es lip-sync básico + idle.
- No implementar VR/AR (WebXR queda fuera del MVP, ver `PROJECT.md`).

## Siguiente paso
`Step9.md` — guardrails de seguridad, pulido y deploy de la demo pública.
