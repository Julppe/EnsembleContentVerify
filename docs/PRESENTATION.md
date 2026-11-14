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

# Uncertainty & Failure Boundaries

- `0 / 3 Flagged` ➔ **Unmarked Webpage Text**
- `1 / 3 Uncertain Split` ➔ **Amber Overline** *(inspect disagreement)*
- `2–3 / 3 Consensus` ➔ **Red Overline** *(named technique + votes)*
- **Where It Can Fail:** Urgent Advocacy (`.org`), Educational AI Images in Encyclopedias, Calm-Toned Factual Errors

---

# Minimalist Progressive UX

`1. Traffic-Light Status Bar` ➔ `2. Inline VLM Votes & Trust Score` ➔ `3. Webpage Preview w/ Coloured Overlines → Model Reasons`

**Live App:** [https://checkem.tech/](https://checkem.tech/) · **Web Slides:** [https://checkem.tech/slides](https://checkem.tech/slides)
