# Gemma 4 31B VL — Lightweight Open-Weight Anchor in a 5-Model Ensemble

## Role in CheckEm
In CheckEm's 5-model cross-family jury (`Gemma 4 31B VL`, `Nemotron 3.5 Super VL`, `Gemini 3.1 Flash Lite VL`, `Kimi K2.6 VL`, and `Claude Haiku 4.5 VL`), Google's open-weight **Gemma 4 31B VL** (`gemma-4-31b`) serves as our **Visual Forensics, Fear Appeal & Counterfactual Framing** juror.

## Added value of the Gemma open weights and smaller parameter size 

1. **Enables the 5-model jury without latency blowup**:
   Gemma 4 31B completes combined vision + section classification in roughly ~1.5–3s, letting CheckEm run **5 diverse VLMs concurrently** within a single frontier model's latency budget.
2. **Cross-Family Error Decorrelation**:
   Closed commercial model families can share correlated blind spots or refusal habits. Including open-weight Gemma 4 alongside NVIDIA MoE (Nemotron), Anthropic (Claude Haiku 4.5), MoonshotAI (Kimi K2.6), and Gemini ensures minority disagreements (`1–2 / 5`) actually surface borderline propaganda rather than rubber-stamping one provider's bias.
3. **Auditable Open Model Behavior**:
   Published Gemma model cards and open tokenizer/vision preprocessing behavior let reviewers inspect *why* Gemma splits with frontier models (for instance, flagging synthetic illustrations inside neutral encyclopedia entries while keeping surrounding prose unmarked).

## Test for model latency
Run [`gemma_ensemble_benchmark.py`](gemma_ensemble_benchmark.py) to compare Gemma 4 31B latency and structured JSON output side-by-side against CheckEm's other lightweight jurors:

```bash
python3 challenges/gemma/gemma_ensemble_benchmark.py --text "Act now before this loophole destroys everything you own."
```
