#!/usr/bin/env bash
set -euo pipefail

#
# Deploy the same FastAPI container multiple times on Azure Container Apps
# (one per student), following README_push_azure.md flow:
# - ACR with admin enabled
# - docker buildx --platform linux/amd64 --push to ACR
# - containerapp create with --registry-username/--registry-password
# - set HUGGINGFACE_API_KEY as env var on the app
#
# Usage:
#   HUGGINGFACE_API_KEY="hf_..." ./deploy_student_aca.sh etu1
#

STUDENT_ID="${1:-}"
if [[ -z "${STUDENT_ID}" ]]; then
  echo "Usage: HUGGINGFACE_API_KEY='hf_...' $0 <student-id>  (ex: etu1)"
  exit 2
fi

az_retry() {
  local -r max_attempts="${1:?max_attempts}"
  shift
  local attempt=1
  local delay=2
  while true; do
    if "$@"; then
      return 0
    fi
    if (( attempt >= max_attempts )); then
      return 1
    fi
    echo "Retrying (${attempt}/${max_attempts}) in ${delay}s: $*" >&2
    sleep "${delay}"
    attempt=$((attempt + 1))
    delay=$((delay * 2))
  done
}

# ---- Defaults (override by exporting env vars) ----
LOCATION="${LOCATION:-westeurope}"
RESOURCE_GROUP="${RESOURCE_GROUP:-rg-hf-fastapi}"
ACR_NAME="${ACR_NAME:-sskhiri}"
ACR_SERVER="${ACR_SERVER:-${ACR_NAME}.azurecr.io}"
ACR_REPO="${ACR_REPO:-hf-fastapi}"
TAG="${TAG:-${STUDENT_ID}}"

# Container Apps
ENV_NAME="${ENV_NAME:-hf-env}"
DEFAULT_APP_NAME="hf-fastapi-app-${STUDENT_ID}"
if [[ -n "${APP_NAME:-}" && "${APP_NAME}" != "${DEFAULT_APP_NAME}" ]]; then
  echo "Warning: ignoring existing APP_NAME='${APP_NAME}' and using '${DEFAULT_APP_NAME}' from student id."
fi
APP_NAME="${DEFAULT_APP_NAME}"
TARGET_PORT="${TARGET_PORT:-8000}"

# Hugging Face token: ask interactively if missing
if [[ -z "${HUGGINGFACE_API_KEY:-}" ]]; then
  if [[ -t 0 ]]; then
    read -r -s -p "Enter HUGGINGFACE_API_KEY (input hidden): " HUGGINGFACE_API_KEY
    echo
  fi
fi

if [[ -z "${HUGGINGFACE_API_KEY:-}" ]]; then
  echo "Error: HUGGINGFACE_API_KEY is required."
  echo "Tip: export HUGGINGFACE_API_KEY='hf_...' then run again."
  exit 2
fi

IMAGE="${ACR_SERVER}/${ACR_REPO}:${TAG}"

echo "== Deploy student '${STUDENT_ID}' =="
echo "RG=${RESOURCE_GROUP}  LOCATION=${LOCATION}"
echo "ACR=${ACR_NAME} (${ACR_SERVER})  IMAGE=${IMAGE}"
echo "ENV=${ENV_NAME}  APP=${APP_NAME}  PORT=${TARGET_PORT}"
echo

echo "== 1) Create RG (idempotent) =="
az group create --name "${RESOURCE_GROUP}" --location "${LOCATION}" 1>/dev/null

echo "== 2) Ensure ACR exists + admin enabled =="
az acr update --name "${ACR_NAME}" --admin-enabled true 1>/dev/null

echo "== 3) Login to ACR =="
az acr login --name "${ACR_NAME}" 1>/dev/null

echo "== 4) Build & push image (linux/amd64) =="
docker buildx build \
  --platform linux/amd64 \
  -t "${IMAGE}" \
  --push .

echo "== 5) Ensure Container Apps environment exists (idempotent) =="
if az containerapp env show --name "${ENV_NAME}" --resource-group "${RESOURCE_GROUP}" 1>/dev/null 2>&1; then
  echo "Environment '${ENV_NAME}' already exists."
else
  az_retry 4 az containerapp env create \
    --name "${ENV_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --location "${LOCATION}" 1>/dev/null
fi

echo "== 6) Get ACR admin credentials for registry pull =="
ACR_PASS="$(az acr credential show --name "${ACR_NAME}" --query "passwords[0].value" -o tsv)"

echo "== 7) Create / update Container App =="
# If it exists, update. Otherwise, create.
if az containerapp show --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" 1>/dev/null 2>&1; then
  az containerapp update \
    --name "${APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --image "${IMAGE}" \
    --set-env-vars "HUGGINGFACE_API_KEY=${HUGGINGFACE_API_KEY}" 1>/dev/null
else
  az containerapp create \
    --name "${APP_NAME}" \
    --resource-group "${RESOURCE_GROUP}" \
    --environment "${ENV_NAME}" \
    --image "${IMAGE}" \
    --target-port "${TARGET_PORT}" \
    --ingress external \
    --registry-server "${ACR_SERVER}" \
    --registry-username "${ACR_NAME}" \
    --registry-password "${ACR_PASS}" \
    --env-vars "HUGGINGFACE_API_KEY=${HUGGINGFACE_API_KEY}" 1>/dev/null
fi

echo "== 8) Show public FQDN =="
FQDN="$(az containerapp show --name "${APP_NAME}" --resource-group "${RESOURCE_GROUP}" --query properties.configuration.ingress.fqdn -o tsv)"
echo "URL: https://${FQDN}"
echo
echo "Test:"
echo "  curl -s https://${FQDN}/health"
echo "  curl -s -X POST https://${FQDN}/generate -H 'Content-Type: application/json' -d '{\"prompt\":\"Hello from ${STUDENT_ID}\"}'"
