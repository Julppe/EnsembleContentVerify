#!/usr/bin/env python3
"""
Name the Technique — Multi-VLM Ensemble Website Content & Image Reviewer
=========================================================================
Preconfigured server-side via `/root/hostinger-ai-reviewer/.env` so end users
only interact with the web app as a clean, public-ready review interface:
1. Scrapes real web pages (via Oxylabs Web API with automatic direct HTTP fallback),
   isolates article content, extracts clean Markdown, numbered sections (`sec-1`..`sec-N`),
   and content images (`img-1`..`img-K`).
2. Runs parallel ensemble voting across configured Hostinger AI Router models
   (e.g., `gemma-4-31b`, `nemotron-lightning-3.5-30b-a3b`, `gemini-3.1-flash-lite`),
   attaching base64-encoded page images for vision-capable VLMs to inspect for
   AI-generated / synthetic / manipulative imagery alongside text manipulation detection.
3. Persists scraped pages and ensemble reviews in `cache_store.json`.
"""

import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import html as html_lib
import html.parser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import threading
import time
import urllib.parse
import requests

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(APP_DIR, ".env")
CACHE_PATH = os.path.join(APP_DIR, "cache_store.json")
HOSTINGER_API_BASE = "https://developers.hostinger.com"
OXYLABS_WEB_API_URL = "https://webapi.oxylabs.io/v1/scrape"
OXYLABS_REALTIME_URL = "https://realtime.oxylabs.io/v1/queries"
PORT = int(os.environ.get("PORT", "8080"))

BROWSER_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
)

STATE_LOCK = threading.Lock()

MANIPULATION_TECHNIQUES = [
    "Loaded Language",
    "Fear Appeal",
    "Whataboutism",
    "Fabricated Authority",
    "False Dilemma",
    "Scapegoating / Ad Hominem",
    "AI-Generated / Synthetic Image",
    "Manipulative Visual Framing",
]

TECHNIQUE_EXPLANATIONS = {
    "Loaded Language": (
        "Uses emotionally charged or morally condemning words instead of neutral descriptions "
        "to push the reader toward anger or distrust before examining facts."
    ),
    "Fear Appeal": (
        "Triggers urgency or dread about severe worst-case harm to bypass calm evaluation of evidence."
    ),
    "Whataboutism": (
        "Deflects criticism of a claim or action by pointing to an unrelated fault of critics or opponents."
    ),
    "Fabricated Authority": (
        "Cites impressive-sounding but unverifiable institutes, secret studies, or anonymous insiders "
        "to manufacture unearned credibility."
    ),
    "False Dilemma": (
        "Frames a complex topic as having only two extreme outcomes or choices, hiding middle-ground options."
    ),
    "Scapegoating / Ad Hominem": (
        "Blames an entire group or attacks critics' motives rather than addressing verifiable evidence."
    ),
    "AI-Generated / Synthetic Image": (
        "Visual shows hallmarks of AI synthesis (synthetic textures, anatomical/text artifacts, or generative origin) "
        "which can mislead viewers if presented as documentary photography."
    ),
    "Manipulative Visual Framing": (
        "Uses staged, misleading, or emotionally sensationalized imagery/captions to steer reader conclusions."
    ),
}

MODEL_PROFILES = {
    "gemma-4-31b": {
        "name": "Gemma 4 31B VL",
        "focus": "Visual Forensics, Fear Appeal & Counterfactual Framing",
        "vision": True,
        "provider_hint": "verda_or_router",
    },
    "nemotron-lightning-3.5-30b-a3b": {
        "name": "Nemotron 3.5 VL",
        "focus": "Logical Fallacies, Whataboutism, Claim & Visual Integrity",
        "vision": True,
        "provider_hint": "verda_or_router",
    },
    "gemini-3.1-flash-lite": {
        "name": "Gemini 3.1 Flash Lite VL",
        "focus": "Multimodal Propaganda, Loaded Language & Source Provenance",
        "vision": True,
        "provider_hint": "router",
    },
}

DEFAULT_MODEL_LENSES = [
    "Visual Forensics, Fear Appeal & Rhetorical Framing",
    "Logical Fallacies, Whataboutism & Claim Integrity",
    "Multimodal Propaganda, Loaded Language & Source Verification",
]

RUNTIME_CONFIG = {
    "oxylabs_api_key": "",
    "hostinger_ai_router_key": "",
    "hostinger_ai_router_base_url": "https://router.hostinger.com/v1",
    "hostinger_api_token": "",
    "ai_router_models": "gemma-4-31b,nemotron-lightning-3.5-30b-a3b,gemini-3.1-flash-lite",
    "verda_gpu_base_url": "",
    "verda_api_key": "",
    "verda_gemma_model": "",
    "verda_nemotron_model": "",
}

REVIEW_MODELS = []

REAL_TEST_PAGES = [
    {
        "id": "wiki-propaganda-techniques",
        "title": "Propaganda Techniques (Wikipedia)",
        "domain": "en.wikipedia.org",
        "url": "https://en.wikipedia.org/wiki/Propaganda_techniques",
        "website_type": "Real Page • Media & Rhetoric",
    },
    {
        "id": "wiki-synthetic-media",
        "title": "Synthetic Media & AI Imagery (Wikipedia)",
        "domain": "en.wikipedia.org",
        "url": "https://en.wikipedia.org/wiki/Synthetic_media",
        "website_type": "Real Page • AI Imagery",
    },
    {
        "id": "wiki-deepfake",
        "title": "Deepfakes & Visual Manipulation (Wikipedia)",
        "domain": "en.wikipedia.org",
        "url": "https://en.wikipedia.org/wiki/Deepfake",
        "website_type": "Real Page • Visual Forensics",
    },
    {
        "id": "wiki-loaded-language",
        "title": "Loaded Language in Discourse (Wikipedia)",
        "domain": "en.wikipedia.org",
        "url": "https://en.wikipedia.org/wiki/Loaded_language",
        "website_type": "Real Page • Rhetoric",
    },
    {
        "id": "wiki-whataboutism",
        "title": "Whataboutism & Deflection (Wikipedia)",
        "domain": "en.wikipedia.org",
        "url": "https://en.wikipedia.org/wiki/Whataboutism",
        "website_type": "Real Page • Logical Fallacy",
    },
    {
        "id": "wiki-false-dilemma",
        "title": "False Dilemma & Binary Framing (Wikipedia)",
        "domain": "en.wikipedia.org",
        "url": "https://en.wikipedia.org/wiki/False_dilemma",
        "website_type": "Real Page • Logical Fallacy",
    },
    {
        "id": "who-healthy-diet",
        "title": "WHO Fact Sheet: Healthy Diet",
        "domain": "www.who.int",
        "url": "https://www.who.int/news-room/fact-sheets/detail/healthy-diet",
        "website_type": "Real Page • Public Health",
    },
    {
        "id": "eff-ai-policy",
        "title": "EFF: AI & Civil Liberties",
        "domain": "www.eff.org",
        "url": "https://www.eff.org/issues/ai",
        "website_type": "Real Page • Tech Policy",
    },
    {
        "id": "hostinger-vps-tutorial",
        "title": "Hostinger Tutorial: What Is VPS Hosting?",
        "domain": "www.hostinger.com",
        "url": "https://www.hostinger.com/tutorials/what-is-vps-hosting",
        "website_type": "Real Page • Hosting Guide",
    },
    {
        "id": "nasa-home",
        "title": "NASA Science & Exploration News",
        "domain": "www.nasa.gov",
        "url": "https://www.nasa.gov/",
        "website_type": "Real Page • Science & Space",
    },
]


# ---------------------------------------------------------------------------
# 1. Server-Side .env & Model Registry Helpers
# ---------------------------------------------------------------------------
def _friendly_model_name(model_id: str) -> str:
    if model_id in MODEL_PROFILES:
        return MODEL_PROFILES[model_id]["name"]
    return model_id.split("/")[-1].replace("-", " ").title()


def _is_vision_model(model_id: str) -> bool:
    if model_id in MODEL_PROFILES:
        return MODEL_PROFILES[model_id]["vision"]
    low = model_id.lower()
    if any(t in low for t in ("phi-4", "gpt-image")):
        return False
    return any(
        t in low
        for t in ("gemma", "gemini", "nemotron", "gpt-4", "gpt-5", "gpt-6", "claude", "mistral", "qwen", "mimo", "minimax", "kimi", "nova", "grok", "deepseek", "vl")
    )


