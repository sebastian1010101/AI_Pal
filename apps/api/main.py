"""
Backend principal — orquesta STT, memoria (pgvector), LLM y TTS.

Contratos de API definidos en docs/ARCHITECTURE.md sección 5.
Decisiones de stack justificadas en docs/DECISIONS.md (ADR-001 a ADR-007).

Estado actual: pipeline conversacional con memoria, Deepgram STT y ElevenLabs TTS.
La voz se implementa en M2 sin avatar (ver ADR-014).
"""

from __future__ import annotations

import asyncio
import base64
import binascii
import json
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic import BaseModel, Field, TypeAdapter
from pydantic_settings import BaseSettings
from sqlalchemy import delete, select

from database import create_database
from models import ConversationMessageRecord, MemoryFactRecord
from prompts.memory_extraction_prompt import MEMORY_EXTRACTION_PROMPT
from prompts.system_prompt import SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Configuración (lee de .env — ver .env.example en la raíz del repo)
# ---------------------------------------------------------------------------

class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://companion:changeme@localhost:5432/ai_companion"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
    voyage_api_key: str = ""
    voyage_embedding_model: str = "voyage-4-lite"
    voyage_embedding_dimension: int = 512
    stt_api_key: str = ""
    stt_model: str = "nova-3"
    tts_api_key: str = ""
    tts_model: str = "eleven_flash_v2_5"
    tts_voice_id: str = "cgSgspJ2msm6clMCkdW9"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
SessionLocal, engine = create_database(settings.database_url)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AI Companion API",
    description="Backend del compañero virtual 3D con memoria persistente.",
    version="0.1.0",
)

# El frontend (apps/web) corre en otro origen — ver ARCHITECTURE.md,
# regla de oro: el frontend nunca llama directo a LLM/STT/TTS, solo a esta API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Modelos (contratos — ver ARCHITECTURE.md sección 5)
# ---------------------------------------------------------------------------

class MessageRequest(BaseModel):
    identity_id: uuid.UUID
    conversation_id: uuid.UUID
    text: Optional[str] = None
    audio_base64: Optional[str] = Field(default=None, max_length=14_000_000)


class PipelineTimings(BaseModel):
    stt_ms: float
    memory_ms: float
    llm_ms: float
    tts_ms: float
    backend_total_ms: float


class MessageResponse(BaseModel):
    text: str
    transcript: str
    audio_base64: Optional[str] = None
    audio_error: Optional[str] = None
    timings: PipelineTimings
    visemes: list[dict] = Field(default_factory=list)


class ExtractedFact(BaseModel):
    text: str = Field(min_length=1, max_length=1000)
    topic: Optional[str] = Field(default=None, max_length=100)
    importance: float = Field(ge=0, le=1)


class MemoryFact(BaseModel):
    id: uuid.UUID
    text: str
    created_at: datetime
    topic: Optional[str] = None
    importance: float


class MemoryFactsResponse(BaseModel):
    facts: list[MemoryFact]


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Pipeline de conversación
# Orden: STT (si hay audio) -> búsqueda de memoria -> LLM -> guardado
#        async de hechos nuevos -> TTS
# Ver ARCHITECTURE.md sección 2 (diagrama de secuencia) para el flujo completo.
# ---------------------------------------------------------------------------

async def transcribe_audio(audio_base64: str) -> str:
    if not settings.stt_api_key:
        raise RuntimeError("STT_API_KEY no está configurada.")

    content_type = "audio/webm"
    encoded_audio = audio_base64
    if audio_base64.startswith("data:"):
        header, separator, encoded_audio = audio_base64.partition(",")
        if not separator or ";base64" not in header:
            raise ValueError("El audio debe usar una URL de datos en base64.")
        content_type = header.removeprefix("data:").split(";", 1)[0]

    if content_type.split(";", 1)[0] not in {"audio/webm", "audio/mpeg", "audio/mp4", "audio/ogg", "audio/wav"}:
        raise ValueError("El formato de audio no está soportado.")

    try:
        audio = base64.b64decode(encoded_audio, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("El audio enviado no es base64 válido.") from exc
    if not audio:
        raise ValueError("El audio enviado está vacío.")
    if len(audio) > 10 * 1024 * 1024:
        raise ValueError("El audio supera el límite de 10 MB.")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            "https://api.deepgram.com/v1/listen",
            params={
                "model": settings.stt_model,
                "language": "es",
                "smart_format": "true",
            },
            headers={
                "Authorization": f"Token {settings.stt_api_key}",
                "Content-Type": content_type,
            },
            content=audio,
        )
    response.raise_for_status()
    try:
        alternatives = response.json()["results"]["channels"][0]["alternatives"]
        transcript = alternatives[0]["transcript"].strip() if alternatives else ""
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Deepgram devolvió una respuesta inesperada.") from exc
    if not transcript:
        raise ValueError("No se detectó voz en la grabación.")
    return transcript


def memory_fact_from_record(record: MemoryFactRecord) -> MemoryFact:
    return MemoryFact(
        id=record.id,
        text=record.text,
        created_at=record.created_at,
        topic=record.topic,
        importance=record.importance,
    )


