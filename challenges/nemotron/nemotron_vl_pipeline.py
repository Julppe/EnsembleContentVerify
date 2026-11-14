#!/usr/bin/env python3
"""
Standalone Nemotron 3.5 Super VL Logical Fallacy & Visual Integrity Runner
==========================================================================
Prefers the managed Nemotron 3.5 Super VL B300 endpoint
(`https://containers.datacrunch.io/nemotron-3-5-super-vl-b300/v1`, model
`nemotron-3.5-super-vl`) using `VERDA_INFERENCE_KEY`, falling back to NVIDIA
Build (`NVIDIA_API_KEY`) or Hostinger AI Router (`HOSTINGER_AI_ROUTER_KEY`).
"""

import argparse
import base64
import json
import os
import random
import time
import requests

APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(APP_ROOT, ".env")
NEMOTRON_B300_BASE_URL = "https://containers.datacrunch.io/nemotron-3-5-super-vl-b300/v1"
NVIDIA_BUILD_BASE_URL = "https://integrate.api.nvidia.com/v1"


def _load_env_defaults():
    if not os.path.exists(ENV_PATH):
        return
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#"):
                continue
            if raw.startswith("nvapi-") and not os.environ.get("NVIDIA_API_KEY"):
                os.environ["NVIDIA_API_KEY"] = raw
                continue
            if "=" in raw:
                k, v = raw.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if v and not os.environ.get(k):
                    os.environ[k] = v


def encode_image_uri(path: str) -> str:
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "png"
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode('ascii')}"


def post_with_backoff(url: str, headers: dict, payload: dict, timeout: int = 75, max_retries: int = 3) -> requests.Response:
    for attempt in range(max_retries + 1):
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code not in (429, 500, 502, 503, 504) or attempt == max_retries:
            return resp
        retry_after = resp.headers.get("Retry-After", "").strip()
        delay = float(retry_after) if retry_after.isdigit() else 1.5 * (2 ** attempt)
        time.sleep(min(15.0, delay + random.uniform(0.1, 0.5)))
    return resp


def analyze_with_nemotron(title: str, text: str, image_path: str | None = None) -> dict:
    _load_env_defaults()
    b300_key = os.environ.get("VERDA_INFERENCE_KEY", "").strip()
    nv_key = (
        os.environ.get("NVIDIA_API_KEY")
        or os.environ.get("NEMOTRON_API_KEY")
        or os.environ.get("NGC_API_KEY")
        or ""
    ).strip()

    if b300_key:
        base_url = os.environ.get("NEMOTRON_INFERENCE_BASE_URL", NEMOTRON_B300_BASE_URL).rstrip("/")
        api_key = b300_key
        model_id = os.environ.get("NEMOTRON_INFERENCE_MODEL", "nemotron-3.5-super-vl")
        provider = "Nemotron 3.5 Super VL B300 API"
    elif nv_key:
        base_url = os.environ.get("NVIDIA_API_BASE_URL", NVIDIA_BUILD_BASE_URL).rstrip("/")
        api_key = nv_key
        model_id = os.environ.get("NVIDIA_NEMOTRON_MODEL", "nvidia/nemotron-3.5-super-vl-120b-a12b")
        provider = "NVIDIA Build API"
    else:
        base_url = os.environ.get("HOSTINGER_AI_ROUTER_BASE_URL", "https://router.hostinger.com/v1").rstrip("/")
        api_key = os.environ.get("HOSTINGER_AI_ROUTER_KEY", "")
        model_id = "nemotron-lightning-3.5-30b-a3b"
        provider = "Hostinger AI Router (fallback)"

    if not api_key:
        raise RuntimeError("Set VERDA_INFERENCE_KEY, NVIDIA_API_KEY, or HOSTINGER_AI_ROUTER_KEY.")

    prompt = (
        "Act as CheckEm's Logical Fallacy & Visual Integrity Juror (Nemotron 3.5 Super VL). "
        "Classify any manipulation techniques (Whataboutism, False Dilemma, Fabricated Authority, "
        "Loaded Language, Fear Appeal, AI-Generated / Synthetic Image) and explain concisely.\n\n"
        f"Title: {title}\nText Section:\n{text}\n\n"
        'Return JSON: {"vote": "questionable"|"clean", "techniques": [...], "trigger_quote": "...", "reason": "..."}'
    )

    content = prompt if not image_path else [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": encode_image_uri(image_path)}},
    ]

    resp = post_with_backoff(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        payload={
            "model": model_id,
            "messages": [
                {"role": "system", "content": "Respond strictly in valid JSON."},
                {"role": "user", "content": content},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
        },
        timeout=75,
    )
    resp.raise_for_status()
    msg = resp.json()["choices"][0]["message"]
    return {
        "provider": provider,
        "model": model_id,
        "endpoint": base_url,
        "reasoning_trace": msg.get("reasoning_content") or msg.get("reasoning"),
        "content": msg.get("content"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="Sample Section")
    parser.add_argument("--text", required=True)
    parser.add_argument("--image", default=None)
    args = parser.parse_args()
    print(json.dumps(analyze_with_nemotron(args.title, args.text, args.image), indent=2))