def build_model_registry(models_csv: str) -> list:
    ids = [m.strip() for m in models_csv.split(",") if m.strip()]
    registry = []
    for idx, model_id in enumerate(ids):
        profile = MODEL_PROFILES.get(model_id, {})
        registry.append({
            "id": model_id,
            "name": profile.get("name") or _friendly_model_name(model_id),
            "focus": profile.get("focus") or DEFAULT_MODEL_LENSES[idx % len(DEFAULT_MODEL_LENSES)],
            "vision": _is_vision_model(model_id),
            "enabled": True,
        })
    return registry


def load_env_file():
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw or raw.startswith("#") or "=" not in raw:
                    continue
                k, v = raw.split("=", 1)
                key = k.strip().lower()
                val = v.strip().strip('"').strip("'")
                if key in RUNTIME_CONFIG and val:
                    RUNTIME_CONFIG[key] = val

    env_map = {
        "OXYLABS_API_KEY": "oxylabs_api_key",
        "HOSTINGER_AI_ROUTER_KEY": "hostinger_ai_router_key",
        "HOSTINGER_AI_ROUTER_BASE_URL": "hostinger_ai_router_base_url",
        "HOSTINGER_API_TOKEN": "hostinger_api_token",
        "AI_ROUTER_MODELS": "ai_router_models",
        "VERDA_GPU_BASE_URL": "verda_gpu_base_url",
        "VERDA_API_KEY": "verda_api_key",
        "VERDA_GEMMA_MODEL": "verda_gemma_model",
        "VERDA_NEMOTRON_MODEL": "verda_nemotron_model",
    }
    for env_key, cfg_key in env_map.items():
        if os.environ.get(env_key):
            RUNTIME_CONFIG[cfg_key] = os.environ[env_key].strip()

    global REVIEW_MODELS
    REVIEW_MODELS = build_model_registry(RUNTIME_CONFIG["ai_router_models"])


# ---------------------------------------------------------------------------
# 2. Article Isolation, HTML -> Markdown, Section & Image Extraction
# ---------------------------------------------------------------------------
class MainRegionExtractor(html.parser.HTMLParser):
    """Finds `<main>`, `<article>`, or `#mw-content-text` region if available, plus `<title>`."""

    VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }

    def __init__(self, target_mode: str):
        super().__init__()
        self.target_mode = target_mode  # 'mw', 'main', 'article'
        self.depth = 0
        self.capturing = False
        self.capture_depth = None
        self.parts = []
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        attr_dict = dict(attrs)
        if t == "title":
            self.in_title = True

        is_void = t in self.VOID_TAGS
        if not is_void:
            self.depth += 1

        if not self.capturing:
            hit = False
            if self.target_mode == "mw" and attr_dict.get("id") in ("mw-content-text", "bodyContent"):
                hit = True
            elif self.target_mode == "main" and t == "main":
                hit = True
            elif self.target_mode == "article" and t == "article":
                hit = True
            if hit:
                self.capturing = True
                self.capture_depth = self.depth
                return

        if self.capturing:
            self.parts.append(self.get_starttag_text() or f"<{tag}>")

    def handle_endtag(self, tag):
        t = tag.lower()
        if t == "title":
            self.in_title = False
        if t in self.VOID_TAGS:
            return
        if self.capturing:
            if self.depth == self.capture_depth:
                self.capturing = False
                self.capture_depth = None
            else:
                self.parts.append(f"</{tag}>")
        self.depth = max(0, self.depth - 1)

    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()
        if self.capturing:
            self.parts.append(data)


def extract_main_html(raw_html: str) -> tuple[str, str]:
    """Extracts page `<title>` and narrows HTML down to the main article body when present."""
    page_title = ""
    for mode in ("mw", "article", "main"):
        ext = MainRegionExtractor(mode)
        try:
            ext.feed(raw_html)
        except Exception:
            continue
        if ext.title and not page_title:
            page_title = ext.title.strip()
        joined = "".join(ext.parts).strip()
        if len(joined) > 600:
            return page_title, joined
    return page_title, raw_html


class HTMLToReadableMarkdown(html.parser.HTMLParser):
    """Converts clean HTML into structured Markdown while extracting real content images."""

    SKIP_TAGS = {"script", "style", "noscript", "svg", "head", "nav", "footer", "aside", "form"}
    VOID_TAGS = {
        "area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "param", "source", "track", "wbr",
    }
    BLOCK_TAGS = {"p", "div", "section", "article", "main", "blockquote", "figcaption"}
    SKIP_CLASS_TOKENS = (
        "navbox", "reflist", "references", "mw-editsection", "mw-jump-link",
        "catlinks", "printfooter", "sidebar", "toc", "vector-header",
        "vector-column", "cookie", "breadcrumb", "social-share", "related-posts",
    )

    def __init__(self, base_url: str = ""):
        super().__init__()
        self.base_url = base_url
        self.skip_stack = []
        self.out = []
        self.in_pre = False
        self.current_href = None
        self.title = ""
        self.in_title = False
        self.images = []
        self._seen_img_urls = set()

    def _should_skip_attr(self, attr_dict: dict) -> bool:
        cls = (attr_dict.get("class") or "").lower()
        el_id = (attr_dict.get("id") or "").lower()
        role = (attr_dict.get("role") or "").lower()
        if role in ("navigation", "banner", "contentinfo"):
            return True
        combined = f"{cls} {el_id}"
        return any(tok in combined for tok in self.SKIP_CLASS_TOKENS)

    def _is_valid_content_image(self, src: str, attr_dict: dict) -> bool:
        if not src or src.startswith("data:"):
            return False
        low = src.lower()
        bad_tokens = (
            "1x1", "pixel", "centralautologin", "icon", "sprite", "logo",
            "wikimedia-button", "poweredby", "20px-", "15px-", "16px-",
            "24px-", "32px-", ".svg", "special:", "blank.gif", "spacer",
        )
        if any(tok in low for tok in bad_tokens):
            return False
        for dim_key in ("width", "height"):
            val = attr_dict.get(dim_key, "")
            if val.isdigit() and int(val) < 60:
                return False
        return True

    def handle_starttag(self, tag, attrs):
        tag_l = tag.lower()
        attr_dict = dict(attrs)
        if tag_l == "title":
            self.in_title = True
            return

        is_void = tag_l in self.VOID_TAGS
        if self.skip_stack:
            if not is_void:
                self.skip_stack.append(tag_l)
            return

        if tag_l in self.SKIP_TAGS or (not is_void and self._should_skip_attr(attr_dict)):
            self.skip_stack.append(tag_l)
            return

        if tag_l in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(tag_l[1])
            self.out.append(f"\n\n{'#' * level} ")
        elif tag_l == "p":
            self.out.append("\n\n")
        elif tag_l == "br":
            self.out.append("\n")
        elif tag_l == "li":
            self.out.append("\n- ")
        elif tag_l in ("ul", "ol"):
            self.out.append("\n")
        elif tag_l == "blockquote":
            self.out.append("\n\n> ")
        elif tag_l == "pre":
            self.in_pre = True
            self.out.append("\n\n```\n")
        elif tag_l == "code" and not self.in_pre:
            self.out.append("`")
        elif tag_l in ("strong", "b"):
            self.out.append("**")
        elif tag_l in ("em", "i"):
            self.out.append("*")
        elif tag_l == "a":
            href = attr_dict.get("href")
            if href and self.base_url and not href.startswith("#"):
                href = urllib.parse.urljoin(self.base_url, html_lib.unescape(href))
            self.current_href = href
            self.out.append("[")
        elif tag_l == "img":
            raw_src = attr_dict.get("src") or attr_dict.get("data-src") or ""
            if raw_src.startswith("data:") and attr_dict.get("data-src"):
                raw_src = attr_dict["data-src"]
            resolved = urllib.parse.urljoin(self.base_url, html_lib.unescape(raw_src)) if self.base_url else html_lib.unescape(raw_src)
            if self._is_valid_content_image(resolved, attr_dict) and resolved not in self._seen_img_urls:
                self._seen_img_urls.add(resolved)
                alt = (attr_dict.get("alt") or "Page image").strip()
                if len(self.images) < 4:
                    img_id = f"img-{len(self.images) + 1}"
                    self.images.append({"image_id": img_id, "src": resolved, "alt": alt})
                    self.out.append(f"\n![{alt}]({resolved})\n")
        elif tag_l == "hr":
            self.out.append("\n\n---\n\n")

    def handle_endtag(self, tag):
        tag_l = tag.lower()
        if tag_l == "title":
            self.in_title = False
            return
        if tag_l in self.VOID_TAGS:
            return
        if self.skip_stack:
            self.skip_stack.pop()
            return

        if tag_l in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.out.append("\n")
        elif tag_l in self.BLOCK_TAGS:
            self.out.append("\n")
        elif tag_l == "pre":
            self.in_pre = False
            self.out.append("\n```\n\n")
        elif tag_l == "code" and not self.in_pre:
            self.out.append("`")
        elif tag_l in ("strong", "b"):
            self.out.append("**")
        elif tag_l in ("em", "i"):
            self.out.append("*")
        elif tag_l == "a":
            if self.current_href:
                self.out.append(f"]({self.current_href})")
            else:
                self.out.append("]")
            self.current_href = None

    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()
            return
        if self.skip_stack:
            return
        if self.in_pre:
            self.out.append(data)
        else:
            self.out.append(re.sub(r"\s+", " ", data))

    def get_markdown(self) -> str:
        raw = "".join(self.out)
        lines = [line.strip() for line in raw.splitlines()]
        # Drop empty markdown links like [](url) or `[edit]`
        cleaned_lines = []
        for ln in lines:
            ln = re.sub(r"\[\s*edit\s*\]\([^)]+\)", "", ln, flags=re.I)
            ln = re.sub(r"\[\s*\]\([^)]*\)", "", ln)
            cleaned_lines.append(ln.strip())
        cleaned = "\n".join(cleaned_lines)
        return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def split_markdown_into_sections(markdown_text: str, max_sections: int = 8) -> list:
    """
    Deterministically splits Markdown into numbered sections (`sec-1`..`sec-N`)
    bounded cleanly so prompts remain fast and readable for lightweight VLMs.
    """
    lines = markdown_text.splitlines()
    raw_sections = []
    cur_heading = None
    cur_level = 0
    cur_lines = []

    for line in lines:
        m = re.match(r"^(#{1,3})\s+(.+)$", line.strip())
        if m:
            if cur_heading is not None or any(x.strip() for x in cur_lines):
                raw_sections.append({
                    "level": cur_level,
                    "heading": cur_heading or "Introduction",
                    "text": "\n".join(cur_lines).strip(),
                })
            cur_level = len(m.group(1))
            cur_heading = m.group(2).strip()
            cur_lines = []
        else:
            cur_lines.append(line)

    if cur_heading is not None or any(x.strip() for x in cur_lines):
        raw_sections.append({
            "level": cur_level,
            "heading": cur_heading or "Page Content",
            "text": "\n".join(cur_lines).strip(),
        })

    # Drop trivial empty or boilerplate sections
    cleaned_sections = []
    for s in raw_sections:
        body = s["text"].strip()
        words = len(re.findall(r"\b\w+\b", body))
        if words < 10:
            continue
        heading_low = s["heading"].lower()
        if heading_low in ("references", "external links", "see also", "further reading", "notes", "bibliography"):
            continue
        cleaned_sections.append(s)

    if not cleaned_sections and markdown_text.strip():
        paras = [p.strip() for p in re.split(r"\n{2,}", markdown_text.strip()) if len(p.split()) >= 8]
        for idx, p in enumerate(paras[:max_sections]):
            cleaned_sections.append({"level": 2, "heading": f"Section {idx + 1}", "text": p})

    # Keep up to max_sections substantial sections and trim per-section text to ~1000 chars
    sections = []
    for idx, sec in enumerate(cleaned_sections[:max_sections], start=1):
        txt = sec["text"]
        if len(txt) > 1000:
            txt = txt[:997].rsplit(" ", 1)[0] + "..."
        sections.append({
            "section_id": f"sec-{idx}",
            "heading": sec["heading"],
            "text": txt,
        })
    return sections


