# Verda Cloud GPU Subchallenge — Self-Hosted Open-Weight Gemma & Nemotron Cluster

## Role in CheckEm
The Hostinger VPS (`https://checkem.tech/`) runs our CPU-light Python web application, web scraper, provenance scorer, and Traefik reverse proxy. To run **fine-tuned open-weights models** (custom Gemma VL QLoRA and Nemotron 3.5 VL adapters, full token log-probabilities, and high-resolution visual tiling) without VRAM constraints, CheckEm integrates with an external **Verda Cloud GPU instance** (NVIDIA A100 / H100 / L40S).

## Architecture: Hostinger Web App <-> Verda Cloud GPU Cluster

```
Hostinger VPS (checkem.tech)
  ├── Oxylabs Scraper + Provenance Scorer + Minimalist UI
  └── AI Ensemble Dispatcher (`app.py`)
         ├── [if VERDA_GPU_BASE_URL set] ──▶ Verda Cloud GPU VM (vLLM / NVIDIA NIM)
         │                                     ├── Port 8001: Gemma VL + CheckEm QLoRA Adapter
         │                                     └── Port 8002: Nemotron 3.5 VL Reasoning Engine
         │                                     (Served via Caddy/Nginx reverse proxy on :8000/v1)
         └── [fallback]                  ──▶ Hostinger AI Router (/v1/chat/completions)
```

## How CheckEm Routes to Verda Cloud (`app.py`)
1. `load_env_file()` reads four Verda settings from `/root/hostinger-ai-reviewer/.env`:
   - `VERDA_GPU_BASE_URL` (e.g. `https://gpu.your-verda-ip.sslip.io/v1` or `http://<verda-ip>:8000/v1`)
   - `VERDA_API_KEY` (bearer token protecting your Verda vLLM gateway)
   - `VERDA_GEMMA_MODEL` (optional served adapter name, e.g. `gemma-checkem-lora`)
   - `VERDA_NEMOTRON_MODEL` (optional served Nemotron model name)
2. Inside `call_hostinger_ai_router()`, whenever `VERDA_GPU_BASE_URL` is set and the juror is **Gemma** or **Nemotron**, CheckEm dispatches inference to your Verda Cloud GPU cluster (`mode: "live_verda_gpu"`).
3. **Graceful High-Availability Fallback**: If the Verda Cloud GPU instance is spun down to save GPU hours outside live demos/training, CheckEm automatically falls back to Hostinger AI Router so `https://checkem.tech/` stays 100% online.

## Quick Deployment on Verda Cloud GPU VM
1. Provision a Verda Cloud instance (Ubuntu + NVIDIA drivers + Docker + NVIDIA Container Toolkit, `>= 2x H100 80GB` or split single-model serving on `1x A100 80GB`).
2. Copy [`docker-compose.verda-gpu.yml`](docker-compose.verda-gpu.yml) and [`deploy_verda.sh`](deploy_verda.sh) onto the Verda instance.
3. Run:
   ```bash
   export HF_TOKEN="hf_..."
   export VERDA_API_KEY="choose-a-strong-bearer-secret"
   bash deploy_verda.sh
   ```
4. Add `VERDA_GPU_BASE_URL=http://<VERDA_PUBLIC_IP>:8000/v1` and `VERDA_API_KEY=...` to `/root/hostinger-ai-reviewer/.env` on the Hostinger VPS and run `docker restart checkem-app`.
