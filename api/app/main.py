import logging
import os
from typing import Any, Literal

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ValidationError, field_validator, model_validator

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "devassist-gpt")

app = FastAPI(
    title="DevAssist-GPT API",
    description="API de chat locale pour l'assistant DevAssist-GPT.",
    version="1.0.0",
)


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Le contenu du message ne peut pas être vide.")
        return value


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def last_message_must_be_from_user(self) -> "ChatRequest":
        if self.messages[-1].role != "user":
            raise ValueError("Le dernier message doit venir de l'utilisateur.")
        return self


class ChatResponse(BaseModel):
    answer: str


class OllamaMessage(BaseModel):
    role: Literal["assistant"]
    content: str = Field(min_length=1)


class OllamaChatResult(BaseModel):
    message: OllamaMessage


async def ollama_request(
    path: str, payload: dict[str, Any] | None = None
) -> Any:
    try:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.request(
                "POST" if payload is not None else "GET",
                f"{OLLAMA_BASE_URL}{path}",
                json=payload,
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        logger.warning("La requête vers Ollama a échoué: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Le service Ollama est momentanément indisponible.",
        ) from exc
    except ValueError as exc:
        logger.warning("Ollama a renvoyé une réponse JSON invalide: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Le service Ollama a renvoyé une réponse invalide.",
        ) from exc


@app.get("/health")
async def health() -> dict[str, str]:
    result = await ollama_request("/api/tags")
    models = result.get("models", []) if isinstance(result, dict) else []
    if not any(
        isinstance(model, dict)
        and model.get("name") in {OLLAMA_MODEL, f"{OLLAMA_MODEL}:latest"}
        for model in models
    ):
        raise HTTPException(
            status_code=503,
            detail=f"Le modèle {OLLAMA_MODEL} n'est pas encore disponible.",
        )
    return {"status": "ok", "model": OLLAMA_MODEL}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    result = await ollama_request(
        "/api/chat",
        {
            "model": OLLAMA_MODEL,
            "messages": [message.model_dump() for message in request.messages],
            "stream": False,
        },
    )
    try:
        response = OllamaChatResult.model_validate(result)
    except ValidationError as exc:
        logger.warning("Ollama a renvoyé une réponse de chat invalide: %s", exc)
        raise HTTPException(
            status_code=502,
            detail="Le service Ollama a renvoyé une réponse de chat invalide.",
        ) from exc
    return ChatResponse(answer=response.message.content)
