# Registro de progreso

> Se actualiza al cerrar cada step de `docs/steps/`, no en cualquier momento. Cada entrada es un registro de ejecución (qué se hizo, cuándo, qué se desvió del plan) — **no** un lugar para justificar decisiones de arquitectura, eso va en `docs/DECISIONS.md` como ADR y se referencia desde acá si aplica.

Formato de cada entrada:

```
## Step N — <título del step> — <fecha>

**Implementado:**
- <lista concreta de lo que quedó funcionando>

**Desvíos del plan del step (si los hubo):**
- <qué se hizo distinto a lo escrito en StepN.md, y por qué — una línea alcanza>

**Pendiente / deuda dejada para después:**
- <algo que quedó a medias a propósito, si aplica>

**Referencias:** <ADR relacionado si se creó uno nuevo en este step, si no, omitir esta línea>
```

---

<!-- Las entradas se agregan acá abajo, en orden, sin borrar las anteriores. -->

## Step 1 — Setup y verificación del esqueleto — 2026-08-17

**Implementado:**
- Se creó `.env` para el entorno local con PostgreSQL configurado y las credenciales de LLM/STT/TTS vacías.
- El servicio `db` levanta con PostgreSQL 16 + pgvector y pasa su healthcheck.
- El servicio `api` construye su imagen e inicia FastAPI sin errores.
- `GET /health` responde `{"status":"ok"}`.
- `POST /session` devuelve un `session_id` UUID.
- `POST /conversation/message` con texto devuelve el eco placeholder sin `LLM_API_KEY` y sin error 500.

**Desvíos del plan del step (si los hubo):**
- Los archivos recibidos no coincidían con las rutas requeridas: se habilitaron `docs/DECISIONS.md`, `apps/api/Dockerfile` y `apps/api/requirements.txt` a partir de sus copias ubicadas incorrectamente.
- PostgreSQL local ya ocupaba el puerto `5432`; se publicó el contenedor en `5433` sin alterar la conexión interna de la API a `db:5432`.
- El healthcheck original consultaba una base inexistente llamada `companion`; se agregó `-d ${POSTGRES_DB:-ai_companion}` para comprobar la base configurada sin generar errores en los logs.

**Pendiente / deuda dejada para después:**
- Quedaron copias redundantes en la raíz (`DECISIONS.md`, `requirements.txt`) y Dockerfiles con sufijo; no se eliminaron porque no afecta Step1.

## Step 2 — System prompt y personalidad del personaje — 2026-08-17

**Implementado:**
- Se definió a Nara como un único personaje con identidad, intereses, forma de hablar y límites explícitos.
- El system prompt quedó en `apps/api/prompts/system_prompt.py` y cubre transparencia como IA, despedidas no manipulativas, respuesta ante angustia real y tono de conversación.
- `main.py` importa y entrega el prompt real a `call_llm`; el placeholder del system prompt fue eliminado sin conectar todavía el proveedor de LLM.
- Se verificaron la sintaxis e importación del prompt y que `POST /conversation/message` conserva el eco esperado sin `LLM_API_KEY`.

**Desvíos del plan del step:**
- Ninguno.

**Pendiente / deuda dejada para después:**
- La memoria y la integración real del LLM permanecen como placeholders para Step3 y Step4, respectivamente.

**Referencias:** ADR-008

## Step 3 — Memoria real: schema, extracción y búsqueda semántica — 2026-08-17

**Implementado:**
- Se agregó el modelo SQLAlchemy `memory_facts` con UUID, `session_id`, texto resumido, embedding `vector(512)`, fecha, tema e importancia validada entre 0 y 1.
- Alembic habilita pgvector y crea la tabla e índice por `session_id`; la migración se ejecuta al iniciar la API.
- Un prompt separado extrae hechos con OpenAI, genera sus embeddings por lotes con Voyage AI y los guarda de forma asíncrona sin conectar todavía el LLM de conversación.
- La búsqueda genera un embedding de consulta y recupera hasta cinco hechos del mismo `session_id` ordenados exclusivamente por distancia coseno.
- `GET /memory/facts` lista la memoria persistida y `DELETE /memory/facts` la elimina realmente, devolviendo la cantidad borrada.
- La prueba real guardó cuatro hechos desde dos mensajes; ante una consulta posterior sobre mascota y truenos recuperó primero los dos hechos antiguos de Moka, por delante de los hechos más recientes sobre una presentación.

**Desvíos del plan del step (si los hubo):**
- Se eligió Voyage AI en vez de un modelo local para reducir imagen Docker y RAM, y OpenAI reemplazó el supuesto inicial de Anthropic por disponibilidad de crédito; ambos cambios quedaron documentados.
- El límite de requests observado en Voyage se resolvió evitando consultas sin memoria, agrupando embeddings de hechos y respetando `Retry-After` con reintentos acotados.

