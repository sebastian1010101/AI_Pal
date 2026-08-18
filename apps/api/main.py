"""
Backend principal — orquesta STT, memoria (pgvector), LLM y TTS.

Contratos de API definidos en docs/ARCHITECTURE.md sección 5.
Decisiones de stack justificadas en docs/DECISIONS.md (ADR-001 a ADR-007).

Estado actual: esqueleto funcional para M1 (chat con memoria, solo texto).
Los pasos de STT/TTS están como placeholders — se activan en M2 (ver PROJECT.md, roadmap).
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import uuid
from datetime import datetime
from typing import Optional

import httpx
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import APITimeoutError, AsyncOpenAI, RateLimitError
from pydantic import BaseModel, Field, TypeAdapter
from pydantic_settings import BaseSettings
from sqlalchemy import delete, select

from database import create_database
from models import MemoryFactRecord
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
    tts_api_key: str = ""

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
    session_id: uuid.UUID
    text: Optional[str] = None
    audio_base64: Optional[str] = None


class MessageResponse(BaseModel):
    text: str
    audio_base64: Optional[str] = None
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
    """
    TODO (M2): llamar a la API de STT configurada (STT_API_KEY).
    Placeholder: no se implementa hasta M2 (ver PROJECT.md, roadmap).
    """
    raise NotImplementedError("STT se implementa en M2 — por ahora usar 'text' en el request.")


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
    session_id: uuid.UUID,
    query_text: str,
    limit: int = 5,
) -> list[MemoryFact]:
    if not settings.voyage_api_key:
        return []
    async with SessionLocal() as database:
        has_memory = await database.scalar(
            select(MemoryFactRecord.id).where(MemoryFactRecord.session_id == session_id).limit(1)
        )
    if has_memory is None:
        return []

    query_embedding = await generate_embedding(query_text, "query")
    distance = MemoryFactRecord.embedding.cosine_distance(query_embedding)
    statement = (
        select(MemoryFactRecord)
        .where(MemoryFactRecord.session_id == session_id)
        .order_by(distance)
        .limit(limit)
    )
    async with SessionLocal() as database:
        records = (await database.scalars(statement)).all()
    return [memory_fact_from_record(record) for record in records]


async def call_llm(system_prompt: str, memory_facts: list[MemoryFact], user_message: str) -> str:
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
    session_id: uuid.UUID,
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
                    session_id=session_id,
                    text=fact.text,
                    embedding=embedding,
                    topic=fact.topic,
                    importance=fact.importance,
                )
                for fact, embedding in zip(facts, embeddings)
            )
            await database.commit()
    except Exception:
        logger.exception("No se pudieron extraer y guardar hechos para la sesión %s", session_id)


async def synthesize_speech(text: str) -> Optional[str]:
    """
    TODO (M2): llamar a la API de TTS configurada (TTS_API_KEY) y devolver
    el audio en base64. Placeholder: devuelve None hasta M2.
    """
    return None


@app.post("/conversation/message", response_model=MessageResponse)
async def post_message(payload: MessageRequest, background_tasks: BackgroundTasks) -> MessageResponse:
    if not payload.text and not payload.audio_base64:
        raise HTTPException(status_code=400, detail="Enviar 'text' o 'audio_base64'.")

    user_text = payload.text
    if not user_text and payload.audio_base64:
        try:
            user_text = await transcribe_audio(payload.audio_base64)
        except NotImplementedError as exc:
            raise HTTPException(status_code=501, detail=str(exc)) from exc

    relevant_facts = await search_relevant_memory(payload.session_id, user_text)

    try:
        llm_response = await call_llm(SYSTEM_PROMPT, relevant_facts, user_text)
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc

    # No bloquea la respuesta (ver ARCHITECTURE.md) — en producción esto
    # se dispara como background task (fastapi.BackgroundTasks) o cola async.
    background_tasks.add_task(extract_and_save_facts, payload.session_id, user_text, llm_response)

    audio = await synthesize_speech(llm_response)

    return MessageResponse(text=llm_response, audio_base64=audio, visemes=[])


# ---------------------------------------------------------------------------
# Memoria — requisito ético ADR-007: el usuario debe poder ver y borrar
# su historial de memoria.
# ---------------------------------------------------------------------------

@app.get("/memory/facts", response_model=MemoryFactsResponse)
async def get_memory_facts(session_id: uuid.UUID) -> MemoryFactsResponse:
    statement = (
        select(MemoryFactRecord)
        .where(MemoryFactRecord.session_id == session_id)
        .order_by(MemoryFactRecord.created_at.desc())
    )
    async with SessionLocal() as database:
        records = (await database.scalars(statement)).all()
    return MemoryFactsResponse(facts=[memory_fact_from_record(record) for record in records])


@app.delete("/memory/facts")
async def delete_memory_facts(session_id: uuid.UUID) -> dict:
    async with SessionLocal() as database:
        result = await database.execute(
            delete(MemoryFactRecord).where(MemoryFactRecord.session_id == session_id)
        )
        await database.commit()
    return {"session_id": str(session_id), "deleted_count": result.rowcount}


# ---------------------------------------------------------------------------
# Sesión — helper simple para pruebas locales mientras no hay auth real.
# ---------------------------------------------------------------------------

@app.post("/session")
async def create_session() -> dict:
    return {"session_id": str(uuid.uuid4())}