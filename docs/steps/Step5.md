# Step 5 — Frontend mínimo: chat de texto

## Objetivo
Tener una interfaz web simple donde se pueda chatear con el personaje, cerrando así el alcance completo de M1 (ver `PROJECT.md` roadmap). Sin avatar ni voz todavía — eso es M2 y M3.

## Prerrequisitos
- Step4 completado (el backend responde correctamente en texto con memoria funcionando).

## Tareas
1. Inicializar `apps/web` como app Next.js (si no existe todavía el scaffold real).
2. Crear una pantalla simple de chat: input de texto, lista de mensajes (usuario / personaje), sin diseño elaborado — la prioridad es que funcione, no que se vea bien todavía.
3. Al cargar la app, llamar a `POST /session` para obtener un `session_id` y guardarlo en el estado del cliente (no hace falta persistencia entre recargas todavía).
4. Conectar el input a `POST /conversation/message` usando `NEXT_PUBLIC_API_URL` (ya definida en `.env.example`).
5. Verificar CORS: el backend ya permite `http://localhost:3000` (ver `main.py`) — confirmar que las llamadas desde el navegador funcionan sin errores de CORS.
6. Probar `docker compose up` completo (los tres servicios) y confirmar que se puede chatear de punta a punta desde el navegador.

## Definición de hecho
Se puede abrir `http://localhost:3000`, escribir un mensaje, y recibir una respuesta del personaje generada por el LLM real, con memoria funcionando entre mensajes de la misma sesión.

## Qué NO hacer en este step
- No agregar Three.js / React Three Fiber todavía — eso es Step8.
- No implementar autenticación de usuarios — un `session_id` por carga de página alcanza para el MVP.
- No pulir el diseño visual — este step es funcional, el pulido final es Step9.

## Siguiente paso
`Step6.md` — checkpoint: validar la hipótesis central antes de seguir a M2. **Este es el paso más importante de todo el roadmap, no un trámite.**
