# Registro de decisiones (DECISIONS.md)

> Formato: cada decisión documenta el contexto, la decisión tomada, las alternativas descartadas y el trade-off aceptado. No editar decisiones pasadas — si algo cambia, agregar una entrada nueva con status "Reemplaza a ADR-00X".

---

## ADR-001 — Backend en FastAPI (no NestJS)

**Estado:** Aceptada

**Contexto:** El backend necesita orquestar STT, LLM, TTS y búsqueda vectorial en pgvector. Las dos opciones evaluadas fueron FastAPI (Python) y NestJS (TypeScript).

**Decisión:** FastAPI.

**Motivo:** El ecosistema de Python es más maduro para trabajar con embeddings, LLMs y librerías de IA en general (la mayoría de SDKs y ejemplos de referencia están en Python primero). Evita fricción de traducir patrones entre lenguajes.

**Trade-off aceptado:** el proyecto queda con dos lenguajes (TS en frontend, Python en backend) en vez de TypeScript end-to-end. Se acepta porque la ventaja en el ecosistema de IA pesa más que la comodidad de un solo lenguaje para un proyecto de este tamaño.

**No reabrir esta decisión a mitad de una fase.**

---

## ADR-002 — Un solo motor de datos: PostgreSQL + pgvector

**Estado:** Aceptada

**Contexto:** El sistema necesita almacenamiento relacional (usuarios, sesiones) y búsqueda vectorial (memoria semántica). Se evaluó usar una vector DB dedicada (ej. Pinecone, Weaviate) separada de la base relacional.

**Decisión:** Un único PostgreSQL con la extensión pgvector para ambos usos.

**Motivo:** Para el volumen de datos de un proyecto de portfolio (no miles de usuarios concurrentes), pgvector es suficiente y evita operar y sincronizar dos sistemas de almacenamiento distintos.

**Trade-off aceptado:** si el proyecto escalara a un volumen serio de usuarios, una vector DB dedicada probablemente tendría mejor rendimiento de búsqueda. Se acepta el límite porque no es un objetivo del proyecto (ver `PROJECT.md`, no-goals).

---

## ADR-003 — Avatar base pre-hecho, no modelado desde cero

**Estado:** Aceptada

**Contexto:** Se evaluó modelar y riggear un personaje 3D original en Blender vs. usar un modelo base con blend shapes estándar (ej. ReadyPlayerMe).

**Decisión:** Modelo base pre-hecho con blend shapes estándar.

**Motivo:** El cuello de botella real de un desarrollador individual en este proyecto es el rigging facial y las animaciones, no la lógica de IA. Modelar desde cero consumiría la mayor parte del tiempo disponible sin aportar valor técnico diferencial al objetivo del proyecto (demostrar el pipeline conversacional + memoria).

**Trade-off aceptado:** el avatar no tiene una identidad visual 100% original. Se acepta porque el diferenciador del proyecto es la memoria y la conversación, no el arte del personaje.

---

## ADR-004 — Lip-sync por análisis de frecuencia, no por modelo de ML

**Estado:** Aceptada

**Contexto:** Existen dos enfoques para lip-sync: (a) modelos de ML que predicen visemas a partir de fonemas (ej. Rhubarb), o (b) análisis de frecuencia del audio en tiempo real (Web Audio API → mapeo a formas de boca).

**Decisión:** Análisis de frecuencia en el navegador.

**Motivo:** Es más rápido de implementar, no requiere preprocesamiento ni modelos adicionales, y da un resultado visualmente aceptable para el objetivo del proyecto (no se busca precisión labial de nivel producción).

**Trade-off aceptado:** el lip-sync es aproximado, no fonéticamente preciso. Documentado también como limitación conocida en `ARCHITECTURE.md`.

---

## ADR-005 — Memoria como hechos extraídos, no historial crudo

**Estado:** Aceptada

**Contexto:** Se evaluó guardar el historial completo de mensajes como memoria (más simple) vs. un paso de extracción que resume hechos relevantes antes de guardarlos.

**Decisión:** Extracción de hechos resumidos, con embedding y metadata, en vez de guardar mensajes crudos.

**Motivo:** Inyectar historial crudo en el prompt escala mal (crece sin límite) y mezcla ruido conversacional con información realmente relevante. Extraer hechos permite una recuperación semántica más precisa y un prompt más corto y controlado.

**Trade-off aceptado:** requiere un paso extra de LLM (costo y latencia adicional) después de cada sesión. Se acepta porque ocurre de forma asíncrona y no bloquea la respuesta al usuario (ver `ARCHITECTURE.md`, sección 2).

