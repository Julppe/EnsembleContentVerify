#!/usr/bin/env python3
"""
Gemma 4 31B VL — Lightweight Open-Weight Parallel Ensemble Probe
=================================================================
Demonstrates why compact open-weight Gemma 4 31B VL makes CheckEm's 5-model
cross-family ensemble practical: runs all configured jurors in parallel on a
sample passage and reports per-model wall-clock latency alongside votes.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import time
import requests

APP_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ENV_PATH = os.path.join(APP_ROOT, ".env")

JURY = [
    ("gemma-4-31b", "Gemma 4 31B VL (Google Open-Weights)"),
    ("nemotron-3.5-super-vl", "Nemotron 3.5 Super VL (NVIDIA Managed API)"),
    ("gemini-3.1-flash-lite", "Gemini 3.1 Flash Lite VL (Google)"),
    ("kimi-k2.6", "Kimi K2.6 VL (MoonshotAI)"),
    ("claude-haiku-4.5", "Claude Haiku 4.5 VL (Anthropic)"),
]


def _load_env_map() -> dict[str, str]:
    vals: dict[str, str] = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                raw = line.strip()
                if not raw or raw.startswith("#") or "=" not in raw:
                    continue
                k, v = raw.split("=", 1)
                if v.strip():
                    vals[k.strip()] = v.strip().strip('"').strip("'")
    for k in (
        "HOSTINGER_AI_ROUTER_BASE_URL",
        "HOSTINGER_AI_ROUTER_KEY",
        "VERDA_INFERENCE_KEY",
        "NEMOTRON_INFERENCE_BASE_URL",
        "NEMOTRON_INFERENCE_MODEL",
    ):
        if os.environ.get(k):
            vals[k] = os.environ[k].strip()
    return vals


def load_router_creds() -> tuple[str, str]:
    env = _load_env_map()
    base_url = env.get("HOSTINGER_AI_ROUTER_BASE_URL", "https://router.hostinger.com/v1")
    api_key = env.get("HOSTINGER_AI_ROUTER_KEY", "")
    return base_url.rstrip("/"), api_key


def probe_juror(base_url: str, api_key: str, model_id: str, label: str, text: str) -> dict:
    t0 = time.time()
    endpoint_url = base_url.rstrip("/")
    auth_key = api_key
    wire_model = model_id
    if model_id == "nemotron-3.5-super-vl":
        env = _load_env_map()
        verda_key = env.get("VERDA_INFERENCE_KEY", "")
        if verda_key:
            endpoint_url = env.get(
                "NEMOTRON_INFERENCE_BASE_URL",
                "https://containers.datacrunch.io/nemotron-3-5-super-vl-b300/v1",
            ).rstrip("/")
            auth_key = verda_key
            wire_model = env.get("NEMOTRON_INFERENCE_MODEL", "nemotron-3.5-super-vl")
        else:
            wire_model = "nemotron-lightning-3.5-30b-a3b"

    prompt = (
        "Classify propaganda techniques (Loaded Language, Fear Appeal, Whataboutism, "
        "Fabricated Authority, False Dilemma, Scapegoating / Ad Hominem). "
        f'Return compact JSON: {{"vote": "questionable"|"clean", "techniques": [...], "reason": "1 sentence"}}\n\nText: {text}'
    )
    resp = requests.post(
        f"{endpoint_url}/chat/completions",
        headers={"Authorization": f"Bearer {auth_key}", "Content-Type": "application/json", "User-Agent": "CheckEm/1.0"},
        json={
            "model": wire_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 2500,
        },
        timeout=60,
    )
    elapsed = round(time.time() - t0, 2)
    resp.raise_for_status()
    msg = resp.json()["choices"][0]["message"]
    content = (msg.get("content") or msg.get("reasoning_content") or msg.get("reasoning") or "").strip()
    return {"model": label, "model_id": model_id, "wire_model": wire_model, "latency_s": elapsed, "response": content}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--text",
        default="Anonymous insiders confirm that refusing this emergency bill will collapse the grid overnight.",
    )
    args = parser.parse_args()

    base_url, api_key = load_router_creds()
    if not api_key:
        raise RuntimeError("HOSTINGER_AI_ROUTER_KEY not found in environment or .env")

    t_wall = time.time()
    results = []
    with ThreadPoolExecutor(max_workers=len(JURY)) as pool:
        futs = [pool.submit(probe_juror, base_url, api_key, mid, lbl, args.text) for mid, lbl in JURY]
        for fut in as_completed(futs):
            results.append(fut.result())
    print(json.dumps({"wall_clock_s": round(time.time() - t_wall, 2), "jurors": results}, indent=2))


if __name__ == "__main__":
    main()
