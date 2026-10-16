from fastapi.testclient import TestClient
from fastapi import HTTPException

from api.app import main

client = TestClient(main.app)


def test_health_reports_model_when_ollama_is_ready(monkeypatch) -> None:
    async def fake_ollama_request(path: str, payload=None):
        assert path == "/api/tags"
        return {"models": [{"name": "devassist-gpt:latest"}]}

    monkeypatch.setattr(main, "ollama_request", fake_ollama_request)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model": "devassist-gpt"}


def test_health_fails_when_model_is_missing(monkeypatch) -> None:
    async def fake_ollama_request(path: str, payload=None):
        return {"models": []}

    monkeypatch.setattr(main, "ollama_request", fake_ollama_request)

    response = client.get("/health")

    assert response.status_code == 503
    assert "n'est pas encore disponible" in response.json()["detail"]


def test_chat_sends_conversation_and_returns_answer(monkeypatch) -> None:
    async def fake_ollama_request(path: str, payload=None):
        assert path == "/api/chat"
        assert payload == {
            "model": "devassist-gpt",
            "messages": [
                {"role": "user", "content": "Bonjour"},
            ],
            "stream": False,
        }
        return {"message": {"role": "assistant", "content": "Bonjour !"}}

    monkeypatch.setattr(main, "ollama_request", fake_ollama_request)

    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "Bonjour"}]},
    )

    assert response.status_code == 200
    assert response.json() == {"answer": "Bonjour !"}


def test_chat_rejects_conversation_ending_with_assistant() -> None:
    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "assistant", "content": "Bonjour !"}]},
    )

    assert response.status_code == 422


def test_chat_accepts_longer_assistant_response(monkeypatch) -> None:
    answer = "a" * 5000

    async def fake_ollama_request(path: str, payload=None):
        return {"message": {"role": "assistant", "content": answer}}

    monkeypatch.setattr(main, "ollama_request", fake_ollama_request)

    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "Explique ce sujet."}]},
    )

    assert response.status_code == 200
    assert response.json() == {"answer": answer}


def test_chat_returns_gateway_error_when_ollama_is_unavailable(monkeypatch) -> None:
    async def fake_ollama_request(path: str, payload=None):
        raise HTTPException(status_code=502, detail="Ollama indisponible.")

    monkeypatch.setattr(main, "ollama_request", fake_ollama_request)

    response = client.post(
        "/api/chat",
        json={"messages": [{"role": "user", "content": "Bonjour"}]},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Ollama indisponible."
