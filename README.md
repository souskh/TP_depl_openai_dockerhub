# Hugging Face Inference + FastAPI — Docker & Azure

Minimal **FastAPI** app with `POST /generate` using **Hugging Face Inference Providers** at `https://router.huggingface.co/v1/chat/completions` (default Hub model **meta-llama/Llama-3.2-1B-Instruct** ; champ JSON `"model"` = dernier segment du nom Hub, surchargeable avec `API_RESPONSE_MODEL`), plus **Docker** and **Azure Container Apps** notes.

Also see **`solution/`** (reference) and **`tp/`** (guided lab).

## Project layout

| Path | Role |
|------|------|
| `main.py` | FastAPI app at repo root |
| `solution/` | Full reference implementation |
| `tp/` | Student TP (incomplete) |
| `requirements.txt` | fastapi, uvicorn, python-dotenv, **requests** |
| `.env.example` | `HUGGINGFACE_API_KEY` |
| `Dockerfile` | Container image on `python:3.12-slim-bookworm` |

## Hugging Face API token

The app reads **`HUGGINGFACE_API_KEY`** (see `.env.example`).

1. Sign in at [huggingface.co](https://huggingface.co).
2. Create an access token: [Settings → Access Tokens](https://huggingface.co/settings/tokens) (read permission is enough for Inference API).
3. Put it in `.env` as `HUGGINGFACE_API_KEY=hf_...` (never commit real tokens).

## Local run (without Docker)

```bash
cd /path/to/TP_depl_openai_dockerhub
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set HUGGINGFACE_API_KEY
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Docs: `http://127.0.0.1:8000/docs`

## Docker: build and run

```bash
docker build -t YOUR_DOCKERHUB_USER/hf-fastapi:latest .
docker run --rm -p 8000:8000 --env-file .env YOUR_DOCKERHUB_USER/hf-fastapi:latest
```

Or:

```bash
docker run --rm -p 8000:8000 -e HUGGINGFACE_API_KEY="$HUGGINGFACE_API_KEY" YOUR_DOCKERHUB_USER/hf-fastapi:latest
```

---

## Azure deployment (step by step)

### Prerequisites

- Docker, Docker Hub account, Azure CLI (`az login`), Azure subscription

### 1. Build and push

```bash
docker build -t YOUR_DOCKERHUB_USER/hf-fastapi:latest .
docker login
docker push YOUR_DOCKERHUB_USER/hf-fastapi:latest
```

### 2. Container Apps — variables (customize)

```bash
export RESOURCE_GROUP="rg-hf-fastapi"
export LOCATION="westeurope"
export ENV_NAME="cae-hf-fastapi"
export APP_NAME="ca-hf-generate"
export IMAGE="docker.io/YOUR_DOCKERHUB_USER/hf-fastapi:latest"
```

Create resource group, Container Apps environment, then app (target port **8000**, external ingress) — same `az containerapp create` flow as any HTTP container.

### 3. Configure `HUGGINGFACE_API_KEY`

```bash
az containerapp secret set \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --secrets hf-api-key=YOUR_HUGGINGFACE_TOKEN

az containerapp update \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --set-env-vars "HUGGINGFACE_API_KEY=secretref:hf-api-key"
```

### 4. Public URL

```bash
az containerapp show \
  --name "$APP_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --query properties.configuration.ingress.fqdn \
  -o tsv
```

Test: `POST https://<fqdn>/generate` with `{"prompt":"..."}`.

### App Service (Linux container)

Set **`WEBSITES_PORT=8000`** and add application setting **`HUGGINGFACE_API_KEY`** (or Key Vault reference).

---

## Test examples

### curl (local)

```bash
curl -s -X POST "http://127.0.0.1:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"The future of AI is"}' | jq .
```

### Health

```bash
curl -s "http://127.0.0.1:8000/health" | jq .
```

Expect `"huggingface_configured": true` when the token is set.

### Postman

- **POST** `http://127.0.0.1:8000/generate`
- Header: `Content-Type: application/json`
- Body: `{"prompt": "Hello"}`  
- Expect **200** and `"model": "gpt2"`.

## Security

- Never commit `.env` or tokens.
- Use Azure secrets / Key Vault in production.

## License

Educational / assignment use.