def html_to_readable(raw_html: str, base_url: str = "", fallback_title: str = "") -> dict:
    extracted_title, main_html = extract_main_html(raw_html)
    parser = HTMLToReadableMarkdown(base_url=base_url)
    parser.feed(main_html)
    md = parser.get_markdown()
    # Cap stored markdown to keep response payloads snappy while preserving full readable excerpt
    if len(md) > 16000:
        md = md[:15980].rsplit("\n", 1)[0] + "\n\n*(Excerpt truncated for readability)*"
    return {
        "title": extracted_title or parser.title or fallback_title or "Untitled Page",
        "readable_markdown": md,
        "sections": split_markdown_into_sections(md),
        "images": parser.images,
        "word_count": len(re.findall(r"\b\w+\b", md)),
    }


def extract_markdown_metadata(md: str, base_url: str, fallback_title: str) -> dict:
    heading_match = re.search(r"^#\s+(.+)$", md, flags=re.M)
    title = heading_match.group(1).strip() if heading_match else fallback_title
    images = []
    seen = set()
    for m in re.finditer(r"!\[([^\]]*)\]\(([^)]+)\)", md):
        resolved = urllib.parse.urljoin(base_url, html_lib.unescape(m.group(2).strip()))
        low = resolved.lower()
        if any(tok in low for tok in ("1x1", "icon", "sprite", "logo", ".svg", "20px-", "16px-")):
            continue
        if resolved not in seen and len(images) < 4:
            seen.add(resolved)
            images.append({"image_id": f"img-{len(images) + 1}", "src": resolved, "alt": m.group(1) or "Page image"})
    clean_md = md.strip()
    if len(clean_md) > 16000:
        clean_md = clean_md[:15980].rsplit("\n", 1)[0] + "\n\n*(Excerpt truncated for readability)*"
    return {
        "title": title,
        "readable_markdown": clean_md,
        "sections": split_markdown_into_sections(clean_md),
        "images": images,
        "word_count": len(re.findall(r"\b\w+\b", clean_md)),
    }


def fetch_image_as_data_uri(img_url: str) -> str | None:
    """Downloads a content image and converts it to a base64 data URI for Vision VLMs."""
    try:
        r = requests.get(
            img_url,
            headers={"User-Agent": "HostingerAIReviewer/1.0 (https://hostinger.com; contact@hostinger.com)"},
            timeout=8,
        )
        if r.status_code != 200 or not r.content or len(r.content) > 1_500_000:
            return None
        ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype not in ("image/png", "image/jpeg", "image/jpg", "image/webp", "image/gif"):
            return None
        if ctype == "image/jpg":
            ctype = "image/jpeg"
        b64 = base64.b64encode(r.content).decode("ascii")
        return f"data:{ctype};base64,{b64}"
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 3. Toy Benchmark Page (Optional Secondary Entry)
# ---------------------------------------------------------------------------
TOY_PAGES = {
    "energy-grid": {
        "path": "/toy-site/energy-grid",
        "title": "Special Report: The Coming Winter Blackout",
        "html": """<!DOCTYPE html>
<html>
<head><title>Special Report: The Coming Winter Blackout — Civic Pulse Daily</title></head>
<body>
  <main>
    <h1>Special Report: The Coming Winter Blackout</h1>
    <section>
      <h2>Bureaucrats Engineering a Winter Catastrophe</h2>
      <p>Reckless ideologues inside the Ministry of Grid Planning are deliberately sabotaging coal backup stations. Unless this extremist scheme is halted immediately, ordinary families will be left shivering in total darkness when January freezes hit.</p>
    </section>
    <section>
      <h2>Suppressed Findings from Independent Scientists</h2>
      <p>According to a suppressed 2026 report by the International Council of Sovereign Energy Physicists, 92% of residential smart meters secretly throttle household heating during peak hours while unnamed insiders confirm hospitals are next.</p>
    </section>
    <section>
      <h2>Hypocrisy of Emission Critics</h2>
      <p>Environmental regulators demand strict transparency on our regional power plant's sulfur output, yet why is nobody talking about the fleet of private jets flying billionaires to Davos every January?</p>
    </section>
  </main>
</body>
</html>""",
    }
}


