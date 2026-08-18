# Step 4 — Conexión real al LLM

## Objetivo
Reemplazar el placeholder de `call_llm` en `main.py` por una llamada real al proveedor configurado en `.env` (`LLM_API_KEY`, `LLM_MODEL`).

## Prerrequisitos
- Step2 completado (system prompt ya existe como archivo propio).
- Step3 completado (hay hechos de memoria reales para inyectar en el prompt, aunque sea con pocos datos de prueba).

## Tareas
1. Completar `LLM_API_KEY` y `LLM_MODEL` en `.env` (no en `.env.example`, que se mantiene sin valores reales).
2. Implementar `call_llm` en `main.py`: construir el mensaje combinando el system prompt (Step2) + los hechos relevantes recuperados (Step3, formateados de forma legible, no como JSON crudo) + el mensaje del usuario.
3. Manejar errores de la API del proveedor (timeout, rate limit) con una respuesta de fallback razonable, no un 500 sin contexto.
4. Probar end-to-end: `POST /conversation/message` con texto real debe devolver una respuesta generada por el LLM, coherente con la personalidad definida en Step2.
5. Probar que la memoria efectivamente cambia la respuesta: mandar un hecho en un mensaje, en un mensaje posterior (mismo `session_id`) preguntar algo relacionado y confirmar que el LLM lo usa en la respuesta.

## Definición de hecho
El endpoint de conversación funciona completamente en texto: recibe un mensaje, usa memoria real cuando es relevante, y responde con la personalidad definida — sin ningún placeholder activo en el camino texto-a-texto.

## Qué NO hacer en este step
- No tocar STT ni TTS — siguen sin implementarse hasta Step7.
- No optimizar costos de tokens todavía (eso puede documentarse como mejora futura, no bloquea este step).

## Siguiente paso
`Step5.md` — frontend mínimo conectado al backend. Con este step termina la parte de backend puro de M1.