---

## ADR-006 — Sin VR/AR, sin multi-personaje, sin estado emocional complejo en el MVP

**Estado:** Aceptada

**Contexto:** La visión de largo plazo del proyecto incluye WebXR y múltiples personajes/personalidades. Se evaluó incluir alguno de estos desde el inicio.

**Decisión:** Ninguno de los tres entra en el MVP (ver `PROJECT.md`, no-goals y roadmap M1-M4).

**Motivo:** Cada uno de estos aumenta significativamente el alcance sin aportar a la hipótesis central del proyecto (sección 2 de `PROJECT.md`). Priorizar validar esa hipótesis con el menor scope posible.

**Trade-off aceptado:** el proyecto se ve menos "espectacular" en una primera demo comparado con un producto multi-personaje en VR. Se acepta porque el objetivo es demostrar profundidad técnica en un pipeline bien hecho, no amplitud de features.

---

## ADR-007 — Guardrails éticos son requisito desde M1, no un extra de M4

**Estado:** Aceptada

**Contexto:** La categoría de "AI companions" tiene antecedentes documentados de tácticas de retención manipulativas y riesgos legales/regulatorios asociados (ver análisis de mercado previo al proyecto).

**Decisión:** Prohibido implementar tácticas de despedida manipulativas o mecánicas de enganche basadas en culpa/urgencia, en cualquier fase del proyecto. Detección de señales de angustia y derivación a recursos reales es un requisito, no un nice-to-have.

**Motivo:** Es tanto una decisión ética como de diferenciación de portfolio: un proyecto que demuestra diseño responsable en una categoría con problemas conocidos de la industria es más valioso que uno que los ignora.

**Trade-off aceptado:** renunciar a los mecanismos de retención más efectivos del mercado (ver `PROJECT.md`, sección 7). Esto es intencional y no debe revertirse por presión de "mejorar métricas".

---

## ADR-008 — Nara como compañera cálida, curiosa y con criterio propio

**Estado:** Aceptada

**Contexto:** M1 requiere un único personaje reconocible y consistente, no un asistente genérico. Se consideró un tono completamente complaciente y afectuoso, uno más excéntrico y humorístico, y uno cálido pero sereno con opiniones propias.

**Decisión:** El personaje se llama Nara. Es cálida, observadora, curiosa y serena; puede disentir con respeto, usa humor seco de forma ocasional y se interesa por historias, juegos narrativos, ciencia ficción, astronomía, diseño y detalles cotidianos. Habla en español conversacional con voseo ligero y responde de forma breve por defecto.

**Motivo:** La calidez facilita una conversación cercana, mientras que el criterio propio, los intereses definidos y la moderación evitan tanto el tono de asistente genérico como una personalidad invasiva o artificialmente intensa.

**Trade-off aceptado:** el tono contenido puede resultar menos efusivo para usuarios que prefieren interacción muy afectuosa, y el voseo le da una identidad regional en vez de un español totalmente neutro.

---

## ADR-009 — Embeddings externos con Voyage AI

**Estado:** Aceptada

**Contexto:** La memoria semántica de Step3 necesita generar embeddings en español. Se evaluó ejecutar localmente `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` y consumir Voyage AI, el proveedor de embeddings recomendado en la documentación de Anthropic. El despliegue previsto para Step9 usa tiers gratuitos de Railway o Render.

**Decisión:** Usar la API de Voyage AI con `voyage-4-lite`, embeddings de 512 dimensiones, `input_type="document"` para hechos e `input_type="query"` para búsquedas. La integración se hará por HTTP con `httpx`, sin agregar el SDK de Voyage ni dependencias locales de ML.

**Motivo:** El modelo local pesa aproximadamente 471 MB y requiere PyTorch, Transformers y dependencias asociadas; incluso con wheels CPU-only aumentaría la imagen Docker en más de 1 GB y consumiría alrededor de 449 MB solo para los pesos float32, además de la RAM del runtime. Eso compromete el deploy en un tier gratuito. Voyage mantiene liviano el backend, delega CPU y RAM de inferencia, coincide con el patrón de ADR-003/ADR-004 y con el uso de APIs externas para componentes ML que no son el diferencial del proyecto. El valor técnico de la memoria está en extraer, persistir y recuperar hechos con pgvector, no en servir el modelo de embeddings.

