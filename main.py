"""
FastAPI service: POST /generate calls Hugging Face Inference via the hosted router
(OpenAI-compatible chat completions). Environment: HUGGINGFACE_API_KEY (required).
Optional: HUGGINGFACE_MODEL (chat/instruct Hub id). Optional: API_RESPONSE_MODEL for JSON "model" field.
"""

from __future__ import annotations

import logging
import os
import sys
from contextlib import asynccontextmanager

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# Load .env for local development; in Azure, set secrets in the portal / Key Vault.
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("hf_inference_api")

# Replaces deprecated https://api-inference.huggingface.co — use Inference Providers router.
HF_ROUTER_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"
_DEFAULT_CHAT_MODEL = "meta-llama/Llama-3.2-1B-Instruct"
ROUTER_MODEL = os.getenv("HUGGINGFACE_MODEL", _DEFAULT_CHAT_MODEL)
MODEL_ID = os.getenv("API_RESPONSE_MODEL") or ROUTER_MODEL.rsplit("/", maxsplit=1)[-1]
REQUEST_TIMEOUT_SEC = 120
MAX_TOKENS = 128


class GenerateRequest(BaseModel):
    """Incoming JSON body for /generate."""

    prompt: str = Field(
        ...,
        min_length=1,
        description="User prompt to send to the model.",
    )


class GenerateResponse(BaseModel):
    """Successful completion payload."""

    text: str = Field(..., description="Model-generated text.")
    model: str = Field(..., description="Model used for the completion.")


class HealthResponse(BaseModel):
    status: str
    huggingface_configured: bool


def _require_api_key() -> str:
    key = os.getenv("HUGGINGFACE_API_KEY")
    if not key or not key.strip():
        logger.error("HUGGINGFACE_API_KEY is missing or empty")
        raise RuntimeError("HUGGINGFACE_API_KEY is not configured")
    return key.strip()


def _hf_router_error_message(payload: object) -> str | None:
    if not isinstance(payload, dict):
        return None
    err = payload.get("error")
    if isinstance(err, dict):
        m = err.get("message")
        return m if isinstance(m, str) else None
    return err if isinstance(err, str) else None


def _extract_router_chat_text(payload: object) -> str | None:
    """Parse OpenAI-style chat completion JSON from router.huggingface.co."""
    if not isinstance(payload, dict):
        return None
    choices = payload.get("choices")
    if not isinstance(choices, list) or len(choices) == 0:
        return None
    first = choices[0]
    if not isinstance(first, dict):
        return None
    msg = first.get("message")
    if not isinstance(msg, dict):
        return None
    content = msg.get("content")
    return content if isinstance(content, str) else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Verify configuration at startup."""
    try:
        _require_api_key()
        logger.info("Startup OK: HUGGINGFACE_API_KEY is set (length hidden)")
    except RuntimeError as e:
        logger.warning("%s — /health will report not ready; /generate will fail.", e)
    yield


app = FastAPI(
    title="Hugging Face Generate API",
    description="Proxies text generation via https://router.huggingface.co (Inference Providers).",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse, tags=["ops"])
async def health() -> HealthResponse:
    """Liveness/readiness: safe to call without credentials for basic checks."""
    try:
        _require_api_key()
        configured = True
    except RuntimeError:
        configured = False
    return HealthResponse(
        status="ok" if configured else "degraded",
        huggingface_configured=configured,
    )


@app.post(
    "/generate",
    response_model=GenerateResponse,
    tags=["generate"],
    responses={
        400: {"description": "Invalid or empty prompt"},
        401: {"description": "Invalid API key"},
        502: {"description": "Upstream or parsing error"},
        503: {"description": "Misconfiguration, rate limit, or model loading"},
        504: {"description": "Timeout"},
    },
)
async def generate(body: GenerateRequest) -> GenerateResponse:
    """Send `prompt` to the Hugging Face router and return assistant text."""
    prompt = body.prompt.strip()
    if not prompt:
        logger.warning("Rejected empty prompt after strip")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="prompt must not be empty",
        )

    try:
        api_key = _require_api_key()
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Server is not configured with HUGGINGFACE_API_KEY",
        ) from None

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": ROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": MAX_TOKENS,
    }

    try:
        logger.info("Calling HF router chat/completions model=%s", ROUTER_MODEL)
        resp = requests.post(
            HF_ROUTER_CHAT_URL,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT_SEC,
        )
    except requests.Timeout as e:
        logger.error("Hugging Face router request timed out: %s", e)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Hugging Face router request timed out.",
        ) from e
    except requests.RequestException as e:
        logger.error("HTTP error calling Hugging Face router: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach Hugging Face router.",
        ) from e

    if resp.status_code in (401, 403):
        logger.warning("Hugging Face auth failed (status %s)", resp.status_code)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or unauthorized Hugging Face API key.",
        )

    if resp.status_code == 429:
        logger.warning("Hugging Face rate limit (429)")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hugging Face rate limit exceeded; retry later.",
        )

    if resp.status_code == 503:
        logger.warning("Hugging Face router unavailable (503)")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hugging Face router temporarily unavailable; retry shortly.",
        )

    if resp.status_code >= 500:
        logger.error("Hugging Face server error: %s %s", resp.status_code, resp.text[:500])
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hugging Face router returned a server error.",
        )

    try:
        body_json = resp.json()
    except ValueError:
        logger.error("Hugging Face returned non-JSON body")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hugging Face returned an invalid response.",
        )

    if resp.status_code >= 400:
        logger.error("Hugging Face client error %s: %s", resp.status_code, body_json)
        msg = _hf_router_error_message(body_json)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=msg or "Hugging Face router request failed.",
        )

    if isinstance(body_json, dict) and body_json.get("error") is not None:
        logger.error("Hugging Face error payload: %s", body_json.get("error"))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hugging Face router returned an error.",
        )

    text = _extract_router_chat_text(body_json)
    if not text or not text.strip():
        logger.error("Hugging Face returned empty assistant content: %s", body_json)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Hugging Face returned an empty generation result.",
        )

    text = text.strip()
    logger.info("HF completion length=%s chars", len(text))
    return GenerateResponse(text=text, model=MODEL_ID)
