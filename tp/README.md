# TP guidé — comment tester (avec `.env`)

Le fichier **`tp/main.py` est volontairement incomplet**. Tant que les étapes 1 → 6 ne sont pas faites, `/generate` ne pourra pas appeler Hugging Face correctement.

## 1. Où placer le `.env`

**Option A (recommandée)** — `.env` à la **racine du repo** :

```bash
cd /chemin/vers/TP_depl_openai_dockerhub
python3 -m venv .venv
source .venv/bin/activate
pip install -r tp/requirements.txt
uvicorn tp.main:app --reload --host 0.0.0.0 --port 8000
```

**Option B** — depuis **`tp/`** :

```bash
cd tp
cp ../.env .env
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Contenu minimal :

```env
HUGGINGFACE_API_KEY=hf_...
```

Token : [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)

## 2. Tester sans tout avoir codé

- **`GET /health`** : voir si `read_huggingface_api_key()` est implémentée.
- **`POST /generate`** : **501** tant que l’étape 6 n’est pas faite (normal).

## 3. TP terminé — exemple

```bash
curl -s -X POST "http://127.0.0.1:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hello"}'
# Attendu : 200, "model": "gpt2"
```

Le JSON d’entrée utilise **`"prompt"`** (`alias="prompt"` sur le champ à renommer).

## 4. Swagger

[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

## 5. Décoder les logs

| Symptôme | Cause probable |
|----------|----------------|
| **501** sur `/generate` | Étape 6 non implémentée |
| Warning **étape 5** | `read_huggingface_api_key()` manquante |
| **Clé absente** après étape 5 | `load_dotenv()` + `HUGGINGFACE_API_KEY` dans `.env` |

## 6. Corrigé

Comparer avec **`solution/`**.
