#!/usr/bin/env bash
set -euo pipefail

echo "Checking NVIDIA GPU availability on Verda Cloud instance..."
nvidia-smi

if [ -z "${VERDA_API_KEY:-}" ]; then
  echo "ERROR: Please export VERDA_API_KEY before running deploy_verda.sh"
  exit 1
fi

echo "Starting Verda GPU OpenAI-compatible vLLM stack..."
docker compose -f docker-compose.verda-gpu.yml up -d

echo "Verda vLLM gateway listening on port 8000."
echo "Set on CheckEm VPS (.env):"
echo "  VERDA_GPU_BASE_URL=http://<VERDA_INSTANCE_IP>:8000/v1"
echo "  VERDA_API_KEY=<your-verda-key>"
echo "  VERDA_GEMMA_MODEL=gemma-checkem-vl"
