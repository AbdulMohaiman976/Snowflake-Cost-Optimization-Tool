# api/storage.py
# Local JSON storage with proper multi-tenant isolation.
# Each (account_name + username) = separate session document.

import os, json, uuid, logging, threading
from datetime import datetime, timezone

log = logging.getLogger("storage")

DB_DIR  = os.path.join(os.path.dirname(__file__), "..", "local_db")
os.makedirs(DB_DIR, exist_ok=True)
DB_FILE = os.path.join(DB_DIR, "sessions.json")

db_lock = threading.Lock()

# ── Internal helpers ───────────────────────────────────────────────

def _read():
    if not os.path.exists(DB_FILE):
        return {"sessions": {}}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log.error(f"DB read error: {e}")
        return {"sessions": {}}

def _write(data: dict):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


# ══════════════════════════════════════════════════════════════════
# SAVE SESSION
# One document per (account_name + username).
# Each connect() call appends a new run → automatic history.
# Returns the raw_id (UUID) for this tenant.
# ══════════════════════════════════════════════════════════════════

def save_session(account_name: str, username: str, analysis: dict) -> str:
    with db_lock:
        db = _read()

        # Find existing session for this tenant (account + user)
        raw_id = None
        for sid, doc in db["sessions"].items():
            if (doc.get("account_name", "").upper() == account_name.upper() and
                    doc.get("username", "").upper() == username.upper()):
                raw_id = sid
                break

        # First time this tenant connects → create new document
        if not raw_id:
            raw_id = str(uuid.uuid4())
            db["sessions"][raw_id] = {
                "_id":          raw_id,
                "account_name": account_name,
                "username":     username,
                "created_at":   datetime.now(timezone.utc).isoformat(),
                "runs":         [],
            }
            log.info(f"New tenant: {account_name}/{username} → {raw_id[:8]}")

        # Append this run
        run_entry = {
            "analyzed_at":      datetime.now(timezone.utc).isoformat(),
            "ai_recommendations": {},   # filled later by background worker
            **analysis,
        }
        db["sessions"][raw_id]["runs"].append(run_entry)
        _write(db)
        log.info(f"Run saved: {raw_id[:8]} | {account_name}/{username} | run #{len(db['sessions'][raw_id]['runs'])}")

    return raw_id


# ══════════════════════════════════════════════════════════════════
# GET LATEST RUN
# ══════════════════════════════════════════════════════════════════

def get_latest_run(raw_id: str) -> dict | None:
    with db_lock:
        db  = _read()
        doc = db["sessions"].get(raw_id)
        if not doc or not doc.get("runs"):
            return None
        return doc["runs"][-1]   # newest run


# ══════════════════════════════════════════════════════════════════
# GET HISTORY
# Returns dict compatible with HistoryResponse model
# ══════════════════════════════════════════════════════════════════

def get_history(raw_id: str) -> dict | None:
    with db_lock:
        db  = _read()
        doc = db["sessions"].get(raw_id)
        if not doc:
            return None

        runs_summary = []
        for run in doc.get("runs", []):
            runs_summary.append({
                "analyzed_at":   run.get("analyzed_at", ""),
                "health_score":  run.get("health", {}).get("overall", 0),
                "health_grade":  run.get("health", {}).get("grade", "—"),
                "grade":         run.get("health", {}).get("grade", "—"),
                "total_cost_usd":run.get("cost", {}).get("total_cost_usd", 0),
                "anomaly_count": run.get("anomaly", {}).get("anomaly_count", 0),
            })

        return {
            "account_name": doc.get("account_name", ""),
            "username":     doc.get("username", ""),
            "created_at":   doc.get("created_at", ""),
            "run_count":    len(runs_summary),
            "runs":         runs_summary,
        }


# ══════════════════════════════════════════════════════════════════
# DELETE SESSION
# ══════════════════════════════════════════════════════════════════

def delete_session(raw_id: str) -> bool:
    with db_lock:
        db = _read()
        if raw_id in db["sessions"]:
            del db["sessions"][raw_id]
            _write(db)
            log.info(f"Session deleted: {raw_id[:8]}")
            return True
        return False


# ══════════════════════════════════════════════════════════════════
# UPDATE AI RECOMMENDATION (called by background worker)
# ══════════════════════════════════════════════════════════════════

def update_ai_recommendation(raw_id: str, module_key: str, recommendation: str):
    """Update AI insight for a module on the latest run.

    `recommendation` may be:
      - str (legacy markdown)
      - dict (new layered structure)
    """
    with db_lock:
        db  = _read()
        doc = db["sessions"].get(raw_id)
        if doc and doc.get("runs"):
            latest = doc["runs"][-1]
            if "ai_recommendations" not in latest:
                latest["ai_recommendations"] = {}
            current = latest["ai_recommendations"].get(module_key)
            if isinstance(current, dict) and isinstance(recommendation, dict):
                merged = {**current, **recommendation}
                # Merge one more level for layer dicts when present
                for k in ("layer1", "layer2", "layer3", "layer4"):
                    if isinstance(current.get(k), dict) and isinstance(recommendation.get(k), dict):
                        merged[k] = {**current[k], **recommendation[k]}
                latest["ai_recommendations"][module_key] = merged
            else:
                latest["ai_recommendations"][module_key] = recommendation
            _write(db)
            log.info(f"AI rec saved: {raw_id[:8]} / {module_key}")


def update_ai_recommendations_bulk(raw_id: str, updates: dict):
    """Bulk update multiple modules' AI insights in a single DB write."""
    if not isinstance(updates, dict) or not updates:
        return
    with db_lock:
        db = _read()
        doc = db["sessions"].get(raw_id)
        if not doc or not doc.get("runs"):
            return
        latest = doc["runs"][-1]
        if "ai_recommendations" not in latest or not isinstance(latest["ai_recommendations"], dict):
            latest["ai_recommendations"] = {}
        for module_key, patch in updates.items():
            current = latest["ai_recommendations"].get(module_key)
            if isinstance(current, dict) and isinstance(patch, dict):
                merged = {**current, **patch}
                for k in ("layer1", "layer2", "layer3", "layer4"):
                    if isinstance(current.get(k), dict) and isinstance(patch.get(k), dict):
                        merged[k] = {**current[k], **patch[k]}
                latest["ai_recommendations"][module_key] = merged
            else:
                latest["ai_recommendations"][module_key] = patch
        _write(db)
        log.info(f"AI recs bulk saved: {raw_id[:8]} / {len(updates)} module(s)")
