# Step 3 — Memoria real: schema, extracción y búsqueda semántica

## Objetivo
Reemplazar los placeholders de memoria en `main.py` por una implementación real sobre pgvector, siguiendo el diseño de `docs/ARCHITECTURE.md` sección 4 y ADR-005.

## Prerrequisitos
- Step1 y Step2 completados.

## Tareas
1. Crear el schema de la tabla de hechos de memoria (SQLAlchemy model): texto del hecho, embedding (vector), `session_id`, fecha, tema, importancia estimada — ver `ARCHITECTURE.md` sección 3 ("PostgreSQL + pgvector").
2. Configurar la migración/creación de tabla (Alembic si se quiere prolijo, o SQL directo para el MVP — documentar la elección en `DECISIONS.md` si se decide no usar Alembic).
3. Implementar `extract_and_save_facts` en `main.py`:
   - Llamar al LLM con un prompt de extracción separado del prompt de conversación (no reusar el system prompt del personaje).
   - Generar embedding del hecho extraído.
   - Guardar en la tabla.
4. Implementar `search_relevant_memory`:
   - Generar embedding del mensaje del usuario.
   - Búsqueda top-k (k=3 a 5) por similitud de coseno en pgvector, filtrado por `session_id`.
5. Implementar de verdad `GET /memory/facts` y `DELETE /memory/facts` (hasta ahora placeholders) — el borrado es requisito no negociable de ADR-007.
6. Probar manualmente: mandar 2-3 mensajes con datos personales inventados, verificar que quedan guardados en la tabla, y que `search_relevant_memory` los recupera al mandar un mensaje relacionado.

## Definición de hecho
Una conversación de prueba genera hechos guardados verificables en la base de datos, y una segunda conversación (mismo `session_id`) recupera esos hechos correctamente por relevancia semántica, no solo por orden cronológico.

## Qué NO hacer en este step
- No implementar ranking combinado de recencia + relevancia — el MVP usa solo similitud semántica (ver `ARCHITECTURE.md` sección 6, limitaciones conocidas).
- No implementar "olvido" de hechos antiguos — el schema debe soportarlo a futuro, pero no es tarea de este step.
- No optimizar performance de la búsqueda todavía — priorizar que funcione correctamente.

## Siguiente paso
`Step4.md` — conexión real al LLM de conversación.
