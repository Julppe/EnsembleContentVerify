---
marp: true
theme: default
paginate: true
---

# CheckEm (`checkem.tech`)
### Multimodal VLM Ensemble for Manipulation Detection & Source Provenance

- **Pillar 1 — Name the Technique**: Classify text & visual manipulation (`Loaded Language`, `Fear Appeal`, `Whataboutism`, `Fabricated Authority`, `False Dilemma`, `Scapegoating`, `AI-Generated Image`, `Manipulative Visual Framing`) and teach the *why* in plain language.
- **Pillar 2 — Trust the Source**: 4-signal page provenance scoring (`Domain Reputation`, `Content Originality`, `Human & Visual Authenticity`, `Citation & Link Integrity`).
- **Pillar 3 — Transparent & Measurable**: Real precision, recall, F1, and False-Positive Rate (including hard negatives).

Live App: https://checkem.tech/ • Live Web Deck: https://checkem.tech/slides

---

# 1. Why Binary "Fake News" Scores Fail Readers

| Traditional Binary Detectors | CheckEm Ensemble Approach |
|---|---|
| Opaque "82% Fake" number | Pinpoints exact phrases & names the persuasion tactic |
| High false positives on news reporting about propaganda | **0.0% Hard-Negative FPR** across 6 Wikipedia manipulation articles |
| Text-only inspection misses AI visuals | Vision VLMs inspect downloaded page images (`base64`) directly |
| Single-model bias | 3-model ensemble jury votes per page, per section & per image |

---

# 2. Pillar 1: Name the Technique

Readers do not just see that a page is flagged — they click any highlighted section or trigger quote to learn:
1. **The Technique Named**: e.g. `Fear Appeal`, `Loaded Language`, `Whataboutism`, `Fabricated Authority`
2. **Plain-Language Lesson**: Why that phrasing steers emotion or bypasses evidence
3. **Individual Model Votes**: Side-by-side reasons from each VLM (`Clean` vs `Questionable`)

---

# 3. Pillar 2: Trust the Source (Provenance Scoring)

Each page receives a transparent **0–100 Trust Score** independent of rhetorical tone:
- **Domain & Publisher Identity (32%)**: HTTPS, authoritative TLDs (`.gov`, `.int`, `.org`), subdomain checks
- **Content Originality (20%)**: Structural block uniqueness & scraped prose depth
- **Human & Visual Authenticity (24%)**: Sentence-length burstiness + VLM synthetic image / fabricated authority signals
- **Citation & Link Network Integrity (24%)**: Outbound citation count & domain diversity

*Example contrast:* `www.who.int` (**85/100 High**) and `www.eff.org` (**87/100 High** even with persuasive advocacy) vs unverified `civic-pulse-daily.hostingersite.com` (**32/100 Low**).

---

# 4. Architecture: Hybrid Scraping + Multi-VLM Jury

```
URL Input / Catalog
   │
   ▼
Oxylabs Web API (with Direct Browser-UA Fallback)
   │  └─▶ Clean Markdown, Sections (sec-1..N), Images (img-1..K)
   ▼
Parallel 3-Model VLM Jury + Provenance Scorer
   ├── Gemma 4 31B VL        (Verda Cloud GPU / Hostinger Router)
   ├── Nemotron 3.5 VL       (Verda Cloud GPU / Hostinger Router)
   └── Gemini 3.1 Flash Lite (Hostinger AI Router)
   │
   ▼
Aggregated JSON + Persistent Cache (`cache_store.json`) -> Minimalist UI
```

---

# 5. Pillar 3: Transparent & Measurable Benchmarks

Evaluated across **11 pages** (**75 text sections**, **22 images**), including **6 Hard Negatives** (Wikipedia articles objectively explaining manipulation concepts):

| Metric | Measured Result |
|---|---|
| Page Precision | **100.0%** (`TP=2, FP=0`) |
| Page Recall / F1 | **100.0%** / **1.00** (`FN=0`) |
| Overall False-Positive Rate | **0.0%** (`0 / 9`) |
| Hard-Negative FPR (Wikipedia) | **0.0%** (`0 / 6`) |
| Image Forensics Precision & Recall | **100.0%** (`4 / 4` synthetic/deepfake illustrations detected) |
| Pairwise Inter-Model Agreement | **100.0%** |

---

# 6. Leveraging Open Models: Gemma VL Fine-Tuning (`challenges/gemma/`)

Beyond zero-shot API inference, Gemma's open weights enable:
- **QLoRA Adapter Tuning** (`challenges/gemma/finetune_gemma_qlora.py`): 4-bit NF4 LoRA training on SemEval propaganda spans paired with hard-negative encyclopedic passages.
- **Logprob Calibration**: Tuning the confidence boundary on `"questionable"` vs `"clean"` log-probabilities to control Precision/FPR trade-offs.
- **Counterfactual Teaching**: Generating neutral, non-manipulative rewrites alongside flagged spans.

---

# 7. Nemotron 3.5 VL & Verda Cloud GPU Hosting (`challenges/nemotron/`, `challenges/verda-cloud/`)

- **Nemotron 3.5 VL Role**: Reasoning-intensive jury member specializing in logical fallacies (*Whataboutism*, *False Dilemma*, *Fabricated Authority*) and infographic/visual scrutiny.
- **Verda Cloud GPU Compute**: Hosts fine-tuned Gemma VL & Nemotron 3.5 VL LoRA adapters on A100/H100 GPUs via vLLM (`challenges/verda-cloud/docker-compose.verda-gpu.yml`).
- Setting `VERDA_GPU_BASE_URL` seamlessly routes Gemma & Nemotron inference from CheckEm to your Verda cluster.

---

# 8. Alignment with Main Challenge Judging Criteria

| Criterion | Weight | CheckEm Delivery |
|---|---:|---|
| **Detection Quality** *(accuracy, FP handling, explainability)* | **40%** | **100% Precision**, **0.0% Hard-Negative FPR** (`0/6` Wikipedia propaganda articles), **100% Visual Forensics Recall**, verbatim trigger quotes + plain-language explanations |
| **Technical Execution & Hostinger Deploy** | **25%** | Live HTTPS production app at [`https://checkem.tech/`](https://checkem.tech/) on Hostinger VPS via Hostinger DNS API, Docker + Traefik TLS, Hostinger AI Router, Oxylabs Scraper & Verda Cloud GPU vLLM option |
| **Originality & Real-World Impact** | **20%** | Separates *Name the Technique* (rhetoric) from *Trust the Source* (provenance); open-weight QLoRA & logprob calibration (`challenges/gemma/`, `challenges/nemotron/`) |
| **Demo Clarity** | **15%** | Minimalist horizontal status bars -> inline vote summary -> full-page highlight reader & clickable vote inspector, plus `/slides` |

---

# 9. Minimalist Progressive UX (`https://checkem.tech/`)

1. **Initial View**: Calm vertical stack of thin horizontal bars showing only Status Icon (Green / Yellow / Red), Page Title, and Expand Chevron.
2. **Inline Dropdown**: Click any bar to inspect per-model votes, flagged section/image counts, Trust Score, and 3 clean options:
   - **Full Page & Highlights** (click any highlighted phrase/image to open per-model reasoning)
   - **Concise Model Summary** (verdict, provenance breakdown, side-by-side model views)
   - **Original Page ↗** (new tab)
