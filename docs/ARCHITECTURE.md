# Arquitectura del sistema

> Este documento explica cómo encajan las piezas del pipeline. Para el qué y el por qué del proyecto, ver `PROJECT.md` en la raíz. Para el historial de decisiones y trade-offs, ver `DECISIONS.md`.

## 1. Visión general del pipeline

```mermaid
flowchart LR
    U[Usuario] -->|voz o texto| WEB[Frontend<br/>Next.js + R3F]
    WEB -->|audio| STT[STT API]
    STT -->|texto transcrito| API[Backend<br/>FastAPI]
    WEB -->|texto directo| API
    API -->|busca contexto relevante| MEM[(PostgreSQL<br/>+ pgvector)]
    MEM -->|hechos relevantes| API
    API -->|prompt + contexto + memoria| LLM[LLM API]
    LLM -->|respuesta texto| API
    API -->|texto respuesta| TTS[TTS API]
    TTS -->|audio| WEB
    API -->|extrae hechos nuevos| MEM
    WEB -->|visemas desde audio| AVATAR[Avatar 3D<br/>lip-sync]
    AVATAR -->|render| U
```

**Regla de oro del diseño:** el backend (`api`) es la única pieza que habla con el LLM, la base de datos y los proveedores de STT/TTS. El frontend nunca llama directamente a esos servicios — evita exponer API keys en el cliente y mantiene toda la lógica de memoria/personalidad en un solo lugar.

## 2. Flujo de una interacción (secuencia)

```mermaid
sequenceDiagram
    participant U as Usuario
    participant W as Frontend (web)
    participant A as Backend (api)
    participant D as PostgreSQL/pgvector
    participant L as LLM

    U->>W: Habla o escribe
    W->>A: POST /conversation/message (audio o texto)
    alt es audio
        A->>A: STT → texto
    end
    A->>D: Búsqueda semántica (embeddings del mensaje actual)
    D-->>A: Top 3-5 hechos relevantes de memoria
    A->>L: system prompt + hechos recuperados + mensaje
    L-->>A: respuesta en texto
    A->>D: (async) evalúa y guarda hechos nuevos dignos de recordar
    A->>A: TTS → audio de la respuesta
    A-->>W: { texto, audio, visemas }
    W->>W: reproduce audio + anima avatar (lip-sync)
    W-->>U: respuesta hablada + animada
```

Nota: el guardado de memoria (`A->>D` async) no debe bloquear la respuesta al usuario — se procesa después de responder, no antes.

## 3. Componentes y responsabilidades

### `apps/web` (Next.js + React Three Fiber)
- Captura de audio/texto del usuario
- Reproducción de audio de respuesta
- Render del avatar 3D y animación de lip-sync a partir de los visemas recibidos (o calculados en el navegador vía Web Audio API, según lo decidido en `DECISIONS.md`)
- **No contiene lógica de negocio** (ni personalidad, ni memoria, ni llamadas directas a LLM/STT/TTS)

### `apps/api` (FastAPI)
- Endpoint principal de conversación (orquesta STT → memoria → LLM → TTS)
- Módulo de memoria: extracción de hechos, generación de embeddings, búsqueda semántica
- System prompt del personaje (personalidad, tono, límites — ver `PROJECT.md` sección 6)
- Guardrails de seguridad (detección de señales de angustia, sin tácticas de despedida manipulativas — `PROJECT.md` sección 7)

### PostgreSQL + pgvector
- Tabla de usuarios/sesiones
- Tabla de "hechos de memoria" con: texto del hecho, embedding, fecha, tema, importancia estimada
- Un solo motor de datos — evita mantener una base relacional y una vector DB por separado

## 4. Diseño de la memoria (detalle)

```mermaid
flowchart TD
    S[Fin de sesión o cada N mensajes] --> E[LLM extrae hechos<br/>dignos de recordar]
    E --> EMB[Genera embedding<br/>de cada hecho]
    EMB --> SAVE[(Guarda en pgvector<br/>texto + embedding + metadata)]

    NS[Nueva sesión / nuevo mensaje] --> QEMB[Embedding del<br/>mensaje actual]
    QEMB --> SEARCH[Búsqueda semántica<br/>top-k en pgvector]
    SAVE -.-> SEARCH
    SEARCH --> INJECT[Inyecta 3-5 hechos<br/>más relevantes en el prompt]
```

Puntos clave a respetar:
- **Nunca** inyectar todo el historial crudo en el prompt — solo hechos resumidos y relevantes al contexto actual.
- La extracción de hechos es un paso propio con el LLM (prompt separado del de conversación), no se mezcla con la respuesta al usuario.
- Cada hecho guarda metadata de importancia/fecha para poder priorizar o hacer "olvido" de hechos poco relevantes con el tiempo (no implementado en el MVP, pero el esquema debe soportarlo desde el inicio).

## 5. Contratos de API (sketch inicial)

```
POST /conversation/message
  body: { session_id, text? , audio_base64? }
  response: { text, audio_base64, visemes[] }

GET /memory/facts?session_id=...
  response: { facts: [{ text, created_at, topic }] }

DELETE /memory/facts?session_id=...
  → borra todo el historial de memoria del usuario (requisito ético, PROJECT.md sección 7)
```

Estos contratos son punto de partida — ajustar y documentar cualquier cambio en `DECISIONS.md`.

## 6. Limitaciones conocidas del MVP (documentar, no ocultar)

- La búsqueda semántica de memoria es simple (top-k por similitud); no hay ranking por recencia + relevancia combinados todavía.
- El lip-sync es por análisis de frecuencia, no por fonemas reales — aceptable visualmente, no es labial-preciso.
- No hay sistema de "olvido" real de memoria antigua, solo el esquema lo soporta.
- Un solo personaje, sin selector de personalidad ni multi-usuario robusto.

Documentar limitaciones explícitamente en la arquitectura es, en sí mismo, una señal de madurez técnica frente a quien revise el repo.
