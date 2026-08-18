# Guía de pasos de desarrollo

> **Para el agente:** trabajar un solo `StepN.md` por sesión, en orden. No saltar pasos ni adelantar tareas de un step posterior, aunque parezca más eficiente. Antes de empezar un step, releer `PROJECT.md`, `docs/ARCHITECTURE.md` y `docs/DECISIONS.md` en la raíz del repo — este índice no repite ese contexto, solo secuencia el trabajo.

Cada `StepN.md` sigue el mismo formato:
- **Objetivo** — qué se logra al terminar este step, en una frase.
- **Prerrequisitos** — qué debe estar hecho antes de empezar.
- **Tareas** — checklist concreto.
- **Definición de hecho** — cómo saber que el step está realmente terminado (no "el código compila", sino un criterio verificable).
- **Qué NO hacer en este step** — límites de scope explícitos, para evitar adelantar trabajo de steps futuros.
- **Siguiente paso** — qué step sigue.

## Mapa de steps → fases del roadmap (PROJECT.md sección 5)

| Step | Fase | Contenido |
|---|---|---|
| Step1 | Setup | Verificar que el esqueleto ya generado levanta (docker-compose, healthcheck) |
| Step2 | M1 | System prompt y personalidad del personaje |
| Step3 | M1 | Memoria real: schema de pgvector + extracción de hechos + búsqueda semántica |
| Step4 | M1 | Conexión real al LLM |
| Step5 | M1 | Frontend mínimo: chat de texto conectado al backend |
| Step6 | M1 (checkpoint) | Validar la hipótesis central antes de seguir — no es código |
| Step7 | M2 | Voz: STT + TTS |
| Step8 | M3 | Avatar 3D + lip-sync |
| Step9 | M4 | Guardrails de seguridad, pulido, deploy de la demo |

**Regla importante:** Step6 es un checkpoint de decisión, no una tarea técnica. Si la hipótesis no se sostiene ahí, el proyecto puede (y debe) detenerse o replantearse antes de invertir en M2-M4. Ver `PROJECT.md` sección 2.