**Trade-off aceptado:** Se agrega una API key, latencia de red y dependencia de disponibilidad, límites y precios de un tercero. Los hechos de memoria pueden contener datos personales del usuario y tanto esos hechos como las consultas semánticas se envían a Voyage AI para generar embeddings; esto amplía la superficie de privacidad y exige informar y gestionar ese proveedor como procesador externo de datos. Cambiar de proveedor, modelo o dimensión requerirá regenerar los embeddings existentes y posiblemente migrar la columna vectorial. Para el volumen de una demo de portfolio, estos costos se aceptan frente al ahorro de imagen, RAM y operación.

---

## ADR-010 — OpenAI como proveedor del LLM

**Estado:** Aceptada

**Contexto:** Step3 necesita una llamada real a un LLM para extraer hechos con un prompt separado, y Step4 conectará posteriormente el flujo de conversación. La configuración inicial y el SDK instalado suponían Anthropic, pero la cuenta disponible no tiene saldo mientras que ya existe crédito utilizable en OpenAI.

**Decisión:** Usar OpenAI como proveedor del LLM y su SDK oficial de Python. `LLM_API_KEY` contendrá una API key de OpenAI y `LLM_MODEL` identificará un modelo de OpenAI, por ejemplo `gpt-4o-mini`. Esta decisión reemplaza cualquier supuesto previo de usar Anthropic para el LLM de extracción o el futuro LLM de conversación. El placeholder de `call_llm` se mantiene hasta Step4.

**Motivo:** Permite completar y verificar el pipeline con crédito ya disponible, sin alterar la arquitectura basada en una API externa ni incorporar inferencia local. El proveedor concreto no es el diferencial técnico del proyecto.

**Trade-off aceptado:** El backend queda acoplado al contrato, disponibilidad, límites y precios de OpenAI hasta que se introduzca una abstracción de proveedores. `VOYAGE_API_KEY` y Voyage AI no cambian: los embeddings continúan generándose con Voyage independientemente del proveedor elegido para el LLM.

---

## ADR-011 — Contexto de memoria y resiliencia del LLM conversacional

**Estado:** Aceptada

**Contexto:** Step4 conecta el flujo conversacional con OpenAI y necesita definir cómo entregar al modelo los hechos recuperados sin alterar la personalidad de Step2, además de evitar respuestas HTTP 500 sin contexto cuando OpenAI sufre un timeout o aplica un rate limit.

**Decisión:** Construir un único mensaje `system` con el system prompt de personalidad sin modificaciones, seguido —solo cuando existan hechos recuperados— por la sección `Hechos relevantes sobre el usuario:` y una viñeta de texto plano por hecho. El mensaje del usuario se envía por separado con rol `user`. Usar `AsyncOpenAI` con timeout de 30 segundos y hasta dos reintentos automáticos del SDK. Si, después de esos intentos, OpenAI devuelve un timeout o rate limit, registrar el error y responder: `Ahora mismo no pude responder por un problema temporal con el servicio. Probá de nuevo en un momento.`

**Motivo:** Un único bloque de instrucciones y contexto es fácil de inspeccionar durante el debugging, mantiene la personalidad antes que la memoria y evita exponer al modelo JSON, UUID, embeddings o metadata irrelevante. Los reintentos acotados absorben fallas transitorias sin mantener indefinidamente abierta la petición, y el fallback ofrece al usuario una explicación accionable sin filtrar detalles internos del proveedor.

**Trade-off aceptado:** Reintentar puede sumar latencia y consumir solicitudes adicionales; el fallback genérico no distingue ante el usuario entre timeout y rate limit. Los hechos recuperados aumentan el tamaño del mensaje `system`, y por ahora no se aplica optimización de tokens según el alcance explícito de Step4.

---

## ADR-012 — Identidad local persistente separada de la conversación

**Estado:** Aceptada

**Contexto:** Step5 decidió solicitar un `session_id` nuevo al backend en cada carga y mantenerlo solo en el estado del cliente. Esa simplificación permitió cerrar el flujo inicial, pero hizo inaccesibles los hechos guardados después de recargar o volver otro día, por lo que no se podía validar la memoria persistente exigida por M1.

**Decisión:** El frontend genera un UUID anónimo la primera vez, lo guarda en `localStorage` y lo reutiliza como `identity_id` en cargas posteriores. Cada carga genera además un `conversation_id` nuevo y efímero. La memoria de largo plazo se asocia a `identity_id`; el contexto corto se delimita por `identity_id` y `conversation_id`. El frontend deja de solicitar `POST /session` al cargar. Esta decisión revisa la simplificación local de Step5; no introduce autenticación ni un sistema multiusuario.

