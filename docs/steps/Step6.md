# Step 6 — Checkpoint: validar la hipótesis antes de seguir

## Objetivo
Decidir, con evidencia de uso real, si tiene sentido invertir en M2-M4 (voz, avatar 3D, pulido) o si hay que replantear el proyecto primero.

**Este step no es código.** Es el punto del roadmap donde se paga (o no) la apuesta de `PROJECT.md` sección 2.

## Prerrequisitos
- Step5 completado: hay una versión de chat de texto con memoria, usable de punta a punta.

## Tareas
1. Usar el chat de texto (sin avatar, sin voz) de forma real durante al menos 2 semanas — idealmente con más de una persona probándolo, pero el uso propio honesto también sirve como señal inicial.
2. Registrar (aunque sea informalmente, en un archivo `docs/notas-validacion.md`) si hay vuelta espontánea a la conversación sin razón artificial, y si la memoria genera algún momento de "se acordó de verdad" que se sintió valioso.
3. Responder explícitamente la pregunta de `PROJECT.md` sección 2: ¿la memoria persistente, sin trucos de manipulación emocional, genera continuidad suficiente?

## Definición de hecho
Existe una conclusión escrita y honesta (no un "sí" automático) sobre si la hipótesis se sostiene, basada en uso real de al menos 2 semanas.

## Qué NO hacer en este step
- No avanzar a Step7 (voz) solo porque "ya se decidió construir el avatar desde el principio" — el objetivo de este checkpoint es poder frenar o redirigir si la señal es débil, no confirmar lo que ya se planeaba hacer.
- No inflar la evaluación para justificar seguir — la utilidad de este proyecto como pieza de portfolio no depende de que la hipótesis se confirme, depende de que el proceso de validación esté bien hecho y documentado.

## Siguiente paso
Si la señal es razonablemente positiva: `Step7.md` — voz (STT + TTS).
Si la señal es débil: documentar el aprendizaje en `docs/DECISIONS.md` como ADR y decidir si el proyecto se cierra en esta fase como pieza de portfolio (un M1 bien ejecutado y bien evaluado es, en sí mismo, un resultado válido de mostrar) o si se ajusta el enfoque antes de seguir.
