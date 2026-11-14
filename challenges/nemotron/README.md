# Nemotron 3.5 VL Subchallenge — Logical Fallacies, Reasoning Traces & Visual Integrity

## Role in CheckEm
In the CheckEm ensemble, **Nemotron 3.5 VL** (`nemotron-lightning-3.5-30b-a3b` via Hostinger Router or self-hosted NVIDIA Nemotron 3.5 VL on Verda Cloud GPUs) serves as our **Logical Fallacy, Whataboutism & Claim Integrity Juror**:
1. **Structural Fallacy Analysis**: Unlike surface sentiment detectors, reasoning-capable Nemotron models excel at detecting logical non-sequiturs such as **Whataboutism** (deflecting criticism to unrelated targets), **False Dilemma** (artificial binary framing), and **Fabricated Authority**.
2. **Hard-Negative Restraint**: Because CheckEm uses explicit reasoning steps, Nemotron separates *descriptive mentions* of fallacies (e.g., Wikipedia's *Whataboutism* article stays unflagged) from active manipulative arguments.
3. **Multimodal Document & Chart Forensics**: When paired with multimodal Nemotron VL weights on Verda Cloud GPUs, it inspects scraped page images, infographics, and screenshot banners to cross-check visual captions against body claims.

## How CheckEm Integrates Nemotron (`app.py`)
- Configured in `MODEL_PROFILES["nemotron-lightning-3.5-30b-a3b"]` with `"vision": True` and automatic fallback handling if a router tier accepts text-only payloads.
- When `VERDA_GPU_BASE_URL` and `VERDA_NEMOTRON_MODEL` are configured in `.env`, CheckEm routes Nemotron directly to your dedicated **Verda Cloud GPU** vLLM/NVIDIA NIM container (`live_verda_gpu`), with automatic fallback to `hostinger_ai_router_base_url`.

## Leveraging Open Nemotron Weights Further
Just like Gemma, hosting open NVIDIA Nemotron weights unlocks:
1. **Reasoning-Trace Auditing**: Returning `msg.get("reasoning")` alongside `content` lets analysts inspect the step-by-step logical chain behind each fallacy classification before producing the concise reader-facing summary.
2. **LoRA Specialization on Logical Fallacy Corpora**: Adapting Nemotron on datasets like *LOGIC* / *Argotario* + CheckEm's Hard Negatives tightens precision on borderline policy journalism vs manipulative spin.
3. **High-Resolution Image Tiling**: On Verda A100/H100 GPUs, vLLM can pass full-resolution chart/meme tiles to Nemotron VL without aggressive thumbnail downscaling so small warped text inside synthetic images remains legible.

## Standalone Test Client
Test Nemotron 3.5 VL directly against either Verda Cloud GPU or Hostinger AI Router using [`nemotron_vl_pipeline.py`](nemotron_vl_pipeline.py):
```bash
python3 challenges/nemotron/nemotron_vl_pipeline.py --title "Test Claim" --text "Why criticize our emissions when elites fly private jets?"
```
