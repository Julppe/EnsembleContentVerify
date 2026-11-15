# CheckEm — See if websites can be trusted or not

[![Live Demo](https://img.shields.io/badge/Live%20Demo-checkem.tech-4f46e5)](https://checkem.tech/)
[![Slides](https://img.shields.io/badge/Slides-checkem.tech%2Fslides-059669)](https://checkem.tech/slides)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**CheckEm** runs a **5-model cross-family VLM jury** that marks suspicious rhetoric and visual media with coloured overlines directly on a simple webpage, scores source provenance independently, and exposes model disagreement instead of hiding behind a single score.

Add your own webpages from the top of the page see how they score.

> **Presentation Deck:** [checkem.tech/slides](https://checkem.tech/slides) · [docs/PRESENTATION.md](docs/PRESENTATION.md)

## App features

- Analyse content: Add sites from the top of the page to be analysed by the models. The site will be listed on the site with detailed analysis from each model.
- Check the details: For each analysed page you can open a view that shows exactly what was flagged by each model and what the other models think of that specific piece of content. 
- Broader overview: Another analysis tab shows highlights of what types of suspicious content the models detected and how prominent it is.

## Tech details

- Concurrently polls `Gemma 4 31B VL`, `Nemotron 3.5 Super VL`, `Gemini 3.1 Flash Lite VL`, `Kimi K2.6 VL`, and `Claude Haiku 4.5 VL` across six text tactics (`Loaded Language`, `Fear Appeal`, `Whataboutism`, `Fabricated Authority`, `False Dilemma`, `Scapegoating / Ad Hominem`) and two visual classes (`AI-Generated / Synthetic Image`, `Manipulative Visual Framing`).
- `compute_provenance_score()` in [`app.py`](app.py) scores `0–100` from four signals (Domain Identity 32%, Originality 20%, Human & Visual Authenticity 24%, Citation Integrity 24%), separating high-trust `.org` advocacy (`www.eff.org`: `87/100`) from low-provenance domains (`civic-pulse-daily.hostingersite.com`: `32/100`).
- CheckEm differentiates `1–2 / 5` uncertain splits (**amber overline**) from `3–5 / 5` majority consensus (**red overline**).
- The used models can be reconfigured in the `.env` file as shown in `.env.example`.
- To rehost the website, API keys are required as also detailed in `.env.example`.

## Why open lightweight and MoE models are used

- Compact open-weight (`Gemma 4 31B VL`) and sparse Mixture-of-Experts (`Nemotron 3.5 Super VL`) architectures make running a **5-model multimodal jury** in parallel fast enough for interactive page review without custom GPU hosting.
- **Cross-Family Error Decorrelation:** Mixing Google Open-Weights (Gemma 4), NVIDIA MoE (Nemotron 3.5), MoonshotAI (Kimi K2.6), Anthropic (Claude Haiku 4.5), and Gemini prevents single-vendor stylistic blind spots from dominating the verdict.

More details on the Gemma use: [`challenges/gemma/README.md`](challenges/gemma/README.md)

More details ion the Nemotron use: [`challenges/nemotron/README.md`](challenges/nemotron/README.md)

## Quickstart

```bash
cp .env.example .env
docker compose up -d --build
```

End users browsing [`https://checkem.tech/`](https://checkem.tech/) need no API keys.
 For local runs without Docker: `pip install -r requirements.txt && python3 app.py`.

## License

MIT — see [`LICENSE`](LICENSE).
