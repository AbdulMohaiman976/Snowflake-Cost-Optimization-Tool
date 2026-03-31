# api/main.py
# Run: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

import sys, os, logging, time, json
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

import backend
import analysis as analysis_module

from api.session  import generate_token, decrypt_session
from api.storage  import save_session, get_latest_run, get_history, delete_session
from api.models   import ConnectRequest, ConnectResponse, HistoryResponse, HealthResponse, AgentRequest, AgentResponse
from api.ai_layers import build_base_insights
from api.ai_service import queue_ai_generation, AI_LLM_ENABLED, _call_groq

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("main")

app = FastAPI(
    title="SnowAdvisor API",
    description="Snowflake Cost Intelligence — multi-tenant REST backend",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ══════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ══════════════════════════════════════════════════════════════════

@app.get("/health", response_model=HealthResponse, tags=["system"])
def health():
    return HealthResponse()


# ══════════════════════════════════════════════════════════════════
# POST /session/connect
# ══════════════════════════════════════════════════════════════════

@app.post("/session/connect", response_model=ConnectResponse, tags=["session"])
def connect(req: ConnectRequest):
    """
    1. Snowflake se connect karo
    2. ACCOUNT_USAGE data nikalo
    3. Full analysis chalaao
    4. MongoDB/local JSON mein save karo (account+user se isolated)
    5. Encrypted session_id + full results return karo
    6. Background mein Groq AI recommendations queue karo
    """
    log.info(f"Connect: account={req.account} user={req.username}")

    # ── Step 1: Snowflake pipeline ──────────────────────────────
    result = backend.run_full_pipeline(
        req.account, req.username, req.password, req.warehouse, req.role
    )
    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Snowflake connection failed"),
        )

    # ── Step 2: Analysis ────────────────────────────────────────
    ar = analysis_module.run_analysis(result["data"], result.get("account_info", {}))

    # Layer 1-3: deterministic per-tab insights (no data mixing)
    tab_queue_map = {
        "warehouse":      ar.get("warehouse", {}),
        "queries":        ar.get("queries", {}),
        "anomaly":        ar.get("anomaly", {}),
        "cost":           ar.get("cost", {}),
        "storage":        ar.get("storage", {}),
        "savings":        ar.get("savings", {}),
        "unused_objects": ar.get("unused_objects", {}),
        "cloud_services": ar.get("cloud_services", {}),
        "notebooks":      ar.get("notebooks", {}),
    }
    base_ai = {k: build_base_insights(k, v, llm_enabled=AI_LLM_ENABLED) for k, v in tab_queue_map.items()}

    # ── Step 3: Save to storage (returns raw_id for this tenant) ─
    account_info = result["account_info"]
    account_name = account_info.get("account", req.account)
    username     = account_info.get("user", req.username)

    raw_id = save_session(
        account_name=account_name,
        username=username,
        analysis={
            "account_info":   account_info,
            "health":         ar["health"],
            "warehouse":      ar["warehouse"],
            "queries":        ar["queries"],
            "anomaly":        ar["anomaly"],
            "cost":           ar["cost"],
            "storage":        ar["storage"],
            "savings":        ar["savings"],
            "unused_objects": ar["unused_objects"],
            "cloud_services": ar["cloud_services"],
            "notebooks":      ar["notebooks"],
            "auto_suspend":   ar["auto_suspend"],
            "ai_json":        ar["ai_json"],
            "ai_recommendations": base_ai,
        },
    )

    # ── Step 4: Encrypt raw_id → session token ───────────────────
    token = generate_token(raw_id)

    # Step 5: Queue Layer 4 (LLM explanation) jobs per tab (optional)
    def _priority_for(insights: dict) -> int:
        alerts = ((insights.get("layer1") or {}).get("alerts") or [])
        severities = {a.get("severity", "LOW") for a in alerts}
        if "HIGH" in severities:
            return 1
        if "MEDIUM" in severities:
            return 5
        return 10

    for module_key, tab_data in tab_queue_map.items():
        if base_ai.get(module_key, {}).get("layer4", {}).get("status") == "pending":
            queue_ai_generation(
                raw_id,
                module_key,
                {"tab_data": tab_data, "base_insights": base_ai.get(module_key, {})},
                priority=_priority_for(base_ai.get(module_key, {})),
            )

    # ── Step 6: Return ───────────────────────────────────────────
    return ConnectResponse(
        session_id=token,
        account_info=account_info,
        analyzed_at=datetime.now(timezone.utc).isoformat(),
        health=ar["health"],
        warehouse=ar["warehouse"],
        queries=ar["queries"],
        anomaly=ar["anomaly"],
        cost=ar["cost"],
        storage=ar["storage"],
        savings=ar["savings"],
        unused_objects=ar["unused_objects"],
        cloud_services=ar["cloud_services"],
        notebooks=ar.get("notebooks", {}),
        auto_suspend=ar.get("auto_suspend", {}),
        ai_json=ar.get("ai_json", {}),
        ai_recommendations=base_ai,   # Layer 1-3 ready instantly; Layer 4 optional
    )


