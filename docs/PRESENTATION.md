---
marp: true
theme: default
paginate: true
---

# CheckEm (`checkem.tech`)

**5-Model Cross-Family VLM Manipulation & Source Provenance Jury**

`Web Page` ➔ `Gemma 4 31B VL` · `Nemotron 3.5 Super VL` · `Gemini 3.1 VL` · `Kimi K2.6 VL` · `Claude Haiku 4.5 VL` ➔ **Name the Technique** + **Trust the Source**

---

# Rhetoric ≠ Provenance

| Source | Ensemble Verdict | Trust Score |
|---|---|---:|
| `eff.org/issues/ai` | 🚩 Persuasive Framing | **87 / 100** |
| `wikipedia.org/Deepfake` | 🟡 Text Clean · AI Images Flagged | **88 / 100** |
| `civic-pulse-daily` (Toy) | 🚩 Unanimous Propaganda | **32 / 100** |

---

# Architecture — Lightweight Models Enable 5-Way Diversity

```text
URL ──▶ Oxylabs Scraper (Sections + Images)
          │
          ├──▶ Hostinger AI Router: Gemma 4 31B VL · Gemini 3.1 VL · Kimi K2.6 VL · Claude Haiku 4.5 VL
          ├──▶ Managed Inference API: nemotron-3.5-super-vl (12B Active MoE)
          └──▶ 4-Signal Provenance Engine
          │
          ▼
Hostinger VPS · https://checkem.tech/
```

---

# Uncertainty & Failure Boundaries

- `0 / 5 Flagged` ➔ **Unmarked Webpage Text**
- `1–2 / 5 Uncertain Split` ➔ **Amber Overline** *(inspect disagreement)*
- `3–5 / 5 Majority Consensus` ➔ **Red Overline** *(named technique + votes)*
- **Where It Can Fail:** Urgent Advocacy (`.org`), Educational AI Images in Encyclopedias, Calm-Toned Factual Errors

**Live App:** [https://checkem.tech/](https://checkem.tech/) · **Web Slides:** [https://checkem.tech/slides](https://checkem.tech/slides)
