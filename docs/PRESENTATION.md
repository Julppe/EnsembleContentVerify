---
marp: true
theme: default
paginate: true
---

# 1. Misinformation Online

- **The Guardian (2025):** [AI chatbots distort and mislead when asked about current affairs, BBC finds](https://www.theguardian.com/technology/2025/feb/11/ai-chatbots-distort-and-mislead-when-asked-about-current-affairs-bbc-finds)
- **BBC Media Centre (2025):** [AI Distortion is new threat to trusted information](https://www.bbc.co.uk/mediacentre/2025/articles/how-distortion-is-affecting-ai-assistants/)
- **The Guardian / WEF (2024):** [AI-driven misinformation ‘biggest short-term threat to global economy’](https://www.theguardian.com/business/2024/jan/10/ai-driven-misinformation-biggest-short-term-threat-to-global-economy)
- **The Guardian (2023):** [Nearly 50 news websites are ‘AI-generated’, a study says. Would I be able to tell?](https://www.theguardian.com/technology/2023/may/08/ai-generated-news-websites-study)

---

# 2. CheckEm — Under the Hood

`Web Page` ➔ `Gemma 4 31B VL` · `Nemotron 3.5 Super VL` · `Gemini 3.1 Lite VL` · `Kimi K2.6 VL` · `Claude Haiku 4.5 VL` ➔ **Name the Technique** + **Trust the Source**

---

# 3. Per-Model Content Flagging

Sample highlighted text in CheckEm ➔ parallel review across all 5 model families with app technique/clean tags (`Fear Appeal`, `Fabricated Authority`, `Loaded Language`, `Clean`).

---

# 4. Ensemble Vote

Per-model `Suspicious` (red) / `Trusted` (green) indicators ➔ aggregated **`Mixed`** (yellow) consensus.

**Live App:** [https://checkem.tech/](https://checkem.tech/) · **Web Slides:** [https://checkem.tech/slides](https://checkem.tech/slides)
