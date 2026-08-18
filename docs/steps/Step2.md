# Step 2 — System prompt y personalidad del personaje

## Objetivo
Definir la personalidad, tono y límites del personaje antes de conectar el LLM real (requisito de ADR-007 — no arrancar M1 sin esto escrito).

## Prerrequisitos
- Step1 completado (el esqueleto levanta).

## Tareas
1. Decidir la identidad del personaje: nombre, rasgos de personalidad, forma de hablar, intereses propios (no un asistente genérico — ver `PROJECT.md`, no-goals: "un solo personaje bien construido").
2. Escribir el system prompt completo en un archivo nuevo `apps/api/prompts/system_prompt.py` (o `.txt`, según se prefiera), no como string embebido en `main.py` — debe poder editarse sin tocar lógica de código.
3. Incluir explícitamente en el prompt:
   - Que el personaje es una IA y no debe fingir ser una persona real si se le pregunta directamente.
   - Instrucción de no usar tácticas de despedida manipulativas (culpa, urgencia artificial) — ver ADR-007.
   - Instrucción de cómo debe comportarse si el usuario expresa angustia real (derivar, no intentar hacer de terapeuta) — ver `PROJECT.md` sección 7.
   - Tono y estilo de las respuestas (longitud, formalidad, uso de humor, etc.).
4. Reemplazar `SYSTEM_PROMPT_PLACEHOLDER` en `main.py` por la carga real de este prompt.
5. Documentar en `docs/DECISIONS.md` (ADR-008) los rasgos de personalidad elegidos y por qué, si hubo alternativas consideradas.

## Definición de hecho
El prompt existe como archivo propio, cubre los 4 puntos obligatorios del punto 3, y `main.py` ya no usa el placeholder.

## Qué NO hacer en este step
- No conectar todavía el LLM real (eso es Step4) — este step es solo el texto del prompt.
- No implementar memoria todavía — el prompt puede referenciar que "recibirá hechos relevantes" sin que la búsqueda esté implementada aún.

## Siguiente paso
`Step3.md` — memoria real con pgvector.
