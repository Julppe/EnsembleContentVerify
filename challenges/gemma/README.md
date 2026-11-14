# Gemma VLM Subchallenge — Visual Forensics, Rhetorical Framing & Open-Weight Fine-Tuning

## Role in CheckEm
In the CheckEm ensemble (`REVIEW_MODELS`), **Gemma (`gemma-4-31b` / open-weight Gemma VLM)** acts as our **Visual Forensics, Fear Appeal & Counterfactual Framing juror**:
1. **Multimodal Inspection**: Inspects base64-encoded content images (`img-1..img-K`) alongside page text sections (`sec-1..sec-N`) to spot AI-generated synthetic textures, anatomical/text artifacts, or manipulative visual framing.
2. **Fear Appeal & Rhetorical Framing**: Detects urgent catastrophe framing and emotionally charged appeals paired with unverified claims.
3. **Hard-Negative Restraint**: Distinguishes neutral reference/encyclopedic articles discussing manipulation concepts from active persuasion.

## How CheckEm Integrates Gemma (`app.py`)
- By default, `AI_ROUTER_MODELS` routes `gemma-4-31b` through the Hostinger AI Router (`/v1/chat/completions`) with multimodal image attachments (`vision: True`).
- When a self-hosted **Verda Cloud GPU** endpoint is configured (`VERDA_GPU_BASE_URL` + optional `VERDA_GEMMA_MODEL`), `call_hostinger_ai_router()` in `app.py` automatically routes Gemma inference directly to your fine-tuned Gemma LoRA adapter served via vLLM on Verda Cloud, falling back transparently to the router if the GPU VM is offline.

## Leveraging Gemma Beyond Zero-Shot Prompting (Because It Is Open-Weights)
Because Gemma provides open model weights, we can unlock three capabilities impossible with closed APIs:

### 1. QLoRA Fine-Tuning for Technique Classification & Span Extraction
Closed prompts sometimes drift on subtle technique boundaries (`Fear Appeal` vs `Loaded Language`) or produce overly broad quotes. Using [`finetune_gemma_qlora.py`](finetune_gemma_qlora.py), you can fine-tune Gemma on a 4-bit QLoRA adapter using:
- **SemEval-2020 Task 11** (*Detection of Propaganda Techniques in News Articles*) formatted into CheckEm's exact strict JSON schema (`section_evaluations` + `trigger_quote`).
- **Hard-Negative Curated Samples** (e.g., Wikipedia articles explaining logical fallacies, WHO fact sheets) labeled `"clean"` so the adapter learns to suppress false positives on journalistic reporting.
- **Neutral Counterfactual Rewrites**: Extending training targets with a `"neutral_rewrite"` field so Gemma teaches readers *how* removing loaded adjectives changes an alarming paragraph into neutral reporting.

### 2. Token Log-Probability Calibration for Controllable Precision / FPR
With self-hosted open-weight Gemma via vLLM (`logprobs=True`), CheckEm can read the exact token probability distribution over `"questionable"` vs `"clean"` inside the JSON output and sweep the decision threshold $\tau$ to trade recall for near-zero False-Positive Rate depending on deployment sensitivity.

### 3. Layer-Wise Visual-Text Attention Probing
Inspecting cross-attention maps between image patches and the `AI-Generated / Synthetic Image` classification token makes image verdicts auditable down to localized artifacts (e.g., garbled text banners or anatomical glitches).

## Running the Fine-Tuning Pipeline (on Verda Cloud GPU)
```bash
pip install torch transformers datasets peft trl bitsandbytes accelerate
python3 challenges/gemma/finetune_gemma_qlora.py \
  --model-id google/gemma-3-27b-it \
  --train-file data/propaganda_train.jsonl \
  --output-dir checkpoints/gemma-checkem-lora
```
Then mount `checkpoints/gemma-checkem-lora` inside [`../verda-cloud/docker-compose.verda-gpu.yml`](../verda-cloud/docker-compose.verda-gpu.yml) and set `VERDA_GEMMA_MODEL=gemma-checkem-lora` in `.env`.
