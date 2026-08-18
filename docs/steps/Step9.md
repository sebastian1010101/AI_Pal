# Step 9 — Guardrails de seguridad, pulido y deploy (M4)

## Objetivo
Cerrar el proyecto a nivel de seguridad, presentación y disponibilidad de una demo pública para portfolio.

## Prerrequisitos
- Step8 completado: el pipeline completo (texto/voz → memoria → LLM → voz → avatar) funciona de punta a punta.

## Tareas

### Seguridad (no negociable — ver ADR-007)
1. Implementar detección básica de señales de angustia en el mensaje del usuario (puede ser un paso adicional del LLM, con un prompt separado y explícito para esto) que dispare una respuesta de derivación a recursos reales, no una simulación de soporte terapéutico.
2. Confirmar que en ningún punto del prompt o del flujo de conversación hay lenguaje diseñado para generar culpa o urgencia artificial al despedirse.
3. Verificar que `DELETE /memory/facts` funciona correctamente y está accesible desde el frontend (no solo desde la API).
4. Agregar al onboarding del frontend un mensaje claro de que el personaje es una IA.

### Pulido
5. Mejorar el diseño visual del frontend (ya no es solo funcional, como en Step5).
6. Agregar manejo de errores visible al usuario (ej. si el LLM o TTS fallan, mostrar un estado de error claro, no que la app se cuelgue en silencio).
7. Revisar y completar `README.md` en la raíz (distinto de `PROJECT.md`) con el formato definido: GIF/video, frase de qué lo diferencia, diagrama, stack, cómo correrlo, link a demo, links a `docs/`.

### Deploy
8. Desplegar `apps/web` en Vercel.
9. Desplegar `apps/api` + base de datos en Railway o Render (ver `PROJECT.md` sección 3).
10. Configurar límite de mensajes por sesión en la demo pública para controlar costo de API si la prueba gente desconocida.
11. Agregar badge de CI (GitHub Actions) si hay tests básicos configurados.

## Definición de hecho
Existe una URL pública funcional del proyecto, el `README.md` está completo con GIF, y los guardrails de seguridad del punto 1-4 están verificablemente implementados, no solo documentados como intención.

## Qué NO hacer en este step
- No agregar features nuevas de producto en este step — es cierre y pulido de lo ya construido, no expansión de scope.

## Siguiente paso
Ninguno — este es el cierre del roadmap M1-M4 definido en `PROJECT.md`. Cualquier trabajo posterior (multi-personaje, VR/AR, estado emocional complejo) requiere una decisión explícita de ampliar el scope del proyecto, documentada como ADR nuevo en `DECISIONS.md`.
