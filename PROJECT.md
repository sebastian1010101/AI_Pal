# AI Companion 3D — Compañero Virtual con Memoria Persistente

> **Nota para el agente de IA que lea este archivo:** este documento es la fuente de verdad del proyecto. Antes de escribir código, léelo completo. Si una instrucción del usuario contradice algo aquí, pregunta antes de asumir — este archivo refleja decisiones ya tomadas y validadas, no un borrador.

## 1. Qué es este proyecto

Un compañero conversacional con un avatar 3D, memoria persistente real entre sesiones, voz propia y personalidad consistente. **Es un proyecto de portfolio técnico, no una startup.** Esto condiciona todas las decisiones de scope: se prioriza la calidad de ingeniería demostrable (arquitectura limpia, decisiones documentadas, pipeline funcionando end-to-end) por encima de crecimiento, monetización o volumen de usuarios.

### Objetivo del proyecto
Demostrar un pipeline conversacional completo (voz + LLM + memoria de largo plazo + avatar 3D animado) funcionando de forma coherente, con decisiones de arquitectura justificadas y documentadas.

### Lo que NO es este proyecto (no-goals explícitos)
- No es una plataforma multi-personaje (un solo personaje bien construido > diez mediocres)
- No es una app con fines de lucro ni pensada para escalar a miles de usuarios
- No busca maximizar tiempo de uso ni retención mediante mecánicas de enganche o manipulación emocional (ver sección 7, Guardrails éticos — es una restricción de diseño, no una sugerencia)
- No incluye VR/AR en el MVP
- No incluye múltiples idiomas, clonación de voz custom, ni estado emocional complejo en el MVP

## 2. Hipótesis a validar (leer antes de programar)

Antes de invertir tiempo en el avatar 3D, hay que validar la hipótesis central del proyecto:

> **¿La memoria persistente genuina —sin trucos de manipulación emocional ni gamificación de la relación— genera suficiente sensación de continuidad como para justificar el resto del pipeline?**

Por eso el roadmap (sección 5) empieza por texto puro, sin avatar ni voz. Si esa fase no se siente bien, no tiene sentido seguir a las fases caras.

## 3. Stack técnico y justificación

| Capa | Tecnología | Por qué |
|---|---|---|
| Frontend | Next.js + React Three Fiber / Three.js | React Three Fiber permite declarar la escena 3D como componentes React, integrándose naturalmente con el estado de la conversación |
| Backend | FastAPI (Python) | Ecosistema maduro para LLM/embeddings; si se prefiere TS end-to-end, NestJS es la alternativa — decidir antes de M1 y no cambiar después |
| Base de datos | PostgreSQL + pgvector | Un solo motor para datos relacionales (perfil, historial) y búsqueda vectorial (memoria semántica) — evita operar dos bases de datos |
| LLM | API de OpenAI (modelo económico, ej. `gpt-4o-mini`) | No se entrena modelo propio; se usa el proveedor con crédito disponible y el valor del proyecto está en la orquestación, no en el modelo (ADR-010) |
| STT | API externa (ej. Deepgram, Whisper API) | Resuelto como commodity, no vale la pena auto-hospedar en el MVP |
| TTS | API externa (ej. ElevenLabs, Inworld TTS) | Igual que STT — priorizar latencia baja sobre calidad máxima |
| Avatar 3D | Modelo base de ReadyPlayerMe (o similar) con blend shapes estándar | No modelar el personaje desde cero — el cuello de botella de un dev solo es rigging/arte, no vale la pena en el MVP |
| Lip-sync | Análisis de frecuencia de audio en el navegador (Web Audio API → visemas) | Evita depender de ML para lip-sync; es el enfoque más rápido de implementar con calidad aceptable |
| Despliegue | Vercel (frontend) + Railway/Render (backend) | Tiers gratuitos suficientes para una demo de portfolio |

**Regla:** cualquier cambio de stack respecto a esta tabla debe registrarse en `docs/DECISIONS.md` con el motivo. No cambiar de tecnología a mitad de una fase sin documentar por qué.

## 4. Estructura del repositorio

```
ai-companion/
├── apps/
│   ├── web/                 # Next.js + React Three Fiber (frontend + avatar)
│   └── api/                 # FastAPI (LLM, memoria, orquestación)
├── packages/
│   └── shared/               # tipos/contratos compartidos entre web y api
├── docs/
│   ├── ARCHITECTURE.md       # diagrama y explicación del pipeline completo
│   └── DECISIONS.md          # registro de decisiones técnicas y trade-offs
├── docker-compose.yml         # levantar todo (postgres, api, web) con un comando
├── .env.example
└── README.md                  # cara pública del proyecto (ver sección 8)
```

