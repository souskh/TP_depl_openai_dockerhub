#!/usr/bin/env bash
set -euo pipefail

# Change APP_URL (and optionally PROMPT), then run:
# bash test_post.sh

APP_URL="https://hf-fastapi-app-monday.redgrass-d540cf0f.westeurope.azurecontainerapps.io"
PROMPT="Hello from etu1"

echo "== POST /generate =="
curl -s -X POST "${APP_URL}/generate" \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"${PROMPT}\"}"
echo