async def generate_embeddings(texts: list[str], input_type: str) -> list[list[float]]:
    if not settings.voyage_api_key:
        raise RuntimeError("VOYAGE_API_KEY no está configurada.")

    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(4):
            response = await client.post(
                "https://api.voyageai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {settings.voyage_api_key}"},
                json={
                    "input": texts,
                    "model": settings.voyage_embedding_model,
                    "input_type": input_type,
                    "output_dimension": settings.voyage_embedding_dimension,
                },
            )
            if response.status_code != 429 or attempt == 3:
                break
            retry_after_header = response.headers.get("Retry-After", "5")
            retry_after = float(retry_after_header) if retry_after_header.replace(".", "", 1).isdigit() else 5
            await asyncio.sleep(min(max(retry_after, 1), 60))

    response.raise_for_status()
    embeddings = [item["embedding"] for item in sorted(response.json()["data"], key=lambda item: item["index"])]
    if len(embeddings) != len(texts) or any(
        len(embedding) != settings.voyage_embedding_dimension for embedding in embeddings
    ):
        raise ValueError("Voyage devolvió embeddings con cantidad o dimensión inesperada.")
    return embeddings


async def generate_embedding(text: str, input_type: str) -> list[float]:
    return (await generate_embeddings([text], input_type))[0]


async def search_relevant_memory(
    identity_id: uuid.UUID,
    query_text: str,
    limit: int = 5,
) -> list[MemoryFact]:
    if not settings.voyage_api_key:
        return []
    async with SessionLocal() as database:
        has_memory = await database.scalar(
            select(MemoryFactRecord.id).where(MemoryFactRecord.identity_id == identity_id).limit(1)
        )
    if has_memory is None:
        return []

    query_embedding = await generate_embedding(query_text, "query")
    distance = MemoryFactRecord.embedding.cosine_distance(query_embedding)
    statement = (
        select(MemoryFactRecord)
        .where(MemoryFactRecord.identity_id == identity_id)
        .order_by(distance)
        .limit(limit)
    )
    async with SessionLocal() as database:
        records = (await database.scalars(statement)).all()
    return [memory_fact_from_record(record) for record in records]


async def load_recent_messages(
    identity_id: uuid.UUID,
    conversation_id: uuid.UUID,
    limit: int = 8,
) -> list[dict[str, str]]:
    statement = (
        select(ConversationMessageRecord)
        .where(
            ConversationMessageRecord.identity_id == identity_id,
            ConversationMessageRecord.conversation_id == conversation_id,
        )
        .order_by(ConversationMessageRecord.created_at.desc(), ConversationMessageRecord.id.desc())
        .limit(limit)
    )
    async with SessionLocal() as database:
        records = list((await database.scalars(statement)).all())
    return [{"role": record.role, "content": record.content} for record in reversed(records)]


async def save_conversation_turn(
    identity_id: uuid.UUID,
    conversation_id: uuid.UUID,
    user_message: str,
    assistant_message: str,
) -> None:
    turn_time = datetime.now(timezone.utc)
    async with SessionLocal() as database:
        database.add_all([
            ConversationMessageRecord(
                identity_id=identity_id,
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                created_at=turn_time,
            ),
            ConversationMessageRecord(
                identity_id=identity_id,
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_message,
                created_at=turn_time + timedelta(microseconds=1),
            ),
        ])
        await database.commit()


async def call_llm(
    system_prompt: str,
    memory_facts: list[MemoryFact],
    recent_messages: list[dict[str, str]],
    user_message: str,
) -> str:
    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY no está configurada.")

    memory_context = "\n".join(f"- {fact.text}" for fact in memory_facts)
    final_system_prompt = system_prompt
    if memory_context:
        final_system_prompt = f"{system_prompt}\n\nHechos relevantes sobre el usuario:\n{memory_context}"

    try:
        response = await AsyncOpenAI(
            api_key=settings.llm_api_key,
            timeout=30,
            max_retries=2,
        ).chat.completions.create(
            model=settings.llm_model or "gpt-4o-mini",
            messages=[
                {"role": "system", "content": final_system_prompt},
                *recent_messages,
                {"role": "user", "content": user_message},
            ],
        )
    except (APITimeoutError, RateLimitError):
        logger.warning("OpenAI no respondió por timeout o rate limit.", exc_info=True)
        return "Ahora mismo no pude responder por un problema temporal con el servicio. Probá de nuevo en un momento."

    response_text = response.choices[0].message.content
    if not response_text:
        raise RuntimeError("OpenAI devolvió una respuesta sin texto.")
    return response_text


async def extract_facts(user_message: str) -> list[ExtractedFact]:
    if not settings.llm_api_key:
        raise RuntimeError("LLM_API_KEY no está configurada para extraer hechos.")

    response = await AsyncOpenAI(api_key=settings.llm_api_key).chat.completions.create(
        model=settings.llm_model or "gpt-4o-mini",
        max_tokens=1024,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": MEMORY_EXTRACTION_PROMPT},
            {"role": "user", "content": user_message},
        ],
    )
    response_text = response.choices[0].message.content or '{"facts": []}'
    return TypeAdapter(list[ExtractedFact]).validate_python(json.loads(response_text)["facts"])


