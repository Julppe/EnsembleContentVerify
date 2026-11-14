#!/usr/bin/env python3
"""
Standalone Nemotron 3.5 VL Logical Fallacy & Visual Integrity Runner
====================================================================
Calls either a self-hosted Verda Cloud GPU vLLM endpoint (`VERDA_GPU_BASE_URL`)
or Hostinger AI Router (`HOSTINGER_AI_ROUTER_BASE_URL`) using the Nemotron 3.5
configuration defined for CheckEm.
"""

import argparse
import base64
import json
import os
import requests


def encode_image_uri(path: str) -> str:
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "png"
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode('ascii')}"


def analyze_with_nemotron(title: str, text: str, image_path: str | None = None) -> dict:
    base_url = (os.environ.get("VERDA_GPU_BASE_URL") or os.environ.get("HOSTINGER_AI_ROUTER_BASE_URL") or "https://router.hostinger.com/v1").rstrip("/")
    api_key = os.environ.get("VERDA_API_KEY") or os.environ.get("HOSTINGER_AI_ROUTER_KEY")
    model_id = os.environ.get("VERDA_NEMOTRON_MODEL") or "nemotron-lightning-3.5-30b-a3b"

    if not api_key:
        raise RuntimeError("Set HOSTINGER_AI_ROUTER_KEY or VERDA_API_KEY in environment.")

    prompt = (
        "Act as CheckEm's Logical Fallacy & Visual Integrity Juror (Nemotron 3.5 VL). "
        "Classify any manipulation techniques (Whataboutism, False Dilemma, Fabricated Authority, "
        "Loaded Language, Fear Appeal, AI-Generated / Synthetic Image) and explain concisely.\n\n"
        f"Title: {title}\nText Section:\n{text}\n\n"
        'Return JSON: {"vote": "questionable"|"clean", "techniques": [...], "trigger_quote": "...", "reason": "..."}'
    )

    content = prompt if not image_path else [
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": encode_image_uri(image_path)}},
    ]

    resp = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={
            "model": model_id,
            "messages": [
                {"role": "system", "content": "Respond strictly in valid JSON."},
                {"role": "user", "content": content},
            ],
            "temperature": 0.1,
            "max_tokens": 2048,
        },
        timeout=60,
    )
    resp.raise_for_status()
    msg = resp.json()["choices"][0]["message"]
    return {
        "model": model_id,
        "endpoint": base_url,
        "reasoning_trace": msg.get("reasoning"),
        "content": msg.get("content"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", default="Sample Section")
    parser.add_argument("--text", required=True)
    parser.add_argument("--image", default=None)
    args = parser.parse_args()
    print(json.dumps(analyze_with_nemotron(args.title, args.text, args.image), indent=2))
