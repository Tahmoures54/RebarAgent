# utils/ai_copy.py
"""Optional LLM rewrite of Copilot headlines. Offline default is a no-op."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def maybe_enrich_report(report: Any) -> None:
    """If REBARAGENT_AI_API_KEY is set, rewrite headline. Failures are silent."""
    key = os.environ.get("REBARAGENT_AI_API_KEY", "").strip()
    if not key or report is None:
        return
    base = os.environ.get("REBARAGENT_AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.environ.get("REBARAGENT_AI_MODEL", "gpt-4o-mini")
    prompt = (
        "One short sentence for a rebar detailer. Be concrete (kg, metres, next click). "
        f"Health {getattr(report, 'health_score', '')}/100. "
        f"Now: {getattr(report, 'headline', '')}. Tip: {getattr(report, 'top_tip', lambda: '')()}"
    )
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You write terse site-engineering coaching. No hype."},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 80,
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        text = text.strip()
        if text:
            report.headline = text[:280]
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, KeyError, TypeError):
        return
