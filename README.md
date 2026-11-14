# CheckEm — Name the Technique & Trust the Source

[![Live Demo](https://img.shields.io/badge/Live%20Demo-checkem.tech-4f46e5)](https://checkem.tech/)
[![Presentation Slides](https://img.shields.io/badge/Slides-checkem.tech%2Fslides-059669)](https://checkem.tech/slides)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Docker Compose](https://img.shields.io/badge/Deploy-Docker%20%2B%20Traefik-2496ed)](docker-compose.yml)

**CheckEm** ([https://checkem.tech/](https://checkem.tech/)) is a multimodal Vision-Language Model (VLM) ensemble web application that evaluates web articles and embedded imagery for propaganda, rhetorical manipulation, and source provenance — explaining every verdict in plain language rather than outputting an opaque score.

> **Interactive Presentation Deck:** View live at [https://checkem.tech/slides](https://checkem.tech/slides) or read the Markdown source in [`docs/PRESENTATION.md`](docs/PRESENTATION.md).

---

## Core Challenge Pillars

### 1. Name the Technique
CheckEm classifies specific manipulation techniques across both extracted article text sections (`sec-1..sec-N`) and images (`img-1..img-K`), highlighting the trigger phrase inline and explaining the tactic in plain language so a reader learns *why* content is persuasive or misleading:
- **Text Manipulation Taxonomy**: `Loaded Language`, `Fear Appeal`, `Whataboutism`, `Fabricated Authority`, `False Dilemma`, `Scapegoating / Ad Hominem`
- **Visual Forensics Taxonomy**: `AI-Generated / Synthetic Image`, `Manipulative Visual Framing`

### 2. Trust the Source (4-Signal Provenance Scoring)
Separate *how* a page argues from *who* is behind it. Every cataloged or submitted URL receives a transparent **0–100 Trust Score** across four measurable dimensions (`compute_provenance_score()` in [`app.py`](app.py)):
1. **Domain & Publisher Identity (32%)**: HTTPS status, TLD authority (`.gov`, `.int`, `.org`), subdomain checks, and institutional reputation.
2. **Content Originality (20%)**: Structural paragraph uniqueness vs cloned boilerplate ratio and depth.
3. **Human & Visual Authenticity (24%)**: Sentence-length variance paired with VLM synthetic image / fabricated-authority detection.
4. **Citation & Link Network Integrity (24%)**: Count and domain diversity of verifiable outbound references vs unlinked "secret report / insider" assertions.

For example, `www.eff.org` scores **87/100 (High Provenance)** as an established `.org` with 33 cited links across 4 domains even when its campaign text uses persuasive rhetoric, whereas the unverified synthetic sample `civic-pulse-daily.hostingersite.com` scores **32/100 (Low Provenance)**.

### 3. Transparent & Measurable Precision / False-Positive Rate
Rather than demoing only easy happy-path propaganda samples, CheckEm includes **6 Hard-Negative Wikipedia pages** (articles *defining* propaganda, deepfakes, loaded language, whataboutism, false dilemma, and synthetic media) alongside public-health, government, advocacy, tutorial, and synthetic propaganda pages.

Measured across our live 11-page evaluation corpus (**75 text sections**, **22 content images**) via [`benchmarks/evaluate.py`](benchmarks/evaluate.py) and `GET /api/metrics`:

| Metric | Measured Result | Scope |
|---|---:|---|
| **Page Precision** | **100.0%** | `TP = 2`, `FP = 0` |
| **Page Recall / F1** | **100.0% / 1.00** | `FN = 0`, `TN = 9` |
| **Overall False-Positive Rate (FPR)** | **0.0%** | `0 / 9` clean pages misclassified |
| **Hard-Negative FPR (Wikipedia)** | **0.0%** | `0 / 6` educational articles about manipulation |
| **Image Forensics Precision & Recall** | **100.0% / 100.0%** | `4 / 4` synthetic/deepfake images flagged |
| **Inter-Model Pairwise Agreement** | **100.0%** | Across all 3 jury models |

> Note on Image vs Text Separation: On *Deepfake (Wikipedia)* (`0/7` flagged text sections, `3/3` flagged illustrative deepfake images) and *Synthetic Media (Wikipedia)* (`0/7` flagged text sections, `1/2` flagged AI-generated artwork image), the ensemble correctly leaves objective encyclopedic prose clean while alerting readers that the embedded visuals are synthetic (`Mixed / Yellow` indicator).

---

## Minimalist Progressive-Disclosure UX

The landing UI ([`static/index.html`](static/index.html)) uses a calm, minimalist progressive disclosure design (Light Mode default + Dark Mode toggle):
1. **Initial View**: Thin horizontal bars showing **only** the traffic-light Status Dot (`Green` = clean, `Yellow` = mixed/partial flags/unreviewed, `Red` = flagged content), Page Title, and Expand Chevron.
2. **Accordion Dropdown**: Clicking a bar expands inline to show per-model votes, flagged section/image counts, the Trust Score, and three actions:
   - **Full Page & Highlights**: Opens the formatted full article with flagged sections, verbatim trigger quotes, and flagged images highlighted — click any highlighted item to inspect each model's vote and plain-language explanation.
   - **Concise Model Summary**: Shows the ensemble tally, detected tactics, 4-signal Trust Score breakdown, and side-by-side model verdicts.
   - **Original Page ↗**: Opens the live source URL in a new tab.

---

## Judging Criteria Alignment

| Judging Criterion | Weight | How CheckEm Delivers |
|---|---:|---|
| **Detection Quality** *(accuracy, false-positive handling, explainability)* | **40%** | `100.0%` Page Precision & `0.0%` Hard-Negative FPR across 6 Wikipedia articles *about* manipulation (`benchmarks/evaluate.py`, `/api/metrics`), `100%` synthetic image recall (`4/4`), inline trigger-quote highlighting, and plain-language pedagogical verdicts. |
| **Technical Execution & Hostinger Deployment** | **25%** | Live on Hostinger VPS at [https://checkem.tech/](https://checkem.tech/) via Hostinger DNS API + Docker Compose + Traefik Let's Encrypt HTTPS, integrated with Hostinger AI Router, Oxylabs Web Scraper, and Verda Cloud GPU vLLM routing. |
| **Originality & Real-World Impact** | **20%** | Separates persuasive framing (**Name the Technique**) from publisher credibility (**Trust the Source** 0–100 provenance score) and leverages open-weight Gemma QLoRA & Nemotron reasoning calibration to suppress false positives. |
| **Demo Clarity** | **15%** | Minimalist 3-tier progressive UI ([`static/index.html`](static/index.html)) plus live keyboard-driven slide presentation at [https://checkem.tech/slides](https://checkem.tech/slides). |

---

## Tech Subchallenges & Model Ensemble Roles

Each open-weight juror and GPU compute backend has its own dedicated directory, documentation, and runnable code under [`challenges/`](challenges/):

| Subchallenge | Role in CheckEm | Directory & README |
|---|---|---|
| **Gemma VLM** | Visual Forensics, Fear Appeal, QLoRA Span Adaptation & Logprob Calibration | [`challenges/gemma/README.md`](challenges/gemma/README.md) |
| **Nemotron 3.5 VL** | Logical Fallacies (`Whataboutism`, `False Dilemma`) & Reasoning Traces | [`challenges/nemotron/README.md`](challenges/nemotron/README.md) |
| **Verda Cloud GPUs** | Self-Hosted vLLM Open-Weight Serving for Fine-Tuned Gemma & Nemotron | [`challenges/verda-cloud/README.md`](challenges/verda-cloud/README.md) |

---

## Quickstart & Deployment

### 1. Configure Server Environment (`.env`)
Copy `.env.example` to `.env` and fill in your credentials (never commit `.env` — end users browsing the web app do not need any keys):
```bash
cp .env.example .env
```

### 2. Run with Docker Compose (Hostinger VPS + Traefik)
```bash
docker compose up -d --build
```
The service listens on `:8080`, labeled for Traefik HTTPS (`checkem.tech` / `www.checkem.tech`), and persists catalog & ensemble evaluations to `cache_store.json`.

### 3. Run Locally Without Docker
```bash
pip install -r requirements.txt
python3 app.py
# Open http://localhost:8080/ and http://localhost:8080/slides
```

### 4. Recompute Benchmark Metrics
```bash
python3 benchmarks/evaluate.py
```

---

## Repository Structure
```text
├── app.py                         # HTTP server, Oxylabs/fallback scraper, provenance & VLM ensemble
├── benchmarks/evaluate.py         # Precision / Recall / Hard-Negative FPR evaluation CLI
├── cache_store.json               # Pre-evaluated 11-page benchmark & review cache
├── challenges/
│   ├── gemma/                     # Gemma QLoRA fine-tuning script & open-weights guide
│   ├── nemotron/                  # Nemotron 3.5 VL fallacy pipeline & README
│   └── verda-cloud/               # Verda GPU vLLM docker-compose & deploy script
├── docs/PRESENTATION.md           # Marp Markdown slide deck
├── static/
│   ├── index.html                 # Minimalist 3-tier progressive web UI
│   └── slides.html                # Interactive 10-slide presentation served at /slides
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```
