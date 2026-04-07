# api/ai_service.py
# Layer 4: LLM Explanation (Optional)
#
# Layer 1-3 are generated locally (rule-based, statistical, forecasting) in api/ai_layers.py.
# This service only generates the optional plain-English explanation layer in the background.

from __future__ import annotations

import json
import logging
import os
import queue
import threading
import time
from typing import Any

import requests

from api.storage import update_ai_recommendation

log = logging.getLogger("ai_service")

# -----------------------------
# Config
# -----------------------------

AI_LLM_ENABLED = os.getenv("AI_LLM_ENABLED", "1").strip().lower() in ("1", "true", "yes", "on")
AI_LLM_MIN_INTERVAL_SEC = float(os.getenv("AI_LLM_MIN_INTERVAL_SEC", "4.5"))
AI_LLM_MAX_RETRIES = int(os.getenv("AI_LLM_MAX_RETRIES", "3"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_URL = os.getenv("GROQ_URL", "https://api.groq.com/openai/v1/chat/completions").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant").strip()

# Priority queue: (priority, timestamp, (raw_id, module_key, payload))
ai_queue: queue.PriorityQueue = queue.PriorityQueue()

_rate_lock = threading.Lock()
_last_llm_call_ts = 0.0


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _rate_limit_wait():
    """Global minimum-interval rate limiting to reduce 429 risk."""
    global _last_llm_call_ts
    with _rate_lock:
        now = time.time()
        wait = max(0.0, (_last_llm_call_ts + AI_LLM_MIN_INTERVAL_SEC) - now)
        if wait > 0:
            time.sleep(wait)
        _last_llm_call_ts = time.time()


def _truncate_json(obj: Any, limit: int) -> str:
    try:
        s = json.dumps(obj or {}, default=str, ensure_ascii=True)
    except Exception:
        s = "{}"
    return s[:limit]


def _build_layer4_prompt(module_key: str, tab_data: dict, base_insights: dict) -> str:
    """Build a per-tab prompt that does NOT mix data across tabs."""

    base_123 = {
        "layer1": (base_insights or {}).get("layer1", {}),
        "layer2": (base_insights or {}).get("layer2", {}),
        "layer3": (base_insights or {}).get("layer3", {}),
    }

    base_str = _truncate_json(base_123, 2500)
    tab_str = _truncate_json(tab_data, 2500)

    return f"""You are a Snowflake cost-optimization agent.

You are given data for ONE TAB only (module_key={module_key}). Do NOT reference or assume anything outside this tab.

Goal: Provide a single, plain-English, immediately implementable fix for this tab.

Constraints:
- If NO clear issues or risks are detected, simply state: "**No issues detected.** Your configuration is within healthy parameters." (Do not show Issue/Impact/Fix sections).
- If an issue is found:
  1) **Issue** (1 sentence summary)
  2) **Impact** (cost/perf/risk)
  3) **Fix** (numbered steps; MUST include ready-to-run SQL using real warehouse/table names; no placeholders)
- Do NOT invent Snowflake features.

Layer 1-3 (already computed):
{base_str}

Tab data (only this tab):
{tab_str}
"""


def _call_groq(prompt: str) -> tuple[str | None, str | None]:
    """Returns (text, error)."""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 600,
    }

    last_err = ""
    for attempt in range(1, AI_LLM_MAX_RETRIES + 1):
        _rate_limit_wait()
        try:
            resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=25)
        except Exception as e:
            last_err = f"request_error: {e}"
            time.sleep(min(10.0, attempt * 2.0))
            continue

        if resp.status_code == 200:
            try:
                text = resp.json()["choices"][0]["message"]["content"]
                return text, None
            except Exception as e:
                return None, f"parse_error: {e}"

        if resp.status_code == 429:
            retry_after = resp.headers.get("Retry-After")
            try:
                ra = float(retry_after) if retry_after else None
            except Exception:
                ra = None
            backoff = ra if ra is not None else min(60.0, (2.0**attempt) * 5.0)
            last_err = f"rate_limited_429: backoff {backoff:.1f}s (attempt {attempt}/{AI_LLM_MAX_RETRIES})"
            log.warning(f"Groq 429: {last_err}")
            time.sleep(backoff)
            continue

        last_err = f"http_{resp.status_code}: {resp.text[:200]}"
        time.sleep(min(10.0, attempt * 2.0))

    return None, last_err or "llm_call_failed"


def ai_worker():
    while True:
        priority = None
        module_key = "unknown"
        try:
            priority, _ts, job = ai_queue.get()
            raw_id, module_key, payload = job
            tab_data = (payload or {}).get("tab_data") or {}
            base_insights = (payload or {}).get("base_insights") or {}

            if not AI_LLM_ENABLED:
                update_ai_recommendation(
                    raw_id,
                    module_key,
                    {
                        "layer4": {
                            "enabled": False,
                            "status": "skipped",
                            "provider": "groq",
                            "model": None,
                            "recommendations_md": "",
                            "error": "",
                            "updated_at": _utc_now_iso(),
                        }
                    },
                )
                continue

            if not GROQ_API_KEY:
                update_ai_recommendation(
                    raw_id,
                    module_key,
                    {
                        "layer4": {
                            "enabled": True,
                            "status": "error",
                            "provider": "groq",
                            "model": GROQ_MODEL,
                            "recommendations_md": "",
                            "error": "GROQ_API_KEY is not set",
                            "updated_at": _utc_now_iso(),
                        }
                    },
                )
                continue

            prompt = _build_layer4_prompt(module_key, tab_data, base_insights)
            text, err = _call_groq(prompt)

            if text:
                update_ai_recommendation(
                    raw_id,
                    module_key,
                    {
                        "layer4": {
                            "enabled": True,
                            "status": "complete",
                            "provider": "groq",
                            "model": GROQ_MODEL,
                            "recommendations_md": text,
                            "error": "",
                            "updated_at": _utc_now_iso(),
                        }
                    },
                )
                log.info(f"AI Layer4 complete: session={raw_id[:8]} module={module_key} chars={len(text)}")
            else:
                update_ai_recommendation(
                    raw_id,
                    module_key,
                    {
                        "layer4": {
                            "enabled": True,
                            "status": "rate_limited" if (err or "").startswith("rate_limited_429") else "error",
                            "provider": "groq",
                            "model": GROQ_MODEL,
                            "recommendations_md": "",
                            "error": err or "llm_call_failed",
                            "updated_at": _utc_now_iso(),
                        }
                    },
                )

        except Exception as e:
            log.error(f"AI worker error (module={module_key}, priority={priority}): {e}", exc_info=True)

        finally:
            try:
                ai_queue.task_done()
            except Exception:
                pass
            time.sleep(0.25)


# Start background thread once on import
_worker_thread = threading.Thread(target=ai_worker, daemon=True)
_worker_thread.start()
log.info("AI worker thread started")


def queue_ai_generation(raw_id: str, module_key: str, data: dict, priority: int = 10):
    """Queue a Layer-4 generation job. `data` must be per-tab only."""
    ai_queue.put((priority, time.time(), (raw_id, module_key, data)))
    log.info(f"Queued AI job: {module_key} (priority={priority})")