# ══════════════════════════════════════════════════════════════════
# GET /session/{token}
# ══════════════════════════════════════════════════════════════════

@app.get("/session/{token}", tags=["session"])
def get_session(token: str):
    """Latest analysis run for this session (includes AI recommendations when ready)."""
    try:
        raw_id = decrypt_session(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    run = get_latest_run(raw_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"session_id": token, **run}


# ══════════════════════════════════════════════════════════════════
# GET /session/{token}/ai
# Returns only the AI recommendations (for polling)
# ══════════════════════════════════════════════════════════════════

@app.get("/session/{token}/ai", tags=["session"])
def get_ai_recommendations(token: str):
    """Poll this endpoint to check if AI recommendations are ready."""
    try:
        raw_id = decrypt_session(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    run = get_latest_run(raw_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Session not found")

    ai_recs = run.get("ai_recommendations", {}) or {}
    total_modules = len(ai_recs) if isinstance(ai_recs, dict) and ai_recs else 10

    def _layer4_done(v) -> bool:
        # Legacy string => done
        if not isinstance(v, dict):
            return bool(v)
        st = ((v.get("layer4") or {}).get("status") or "").lower()
        return st in ("complete", "skipped", "error", "rate_limited")

    done_modules = len([v for v in (ai_recs.values() if isinstance(ai_recs, dict) else []) if _layer4_done(v)])

    return {
        "session_id":       token,
        "ai_recommendations": ai_recs,
        "status":           "complete" if done_modules >= total_modules else "generating",
        "done":             done_modules,
        "total":            total_modules,
        "pct":              round(done_modules / total_modules * 100),
    }


# ─────────────────────────────────────────────────────────────
# AGENT (LangGraph-inspired single-path flow)
# ─────────────────────────────────────────────────────────────

def _build_agent_prompt(tab: str, tab_data: dict, ai_rec: dict, mode: str) -> str:
    tab_str = json.dumps(tab_data or {}, default=str)[:2500]
    ai_str  = json.dumps(ai_rec or {}, default=str)[:1200]
    mode_desc = "Take action automatically (but only return the SQL, do not execute)" if mode == "auto" else "Return a clear, ordered list of steps to fix the issue."
    return f"""You are a Snowflake cost-optimization agent working on one dashboard tab: {tab}.
Data for this tab (only): {tab_str}
Existing insights for this tab: {ai_str}
User mode: {mode_desc}

Requirements:
- If there are anomalies or warnings, identify the top cost driver and fix it.
- Output concise markdown only. Format:
  **Issue**: <1 sentence>
  **Impact**: <cost/perf risk>
  **Plan**: numbered steps with ready-to-run SQL. Use actual warehouses/tables from the data when present. No placeholders.
- If action needs approval, prefix the step with [APPROVAL] and explain risk briefly.
- If no clear issue, give two preventative optimizations tied to the tab data.
- Do NOT invent Snowflake features (e.g., statistical detection toggle). Stay within warehouse/query/storage controls and resource monitors."""


@app.post("/agent/{tab}", response_model=AgentResponse, tags=["agent"])
def run_agent(tab: str, req: AgentRequest):
    t0 = time.time()
    try:
        raw_id = decrypt_session(req.token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    run = get_latest_run(raw_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Session not found")

    tab_data = run.get(tab)
    if tab_data is None:
        raise HTTPException(status_code=404, detail=f"Tab '{tab}' not found in session")

    ai_rec = (run.get("ai_recommendations") or {}).get(tab, {})

    prompt = _build_agent_prompt(tab, tab_data, ai_rec, req.mode)
    text, err = _call_groq(prompt)
    if err:
        raise HTTPException(status_code=502, detail=f"Agent LLM error: {err}")

    return AgentResponse(status="ok", plan=text, took_ms=int((time.time() - t0) * 1000))


# ══════════════════════════════════════════════════════════════════
# GET /session/{token}/history
# ══════════════════════════════════════════════════════════════════

@app.get("/session/{token}/history", response_model=HistoryResponse, tags=["session"])
def get_session_history(token: str):
    """All historical runs for this session (health score trend)."""
    try:
        raw_id = decrypt_session(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    hist = get_history(raw_id)
    if hist is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return HistoryResponse(
        session_id=token,
        account=hist["account_name"],
        runs=hist["runs"],
    )


# ══════════════════════════════════════════════════════════════════
# DELETE /session/{token}
# ══════════════════════════════════════════════════════════════════

@app.delete("/session/{token}", tags=["session"])
def remove_session(token: str):
    """Delete all data for this session (GDPR / logout)."""
    try:
        raw_id = decrypt_session(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid or expired session token")

    deleted = delete_session(raw_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return {"message": "Session deleted successfully"}