**Motivo:** Separar identidad y conversación permite recuperar recuerdos entre días sin mezclar el historial reciente de conversaciones distintas. Un UUID local tiene el menor alcance suficiente para validar M1 antes de implementar autenticación.

**Trade-off aceptado:** La identidad depende del navegador y del almacenamiento local: se pierde al borrar los datos, no se comparte entre dispositivos y quien copie el UUID podría acceder a la misma memoria porque todavía no existe autenticación. Es aceptable para un único usuario de prueba local, no para una demo pública multiusuario.

---

## ADR-013 — Contexto corto limitado a los últimos ocho mensajes

**Estado:** Aceptada

**Contexto:** ADR-005 evita usar el historial crudo como memoria de largo plazo, pero enviar únicamente hechos semánticos hacía que el modelo pudiera perder el turno inmediatamente anterior. La memoria factual persistente y la coherencia local de una conversación cumplen funciones distintas.

**Decisión:** Guardar los mensajes de usuario y asistente por `conversation_id` e incluir en cada llamada los últimos ocho mensajes anteriores —cuatro intercambios completos—, en orden cronológico, además del mensaje actual y de los hechos recuperados por pgvector. El límite es fijo; los mensajes más antiguos se excluyen del prompt, aunque permanezcan almacenados. Una carga nueva crea otra conversación y no arrastra este historial crudo.

**Motivo:** Ocho mensajes ofrecen contexto suficiente para referencias recientes y correcciones sin permitir que el prompt crezca sin límite. Mantener este contexto separado de los hechos preserva ADR-005: el historial reciente sostiene el hilo; los hechos resumidos sostienen la continuidad entre conversaciones.

**Trade-off aceptado:** Una referencia a más de cuatro intercambios puede salir de la ventana si no fue extraída como hecho, y almacenar mensajes crudos aumenta el volumen y la sensibilidad de los datos. Un límite fijo por cantidad de mensajes tampoco controla tokens con precisión; si aparecen mensajes extensos deberá evolucionar a un presupuesto de tokens.

---

## ADR-014 — Deepgram y ElevenLabs para el pipeline de voz

**Estado:** Aceptada

**Contexto:** Step7 necesita convertir grabaciones completas del navegador a texto y sintetizar cada respuesta sin exponer credenciales en el frontend. `PROJECT.md` ya limitaba las opciones de STT a servicios externos como Deepgram o Whisper API y las de TTS a servicios como ElevenLabs o Inworld, priorizando latencia sobre calidad máxima.

**Decisión:** Usar Deepgram Nova-3 para STT pregrabado en español y ElevenLabs Flash v2.5 para TTS en MP3, con la voz preset Jessica. El navegador captura WebM/Opus mediante `MediaRecorder`, lo envía como base64 al endpoint existente y reproduce el MP3 base64 de la respuesta. Todas las llamadas a proveedores permanecen en FastAPI. Si ElevenLabs falla, el backend conserva estado HTTP 200 y la respuesta textual, devuelve `audio_base64: null` y un `audio_error` no fatal para que la interfaz degrade a solo texto.

**Motivo:** Nova-3 acepta directamente el formato generado por el navegador y evita transcodificación local. Flash v2.5 está optimizado para baja latencia y soporta español. Una voz preset respeta el no-goal de no implementar clonación de voz en el MVP.

**Trade-off aceptado:** El flujo no usa streaming: el backend espera la grabación completa, la respuesta completa del LLM y el MP3 completo antes de reproducir. Base64 agrega tamaño a request y response, pero conserva el contrato simple de Step7. En la prueba real de navegador del 2026-08-18, aun usando ElevenLabs Flash v2.5, transcurrieron 4,61 segundos desde presionar `Detener` hasta el evento `playing`; supera el objetivo de referencia de 2,5 segundos. Se acepta esta latencia para cerrar el pipeline secuencial de M2 y se deja como optimización explícita evaluar streaming de TTS o del pipeline antes de la demo final, sin cambiar identidad ni memoria.

---

## Plantilla para nuevas decisiones

```
## ADR-00X — <título corto>

**Estado:** Propuesta | Aceptada | Reemplazada por ADR-00Y

**Contexto:** ¿Qué problema o disyuntiva motivó esta decisión?

**Decisión:** ¿Qué se decidió?

**Motivo:** ¿Por qué esta opción sobre las alternativas?

**Trade-off aceptado:** ¿Qué se pierde o se limita a cambio?
```
