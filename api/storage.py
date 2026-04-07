# api/storage.py
# MongoDB storage with proper multi-tenant isolation.
# Each (account_name + username) = separate session document in Atlas.

import os, uuid, logging, json, certifi
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

log = logging.getLogger("storage")

# ── Storage Configuration ───────────────────────────────────────────────

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB  = os.getenv("MONGO_DB", "snowadvisor")

# ── MongoDB Initialization ───────────────────────────────────────────

client = None
db = None
sessions_col = None

try:
    # Simple connection attempt, relying on certifi for CA validation
    client = MongoClient(
        MONGO_URI, 
        serverSelectionTimeoutMS=5000, 
        tlsCAFile=certifi.where()
    )
    db = client[MONGO_DB]
    sessions_col = db["sessions"]
    # Check if we can actually reach the server
    client.server_info()
    sessions_col.create_index([("account_name", 1), ("username", 1)], background=True)
    log.info(f"MongoDB connected: {MONGO_DB}")
except Exception as e:
    log.error(f"FATAL: MongoDB connection failed ({e}). Exiting.")
    raise RuntimeError(f"MongoDB connection failed: {e}")



# ══════════════════════════════════════════════════════════════════
# SAVE SESSION
# One document per (account_name + username).
# Each connect() call appends a new run → automatic history.
# Returns the raw_id (UUID) for this tenant.
# ══════════════════════════════════════════════════════════════════

def save_session(account_name: str, username: str, analysis: dict) -> str:
    query = {
        "account_name": account_name.upper(),
        "username":     username.upper()
    }

    # 1. Look for existing tenant
    doc = sessions_col.find_one(query)

    if doc:
        raw_id = doc["_id"]
    else:
        # Create new tenant
        raw_id = str(uuid.uuid4())
        new_tenant = {
            "_id":          raw_id,
            "account_name": account_name.upper(),
            "username":     username.upper(),
            "created_at":   datetime.now(timezone.utc),
            "runs":         [],
        }
        sessions_col.insert_one(new_tenant)
        log.info(f"New MongoDB tenant: {account_name}/{username} → {raw_id[:8]}")

    # 2. Append this run to the tenant's list
    run_entry = {
        "analyzed_at":      datetime.now(timezone.utc),
        "ai_recommendations": {},
        **analysis,
    }

    sessions_col.update_one({"_id": raw_id}, {"$push": {"runs": run_entry}})
    log.info(f"Run saved to Atlas: {raw_id[:8]} | {account_name}/{username}")
    return raw_id


# ══════════════════════════════════════════════════════════════════
# GET LATEST RUN
# ══════════════════════════════════════════════════════════════════

def get_latest_run(raw_id: str) -> dict | None:
    doc = sessions_col.find_one({"_id": raw_id}, {"runs": {"$slice": -1}})
    if not doc or not doc.get("runs"):
        return None
    return doc["runs"][0]   # slice -1 returns a list with 1 element


# ══════════════════════════════════════════════════════════════════
# GET HISTORY
# ══════════════════════════════════════════════════════════════════

def get_history(raw_id: str) -> dict | None:
    doc = sessions_col.find_one({"_id": raw_id})
        
    if not doc:
        return None

    runs_summary = []
    for run in doc.get("runs", []):
        runs_summary.append({
            "analyzed_at":   run.get("analyzed_at", "").isoformat() if isinstance(run.get("analyzed_at"), datetime) else run.get("analyzed_at", ""),
            "health_score":  run.get("health", {}).get("overall", 0),
            "health_grade":  run.get("health", {}).get("grade", "—"),
            "total_cost_usd":run.get("cost", {}).get("total_cost_usd", 0),
            "anomaly_count": run.get("anomaly", {}).get("anomaly_count", 0),
        })

    return {
        "account_name": doc.get("account_name", ""),
        "username":     doc.get("username", ""),
        "created_at":   doc.get("created_at", "").isoformat() if isinstance(doc.get("created_at"), datetime) else doc.get("created_at", ""),
        "run_count":    len(runs_summary),
        "runs":         runs_summary,
    }


# ══════════════════════════════════════════════════════════════════
# DELETE SESSION
# ══════════════════════════════════════════════════════════════════

def delete_session(raw_id: str) -> bool:
    res = sessions_col.delete_one({"_id": raw_id})
    deleted = res.deleted_count > 0

    if deleted:
        log.info(f"Session deleted from Atlas: {raw_id[:8]}")
        return True
    return False


# ══════════════════════════════════════════════════════════════════
# UPDATE AI RECOMMENDATION
# ══════════════════════════════════════════════════════════════════

def update_ai_recommendation(raw_id: str, module_key: str, recommendation: dict):
    doc = sessions_col.find_one({"_id": raw_id}, {"runs": 1})
        
    if not doc or not doc.get("runs"):
        return

    last_idx = len(doc["runs"]) - 1
    
    if isinstance(recommendation, dict) and "layer4" in recommendation:
        field_path = f"runs.{last_idx}.ai_recommendations.{module_key}.layer4"
        val = recommendation["layer4"]
    else:
        field_path = f"runs.{last_idx}.ai_recommendations.{module_key}"
        val = recommendation
    
    update_op = {"$set": {field_path: val}}
    
    sessions_col.update_one({"_id": raw_id}, update_op)
    log.info(f"AI rec saved to Atlas: {raw_id[:8]} / {module_key}")


def update_ai_recommendations_bulk(raw_id: str, updates: dict):
    if not isinstance(updates, dict) or not updates:
        return
    
    doc = sessions_col.find_one({"_id": raw_id}, {"runs": 1})
        
    if not doc or not doc.get("runs"):
        return

    last_idx = len(doc["runs"]) - 1
    
    mongo_set = {}
    for module_key, patch in updates.items():
        if isinstance(patch, dict):
            for layer_key in ("layer1", "layer2", "layer3", "layer4"):
                if layer_key in patch:
                    mongo_set[f"runs.{last_idx}.ai_recommendations.{module_key}.{layer_key}"] = patch[layer_key]
            
            # If no layers found, update the whole module key
            layers = ("layer1", "layer2", "layer3", "layer4")
            if not any(lk in (patch[module_key] if module_key in patch else patch) for lk in layers):
                 mongo_set[f"runs.{last_idx}.ai_recommendations.{module_key}"] = patch
        else:
            mongo_set[f"runs.{last_idx}.ai_recommendations.{module_key}"] = patch

    if mongo_set:
        update_op = {"$set": mongo_set}
        sessions_col.update_one({"_id": raw_id}, update_op)
        log.info(f"AI recs bulk saved to Atlas: {raw_id[:8]} / {len(updates)} module(s)")
