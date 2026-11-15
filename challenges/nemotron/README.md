# Nemotron 3.5 Super VL — Sparse MoE reasoning in a 5-model jury

## Model importance to the app

In CheckEm we use a 5-model cross-family jury (`Gemma 4 31B VL`, `Nemotron 3.5 Super VL`, `Gemini 3.1 Flash Lite VL`, `Kimi K2.6 VL`, and `Claude Haiku 4.5 VL`), **Nemotron 3.5 Super VL** (`nemotron-3.5-super-vl`). 
- Instead of running a dense 120B parameter forward pass, Nemotron's sparse Mixture-of-Experts (MoE) routing activates only **12B parameters per token** in **Super VL**. That lightweight active compute delivers fast vision + reasoning latency (~1s) so CheckEm can pair NVIDIA reasoning alongside Gemma 4, Gemini, Kimi K2.6, and Claude Haiku 4.5 concurrently.
- Step-by-step reasoning traces (`reasoning_content` / `reasoning`) help keep neutral reference articles (such as Wikipedia's *Whataboutism* or *Propaganda Techniques* entries) cleanly unmarked.

## API implementation details

`call_hostinger_ai_router()` in `app.py` routes Nemotron calls cleanly with exponential backoff (`_post_with_backoff`):
1. **Primary Endpoint (`VERDA_INFERENCE_KEY`)**: Calls `https://containers.datacrunch.io/nemotron-3-5-super-vl-b300/v1/chat/completions` with `model="nemotron-3.5-super-vl"` (`text` + `image` support, parsing `content` or `reasoning_content` / `reasoning`).
2. **Optional Fallback (`NVIDIA_API_KEY`)**: Supports OpenAI-compatible NVIDIA Build (`https://integrate.api.nvidia.com/v1`, model `nvidia/nemotron-3.5-super-vl-120b-a12b`) with retry/backoff for 40 RPM limits.
3. **Router Fallback**: Falls back transparently to Hostinger AI Router (`nemotron-lightning-3.5-30b-a3b`) if the dedicated endpoint is unreachable.

## Standalone testing

Run [`nemotron_vl_pipeline.py`](nemotron_vl_pipeline.py) directly against the configured endpoint:

```bash
python3 challenges/nemotron/nemotron_vl_pipeline.py \
  --title "Test Claim" \
  --text "Why criticize our emissions when elites fly private jets?"
```