## 5. Roadmap por fases (M1–M4)

Cada fase es un milestone en GitHub Projects. No avanzar a la siguiente fase sin haber probado la anterior con uso real (aunque sea propio).

### M1 — Chat con memoria persistente (solo texto)
**Objetivo:** validar la hipótesis de la sección 2.
- Un solo personaje con personalidad fija (system prompt bien trabajado, no genérico)
- Memoria: extraer hechos relevantes de cada conversación y guardarlos en pgvector con embeddings; al iniciar una nueva sesión, recuperar los más relevantes al contexto actual e inyectarlos en el prompt
- Sin autenticación compleja: un usuario de prueba alcanza
- **Criterio de salida de la fase:** usarlo tú mismo (o 2-3 personas) durante al menos 2 semanas reales. Si vuelves espontáneamente sin razón artificial, la hipótesis se sostiene.

### M2 — Voz (STT + TTS)
- Integrar STT para input de voz y TTS para output
- Sigue sin avatar — solo audio
- Medir latencia extremo a extremo (objetivo: menos de 2.5s percibidos)

### M3 — Avatar 3D + lip-sync
- Cargar modelo base con blend shapes
- Implementar lip-sync por análisis de frecuencia (no ML)
- Animaciones básicas de idle/hablando (sin sistema emocional complejo todavía)

### M4 — Pulido, seguridad y demo
- Guardrails de seguridad (sección 7)
- Deploy de la demo pública
- Pulido de UI, README con GIF, `docs/ARCHITECTURE.md` final

## 6. Diseño de la memoria (detalle técnico)

Esto es el componente más importante del proyecto para el objetivo de portfolio — hay que hacerlo bien, no solo "funcional".

- **No guardar el historial completo de la conversación como memoria.** Guardar hechos extraídos y resumidos (ej. "está preparando una presentación para el proyecto X", no el mensaje literal).
- Pipeline sugerido: después de cada sesión (o cada N mensajes), un paso de extracción con el LLM identifica hechos nuevos dignos de recordar → se generan embeddings → se guardan en pgvector con metadata (fecha, tema, importancia estimada).
- Al iniciar una conversación nueva, hacer una búsqueda semántica sobre los últimos mensajes del usuario para recuperar los 3-5 hechos más relevantes, no todo el historial.
- Documentar en `DECISIONS.md` cómo se decide qué es "digno de recordar" — este criterio es una de las partes más interesantes de explicar en una entrevista técnica.

## 7. Guardrails éticos (no negociables, implementar desde M1)

Estos no son "nice to have" para después — se documentó en el análisis previo del proyecto como riesgo real de la categoría (dependencia emocional, casos legales por manipulación, regulación creciente en 2026):

- El personaje debe dejar claro en algún momento del onboarding que es una IA, sin ambigüedad
- **Prohibido implementar tácticas de despedida manipulativas** (culpa, urgencia artificial, "te voy a extrañar" diseñado para generar re-engagement) — esto es parte de lo que diferencia éticamente este proyecto de la categoría estándar del mercado
- Si el usuario expresa señales de angustia real o ideación de daño, el sistema debe poder derivar a recursos reales, nunca simular ser soporte terapéutico
- No hay notificaciones push diseñadas para generar culpa o FOMO
- Los datos de memoria son sensibles: cifrado en reposo como mínimo, y un mecanismo claro para que el usuario pueda borrar su historial

## 8. README.md (para la raíz pública del repo)

El `PROJECT.md` (este archivo) es para desarrollo interno. El `README.md` es la cara pública y debe incluir, en este orden:
1. GIF o video corto del avatar respondiendo con lip-sync (lo primero que se ve)
2. Una frase de qué lo hace distinto ("memoria persistente real", no "chatbot con avatar")
3. Diagrama simple del pipeline
4. Stack técnico (tabla resumida de la sección 3)
5. Cómo correrlo localmente (`docker-compose up`)
6. Link a demo desplegada
7. Link a `docs/ARCHITECTURE.md` y `docs/DECISIONS.md`

## 9. Variables de entorno esperadas (`.env.example`)

```
DATABASE_URL=
LLM_API_KEY=
LLM_MODEL=
STT_API_KEY=
TTS_API_KEY=
```

(Completar con los proveedores elegidos una vez decididos en M1.)

## 10. Checklist antes de empezar a programar

- [ ] Decidir FastAPI vs NestJS y no volver a discutirlo
- [ ] Escribir el system prompt del personaje (personalidad, tono, límites) antes de tocar código de memoria
- [ ] Crear el repo con la estructura de la sección 4 vacía, con `docker-compose.yml` funcional desde el commit inicial
- [ ] Crear el tablero de GitHub Projects con las 4 fases como milestones
