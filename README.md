# CheckEm — Name the Technique & Trust the Source

[![Live Demo](https://img.shields.io/badge/Live%20Demo-checkem.tech-4f46e5)](https://checkem.tech/)
[![Presentation Slides](https://img.shields.io/badge/Slides-checkem.tech%2Fslides-059669)](https://checkem.tech/slides)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue)](https://www.python.org/)
[![Docker Compose](https://img.shields.io/badge/Deploy-Docker%20%2B%20Traefik-2496ed)](docker-compose.yml)

**CheckEm** ([https://checkem.tech/](https://checkem.tech/)) is a multimodal Vision-Language Model (VLM) ensemble web application that highlights suspicious framing directly over webpage previews, explains the manipulation tactic in plain language, and makes **model uncertainty and failure boundaries** visible to the reader instead of hiding behind an opaque score.

> **Visual Presentation Deck (5 Slides):** View live at [https://checkem.tech/slides](https://checkem.tech/slides) or read [`docs/PRESENTATION.md`](docs/PRESENTATION.md).

---

## Core Design Principles

### 1. Name the Technique
CheckEm runs parallel text and vision inference across extracted page sections (`sec-1..sec-N`) and images (`img-1..img-K`). Inside the full-page preview, suspicious passages and visuals are highlighted with **coloured overlining** (amber for minority/uncertain flags, red for multi-model consensus), and clicking any highlight reveals every juror's vote, quote, and plain-language explanation:
- **Text Manipulation Taxonomy**: `Loaded Language`, `Fear Appeal`, `Whataboutism`, `Fabricated Authority`, `False Dilemma`, `Scapegoating / Ad Hominem`
- **Visual Forensics Taxonomy**: `AI-Generated / Synthetic Image`, `Manipulative Visual Framing`

### 2. Trust the Source (4-Signal Provenance Scoring)
CheckEm deliberately separates *rhetorical tone* from *who stands behind the page* (`compute_provenance_score()` in [`app.py`](app.py)):
1. **Domain & Publisher Identity (32%)**: HTTPS status, TLD authority (`.gov`, `.int`, `.org`), subdomain checks, and institutional reputation.
2. **Content Originality (20%)**: Unique structural block ratio vs duplicated boilerplate.
3. **Human & Visual Authenticity (24%)**: Sentence-length variance paired with VLM synthetic-image and fabricated-authority signals.
4. **Citation & Link Network Integrity (24%)**: Verifiable outbound links and domain diversity vs unlinked "secret report" claims.

This keeps credible advocacy distinct from fabricated sites: e.g., `www.eff.org` retains a **High Provenance (`87/100`)** score even when its campaign text is flagged for persuasive framing, whereas `civic-pulse-daily.hostingersite.com` scores **Low Provenance (`32/100`)**.

### 3. Embracing Uncertainty & Exposing Where AI Fails
Propaganda and manipulation detection is inherently ambiguous — headline claims of "100% accuracy" on small test sets hide where automated systems break down. Instead of presenting brittle certainty, CheckEm is built to **surface uncertainty and expose likely failure modes directly in the UI**:

- **Disagreement Visualized In-Place**: Rather than collapsing predictions into a binary label, the webpage preview differentiates **1/3 minority suspicion (amber overline — uncertain / inspect disagreement)** from **2/3–3/3 consensus (red overline)**, while leaving unflagged text untouched so clean passages read naturally.
- **Educational Context vs Active Persuasion**: Pages *describing* propaganda or synthetic media (such as Wikipedia's *Deepfake* or *Synthetic Media* entries) test the boundary between neutral reference prose and embedded illustrative examples — where CheckEm leaves the encyclopedia text clean while overlining specific synthetic images (`1/3` or `3/3` votes) so you can see why one model reacted to an image while prose remained objective.
- **Known Failure Modes Surfaced to the User**:
  1. **Advocacy Policy Prose vs Manipulation**: Legitimate advocacy organizations (e.g., `eff.org`) use urgent words like *"threaten"* or *"dangerous"* to rally readers; rhetorical classifiers may flag that urgency even when provenance is trustworthy (`87/100`).
  2. **Calm-Toned Factual Errors**: Rhetorical classifiers inspect *how* claims are framed, not real-time ground-truth databases — calm, dry misinformation without loaded language or broken citations can evade style-based flags.
  3. **Vision Model Split Votes on Compressed Thumbnails**: Downscaled web thumbnails can cause `1/3` split votes on genuine vs AI-generated graphics; CheckEm exposes every individual vision rationale rather than hiding split votes.

---

## Minimalist Progressive-Disclosure UX

The landing UI ([`static/index.html`](static/index.html)) follows a quiet, progressive disclosure flow (Light Mode default + Dark Mode toggle):
1. **Initial View**: Only thin horizontal bars with Status Dot (`Green` = clean, `Yellow` = split / partial / unreviewed, `Red` = majority flagged), Page Title, and Expand Chevron.
2. **Inline Dropdown**: Click any bar to see which model voted what, flagged counts, Trust Score, and three actions:
   - **Full Page Preview**: Renders the page like a clean webpage with **coloured overlining only on content flagged by at least one model** — click any overlined text or image to inspect the models' votes and disagreements.
   - **Concise Model Summary**: Displays the ensemble tally, Trust the Source breakdown, and each model's concise view.
   - **Original Page ↗**: Opens the live source URL in a new tab.

---

## Tech Subchallenges & Open-Weight Compute

Each open-weight juror and GPU backend has its own dedicated README and runnable code under [`challenges/`](challenges/):

| Subchallenge | Role in CheckEm | Directory & README |
|---|---|---|
| **Gemma VLM** | Visual Forensics, Fear Appeal, QLoRA Span Adaptation & Logprob Calibration | [`challenges/gemma/README.md`](challenges/gemma/README.md) |
| **Nemotron 3.5 VL** | Logical Fallacies (`Whataboutism`, `False Dilemma`) & Reasoning Traces | [`challenges/nemotron/README.md`](challenges/nemotron/README.md) |
| **Verda Cloud GPUs** | Self-Hosted vLLM Open-Weight Serving for Fine-Tuned Gemma & Nemotron | [`challenges/verda-cloud/README.md`](challenges/verda-cloud/README.md) |

---

## Quickstart & Deployment

### 1. Configure Server Environment (`.env`)
Copy `.env.example` to `.env` and fill in your backend keys (end users browsing the site do not need any keys):
```bash
cp .env.example .env
```

### 2. Run with Docker Compose (Hostinger VPS + Traefik)
```bash
docker compose up -d --build
```
The service listens on `:8080`, routed via Traefik HTTPS (`checkem.tech`), persisting state in `cache_store.json`.

### 3. Run Locally Without Docker
```bash
pip install -r requirements.txt
python3 app.py
# Open http://localhost:8080/ and http://localhost:8080/slides
```

---

## Repository Structure
```text
├── app.py                         # HTTP server, Oxylabs/fallback scraper, provenance & VLM ensemble
├── cache_store.json               # Pre-scraped real websites and multi-VLM ensemble reviews
├── challenges/
│   ├── gemma/                     # Gemma QLoRA fine-tuning script & open-weights guide
│   ├── nemotron/                  # Nemotron 3.5 VL fallacy pipeline & README
│   └── verda-cloud/               # Verda GPU vLLM docker-compose & deploy script
├── docs/PRESENTATION.md           # Marp Markdown 5-slide visual deck
├── static/
│   ├── index.html                 # Minimalist 3-tier progressive web UI with overlined page preview
│   └── slides.html                # Visual-first 5-slide presentation served at /slides
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```
