import requests
from fastapi.testclient import TestClient

import main as app_module


client = TestClient(app_module.app)


class DummyResponse:
    def __init__(self, status_code: int, payload: dict, text: str = ""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload


def test_health_returns_degraded_when_key_missing(monkeypatch):
    monkeypatch.delenv("HUGGINGFACE_API_KEY", raising=False)

    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "degraded", "huggingface_configured": False}


def test_health_returns_ok_when_key_exists(monkeypatch):
    monkeypatch.setenv("HUGGINGFACE_API_KEY", "hf_test_key")

    resp = client.get("/health")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "huggingface_configured": True}


def test_generate_rejects_blank_prompt():
    resp = client.post("/generate", json={"prompt": "   "})

    assert resp.status_code == 400
    assert resp.json()["detail"] == "prompt must not be empty"


def test_generate_returns_model_text(monkeypatch):
    monkeypatch.setenv("HUGGINGFACE_API_KEY", "hf_test_key")

    def fake_post(*args, **kwargs):
        return DummyResponse(
            status_code=200,
            payload={
                "choices": [
                    {"message": {"content": "Hello from unit test"}}
                ]
            },
        )

    monkeypatch.setattr(requests, "post", fake_post)

    resp = client.post("/generate", json={"prompt": "hi"})

    assert resp.status_code == 200
    assert resp.json()["text"] == "Hello from unit test"
    assert "model" in resp.json()
