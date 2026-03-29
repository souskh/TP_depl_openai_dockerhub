"""
TP — API FastAPI + Hugging Face (version simple)
================================================
Complète les étapes dans l’ordre. Durée visée : 1–2 h.
Compare avec ../solution/main.py quand tu as fini.
"""

import os

# =============================================================================
# STEP 1 — Charger le fichier .env
# =============================================================================
# TODO: importe load_dotenv depuis le module dotenv
# HINT: from dotenv import load_dotenv
#
# TODO: appelle load_dotenv() une fois (au démarrage du module)
# HINT: load_dotenv()
# =============================================================================


from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# =============================================================================
# STEP 2 — Bibliothèque pour appeler l’API en HTTP
# =============================================================================
# TODO: importe le module requests (déjà dans requirements.txt)
# HINT: import requests
# =============================================================================


app = FastAPI(title="TP Hugging Face", version="0.1")


# =============================================================================
# STEP 3 — URL du routeur Hugging Face + nom du modèle
# =============================================================================
# Le vieux domaine api-inference.huggingface.co n’est plus utilisé.
# On utilise le routeur (format proche d’OpenAI).
#
# TODO: crée deux variables (en MAJUSCULES, constantes) :
#   HF_URL = "https://router.huggingface.co/v1/chat/completions"
#   HF_MODEL = "meta-llama/Llama-3.2-1B-Instruct"
#
# HINT: copie-colle les deux lignes ci-dessus après les TODO
# =============================================================================

HF_URL = None  # TODO: remplacer par la bonne chaîne
HF_MODEL = None  # TODO: remplacer par la bonne chaîne


# =============================================================================
# STEP 4 — Modèle Pydantic pour le JSON d’entrée
# =============================================================================
# Le client envoie : {"prompt": "ton texte"}
#
# TODO: renomme le champ `a_remplacer` en `prompt`
#       (garde min_length=1 et alias="prompt" si tu veux le même JSON)
#
# HINT: prompt: str = Field(..., min_length=1, alias="prompt")
# =============================================================================


class GenerateRequest(BaseModel):
    a_remplacer: str = Field(
        ...,
        min_length=1,
        alias="prompt",
        description="TODO STEP 4: renommer en prompt",
    )


# =============================================================================
# STEP 5 — Lire la clé API (sans la mettre dans le code !)
# =============================================================================
# TODO: écris une fonction get_hf_token() qui :
#   - lit HUGGINGFACE_API_KEY avec os.getenv
#   - enlève les espaces avec .strip() si la valeur existe
#   - retourne None si la clé est absente ou vide après strip
#
# HINT:
#   key = os.getenv("HUGGINGFACE_API_KEY")
#   if key:
#       key = key.strip()
#   if not key:
#       return None
#   return key
# =============================================================================


def get_hf_token():
    # TODO STEP 5
    return None


@app.get("/health")
def health():
    """Petit test : GET http://127.0.0.1:8000/health"""
    return {"status": "ok"}


@app.post("/generate")
def generate(body: GenerateRequest):
    """
    STEP 6 — Appeler Hugging Face et renvoyer du JSON.

    Corps attendu : {"prompt": "..."}
    Réponse voulue  : {"text": "...", "model": "..."}  (model = dernier mot du nom Hub, ex. Llama-3.2-1B-Instruct)

    À faire :
    1) Récupère la clé avec get_hf_token(). Si None → HTTPException 503 avec un message clair.
    2) Prépare le corps JSON pour le routeur (chat) :
         {
           "model": <HF_MODEL>,
           "messages": [{"role": "user", "content": <le prompt du body>}],
           "max_tokens": 128,
         }
    3) requests.post(HF_URL, headers={...}, json=..., timeout=60)
       Headers : Authorization: Bearer <clé>  et  Content-Type: application/json
    4) Si status_code != 200 → HTTPException 502 avec un message simple (tu peux mettre resp.text[:200] dans le message)
    5) Parse resp.json() : le texte généré est dans choices[0]["message"]["content"]
    6) return {"text": texte, "model": ...}  (model = partie après le dernier / de HF_MODEL, ou une constante)

    HINT pour le texte du prompt après STEP 4 :
       prompt = body.prompt
    (tant que STEP 4 n’est pas faite, tu peux utiliser body.a_remplacer pour tester)
    """
    # TODO STEP 6 — remplace tout le bloc ci-dessous par ton code

    raise HTTPException(
        status_code=501,
        detail="TP: complète STEP 6 (voir docstring de generate).",
    )
