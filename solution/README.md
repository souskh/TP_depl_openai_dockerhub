# Solution — Hugging Face Inference + FastAPI (référence)

Implémentation complète. Les étudiants travaillent dans **`../tp/`** ; compare avec ce dossier une fois le TP terminé.

## Comment tester la solution (FR)

1. **Token Hugging Face** — Crée un token sur [Settings → Access Tokens](https://huggingface.co/settings/tokens). Mets **`HUGGINGFACE_API_KEY`** dans **`.env` dans le dossier `solution/`** si tu lances `uvicorn` depuis `solution/`.

   ```bash
   cd solution
   cp .env.example .env          # puis édite HUGGINGFACE_API_KEY
   cp ../.env .env               # alternative si tu as déjà un .env à la racine
   ```

2. **Python** :

   ```bash
   cd solution
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Vérifier** : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
   - `GET /health` → `"huggingface_configured": true`, `"status": "ok"`  
   - `POST /generate` → `{"text":"...","model":"Llama-3.2-1B-Instruct"}` (ou la valeur de `API_RESPONSE_MODEL`)

4. **Docker** : `docker run ... --env-file .env` (ou `-e HUGGINGFACE_API_KEY=...`)

Si `degraded` ou **503** « not configured », vérifie `.env` dans **`solution/`** et le nom exact **`HUGGINGFACE_API_KEY`**.

### Dépannage Hugging Face

L’API utilise le **routeur** `router.huggingface.co` (l’ancien `api-inference.huggingface.co` n’est plus pris en charge).

- **503** : surcharge ou indisponibilité temporaire ; réessaie.  
- **429** : limite de débit ; réessaie plus tard.  
- **401** : token invalide, expiré, ou sans permission *Inference Providers*.  
- **`not supported by any provider you have enabled`** : va sur [Inference Providers](https://hf.co/settings/inference-providers) et active au moins un fournisseur qui sert ton modèle, ou change **`HUGGINGFACE_MODEL`** pour un modèle listé comme disponible (le défaut **Llama-3.2-1B-Instruct** convient souvent après acceptation des conditions Llama sur le Hub).
- **`model_not_found`** : utilise un **ID Hub complet** (pas un raccourci type `gpt2`).

## Layout

| File | Role |
|------|------|
| `main.py` | FastAPI → routeur HF ; défaut `meta-llama/Llama-3.2-1B-Instruct` (surcharge `HUGGINGFACE_MODEL`) |
| `requirements.txt` | fastapi, uvicorn, python-dotenv, requests |
| `.env.example` | `HUGGINGFACE_API_KEY` |
| `Dockerfile` | Port **8000** |

## Run locally (EN)

```bash
cd solution
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set HUGGINGFACE_API_KEY
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Docker

```bash
cd solution
docker build -t YOUR_DOCKERHUB_USER/hf-fastapi:latest .
docker run --rm -p 8000:8000 --env-file .env YOUR_DOCKERHUB_USER/hf-fastapi:latest
```

## Azure (summary)

Déploie l’image puis configure **`HUGGINGFACE_API_KEY`** (secret Container Apps ou réglage d’application App Service).

## Test with curl

```bash
# Expected: 200, {"text":"...","model":"Llama-3.2-1B-Instruct"} (sauf si API_RESPONSE_MODEL défini)
curl -s -X POST "http://127.0.0.1:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"The meaning of life is"}'

curl -s "http://127.0.0.1:8000/health"
```

## Security

Ne commite pas `.env` ni les tokens.
