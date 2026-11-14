---
marp: true
theme: default
paginate: true
---

# CheckEm (`checkem.tech`)

**Multimodal Manipulation & Source Provenance Jury**

`Web Page` ➔ `Gemma 4 VL` · `Nemotron 3.5 VL` · `Gemini 3.1 VL` ➔ **Name the Technique** + **Trust the Source**

---

# Rhetoric ≠ Provenance

| Source | Ensemble Verdict | Trust Score |
|---|---|---:|
| `eff.org/issues/ai` | 🚩 3/3 Persuasive Framing | **87 / 100** |
| `wikipedia.org/Deepfake` | 🟡 Text Clean · 3/3 AI Images | **88 / 100** |
| `civic-pulse-daily` (Toy) | 🚩 3/3 Propaganda | **32 / 100** |

---

# Architecture

```text
URL ──▶ Oxylabs Scraper (Sections + Images)
          │
          ├──▶ Hostinger AI Router (Gemma 4 VL, Nemotron 3.5 VL, Gemini VL)
          ├──▶ Verda Cloud GPU vLLM (Open-Weight QLoRA + Logprobs)
          └──▶ 4-Signal Provenance Engine
          │
          ▼
Hostinger VPS · https://checkem.tech/
```

---

# Measured Accuracy

- **Page Precision:** `100%` (`TP=2, FP=0, F1=1.00`)
- **Hard-Negative FPR:** `0.0%` (`0/6` Wikipedia propaganda articles)
- **Visual Recall:** `100%` (`4/4` synthetic images)
- **Jury Agreement:** `100%` across `11 Pages · 75 Sections · 22 Images`

---

# Minimalist Progressive UX

`1. Traffic-Light Status Bar` ➔ `2. Inline VLM Votes & Trust Score` ➔ `3. Clickable Highlight → Model Reasons`

**Live App:** [https://checkem.tech/](https://checkem.tech/) · **Web Slides:** [https://checkem.tech/slides](https://checkem.tech/slides)