async def extract_and_save_facts(
    identity_id: uuid.UUID,
    user_message: str,
    llm_response: str,
) -> None:
    try:
        facts = await extract_facts(user_message)
        if not facts:
            return
        embeddings = await generate_embeddings([fact.text for fact in facts], "document")
        async with SessionLocal() as database:
            database.add_all(
                MemoryFactRecord(
                    identity_id=identity_id,
                    text=fact.text,
                    embedding=embedding,
                    topic=fact.topic,
                    importance=fact.importance,
                )
                for fact, embedding in zip(facts, embeddings)
            )
            await database.commit()
    except Exception:
        logger.exception("No se pudieron extraer y guardar hechos para la identidad %s", identity_id)


async def synthesize_speech(text: str) -> str:
    if not settings.tts_api_key:
        raise RuntimeError("TTS_API_KEY no está configurada.")

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{settings.tts_voice_id}",
            params={"output_format": "mp3_44100_128"},
            headers={
                "xi-api-key": settings.tts_api_key,
                "Accept": "audio/mpeg",
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": settings.tts_model,
            },
        )
    response.raise_for_status()
    if not response.content:
        raise ValueError("ElevenLabs devolvió audio vacío.")
    return base64.b64encode(response.content).decode("ascii")


@app.post("/conversation/message", response_model=MessageResponse)
async def post_message(payload: MessageRequest, background_tasks: BackgroundTasks) -> MessageResponse:
    request_started = time.perf_counter()
    if not payload.text and not payload.audio_base64:
        raise HTTPException(status_code=400, detail="Enviar 'text' o 'audio_base64'.")

    stt_ms = 0.0
    user_text = payload.text
    if not user_text and payload.audio_base64:
        stage_started = time.perf_counter()
        try:
            user_text = await transcribe_audio(payload.audio_base64)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except (RuntimeError, httpx.HTTPError) as exc:
            logger.exception("Deepgram no pudo transcribir el audio.")
            raise HTTPException(status_code=502, detail="No se pudo transcribir el audio.") from exc
        stt_ms = (time.perf_counter() - stage_started) * 1000

    stage_started = time.perf_counter()
    relevant_facts = await search_relevant_memory(payload.identity_id, user_text)
    recent_messages = await load_recent_messages(payload.identity_id, payload.conversation_id)
    memory_ms = (time.perf_counter() - stage_started) * 1000

    stage_started = time.perf_counter()
    try:
        llm_response = await call_llm(SYSTEM_PROMPT, relevant_facts, recent_messages, user_text)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc
    llm_ms = (time.perf_counter() - stage_started) * 1000

    await save_conversation_turn(payload.identity_id, payload.conversation_id, user_text, llm_response)

    # No bloquea la respuesta (ver ARCHITECTURE.md) — en producción esto
    # se dispara como background task (fastapi.BackgroundTasks) o cola async.
    background_tasks.add_task(extract_and_save_facts, payload.identity_id, user_text, llm_response)

    audio = None
    audio_error = None
    stage_started = time.perf_counter()
    try:
        audio = await synthesize_speech(llm_response)
    except (RuntimeError, ValueError, httpx.HTTPError):
        logger.warning("ElevenLabs no pudo sintetizar la respuesta; se devuelve solo texto.", exc_info=True)
        audio_error = "La voz no está disponible temporalmente; la respuesta se muestra en texto."
    tts_ms = (time.perf_counter() - stage_started) * 1000

    timings = PipelineTimings(
        stt_ms=round(stt_ms, 1),
        memory_ms=round(memory_ms, 1),
        llm_ms=round(llm_ms, 1),
        tts_ms=round(tts_ms, 1),
        backend_total_ms=round((time.perf_counter() - request_started) * 1000, 1),
    )
    return MessageResponse(
        text=llm_response,
        transcript=user_text,
        audio_base64=audio,
        audio_error=audio_error,
        timings=timings,
        visemes=[],
    )


# ---------------------------------------------------------------------------
# Memoria — requisito ético ADR-007: el usuario debe poder ver y borrar
# su historial de memoria.
# ---------------------------------------------------------------------------

@app.get("/memory/facts", response_model=MemoryFactsResponse)
async def get_memory_facts(identity_id: uuid.UUID) -> MemoryFactsResponse:
    statement = (
        select(MemoryFactRecord)
        .where(MemoryFactRecord.identity_id == identity_id)
        .order_by(MemoryFactRecord.created_at.desc())
    )
    async with SessionLocal() as database:
        records = (await database.scalars(statement)).all()
    return MemoryFactsResponse(facts=[memory_fact_from_record(record) for record in records])


@app.delete("/memory/facts")
async def delete_memory_facts(identity_id: uuid.UUID) -> dict:
    async with SessionLocal() as database:
        result = await database.execute(
            delete(MemoryFactRecord).where(MemoryFactRecord.identity_id == identity_id)
        )
        await database.commit()
    return {"identity_id": str(identity_id), "deleted_count": result.rowcount}