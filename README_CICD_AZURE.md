# CI/CD Azure + Tests Unitaires (Résumé)

Ce document résume la mise en place demandée :

- Exécuter les tests unitaires à chaque Pull Request vers `main`
- Après merge sur `main`, builder et pousser l'image Docker vers Azure Container Registry (ACR)

---

## 1) Ce qui a été ajouté dans le repo

- Workflow GitHub Actions : `.github/workflows/ci-cd.yml`
- Tests unitaires : `tests/units/test_main.py`

Comportement du workflow :

- `pull_request` vers `main` -> job `unit-tests`
- `push` sur `main` -> job `unit-tests` puis `push-image-to-acr`

---

## 2) Secrets GitHub à configurer

Dans `GitHub > Settings > Secrets and variables > Actions`, ajouter :

- `AZURE_CREDENTIALS` (JSON complet pour `azure/login`)
- `ACR_NAME` (ex: `monacrhf12345`)
- `ACR_LOGIN_SERVER` (ex: `monacrhf12345.azurecr.io`)
- `ACR_REPOSITORY` (ex: `hf-fastapi`)

---

## 3) Format attendu pour `AZURE_CREDENTIALS`

Coller un JSON complet de ce type :

```json
{
  "clientId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "clientSecret": "xxxxxxxxxxxxxxxx",
  "subscriptionId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "tenantId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "activeDirectoryEndpointUrl": "https://login.microsoftonline.com",
  "resourceManagerEndpointUrl": "https://management.azure.com/",
  "activeDirectoryGraphResourceId": "https://graph.windows.net/",
  "sqlManagementEndpointUrl": "https://management.core.windows.net:8443/",
  "galleryEndpointUrl": "https://gallery.azure.com/",
  "managementEndpointUrl": "https://management.core.windows.net/"
}
```

Important :
- Si un `clientSecret` a ete expose, il faut le revoquer et en generer un nouveau.

---

## 4) Processus de travail

1. Créer une branche
2. Push du code
3. Ouvrir une PR vers `main`
4. Vérifier que les tests passent (`unit-tests`)
5. Merge dans `main`
6. Vérifier le job `push-image-to-acr` (build + push Docker)

---

## 5) Verification du push image dans ACR

Commande utile :

```bash
az acr repository show-tags -n monacrhf12345 --repository hf-fastapi -o table
```

Tags attendus :
- `latest`
- `${GITHUB_SHA}` (tag du commit du workflow)

---

## 6) Déploiement des apps étudiants

Script de deploiement multi-etudiants :

- `deploy_student_aca.sh`

Exemple :

```bash
./deploy_student_aca.sh etu1
./deploy_student_aca.sh etu2
./deploy_student_aca.sh etu3
./deploy_student_aca.sh etu4
```

Le script demande `HUGGINGFACE_API_KEY` en interactif si elle n'est pas deja exportee.

---

## 7) Scripts de test API par URL

- `test_get.sh` -> teste `GET /health`
- `test_post.sh` -> teste `POST /generate`

L'etudiant modifie juste `APP_URL` (et `PROMPT` pour le post), puis execute :

```bash
bash test_get.sh
bash test_post.sh
```

---

## 8) Notes

- Le workflow pousse l'image vers ACR apres merge sur `main`.
- La CI des tests unitaires s'exécute sur PR.
- Pour plus de securite a terme, migration conseillee vers auth OIDC GitHub (sans secret statique).