**Pendiente / deuda dejada para después:**
- `call_llm` continúa como placeholder; la integración del LLM de conversación y la inyección efectiva de los hechos recuperados corresponden exclusivamente a Step4.
- No se implementaron ranking por recencia, olvido ni índice vectorial aproximado, según el alcance explícito del MVP.

**Referencias:** ADR-009, ADR-010

## Step 4 — Conexión real al LLM — 2026-08-18

**Implementado:**
- Se reemplazó el placeholder de `call_llm` por una llamada real a OpenAI mediante `AsyncOpenAI` y el modelo configurado en `LLM_MODEL`.
- El prompt de personalidad de Step2 y los hechos recuperados se combinan en un único mensaje `system`; la memoria se presenta bajo `Hechos relevantes sobre el usuario:` como viñetas de texto plano, seguida por el mensaje `user` separado.
- La llamada conversacional tiene timeout de 30 segundos y hasta dos reintentos automáticos; si OpenAI agota los intentos por timeout o rate limit, devuelve un fallback legible en vez de un error 500.
- Se verificaron de forma aislada el formato exacto de mensajes, la configuración de timeout/reintentos y el fallback tanto ante timeout como ante rate limit.
- La prueba real usó la sesión de Step3 y el mensaje `¿Qué podría hacer para que Moka esté más tranquila esta noche?`. La búsqueda recuperó primero `Moka se esconde debajo de la cama cuando hay tormenta.` y `La gata del usuario se llama Moka.`; OpenAI respondió en español, con voseo y tono breve de Nara, sugiriendo prepararle un lugar cómodo debajo de la cama durante la tormenta, usando así hechos que el mensaje actual no había mencionado.

**Desvíos del plan del step:**
- Ninguno.

**Pendiente / deuda dejada para después:**
- No se optimizó el tamaño del contexto ni el costo de tokens, según el alcance explícito de Step4.
- STT, TTS y frontend permanecen sin cambios para sus steps posteriores.

**Referencias:** ADR-010, ADR-011

## Step 5 — Frontend mínimo: chat de texto — 2026-08-18

**Implementado:**
- Se inicializó `apps/web` como una aplicación Next.js con App Router y TypeScript, usando versiones fijadas y sin dependencias de avatar, Three.js, STT ni TTS.
- La pantalla crea un `session_id` mediante `POST /session` al cargar y lo conserva únicamente en estado React durante la vida de la pestaña, sin cookies ni almacenamiento persistente.
- El chat muestra mensajes de usuario y Nara y envía texto a `POST /conversation/message` exclusivamente mediante `NEXT_PUBLIC_API_URL`; el frontend no llama directamente a proveedores de LLM, embeddings, STT o TTS.
- Las llamadas del navegador usan un `AbortController` de 45 segundos, dejando margen al timeout y fallback de 30 segundos del backend. Los errores HTTP, de red y timeout se muestran en la interfaz; ante un envío fallido, el texto vuelve al input para permitir reintento.
- Se agregó el `apps/web/Dockerfile` esperado por Compose y el frontend pasa typecheck, build de producción y `npm audit` sin vulnerabilidades reportadas.
- Se levantaron `db`, `api` y `web` con `docker compose up --build` y se probó el flujo en Chrome real desde `http://localhost:3000`. La secuencia fue: `Mi planta favorita se llama Aurora y es una monstera. Recordalo para después.` y luego `¿Cómo se llama mi planta favorita y qué tipo de planta es?`; Nara respondió `Tu planta favorita se llama Aurora y es una monstera.`, demostrando uso de la memoria persistida, ya que el backend no recibe el historial crudo en la segunda llamada.
- La captura de red del navegador mostró `POST /session`, el preflight `OPTIONS /conversation/message` y dos `POST /conversation/message` con estado 200 y `Access-Control-Allow-Origin: http://localhost:3000`. No hubo errores visibles ni errores en la consola del navegador.
- Corrección de coherencia: el system prompt ahora informa explícitamente que Nara puede conservar ciertos hechos relevantes para mensajes posteriores de la sesión actual, pero le prohíbe prometer memoria total, permanente o disponible tras recargar/iniciar otra sesión. Al repetir en Chrome el caso de Aurora, el primer turno respondió `La guardaré para esta conversación.` en vez de negar su capacidad y el segundo volvió a identificar correctamente el nombre y tipo de planta; las cuatro solicitudes conservaron estado 200, CORS correcto y consola sin errores.

**Desvíos del plan del step:**
- El scaffold inicial solo contenía `Dockerfile.web`, mientras que Compose referencia `apps/web/Dockerfile`; se creó el archivo en la ruta esperada.