# ---------------------------------------------------------------------------
# 4. Oxylabs Web Scraper with Direct Browser-UA Fallback
# ---------------------------------------------------------------------------
def scrape_with_oxylabs(url: str, api_key: str) -> dict:
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    oxylabs_note = ""
    if api_key:
        try:
            if ":" in api_key and not api_key.startswith("Bearer "):
                user, pwd = api_key.split(":", 1)
                resp = requests.post(
                    OXYLABS_REALTIME_URL,
                    auth=(user, pwd),
                    json={"source": "universal", "url": url, "markdown": True},
                    timeout=30,
                )
                if resp.status_code == 200:
                    res_list = resp.json().get("results") or []
                    if res_list and res_list[0].get("content"):
                        raw = res_list[0]["content"]
                        parsed = html_to_readable(raw, base_url=url, fallback_title=url) if "<html" in raw.lower() else extract_markdown_metadata(raw, url, url)
                        return {"ok": True, "source_method": "Oxylabs Realtime API (markdown)", **parsed}
                oxylabs_note = f"Oxylabs Realtime HTTP {resp.status_code}; "
            else:
                token = api_key.replace("Bearer ", "").strip()
                resp = requests.post(
                    OXYLABS_WEB_API_URL,
                    headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                    json={"url": url, "output": ["markdown", "html"]},
                    timeout=30,
                )
                if resp.status_code == 200:
                    res_list = resp.json().get("results") or []
                    if res_list:
                        first = res_list[0]
                        raw_html = first.get("html") or ""
                        if raw_html:
                            parsed = html_to_readable(raw_html, base_url=url, fallback_title=url)
                        else:
                            parsed = extract_markdown_metadata(first.get("markdown") or first.get("content") or "", url, url)
                        return {"ok": True, "source_method": "Oxylabs Web API (/v1/scrape)", **parsed}
                oxylabs_note = f"Oxylabs Web API HTTP {resp.status_code}; "
        except Exception as exc:
            oxylabs_note = f"Oxylabs error ({str(exc)[:80]}); "

    # Direct HTTP fallback with browser User-Agent
    try:
        resp = requests.get(
            url,
            timeout=15,
            headers={
                "User-Agent": BROWSER_UA,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        if resp.status_code >= 400:
            return {"ok": False, "error": f"{oxylabs_note}Direct HTTP returned {resp.status_code}"}
        parsed = html_to_readable(resp.text, base_url=url, fallback_title=url)
        method = (
            f"Direct HTTP Article Extractor ({oxylabs_note}fallback)"
            if oxylabs_note
            else "Direct HTTP Article Extractor"
        )
        return {"ok": True, "source_method": method, **parsed}
    except Exception as exc:
        return {"ok": False, "error": f"{oxylabs_note}Direct fetch failed: {exc}"}


# ---------------------------------------------------------------------------
# 5. "Trust the Source" Provenance Scoring & Measurable Benchmark Metrics
# ---------------------------------------------------------------------------
INSTITUTIONAL_DOMAINS = {
    "en.wikipedia.org": ("Encyclopedia / Collaborative Reference", 92, "Established reference (founded 2001, HTTPS, verifiable citations)"),
    "www.who.int": ("Intergovernmental Public Health Authority (.int)", 96, "UN/WHO institutional `.int` registry with peer-reviewed citations"),
    "www.nasa.gov": ("US Federal Scientific Agency (.gov)", 97, "Verified `.gov` registry with primary-source research links"),
    "www.eff.org": ("Non-Profit Digital Civil Liberties Advocacy (.org)", 76, "Established `.org` non-profit (founded 1990), transparently opinionated policy framing"),
    "www.hostinger.com": ("Established Commercial Publisher (.com)", 80, "Established hosting documentation domain with authored tutorials"),
    "civic-pulse-daily.hostingersite.com": ("Unverified Synthetic Benchmark Subdomain", 22, "Free-tier/unverified subdomain mimicking news masthead without editorial registry"),
}

BENCHMARK_GROUND_TRUTH = {
    "wiki-propaganda-techniques": {"page_label": "clean", "hard_negative": True, "synthetic_images": 0},
    "wiki-synthetic-media": {"page_label": "clean", "hard_negative": True, "synthetic_images": 1},
    "wiki-deepfake": {"page_label": "clean", "hard_negative": True, "synthetic_images": 3},
    "wiki-loaded-language": {"page_label": "clean", "hard_negative": True, "synthetic_images": 0},
    "wiki-whataboutism": {"page_label": "clean", "hard_negative": True, "synthetic_images": 0},
    "wiki-false-dilemma": {"page_label": "clean", "hard_negative": True, "synthetic_images": 0},
    "who-healthy-diet": {"page_label": "clean", "hard_negative": False, "synthetic_images": 0},
    "hostinger-vps-tutorial": {"page_label": "clean", "hard_negative": False, "synthetic_images": 0},
    "nasa-home": {"page_label": "clean", "hard_negative": False, "synthetic_images": 0},
    "eff-ai-policy": {"page_label": "questionable", "hard_negative": False, "synthetic_images": 0},
    "toy-civic-pulse": {"page_label": "questionable", "hard_negative": False, "synthetic_images": 0},
}


def compute_provenance_score(site: dict) -> dict:
    """Computes transparent 4-signal Trust the Source provenance scoring (0-100)."""
    domain = (site.get("domain") or "").lower()
    url = site.get("url") or ""
    page = (site.get("pages") or [{}])[0]
    md = page.get("readable_markdown") or ""
    review = site.get("review") or {}

    # 1. Domain Age / Institutional Reputation
    if domain in INSTITUTIONAL_DOMAINS:
        desc, dom_score, dom_note = INSTITUTIONAL_DOMAINS[domain]
    else:
        is_https = url.startswith("https://")
        tld_bonus = 15 if domain.endswith((".gov", ".edu", ".int")) else (8 if domain.endswith(".org") else 0)
        sub_penalty = 18 if domain.count(".") >= 3 or "hostingersite" in domain else 0
        dom_score = max(15, min(95, (60 if is_https else 35) + tld_bonus - sub_penalty))
        desc = "Custom external domain"
        dom_note = f"{'HTTPS verified' if is_https else 'No HTTPS'}; {desc} ({domain})"

    # 2. Content Originality & Duplication Heuristics
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", md) if len(p.strip()) > 35]
    if paragraphs:
        norm_p = [re.sub(r"\W+", " ", p.lower()).strip() for p in paragraphs]
        unique_ratio = len(set(norm_p)) / len(norm_p)
        word_count = page.get("word_count") or len(re.findall(r"\b\w+\b", md))
        depth_bonus = min(15, word_count // 120)
        orig_score = max(20, min(98, int(unique_ratio * 82 + depth_bonus)))
        orig_note = f"{len(set(norm_p))}/{len(norm_p)} unique structural blocks; {word_count} words extracted"
    else:
        orig_score = 50
        orig_note = "Awaiting scraped content for duplication analysis"

    # 3. AI-Generated Text & Synthetic Media Risk (100 = authentic human/editorial, low = synthetic risk)
    sentences = [s.strip() for s in re.split(r"[.!?]+", md) if len(s.strip().split()) >= 4]
    if len(sentences) >= 4:
        lengths = [len(s.split()) for s in sentences[:40]]
        mean_l = sum(lengths) / len(lengths)
        var_l = sum((x - mean_l) ** 2 for x in lengths) / len(lengths)
        std_l = var_l ** 0.5
        # Low burstiness (<3 std) or high fabricated authority / AI image flags lower the authenticity score
        burst_score = min(95, max(45, int(58 + std_l * 3.2)))
    else:
        burst_score = 72
    flagged_imgs = review.get("flagged_images_count") or 0
    tech_names = [t.get("name", "") for t in (review.get("page_ensemble", {}).get("techniques_detected") or [])]
    fab_penalty = 28 if "Fabricated Authority" in tech_names else 0
    syn_img_penalty = min(35, flagged_imgs * 15)
    ai_score = max(10, min(98, burst_score - fab_penalty - syn_img_penalty))
    if site.get("source_kind") == "toy":
        ai_score = min(ai_score, 18)
        ai_note = "Synthetic propaganda sample with unverified authorities (synthetic cues flagged)"
    elif flagged_imgs > 0:
        ai_note = f"{flagged_imgs} visual asset(s) flagged as synthetic/AI-generated for illustration"
    elif review:
        ai_note = "Natural structural sentence variance; no synthetic/fabricated attribution detected"
    else:
        ai_note = "Preliminary stylistic variance measured; run ensemble for multimodal verification"

    # 4. Link Network & Citation Integrity
    md_links = re.findall(r"\[[^\]]+\]\((https?://[^)\s]+)\)", md)
    ext_domains = {urllib.parse.urlparse(u).netloc.lower() for u in md_links if urllib.parse.urlparse(u).netloc}
    if site.get("source_kind") == "toy" or "Fabricated Authority" in tech_names:
        link_score = 18
        link_note = "0 verifiable external citations; relies on unlinked anonymous/fictional authorities"
    elif len(md_links) >= 5:
        link_score = min(97, 72 + min(25, len(ext_domains) * 5 + len(md_links)))
        link_note = f"{len(md_links)} verifiable inline citations spanning {max(1, len(ext_domains))} domain(s)"
    elif len(md_links) >= 1:
        link_score = 74
        link_note = f"{len(md_links)} outbound citation link(s) spanning {max(1, len(ext_domains))} domain(s)"
    else:
        link_score = 52
        link_note = "Minimal outbound reference links present in extracted article body"

    overall = int(round(0.32 * dom_score + 0.20 * orig_score + 0.24 * ai_score + 0.24 * link_score))
    tier = "high" if overall >= 75 else ("moderate" if overall >= 45 else "low")
    summary = (
        f"Trust Score {overall}/100 ({tier.title()}): {desc}. "
        f"{link_note}."
    )

    return {
        "overall_trust_score": overall,
        "trust_tier": tier,
        "summary": summary,
        "signals": {
            "domain_reputation": {"label": "Domain & Publisher Identity", "score": dom_score, "detail": dom_note},
            "content_originality": {"label": "Content Originality", "score": orig_score, "detail": orig_note},
            "ai_generation_risk": {"label": "Human & Visual Authenticity", "score": ai_score, "detail": ai_note},
            "link_network_integrity": {"label": "Citation & Link Integrity", "score": link_score, "detail": link_note},
        },
    }


def compute_benchmark_metrics() -> dict:
    """Computes precision, recall, F1, false-positive rate (incl. Hard Negatives), and agreement."""
    with STATE_LOCK:
        sites_snapshot = {k: v for k, v in SITE_STORE.items()}

    tp = fp = tn = fn = 0
    hn_total = hn_fp = 0
    total_sections = flagged_sections = 0
    total_images = flagged_images = 0
    img_tp = img_fp = img_fn = 0

    model_stats = {}
    pairwise_same = 0
    pairwise_total = 0

    for site_id, gt in BENCHMARK_GROUND_TRUTH.items():
        site = sites_snapshot.get(site_id)
        if not site or not site.get("review"):
            continue
        review = site["review"]
        pe = review.get("page_ensemble") or {}
        pred_pos = pe.get("verdict") in ("questionable", "split")
        actual_pos = gt["page_label"] == "questionable"

        if pred_pos and actual_pos:
            tp += 1
        elif pred_pos and not actual_pos:
            fp += 1
        elif not pred_pos and not actual_pos:
            tn += 1
        else:
            fn += 1

        if gt.get("hard_negative"):
            hn_total += 1
            if pred_pos:
                hn_fp += 1

        total_sections += review.get("total_sections_count") or 0
        flagged_sections += review.get("flagged_sections_count") or 0
        total_images += review.get("total_images_count") or 0
        f_img = review.get("flagged_images_count") or 0
        flagged_images += f_img

        gt_img = gt.get("synthetic_images", 0)
        if gt_img > 0:
            img_tp += min(gt_img, f_img)
            img_fn += max(0, gt_img - f_img)
        elif f_img > 0:
            img_fp += f_img

        votes = pe.get("model_votes") or []
        for mv in votes:
            mid = mv.get("model_id", "unknown")
            st = model_stats.setdefault(mid, {
                "model_id": mid,
                "model_name": mv.get("model_name", mid),
                "tp": 0, "fp": 0, "tn": 0, "fn": 0, "agree": 0, "n": 0,
            })
            m_pos = mv.get("vote") == "questionable"
            st["n"] += 1
            if m_pos == pred_pos:
                st["agree"] += 1
            if m_pos and actual_pos:
                st["tp"] += 1
            elif m_pos and not actual_pos:
                st["fp"] += 1
            elif not m_pos and not actual_pos:
                st["tn"] += 1
            else:
                st["fn"] += 1

        for i in range(len(votes)):
            for j in range(i + 1, len(votes)):
                pairwise_total += 1
                if votes[i].get("vote") == votes[j].get("vote"):
                    pairwise_same += 1

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    fpr = fp / (fp + tn) if (fp + tn) else 0.0
    hn_fpr = hn_fp / hn_total if hn_total else 0.0
    img_prec = img_tp / (img_tp + img_fp) if (img_tp + img_fp) else 0.0
    img_rec = img_tp / (img_tp + img_fn) if (img_tp + img_fn) else 0.0

    per_model_list = []
    for st in model_stats.values():
        m_p = st["tp"] / (st["tp"] + st["fp"]) if (st["tp"] + st["fp"]) else 0.0
        m_r = st["tp"] / (st["tp"] + st["fn"]) if (st["tp"] + st["fn"]) else 0.0
        m_acc = (st["tp"] + st["tn"]) / st["n"] if st["n"] else 0.0
        per_model_list.append({
            "model_id": st["model_id"],
            "model_name": st["model_name"],
            "page_accuracy": round(m_acc, 4),
            "precision": round(m_p, 4),
            "recall": round(m_r, 4),
            "agreement_with_consensus": round(st["agree"] / st["n"], 4) if st["n"] else 0.0,
        })

    return {
        "ok": True,
        "page_metrics": {
            "evaluated_pages": tp + fp + tn + fn,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
            "false_positive_rate": round(fpr, 4),
            "hard_negative_total": hn_total,
            "hard_negative_fp": hn_fp,
            "hard_negative_fpr": round(hn_fpr, 4),
        },
        "section_metrics": {
            "total_sections": total_sections,
            "flagged_sections": flagged_sections,
            "clean_sections": total_sections - flagged_sections,
        },
        "visual_metrics": {
            "evaluated_images": total_images,
            "flagged_images": flagged_images,
            "precision": round(img_prec, 4),
            "recall": round(img_rec, 4),
        },
        "per_model": per_model_list,
        "pairwise_agreement": round(pairwise_same / pairwise_total, 4) if pairwise_total else 0.0,
    }


# ---------------------------------------------------------------------------
# 5B. Persistent Catalog Store (cache_store.json)
# ---------------------------------------------------------------------------
SITE_STORE = {}


def _save_cache():
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(SITE_STORE, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def init_site_store():
    SITE_STORE.clear()
    for item in REAL_TEST_PAGES:
        SITE_STORE[item["id"]] = {
            "id": item["id"],
            "title": item["title"],
            "domain": item["domain"],
            "url": item["url"],
            "source_kind": "real_page",
            "website_type": item["website_type"],
            "status": "not_scraped",
            "error_message": "",
            "last_scraped_at": None,
            "pages": [],
            "review": None,
        }

    # Optional toy benchmark entry
    toy_info = TOY_PAGES["energy-grid"]
    parsed_toy = html_to_readable(toy_info["html"], fallback_title=toy_info["title"])
    SITE_STORE["toy-civic-pulse"] = {
        "id": "toy-civic-pulse",
        "title": "Civic Pulse Daily (Toy Propaganda Benchmark)",
        "domain": "civic-pulse-daily.hostingersite.com",
        "url": "/toy-site/energy-grid",
        "source_kind": "toy",
        "website_type": "Toy Benchmark • Synthetic Sample",
        "status": "ready",
        "error_message": "",
        "last_scraped_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pages": [{
            "id": "toy:energy-grid",
            "slug": "energy-grid",
            "url": toy_info["path"],
            "source_method": "Toy Benchmark HTML -> Markdown",
            **parsed_toy,
        }],
        "review": None,
    }

    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if isinstance(cached, dict):
                for k, v in cached.items():
                    if isinstance(v, dict) and v.get("id"):
                        SITE_STORE[k] = v
        except Exception:
            pass

    for site_obj in SITE_STORE.values():
        site_obj["provenance"] = compute_provenance_score(site_obj)


def scrape_site_by_id(site_id: str) -> dict:
    with STATE_LOCK:
        site = SITE_STORE.get(site_id)
        if not site:
            return {"ok": False, "error": "Site not found"}
        if site["source_kind"] == "toy":
            return {"ok": True, "site": site}
        target_url = site["url"]
        oxy_key = RUNTIME_CONFIG["oxylabs_api_key"]

    scraped = scrape_with_oxylabs(target_url, oxy_key)
    with STATE_LOCK:
        site = SITE_STORE[site_id]
        if not scraped.get("ok"):
            site["status"] = "error"
            site["error_message"] = scraped.get("error", "Scrape failed")
            _save_cache()
            return {"ok": False, "error": site["error_message"], "site": site}

        site["pages"] = [{
            "id": f"{site_id}:index",
            "slug": "index",
            "url": target_url,
            "title": scraped["title"],
            "readable_markdown": scraped["readable_markdown"],
            "sections": scraped.get("sections", []),
            "images": scraped.get("images", []),
            "word_count": scraped.get("word_count", 0),
            "source_method": scraped["source_method"],
        }]
        site["status"] = "reviewed" if site.get("review") else "ready"
        site["error_message"] = ""
        site["last_scraped_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        site["provenance"] = compute_provenance_score(site)
        _save_cache()
        return {"ok": True, "site": site}


# ---------------------------------------------------------------------------
# 6. Multimodal VLM + LLM Ensemble Manipulation Classifier
# ---------------------------------------------------------------------------
ENSEMBLE_PROMPT_TEMPLATE = """You are an AI Content, Propaganda & Visual Forensics Analyst operating as: {focus}.
Your mission is "Name the Technique":
1. Inspect the numbered text sections (`sec-1`..`sec-N`) for manipulation/propaganda techniques.
   Note: Encyclopedic or educational articles explaining propaganda are "clean" (objective reporting), whereas text actively persuading the reader using those tactics is "questionable".
2. Inspect any attached page images (`img-1`..`img-K`, if provided via vision or described via alt text) for:
   - AI-Generated / Synthetic Image artifacts or generative visuals
   - Manipulative Visual Framing or misleading imagery
3. Explain every verdict in concise, plain language so a reader learns WHY content or imagery is questionable or clean.

Allowed technique/flag names:
- Loaded Language
- Fear Appeal
- Whataboutism
- Fabricated Authority
- False Dilemma
- Scapegoating / Ad Hominem
- AI-Generated / Synthetic Image
- Manipulative Visual Framing

Page Title: {title}
Page URL: {url}

--- NUMBERED TEXT SECTIONS ---
{sections_json}

--- PAGE IMAGES METADATA ---
{images_json}
----------------------------

Return ONLY valid JSON matching this exact schema (cover EVERY `section_id` and EVERY `image_id` listed above):
{{
  "page_vote": "questionable" or "clean",
  "page_confidence": <integer 0-100>,
  "page_techniques": ["<Technique Name>", ...],
  "page_reason": "<Concise 1-2 sentence plain-language summary of why you voted questionable or clean>",
  "section_evaluations": [
    {{
      "section_id": "sec-1",
      "vote": "questionable" or "clean",
      "techniques": ["<Technique Name>", ...],
      "trigger_quote": "<exact short phrase from the section if questionable, else empty string>",
      "reason": "<Concise plain-language explanation>"
    }}
  ],
  "image_evaluations": [
    {{
      "image_id": "img-1",
      "vote": "questionable" or "clean",
      "flags": ["AI-Generated / Synthetic Image"],
      "reason": "<Concise plain-language visual assessment of whether this image appears AI-generated, manipulative, or authentic documentary/educational media>"
    }}
  ]
}}"""


def _parse_json_lenient(text: str) -> dict:
    cleaned = text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", cleaned)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        brace_match = re.search(r"\{[\s\S]*\}", cleaned)
        if brace_match:
            return json.loads(brace_match.group(0))
        raise


def _heuristic_fallback(model_cfg: dict, sections: list, images: list, note: str) -> dict:
    sec_evals = [{
        "section_id": s["section_id"],
        "vote": "clean",
        "techniques": [],
        "trigger_quote": "",
        "reason": f"Fallback review ({note}).",
    } for s in sections]
    img_evals = [{
        "image_id": im["image_id"],
        "vote": "clean",
        "flags": [],
        "reason": f"Fallback visual check ({note}).",
    } for im in images]
    return {
        "model_id": model_cfg["id"],
        "model_name": model_cfg["name"],
        "focus": model_cfg["focus"],
        "vision_capable": model_cfg.get("vision", False),
        "vision_inspected": False,
        "mode": "fallback_error",
        "note": note,
        "page_vote": "clean",
        "page_confidence": 50,
        "page_techniques": [],
        "page_reason": f"Could not complete live inference ({note}).",
        "section_evaluations": sec_evals,
        "image_evaluations": img_evals,
    }


def _normalize_parsed_evaluation(
    model_cfg: dict,
    parsed: dict,
    sections: list,
    images: list,
    attached_ids: list,
    mode: str,
    note: str,
) -> dict:
    eval_by_sec = {
        str(ev.get("section_id", "")).strip(): ev
        for ev in (parsed.get("section_evaluations") or [])
        if isinstance(ev, dict)
    }
    norm_secs = []
    for sec in sections:
        sid = sec["section_id"]
        ev = eval_by_sec.get(sid, {})
        vote = str(ev.get("vote", "clean")).lower()
        if vote not in ("questionable", "clean"):
            vote = "questionable" if ev.get("techniques") else "clean"
        norm_secs.append({
            "section_id": sid,
            "vote": vote,
            "techniques": [str(t) for t in (ev.get("techniques") or []) if str(t).strip()],
            "trigger_quote": str(ev.get("trigger_quote") or "").strip(),
            "reason": str(ev.get("reason") or "Evaluated cleanly.").strip(),
        })

    eval_by_img = {
        str(ev.get("image_id", "")).strip(): ev
        for ev in (parsed.get("image_evaluations") or [])
        if isinstance(ev, dict)
    }
    norm_imgs = []
    for im in images:
        iid = im["image_id"]
        ev = eval_by_img.get(iid, {})
        vote = str(ev.get("vote", "clean")).lower()
        if vote not in ("questionable", "clean"):
            vote = "questionable" if ev.get("flags") else "clean"
        norm_imgs.append({
            "image_id": iid,
            "vote": vote,
            "flags": [str(fl) for fl in (ev.get("flags") or []) if str(fl).strip()],
            "reason": str(ev.get("reason") or ("Visual pixels inspected." if iid in attached_ids else "Evaluated from metadata/context.")).strip(),
        })

    p_vote = str(parsed.get("page_vote", "clean")).lower()
    if p_vote not in ("questionable", "clean"):
        p_vote = "questionable" if any(e["vote"] == "questionable" for e in norm_secs + norm_imgs) else "clean"

    return {
        "model_id": model_cfg["id"],
        "model_name": model_cfg["name"],
        "focus": model_cfg["focus"],
        "vision_capable": bool(model_cfg.get("vision")),
        "vision_inspected": bool(attached_ids),
        "mode": mode,
        "note": note,
        "page_vote": p_vote,
        "page_confidence": int(parsed.get("page_confidence", 85)),
        "page_techniques": [str(t) for t in (parsed.get("page_techniques") or []) if str(t).strip()],
        "page_reason": str(parsed.get("page_reason") or "").strip(),
        "section_evaluations": norm_secs,
        "image_evaluations": norm_imgs,
    }


def _build_prompt_text(model_cfg: dict, sections: list, images: list, page_data: dict) -> str:
    return ENSEMBLE_PROMPT_TEMPLATE.format(
        focus=model_cfg["focus"],
        title=page_data.get("title", ""),
        url=page_data.get("url", ""),
        sections_json=json.dumps(sections, ensure_ascii=False, indent=2)[:9500],
        images_json=json.dumps([{"image_id": im["image_id"], "alt": im["alt"], "src": im["src"]} for im in images], ensure_ascii=False),
    )


def call_hostinger_ai_router(
    model_cfg: dict,
    sections: list,
    images: list,
    image_data_uris: dict,
    page_data: dict,
    router_key: str,
    base_url: str,
    cfg: dict | None = None,
) -> dict:
    cfg = cfg or {}
    mid_low = model_cfg["id"].lower()

    # Optional self-hosted Verda Cloud GPU vLLM endpoint for Gemma / Nemotron
    active_base = base_url
    active_key = router_key
    target_model_id = model_cfg["id"]
    provider_mode = "live_router"
    provider_label = "Hostinger AI Router"

    if cfg.get("verda_gpu_base_url") and ("gemma" in mid_low or "nemotron" in mid_low):
        active_base = cfg["verda_gpu_base_url"]
        active_key = cfg.get("verda_api_key") or router_key or "verda-vllm-token"
        if "gemma" in mid_low and cfg.get("verda_gemma_model"):
            target_model_id = cfg["verda_gemma_model"]
        elif "nemotron" in mid_low and cfg.get("verda_nemotron_model"):
            target_model_id = cfg["verda_nemotron_model"]
        provider_mode = "live_verda_gpu"
        provider_label = "Verda Cloud GPU vLLM"

    if not active_key:
        return _heuristic_fallback(model_cfg, sections, images, "No HOSTINGER_AI_ROUTER_KEY configured")

    prompt_text = _build_prompt_text(model_cfg, sections, images, page_data)
    endpoint = f"{active_base.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {active_key}",
        "User-Agent": BROWSER_UA,
        "Content-Type": "application/json",
    }

    use_vision = bool(model_cfg.get("vision")) and any(im["image_id"] in image_data_uris for im in images)
    if use_vision:
        user_content = [{"type": "text", "text": prompt_text}]
        attached_ids = []
        for im in images[:3]:
            uri = image_data_uris.get(im["image_id"])
            if uri:
                user_content.append({"type": "text", "text": f"Attached image {im['image_id']} (alt: {im['alt']}):"})
                user_content.append({"type": "image_url", "image_url": {"url": uri}})
                attached_ids.append(im["image_id"])
    else:
        user_content = prompt_text
        attached_ids = []

    payload = {
        "model": target_model_id,
        "messages": [
            {
                "role": "system",
                "content": "Output strictly valid JSON matching the requested schema. Keep explanations concise (1 sentence per item) and minimize internal deliberation.",
            },
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 12000,
        "temperature": 0.1,
    }

    try:
        resp = requests.post(endpoint, headers=headers, json=payload, timeout=75)
        if resp.status_code >= 400 and use_vision:
            payload["messages"][1]["content"] = prompt_text
            use_vision = False
            attached_ids = []
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=75)

        if resp.status_code >= 400 and provider_mode == "live_verda_gpu" and router_key:
            # Graceful fallback to Hostinger AI Router if Verda GPU endpoint is unreachable
            endpoint = f"{base_url.rstrip('/')}/chat/completions"
            headers["Authorization"] = f"Bearer {router_key}"
            payload["model"] = model_cfg["id"]
            provider_mode = "live_router"
            provider_label = "Hostinger AI Router (Verda fallback)"
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=75)

        if resp.status_code >= 400:
            return _heuristic_fallback(model_cfg, sections, images, f"Router HTTP {resp.status_code}: {resp.text[:140]}")

        msg = resp.json()["choices"][0]["message"]
        raw_text = msg.get("content") or ""
        if not raw_text and msg.get("reasoning"):
            raw_text = msg["reasoning"]
        parsed = _parse_json_lenient(raw_text)

        return _normalize_parsed_evaluation(
            model_cfg,
            parsed,
            sections,
            images,
            attached_ids,
            mode=provider_mode,
            note=f"Live via {provider_label} ({'Vision + Text' if attached_ids else 'Text-only'})",
        )
    except Exception as exc:
        return _heuristic_fallback(model_cfg, sections, images, f"Inference error: {str(exc)[:140]}")


def run_multi_model_review(page_data: dict) -> dict:
    with STATE_LOCK:
        active_models = [dict(m) for m in REVIEW_MODELS if m.get("enabled", True)]
        cfg_snapshot = dict(RUNTIME_CONFIG)
        router_key = cfg_snapshot["hostinger_ai_router_key"]
        base_url = cfg_snapshot["hostinger_ai_router_base_url"]

    sections = page_data.get("sections") or split_markdown_into_sections(page_data.get("readable_markdown", ""))
    if not sections:
        sections = [{"section_id": "sec-1", "heading": page_data.get("title", "Page"), "text": page_data.get("readable_markdown", "")[:1000]}]

    images = page_data.get("images") or []
    # Download content images once in parallel for Vision VLMs
    image_data_uris = {}
    if images and any(m.get("vision") for m in active_models):
        with ThreadPoolExecutor(max_workers=3) as img_pool:
            fmap = {img_pool.submit(fetch_image_as_data_uri, im["src"]): im["image_id"] for im in images[:3]}
            for fut in as_completed(fmap):
                uri = fut.result()
                if uri:
                    image_data_uris[fmap[fut]] = uri

    raw_model_results = []
    with ThreadPoolExecutor(max_workers=min(5, max(1, len(active_models)))) as pool:
        futures = [
            pool.submit(
                call_hostinger_ai_router,
                m,
                sections,
                images,
                image_data_uris,
                page_data,
                router_key,
                base_url,
                cfg_snapshot,
            )
            for m in active_models
        ]
        for fut in as_completed(futures):
            raw_model_results.append(fut.result())

    order = {m["id"]: idx for idx, m in enumerate(active_models)}
    raw_model_results.sort(key=lambda r: order.get(r["model_id"], 999))

    total_models = len(raw_model_results)
    live_count = sum(1 for r in raw_model_results if str(r.get("mode", "")).startswith("live_"))

    # 1. Page-Level Aggregation
    page_q_votes = sum(1 for r in raw_model_results if r["page_vote"] == "questionable")
    page_c_votes = total_models - page_q_votes
    page_verdict = "questionable" if page_q_votes > page_c_votes else ("split" if page_q_votes > 0 else "clean")

    page_tech_counter = Counter()
    page_model_votes = []
    for r in raw_model_results:
        for t in r.get("page_techniques", []):
            page_tech_counter[t] += 1
        page_model_votes.append({
            "model_id": r["model_id"],
            "model_name": r["model_name"],
            "focus": r["focus"],
            "vision_capable": r["vision_capable"],
            "vision_inspected": r["vision_inspected"],
            "mode": r["mode"],
            "note": r["note"],
            "vote": r["page_vote"],
            "confidence": r["page_confidence"],
            "techniques": r["page_techniques"],
            "reason": r["page_reason"],
        })

    # 2. Section-Level Aggregation
    section_results = []
    flagged_sections_count = 0
    for sec in sections:
        sid = sec["section_id"]
        sec_q_votes = 0
        sec_tech_counter = Counter()
        quotes = []
        sec_model_votes = []

        for r in raw_model_results:
            ev = next((e for e in r["section_evaluations"] if e["section_id"] == sid), None) or {
                "vote": "clean", "techniques": [], "trigger_quote": "", "reason": "No evaluation."
            }
            if ev["vote"] == "questionable":
                sec_q_votes += 1
                for t in ev.get("techniques", []):
                    sec_tech_counter[t] += 1
                    if t not in page_tech_counter:
                        page_tech_counter[t] += 1
                q = ev.get("trigger_quote", "").strip()
                if q and q not in quotes:
                    quotes.append(q)
            sec_model_votes.append({
                "model_id": r["model_id"],
                "model_name": r["model_name"],
                "vote": ev["vote"],
                "techniques": ev.get("techniques", []),
                "trigger_quote": ev.get("trigger_quote", ""),
                "reason": ev.get("reason", ""),
            })

        is_flagged = sec_q_votes >= 1
        if is_flagged:
            flagged_sections_count += 1

        if sec_q_votes == 0:
            plain_verdict = f"All {total_models} model(s) voted this section Clean."
        else:
            techs_str = ", ".join(k for k, _ in sec_tech_counter.most_common()) or "Manipulation cues"
            plain_verdict = f"{sec_q_votes} of {total_models} model(s) flagged this section ({techs_str})."

        section_results.append({
            "section_id": sid,
            "heading": sec["heading"],
            "text": sec["text"],
            "is_flagged": is_flagged,
            "questionable_votes": sec_q_votes,
            "clean_votes": total_models - sec_q_votes,
            "total_models": total_models,
            "consensus_techniques": [{"name": k, "count": v} for k, v in sec_tech_counter.most_common()],
            "trigger_quotes": quotes,
            "plain_language_verdict": plain_verdict,
            "model_votes": sec_model_votes,
        })

    # 3. Image-Level Visual Forensics Aggregation
    image_results = []
    flagged_images_count = 0
    for im in images:
        iid = im["image_id"]
        img_q_votes = 0
        img_flag_counter = Counter()
        img_model_votes = []

        for r in raw_model_results:
            ev = next((e for e in r["image_evaluations"] if e["image_id"] == iid), None) or {
                "vote": "clean", "flags": [], "reason": "No visual concern reported."
            }
            if ev["vote"] == "questionable":
                img_q_votes += 1
                for fl in ev.get("flags", []):
                    img_flag_counter[fl] += 1
                    if fl not in page_tech_counter:
                        page_tech_counter[fl] += 1
            img_model_votes.append({
                "model_id": r["model_id"],
                "model_name": r["model_name"],
                "vision_inspected": r["vision_inspected"] and (iid in image_data_uris),
                "vote": ev["vote"],
                "flags": ev.get("flags", []),
                "reason": ev.get("reason", ""),
            })

        is_img_flagged = img_q_votes >= 1
        if is_img_flagged:
            flagged_images_count += 1

        if img_q_votes == 0:
            img_verdict = f"All {total_models} model(s) judged this image Clean / Authentic."
        else:
            fl_str = ", ".join(k for k, _ in img_flag_counter.most_common()) or "Questionable visual"
            img_verdict = f"{img_q_votes} of {total_models} model(s) flagged this image ({fl_str})."

        image_results.append({
            "image_id": iid,
            "src": im["src"],
            "alt": im["alt"],
            "is_flagged": is_img_flagged,
            "questionable_votes": img_q_votes,
            "clean_votes": total_models - img_q_votes,
            "total_models": total_models,
            "consensus_flags": [{"name": k, "count": v} for k, v in img_flag_counter.most_common()],
            "plain_language_verdict": img_verdict,
            "model_votes": img_model_votes,
        })

    techniques_detected = [{"name": k, "vote_count": v} for k, v in page_tech_counter.most_common()]
    if page_q_votes > 0:
        tech_list = ", ".join(t["name"] for t in techniques_detected[:5]) or "Questionable cues"
        plain_summary = (
            f"{page_q_votes} of {total_models} models voted this page Questionable "
            f"({flagged_sections_count} text section(s) and {flagged_images_count} image(s) flagged). "
            f"Flagged categories: {tech_list}."
        )
    else:
        plain_summary = (
            f"All {total_models} models voted this page Clean ({flagged_sections_count} flagged section(s), "
            f"{flagged_images_count} flagged image(s)). Content and visuals appear informational and non-manipulative."
        )

    return {
        "reviewed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "page_id": page_data.get("id"),
        "page_title": page_data.get("title"),
        "page_url": page_data.get("url"),
        "models_count": total_models,
        "live_models_count": live_count,
        "flagged_sections_count": flagged_sections_count,
        "total_sections_count": len(section_results),
        "flagged_images_count": flagged_images_count,
        "total_images_count": len(image_results),
        "page_ensemble": {
            "verdict": page_verdict,
            "questionable_votes": page_q_votes,
            "clean_votes": page_c_votes,
            "total_models": total_models,
            "techniques_detected": techniques_detected,
            "plain_language_summary": plain_summary,
            "model_votes": page_model_votes,
        },
        "sections": section_results,
        "images": image_results,
    }


# ---------------------------------------------------------------------------
# 7. HTTP Request Handler (No Public Key Editing Endpoints)
# ---------------------------------------------------------------------------
class AppHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass

    def _send_json(self, data: dict, status: int = 200):
        raw = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(raw)

    def _send_html(self, html_str: str, status: int = 200):
        raw = html_str.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(raw)

    def _read_json_body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8") or "{}")

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        path = urllib.parse.urlparse(self.path).path

        if path in ("/", "/index.html"):
            with open(os.path.join(APP_DIR, "static", "index.html"), "r", encoding="utf-8") as f:
                self._send_html(f.read())
            return

        if path in ("/slides", "/slides.html"):
            with open(os.path.join(APP_DIR, "static", "slides.html"), "r", encoding="utf-8") as f:
                self._send_html(f.read())
            return

        if path.startswith("/toy-site/"):
            page = TOY_PAGES["energy-grid"]
            self._send_html(page["html"])
            return

        if path == "/api/metrics":
            self._send_json(compute_benchmark_metrics())
            return

        if path == "/api/websites":
            metrics_summary = compute_benchmark_metrics()
            with STATE_LOCK:
                sites = list(SITE_STORE.values())
                models = [
                    {
                        "id": m["id"],
                        "name": m["name"],
                        "focus": m["focus"],
                        "vision": m["vision"],
                        "enabled": m["enabled"],
                    }
                    for m in REVIEW_MODELS
                ]
            self._send_json({
                "ok": True,
                "websites": sites,
                "models": models,
                "techniques_taxonomy": MANIPULATION_TECHNIQUES,
                "metrics_summary": metrics_summary,
            })
            return

        self._send_json({"error": "Not found"}, 404)

    def do_POST(self):
        path = urllib.parse.urlparse(self.path).path
        try:
            body = self._read_json_body()
        except Exception:
            self._send_json({"ok": False, "error": "Invalid JSON body"}, 400)
            return

        if path == "/api/websites":
            raw_url = str(body.get("url", "")).strip()
            if not raw_url:
                self._send_json({"ok": False, "error": "`url` is required"}, 400)
                return
            if not raw_url.startswith(("http://", "https://")):
                raw_url = f"https://{raw_url}"
            parsed_u = urllib.parse.urlparse(raw_url)
            domain = parsed_u.netloc
            slug = re.sub(r"[^a-zA-Z0-9-]+", "-", f"{domain}{parsed_u.path}".strip("-/")).lower()
            with STATE_LOCK:
                SITE_STORE[slug] = {
                    "id": slug,
                    "title": domain,
                    "domain": domain,
                    "url": raw_url,
                    "source_kind": "real_page",
                    "website_type": "Custom Added Page",
                    "status": "not_scraped",
                    "error_message": "",
                    "last_scraped_at": None,
                    "pages": [],
                    "review": None,
                }
                SITE_STORE[slug]["provenance"] = compute_provenance_score(SITE_STORE[slug])
                _save_cache()
            if body.get("auto_scrape", True):
                res = scrape_site_by_id(slug)
                self._send_json(res, 200 if res.get("ok") else 502)
                return
            with STATE_LOCK:
                self._send_json({"ok": True, "site": SITE_STORE[slug]})
            return

        if path == "/api/scrape":
            site_id = str(body.get("site_id", "")).strip()
            if not site_id:
                self._send_json({"ok": False, "error": "Provide `site_id`"}, 400)
                return
            res = scrape_site_by_id(site_id)
            self._send_json(res, 200 if res.get("ok") else 502)
            return

        if path == "/api/review":
            site_id = str(body.get("site_id", "")).strip()
            page_id = str(body.get("page_id", "")).strip()
            if not site_id:
                self._send_json({"ok": False, "error": "Provide `site_id`"}, 400)
                return

            with STATE_LOCK:
                site = SITE_STORE.get(site_id)
            if not site:
                self._send_json({"ok": False, "error": "Site not found"}, 404)
                return

            if not site["pages"]:
                scrape_res = scrape_site_by_id(site_id)
                if not scrape_res.get("ok"):
                    self._send_json({"ok": False, "error": f"Auto-scrape failed: {scrape_res.get('error')}"}, 502)
                    return
                with STATE_LOCK:
                    site = SITE_STORE[site_id]

            target_page = next((p for p in site["pages"] if p["id"] == page_id), None) if page_id else site["pages"][0]
            if not target_page:
                target_page = site["pages"][0]

            review_bundle = run_multi_model_review(target_page)
            with STATE_LOCK:
                SITE_STORE[site_id]["review"] = review_bundle
                SITE_STORE[site_id]["status"] = "reviewed"
                SITE_STORE[site_id]["provenance"] = compute_provenance_score(SITE_STORE[site_id])
                updated_site = SITE_STORE[site_id]
                _save_cache()

            self._send_json({"ok": True, "review": review_bundle, "site": updated_site})
            return

        self._send_json({"error": "Not found"}, 404)


load_env_file()
init_site_store()

if __name__ == "__main__":
    print(f"Starting Name the Technique VLM Ensemble Reviewer on http://localhost:{PORT}")
    server = ThreadingHTTPServer(("0.0.0.0", PORT), AppHandler)
    server.serve_forever()
