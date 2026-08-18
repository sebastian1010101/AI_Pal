# Step 1 — Setup y verificación del esqueleto

## Objetivo
Confirmar que la estructura base del repo (docker-compose, Dockerfiles, backend esqueleto) levanta correctamente antes de escribir lógica nueva.

## Prerrequisitos
- `PROJECT.md`, `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` ya existen en el repo.
- `docker-compose.yml`, `apps/api/Dockerfile`, `apps/web/Dockerfile`, `apps/api/main.py`, `apps/api/requirements.txt`, `.env.example`, `.gitignore` ya existen.
- `apps/web` todavía puede no tener contenido real (se resuelve en Step5) — no es bloqueante para este step.

## Tareas
1. Copiar `.env.example` a `.env` y completar `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` (dejar `LLM_API_KEY`, `STT_API_KEY`, `TTS_API_KEY` vacíos por ahora — no se necesitan todavía).
2. Levantar solo el servicio `db`: `docker compose up db -d`. Confirmar con `docker compose ps` que el healthcheck pasa.
3. Levantar el servicio `api`: `docker compose up api`. Debe iniciar sin errores aunque el resto del pipeline esté sin implementar (los placeholders de `main.py` no impiden que el servidor arranque).
4. Probar `GET /health` en `http://localhost:8000/health` → debe responder `{"status": "ok"}`.
5. Probar `POST /session` → debe devolver un `session_id`.
6. Probar `POST /conversation/message` con `{"session_id": "...", "text": "hola"}` → sin `LLM_API_KEY` configurada, debe responder con el eco placeholder, no un error 500.

## Definición de hecho
Los tres endpoints del punto 4-6 responden como se espera, sin errores de conexión a base de datos ni de build de Docker. No hace falta que la lógica real (memoria, LLM) esté implementada — solo que el esqueleto sea estable.

## Qué NO hacer en este step
- No implementar `search_relevant_memory`, `call_llm`, ni ninguna función marcada `TODO` en `main.py` — eso es Step3 y Step4.
- No tocar `apps/web` todavía.
- No agregar dependencias nuevas al `requirements.txt` sin necesidad concreta de este step.

## Siguiente paso
`Step2.md` — escribir el system prompt del personaje.