**Pendiente / deuda dejada para después:**
- El diseño visual continúa deliberadamente básico; el pulido corresponde a Step9.
- El alcance técnico de M1 queda completo. El criterio de salida de M1 requiere uso real durante al menos dos semanas y se evaluará en Step6 antes de decidir si avanzar a M2; Step6 no se inició.

**Referencias:** Step5, PROJECT.md M1, ARCHITECTURE.md regla de oro

## Step 6 — Checkpoint de validación — 2026-08-18

**Implementado:**
- Se registró una comprobación de uso real posterior a Step5.5: al volver a la aplicación y recargar la página, Nara conservó entre conversaciones información personal como el nombre o la edad mediante la identidad persistente.
- En esa comprobación, las respuestas se percibieron creativas y simpáticas, sin el tono robótico observado en las pruebas exploratorias anteriores.
- El dueño del proyecto decidió avanzar a M2 asumiendo explícitamente el riesgo de invertir en voz sin completar la validación prevista.

**Desvíos del plan del step:**
- Step6 se cierra por una decisión explícita de producto basada en un solo día de señal positiva, no en las dos semanas de uso real exigidas por `Step6.md` y por el criterio de salida de M1.
- La evidencia disponible todavía es insuficiente para considerar confirmada de forma robusta la hipótesis de `PROJECT.md` sección 2; este cierre autoriza avanzar a M2, pero no debe citarse como validación completa de la continuidad generada por la memoria persistente.

**Pendiente / deuda dejada para después:**
- Continúa pendiente acumular uso real durante al menos dos semanas y reevaluar la hipótesis con más evidencia, incluyendo posibles fallos, recuerdos irrelevantes y nuevas vueltas espontáneas.

**Referencias:** Step6, PROJECT.md §2 y M1, `docs/notas-validacion.md`

## Step 7 — Voz: STT + TTS (M2) — 2026-08-18

**Implementado:**
- Se integró Deepgram Nova-3 para transcribir grabaciones completas en español y ElevenLabs Flash v2.5 con la voz preset Jessica para sintetizar respuestas en MP3; las credenciales permanecen exclusivamente en FastAPI.
- El navegador captura WebM/Opus mediante `MediaRecorder`, permite iniciar y detener la grabación, envía el audio como base64 al contrato existente y muestra la transcripción devuelta por el backend.
- La respuesta de Nara conserva texto y audio reproducible. El frontend mide con `performance.now()` desde que se presiona `Detener` hasta el evento `playing` del audio y muestra el resultado en la interfaz.
- El flujo de voz reutiliza sin cambios el `identity_id` persistente de `localStorage` y el `conversation_id` de la carga actual. En la prueba real, Deepgram transcribió `Hola, agente.` y Nara respondió por voz llamando al usuario `Sebas`, conservando la continuidad existente.
- La prueba real de navegador midió **4,61 s** de latencia extremo a extremo. El pipeline funciona, pero no cumple el objetivo de referencia de menos de 2,5 s.
- Se verificaron proveedor STT y TTS por separado, endpoint completo, rechazo de formatos inválidos, sintaxis Python, typecheck y build de producción del frontend.
- El backend devuelve tiempos instrumentados de STT, memoria, LLM, TTS y total; el frontend los muestra junto con la diferencia atribuible a preparación, red y comienzo de reproducción.
- El 2026-08-19 se forzó un fallo real de ElevenLabs con una clave inválida aislada, sin modificar `.env`: el proveedor respondió 401, pero `/conversation/message` conservó HTTP 200 y devolvió `text: "Fallback confirmado."`, `audio_base64: null` y el aviso no fatal `La voz no está disponible temporalmente; la respuesta se muestra en texto.` La interfaz acepta ese contrato, muestra el texto y el aviso y no intenta reproducir audio.

**Desvíos del plan del step:**
- La primera prueba de micrófono quedaba indefinidamente en `Pensando y preparando la voz…`: la limpieza de React Strict Mode mantenía una marca de desmontaje y descartaba el audio antes del request. Se corrigió reiniciando esa marca en cada montaje y se repitió exitosamente la prueba real.
- Se mantuvo el flujo secuencial sin streaming previsto por Step7. Incluso con el modelo TTS de baja latencia Flash v2.5, la medición de 4,61 s superó el objetivo de 2,5 s; el trade-off quedó documentado en ADR-014.

**Pendiente / deuda dejada para después:**
- Evaluar streaming de TTS o del pipeline para reducir el tiempo hasta el primer audio antes de la demo final. La medición actual corresponde a una prueba real, no a un benchmark estadístico con múltiples muestras.
- Los visemas permanecen vacíos y no se implementó avatar ni lip-sync; corresponden exclusivamente a Step8 y no se iniciaron.

**Referencias:** ADR-014 (fallback de TTS y trade-off de latencia), ADR-013 (contexto corto, no fallback), Step7, PROJECT.md M2
