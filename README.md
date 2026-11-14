# CheckEm — Name the Technique & Trust the Source

[![Live Demo](https://img.shields.io/badge/Live%20Demo-checkem.tech-4f46e5)](https://checkem.tech/)
[![Slides](https://img.shields.io/badge/Slides-checkem.tech%2Fslides-059669)](https://checkem.tech/slides)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CheckEm** is a multimodal VLM ensemble web app that marks suspicious rhetoric and synthetic media with coloured overlines directly on a natural webpage preview, scores source provenance independently, and exposes model disagreement instead of hiding behind a single score.

> **Presentation Deck:** [checkem.tech/slides](https://checkem.tech/slides) · [docs/PRESENTATION.md](docs/PRESENTATION.md)

## Core Pillars

1. **Name the Technique** — Parallel text and vision voting flags six text tactics (`Loaded Language`, `Fear Appeal`, `Whataboutism`, `Fabricated Authority`, `False Dilemma`, `Scapegoating / Ad Hominem`) and two visual classes (`AI-Generated / Synthetic Image`, `Manipulative Visual Framing`), overlining flagged spans in-place with clickable juror explanations.
2. **Trust the Source** — `compute_provenance_score()` in [`app.py`](app.py) scores `0–100` from four signals (Domain Identity 32%, Originality 20%, Human & Visual Authenticity 24%, Citation Integrity 24%), separating high-trust `.org` advocacy (`www.eff.org`: `87/100`) from low-provenance domains (`civic-pulse-daily.hostingersite.com`: `32/100`).
3. **Uncertainty & Where It Can Fail** — Instead of hiding ambiguity behind brittle accuracy numbers, CheckEm differentiates `1/3` uncertain splits (**amber overline**) from `2–3/3` consensus (**red overline**) and surfaces three failure boundaries:
   - **Urgent `.org` Advocacy:** Credible advocacy triggers rhetorical flags despite high source provenance.
   - **Encyclopedic AI Illustrations:** Neutral articles *about* synthetic media trigger image flags while prose stays unmarked.
   - **Calm Factual Errors:** Style classifiers inspect persuasion, not live ground-truth fact databases.

## Tech Subchallenges

| Component | Role in CheckEm | Guide |
|---|---|---|
| **Gemma VLM** | Visual forensics, fear appeal, QLoRA span tuning & logprob calibration | [`challenges/gemma/README.md`](challenges/gemma/README.md) |
| **Nemotron 3.5 VL** | Logical fallacies (`Whataboutism`, `False Dilemma`) & reasoning traces | [`challenges/nemotron/README.md`](challenges/nemotron/README.md) |
| **Verda Cloud GPUs** | Self-hosted vLLM serving for open-weight Gemma & Nemotron adapters | [`challenges/verda-cloud/README.md`](challenges/verda-cloud/README.md) |

## Quickstart

```bash
cp .env.example .env
docker compose up -d --build
```

End users browsing [`https://checkem.tech/`](https://checkem.tech/) need no API keys. For local runs without Docker: `pip install -r requirements.txt && python3 app.py`.

## License

MIT — see [`LICENSE`](LICENSE).
