# 🚀 TP — Déploiement d'une API FastAPI avec Docker et Azure

## 🎯 Objectif

Mettre en place une API de génération de texte utilisant Hugging Face, la conteneuriser avec Docker, puis la déployer sur Azure Container Apps.

---

## 🧱 Architecture

```
[ Local (PC) ]
     ↓
   curl / Postman
     ↓
[ Azure Container Apps ]
     ↓
[ API FastAPI (Docker) ]
     ↓
[ Hugging Face API ]
```

---

## ⚙️ Prérequis

* Compte Azure
* Azure CLI installé
* Docker installé (Colima ou Docker Desktop)
* Clé API Hugging Face

---

## 🔐 1. Connexion à Azure

```bash
az login
```

---

## 📦 2. Création du Resource Group

```bash
az group create --name rg-hf-fastapi --location westeurope
```

---

## 🐳 3. Création du Azure Container Registry (ACR)

```bash
az acr create \
  --resource-group rg-hf-fastapi \
  --name monacrhf12345 \
  --sku Basic
```

---

## 🔑 4. Activer les credentials ACR

```bash
az acr update \
  --name monacrhf12345 \
  --admin-enabled true
```

---

## 🔐 5. Connexion au registry

```bash
az acr login --name monacrhf12345
```

---

## 🧱 6. Build & Push de l’image Docker (IMPORTANT : AMD64)

```bash
docker buildx build \
  --platform linux/amd64 \
  -t monacrhf12345.azurecr.io/hf-fastapi:latest \
  --push .
```

---

## ☁️ 7. Création de l’environnement Azure

```bash
az containerapp env create \
  --name hf-env \
  --resource-group rg-hf-fastapi \
  --location westeurope
```

---

## 🚀 8. Déploiement de l’application

```bash
az containerapp create \
  --name hf-fastapi-app \
  --resource-group rg-hf-fastapi \
  --environment hf-env \
  --image monacrhf12345.azurecr.io/hf-fastapi:latest \
  --target-port 8000 \
  --ingress external \
  --registry-server monacrhf12345.azurecr.io \
  --registry-username monacrhf12345 \
  --registry-password <password>
```

---

## 🔐 9. Ajouter la clé API Hugging Face

```bash
az containerapp update \
  --name hf-fastapi-app \
  --resource-group rg-hf-fastapi \
  --set-env-vars HUGGINGFACE_API_KEY=hf_xxxxx
```

---

## 🌍 10. Récupérer l’URL publique

```bash
az containerapp show \
  --name hf-fastapi-app \
  --resource-group rg-hf-fastapi \
  --query properties.configuration.ingress.fqdn
```

---

## 🧪 11. Test de l’API

```bash
curl -X POST https://<url>/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt":"Hello from Azure"}'
```

---

## ✅ Résultat attendu

```json
{
  "text": "...",
  "model": "gpt2"
}
```

---

## 🧠 Compétences acquises

* Création d’une API avec FastAPI
* Conteneurisation avec Docker
* Gestion des registres (ACR)
* Déploiement cloud avec Azure Container Apps
* Gestion des variables d’environnement (API keys)
* Test d’API via curl / Postman

---

## ⚠️ Bonnes pratiques

* Ne jamais exposer sa clé API dans le code
* Utiliser des variables d’environnement
* Supprimer ou régénérer les clés après usage

---

## 🎯 Conclusion

Ce TP démontre la mise en place complète d’une API cloud, de sa conception locale jusqu’à son déploiement public avec intégration d’un service externe.

---
