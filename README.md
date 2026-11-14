# CheckEm — Name the Technique & Trust the Source

[![Live Demo](https://img.shields.io/badge/Live%20Demo-checkem.tech-4f46e5)](https://checkem.tech/)
[![Slides](https://img.shields.io/badge/Slides-checkem.tech%2Fslides-059669)](https://checkem.tech/slides)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CheckEm** runs a **5-model cross-family VLM jury** that marks suspicious rhetoric and synthetic media with coloured overlines directly on a natural webpage preview, scores source provenance independently, and exposes model disagreement instead of hiding behind a single score.

> **Presentation Deck:** [checkem.tech/slides](https://checkem.tech/slides) · [docs/PRESENTATION.md](docs/PRESENTATION.md)

## Core Pillars

1. **Name the Technique (5-Model Cross-Family Jury)** — Concurrently polls `Gemma 4 31B VL`, `Nemotron 3.5 Super VL`, `Gemini 3.1 Flash Lite VL`, `Kimi K2.6 VL`, and `Claude Haiku 4.5 VL` across six text tactics (`Loaded Language`, `Fear Appeal`, `Whataboutism`, `Fabricated Authority`, `False Dilemma`, `Scapegoating / Ad Hominem`) and two visual classes (`AI-Generated / Synthetic Image`, `Manipulative Visual Framing`), overlining flagged spans in-place with clickable juror explanations.
2. **Trust the Source** — `compute_provenance_score()` in [`app.py`](app.py) scores `0–100` from four signals (Domain Identity 32%, Originality 20%, Human & Visual Authenticity 24%, Citation Integrity 24%), separating high-trust `.org` advocacy (`www.eff.org`: `87/100`) from low-provenance domains (`civic-pulse-daily.hostingersite.com`: `32/100`).
3. **Uncertainty & Where It Can Fail** — CheckEm differentiates `1–2 / 5` uncertain splits (**amber overline**) from `3–5 / 5` majority consensus (**red overline**) and exposes three failure boundaries:
   - **Urgent `.org` Advocacy:** Credible advocacy triggers rhetorical flags despite high source provenance.
   - **Encyclopedic AI Illustrations:** Neutral articles *about* synthetic media trigger image flags while prose stays unmarked.
   - **Calm Factual Errors:** Style classifiers inspect persuasion, not live ground-truth fact databases.

## Why Open-Weight Lightweight & Sparse MoE Models Matter

- **Larger Ensemble Without Latency Blowup:** Compact open-weight (`Gemma 4 31B VL`) and sparse Mixture-of-Experts (`Nemotron 3.5 Super VL`, activating 12B of 120B parameters per token) architectures make running a **5-model multimodal jury** in parallel fast enough for interactive page review without custom GPU hosting.
- **Cross-Family Error Decorrelation:** Mixing Google Open-Weights (Gemma 4), NVIDIA MoE (Nemotron 3.5), MoonshotAI (Kimi K2.6), Anthropic (Claude Haiku 4.5), and Gemini prevents single-vendor stylistic blind spots from dominating the verdict.

| Open-Weight Track | Role in 5-Model Jury | Guide |
|---|---|---|
| **Gemma 4 31B VL** | Lightweight open-weight visual forensics, fear appeal & ensemble latency probe | [`challenges/gemma/README.md`](challenges/gemma/README.md) |
| **Nemotron 3.5 Super VL** | Sparse MoE logical fallacies (`Whataboutism`, `False Dilemma`) & NVIDIA Build API client | [`challenges/nemotron/README.md`](challenges/nemotron/README.md) |

## Quickstart

```bash
cp .env.example .env
docker compose up -d --build
```

End users browsing [`https://checkem.tech/`](https://checkem.tech/) need no API keys. Set `VERDA_INFERENCE_KEY` in `.env` to route `nemotron-3.5-super-vl` directly to `https://containers.datacrunch.io/nemotron-3-5-super-vl-b300/v1` (with automatic NVIDIA Build / Hostinger AI Router fallbacks). For local runs without Docker: `pip install -r requirements.txt && python3 app.py`.

## License

MIT — see [`LICENSE`](LICENSE).
