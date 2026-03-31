# dashboard.py  —  SnowAdvisor Business Intelligence Dashboard
# Run:  streamlit run dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json

import backend  # kept for fallback only — primary flow uses FastAPI
import analysis  # kept for fallback only
import requests as _req

# ─────────────────────────────────────────────────────────────────
# API CONFIG  — FastAPI backend URL
# ─────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000"   # change to production URL when deployed

# ─────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SnowAdvisor",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# GLOBAL CSS  — Dark Business Theme
# ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

/* ── Base ─────────────────────────────────────────────────── */
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif !important; }
.main { background: #080e1a; }
.main .block-container { padding: 1.5rem 2rem 3rem; max-width: 1400px; }
section[data-testid="stSidebar"] { background: #060b14 !important; border-right: 1px solid #1a2740; }

/* ── Hide defaults ────────────────────────────────────────── */
#MainMenu, header, footer, .stDeployButton { display: none !important; }

/* ── Sidebar inputs ───────────────────────────────────────── */
section[data-testid="stSidebar"] label { color: #7a8fa8 !important; font-size: 0.72rem !important; font-weight: 600 !important; letter-spacing: 0.08em; text-transform: uppercase; }
section[data-testid="stSidebar"] input { background: #0f1a2e !important; border: 1px solid #1e3050 !important; color: #e2eaf5 !important; border-radius: 8px !important; font-size: 0.85rem !important; }
section[data-testid="stSidebar"] input:focus { border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.15) !important; }
section[data-testid="stSidebar"] .stButton button { background: linear-gradient(135deg,#1d4ed8,#2563eb) !important; color: #fff !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; font-size: 0.88rem !important; padding: 0.6rem 1.2rem !important; width: 100% !important; transition: all 0.2s; }
section[data-testid="stSidebar"] .stButton button:hover { background: linear-gradient(135deg,#1e40af,#1d4ed8) !important; transform: translateY(-1px); box-shadow: 0 4px 16px rgba(37,99,235,0.4) !important; }
section[data-testid="stSidebar"] * { color: #c8d6e8 !important; }

/* ── Metric cards ─────────────────────────────────────────── */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg,#0d1829,#0f1e33);
    border: 1px solid #1a2e4a;
    border-radius: 14px;
    padding: 1.1rem 1.3rem;
    position: relative; overflow: hidden;
}
div[data-testid="metric-container"]::before {
    content: ""; position: absolute; top: 0; left: 0;
    right: 0; height: 2px;
    background: linear-gradient(90deg,#2563eb,#7c3aed);
}
div[data-testid="metric-container"] label { color: #4d7aaa !important; font-size: 0.68rem !important; font-weight: 700 !important; text-transform: uppercase; letter-spacing: 0.1em; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #e8f0fa !important; font-size: 1.9rem !important; font-weight: 700 !important; font-family: 'DM Mono', monospace !important; }
div[data-testid="metric-container"] div[data-testid="stMetricDelta"] { font-size: 0.75rem !important; }

/* ── Tabs ─────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] { background: #0b1220; border-radius: 12px; padding: 4px; gap: 2px; border: 1px solid #1a2e4a; }
.stTabs [data-baseweb="tab"] { border-radius: 9px !important; color: #4d6a8a !important; font-weight: 500 !important; font-size: 0.82rem !important; padding: 0.45rem 0.9rem !important; transition: all 0.2s; }
.stTabs [aria-selected="true"] { background: linear-gradient(135deg,#1d4ed8,#2563eb) !important; color: #fff !important; font-weight: 600 !important; box-shadow: 0 2px 12px rgba(37,99,235,0.35) !important; }

/* ── Dataframe ────────────────────────────────────────────── */
.stDataFrame { background: transparent !important; }
.stDataFrame [data-testid="stDataFrameResizable"] { border: 1px solid #1a2e4a !important; border-radius: 12px !important; overflow: hidden; }
iframe { background: #080e1a !important; }

/* ── Expander ─────────────────────────────────────────────── */
details { background: #0b1220 !important; border: 1px solid #1a2e4a !important; border-radius: 12px !important; padding: 0.3rem 0.8rem !important; }
details summary { color: #7a9cc0 !important; font-size: 0.85rem !important; font-weight: 600 !important; }

/* ── Selectbox ────────────────────────────────────────────── */
.stSelectbox select, div[data-baseweb="select"] { background: #0f1a2e !important; border-color: #1a2e4a !important; color: #c8d6e8 !important; }

/* ── Download button ──────────────────────────────────────── */
.stDownloadButton button { background: linear-gradient(135deg,#059669,#10b981) !important; color: #fff !important; border: none !important; border-radius: 10px !important; font-weight: 600 !important; }

/* ── Alert / info boxes ───────────────────────────────────── */
.stAlert { background: #0b1220 !important; border-radius: 10px !important; }

/* ── Custom cards ─────────────────────────────────────────── */
.sa-card {
    background: linear-gradient(135deg,#0d1829,#0f1e33);
    border: 1px solid #1a2e4a;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.6rem;
}
.sa-rec-high   { border-left: 4px solid #ef4444 !important; background: linear-gradient(90deg,#1a0808,#0d1829) !important; }
.sa-rec-medium { border-left: 4px solid #f59e0b !important; background: linear-gradient(90deg,#1a1008,#0d1829) !important; }
.sa-rec-low    { border-left: 4px solid #10b981 !important; background: linear-gradient(90deg,#081a10,#0d1829) !important; }
.sa-title  { font-size: 0.88rem; font-weight: 600; color: #c8daf0; margin: 0 0 0.3rem; }
.sa-detail { font-size: 0.78rem; color: #5a7a9a; line-height: 1.5; }
.sa-label  { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 0.68rem; font-weight: 700; letter-spacing: 0.06em; }
.sa-high   { background: #3b0a0a; color: #fca5a5; }
.sa-medium { background: #3b2008; color: #fcd34d; }
.sa-low    { background: #083b1a; color: #6ee7b7; }
.sa-ok     { background: #082838; color: #7dd3fc; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────────────────────────
for k, v in [("connected", False), ("result", None), ("ar", None),
               ("session_id", None), ("ai_recs", {}), ("agent_results", {})]:
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────
PLOTLY_DARK = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#7a9cc0", family="DM Sans"),
    margin=dict(l=0, r=0, t=32, b=0),
)

AXIS_STYLE = dict(showgrid=True, gridcolor="#0f1e33", showline=False, zeroline=False)

def sc(v):
    if v >= 75: return "#10b981"
    if v >= 50: return "#f59e0b"
    return "#ef4444"

def sg(v):
    if v >= 75: return "Good"
    if v >= 50: return "Fair"
    return "Poor"

def _ai_layer4_done(v) -> bool:
    if isinstance(v, dict):
        stt = ((v.get("layer4") or {}).get("status") or "").lower()
        return stt in ("complete", "skipped", "error", "rate_limited")
    return bool(v)


def render_ai_recs(module_key: str):
    """Render AI insights (LLM output only, no layer labels)."""
    ai_recs = st.session_state.get("ai_recs", {}) or {}
    rec = ai_recs.get(module_key)
    sid = st.session_state.get("session_id")

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("**AI Insights**")

    if isinstance(rec, dict):
        l4 = rec.get("layer4") or {}
        stt = (l4.get("status") or "").lower()
        if stt == "complete" and l4.get("recommendations_md"):
            st.markdown(l4.get("recommendations_md", ""))
        elif stt == "pending" and sid:
            col_info, col_btn = st.columns([4, 1])
            with col_info:
                st.markdown(
                    "<div style='background:#0b1220;border-left:4px solid #374151;border-radius:10px;padding:0.8rem 1rem;border:1px solid #1a2e4a;'>"
                    "<p style='color:#7a9cc0;font-size:0.8rem;margin:0;'>AI insights are generating...</p>"
                    "</div>",
                    unsafe_allow_html=True,
                )
            with col_btn:
                if st.button("🔄 Refresh", key=f"ai_refresh_{module_key}", use_container_width=True):
                    _poll_ai_recs()
                    st.rerun()
        elif stt in ("rate_limited", "error"):
            st.warning("AI insights not available right now. Please refresh.")
        else:
            body = l4 if l4 else rec
            if isinstance(body, str):
                st.markdown(body)
            elif isinstance(body, dict) and body.get("recommendations_md"):
                st.markdown(body["recommendations_md"])
            else:
                st.info("No AI insights yet for this tab.")
        return

    if isinstance(rec, str):
        st.markdown(rec)
        return

    if sid:
        col_info, col_btn = st.columns([4, 1])
        with col_info:
            st.markdown(
                "<div style='background:#0b1220;border-left:4px solid #374151;border-radius:10px;padding:0.8rem 1rem;border:1px solid #1a2e4a;'>"
                "<p style='color:#4d6a8a;font-size:0.8rem;margin:0;'>AI insights are not available yet. Click Refresh to check.</p>"
                "</div>",
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button("🔄 Refresh", key=f"ai_refresh_{module_key}", use_container_width=True):
                _poll_ai_recs()
                st.rerun()
    else:
        st.info("No AI insights yet for this tab.")


def render_agent_plan(tab_key: str):
    """Call the backend LangGraph agent and show its plan."""
    sid = st.session_state.get("session_id")
    if not sid:
        return

    res_key = f"agent_{tab_key}"
    if st.button("🤖 Generate agent plan", key=f"btn_{res_key}", use_container_width=True):
        try:
            resp = _req.post(f"{API_URL}/agent/{tab_key}",
                             json={"token": sid, "mode": "steps"},
                             timeout=40)
            if resp.status_code == 200:
                st.session_state["agent_results"][res_key] = resp.json()
            else:
                st.session_state["agent_results"][res_key] = {"status": "error", "plan": f"Error {resp.status_code}: {resp.text}"}
        except Exception as e:
            st.session_state["agent_results"][res_key] = {"status": "error", "plan": f"Request failed: {e}"}
        st.rerun()

    result = st.session_state.get("agent_results", {}).get(res_key)
    if result:
        if result.get("status") == "ok":
            st.markdown(result.get("plan", ""))
        else:
            st.warning(result.get("plan", "Agent error"))

def _poll_ai_recs():
    """FastAPI /ai endpoint se latest AI recommendations fetch karo."""
    sid = st.session_state.get("session_id")
    if not sid:
        return
    try:
        resp = _req.get(f"{API_URL}/session/{sid}/ai", timeout=8)
        if resp.status_code == 200:
            data = resp.json()
            st.session_state.ai_recs = data.get("ai_recommendations", {})
            done  = data.get("done", 0)
            total = data.get("total", 10)
            log_msg = f"AI recs: {done}/{total} ready"
            return done, total
    except Exception:
        pass
    return 0, 10

def show_recs(recs):
    if not recs:
        st.markdown('<div class="sa-card" style="border-left:4px solid #10b981;"><p class="sa-title">✅ No issues found in this area</p></div>', unsafe_allow_html=True)
        return
    for r in recs:
        sev = r.get("severity", "LOW")
        cls = {"HIGH": "sa-rec-high", "MEDIUM": "sa-rec-medium", "LOW": "sa-rec-low"}.get(sev, "sa-rec-low")
        lbl = {"HIGH": "sa-high", "MEDIUM": "sa-medium", "LOW": "sa-low"}.get(sev, "sa-low")
        ico = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(sev, "🟢")
        st.markdown(
            f'<div class="sa-card {cls}">'
            f'<p class="sa-title">{ico} {r.get("title","")}'
            f' &nbsp;<span class="sa-label {lbl}">{sev}</span></p>'
            f'<p class="sa-detail">{r.get("detail","")}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if r.get("fix_sql"):
            with st.expander("View Fix SQL"):
                st.code(r["fix_sql"], language="sql")

def mini_score(label, score):
    c = sc(score)
    return f"""<div style='background:#0b1220;border:1px solid #1a2e4a;border-radius:10px;
    padding:0.7rem 1rem;text-align:center;'>
    <div style='font-size:0.62rem;color:#4d6a8a;font-weight:700;text-transform:uppercase;
    letter-spacing:0.08em;margin-bottom:4px;'>{label}</div>
    <div style='font-size:1.6rem;font-weight:700;color:{c};font-family:"DM Mono",monospace;'>{score}</div>
    <div style='font-size:0.65rem;color:{c};margin-top:2px;'>{sg(score)}</div>
    </div>"""

# ─────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding:1.2rem 0 0.8rem;'>
      <div style='font-size:1.5rem;font-weight:800;color:#e8f0fa;letter-spacing:-0.02em;'>
        ❄️ SnowAdvisor
      </div>
      <div style='font-size:0.7rem;color:#2d5a8a;font-weight:600;text-transform:uppercase;
      letter-spacing:0.12em;margin-top:2px;'>Cost Intelligence Platform</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    if st.session_state.connected:
        info = st.session_state.result["account_info"]
        sid  = st.session_state.session_id or ""
        st.markdown(f"""
        <div style='background:#0a1628;border:1px solid #0d3060;border-radius:12px;
        padding:1rem;margin-bottom:1rem;'>
          <div style='font-size:0.62rem;color:#2d6aaa;font-weight:700;text-transform:uppercase;
          letter-spacing:0.1em;'>Connected Account</div>
          <div style='font-size:0.95rem;font-weight:700;color:#60a5fa;margin:4px 0;'>
          {info.get("account","")}</div>
          <div style='font-size:0.72rem;color:#4d7aaa;'>
          👤 {info.get("user","")} &nbsp;·&nbsp; 🔑 {info.get("role","")}</div>
        </div>
        """, unsafe_allow_html=True)

        # Show session ID (truncated) — user can copy to reload later
        if sid:
            with st.expander("🔑 Session ID (copy to reload)"):
                st.code(sid, language=None)
                st.caption("Paste this in 'Load Session' to reload without reconnecting.")

        if st.button("⬅ Disconnect", use_container_width=True):
            st.session_state.connected  = False
            st.session_state.result     = None
            st.session_state.ar         = None
            st.session_state.session_id = None
            st.rerun()

    else:
        # ── TABS: New Connection | Load Session ───────────────────
        tab_new, tab_load = st.tabs([
    'New Connection',
    'Load Session',
])

        # ── TAB 1: New Connection → FastAPI ──────────────────────
        with tab_new:
            st.markdown('<p style="font-size:0.75rem;color:#4d6a8a;margin:0 0 0.8rem;">Connect your Snowflake account to begin analysis.</p>', unsafe_allow_html=True)
            with st.form("sf_form"):
                account   = st.text_input("Account Identifier", placeholder="abc12345.us-east-1")
                username  = st.text_input("Username")
                password  = st.text_input("Password", type="password")
                with st.expander("Advanced Settings"):
                    warehouse = st.text_input("Warehouse", value="COMPUTE_WH")
                    role      = st.text_input("Role", value="ACCOUNTADMIN")
                submitted = st.form_submit_button("🔗 Connect & Analyze", use_container_width=True)

            if submitted:
                if not account or not username or not password:
                    st.error("All fields are required.")
                else:
                    # ── Check if FastAPI is running ───────────────
                    try:
                        ping = _req.get(f"{API_URL}/health", timeout=3)
                        api_ok = ping.status_code == 200
                    except Exception:
                        api_ok = False

                    if api_ok:
                        # ── PRIMARY FLOW: via FastAPI ─────────────
                        with st.spinner("🔗 Connecting via API..."):
                            try:
                                resp = _req.post(
                                    f"{API_URL}/session/connect",
                                    json={"account": account, "username": username,
                                          "password": password, "warehouse": warehouse,
                                          "role": role},
                                    timeout=120,
                                )
                                if resp.status_code == 200:
                                    data = resp.json()
                                    # Map API response → session state
                                    st.session_state.session_id = data["session_id"]
                                    st.session_state.result = {
                                        "account_info": data["account_info"],
                                        "filename":     f"API session · {data['analyzed_at'][:19]}",
                                        "filepath":     None,
                                    }
                                    st.session_state.ar = {
                                        "health":        data["health"],
                                        "warehouse":     data["warehouse"],
                                        "queries":       data["queries"],
                                        "anomaly":       data["anomaly"],
                                        "cost":          data["cost"],
                                        "storage":       data["storage"],
                                        "savings":       data["savings"],
                                        "auto_suspend":  data.get("auto_suspend", {}),
                                        "notebooks":     data.get("notebooks", {}),
                                        "unused_objects":data.get("unused_objects", {}),
                                        "cloud_services":data.get("cloud_services", {}),
                                        "ai_json":       data.get("ai_json", {}),
                                    }
                                    st.session_state.ai_recs   = data.get("ai_recommendations", {}) or {}
                                    st.session_state.connected = True
                                    st.rerun()
                                else:
                                    err = resp.json().get("detail", resp.text)
                                    st.error(f"API Error: {err}")
                                    if "IMPORTED PRIVILEGES" in str(err):
                                        st.code("GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE ACCOUNTADMIN;", language="sql")
                            except _req.exceptions.Timeout:
                                st.error("Analysis is taking longer than expected. Try again — Snowflake connection may be slow.")
                            except Exception as e:
                                st.error(f"API call failed: {e}")
                    else:
                        # ── FALLBACK FLOW: direct backend (no FastAPI) ──
                        st.warning("⚠️ FastAPI not running — using direct mode (data won't be saved to MongoDB)")
                        with st.spinner("Connecting to Snowflake directly..."):
                            r = backend.run_full_pipeline(account, username, password, warehouse, role)
                        if not r["success"]:
                            st.error(r["error"])
                            if r.get("account_info") and not r.get("access_ok"):
                                st.code("GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE ACCOUNTADMIN;", language="sql")
                        else:
                            with st.spinner("Running analysis..."):
                                ar = analysis.run_analysis(r["data"], r.get("account_info", {}))
                            st.session_state.result     = r
                            st.session_state.ar         = ar
                            st.session_state.session_id = None
                            st.session_state.connected  = True
                            st.rerun()

        # ── TAB 2: Load Existing Session ─────────────────────────
        with tab_load:
            st.markdown('<p style="font-size:0.75rem;color:#4d6a8a;margin:0 0 0.8rem;">Paste a previous session ID to reload your last analysis without reconnecting.</p>', unsafe_allow_html=True)
            prev_token = st.text_area("Session ID", height=80, placeholder="Paste your session_id token here...")
            if st.button("📂 Load Session", use_container_width=True):
                if not prev_token.strip():
                    st.error("Please paste a session ID.")
                else:
                    with st.spinner("Loading session from MongoDB..."):
                        try:
                            resp = _req.get(
                                f"{API_URL}/session/{prev_token.strip()}",
                                timeout=15,
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                st.session_state.session_id = prev_token.strip()
                                st.session_state.result = {
                                    "account_info": data.get("account_info", {}),
                                    "filename":     f"Loaded session · {data.get('analyzed_at','')[:19]}",
                                    "filepath":     None,
                                }
                                st.session_state.ar = {
                                    "health":        data.get("health", {}),
                                    "warehouse":     data.get("warehouse", {}),
                                    "queries":       data.get("queries", {}),
                                    "anomaly":       data.get("anomaly", {}),
                                    "cost":          data.get("cost", {}),
                                    "storage":       data.get("storage", {}),
                                    "savings":       data.get("savings", {}),
                                    "auto_suspend":  data.get("auto_suspend", {}),
                                    "notebooks":     data.get("notebooks", {}),
                                    "unused_objects":data.get("unused_objects", {}),
                                    "cloud_services":data.get("cloud_services", {}),
                                    "ai_json":       data.get("ai_json", {}),
                                }
                                st.session_state.ai_recs   = data.get("ai_recommendations", {}) or {}
                                st.session_state.connected = True
                                st.rerun()
                            elif resp.status_code == 401:
                                st.error("Invalid session token — it may have expired or been corrupted.")
                            elif resp.status_code == 404:
                                st.error("Session not found in database.")
                            else:
                                st.error(f"Error {resp.status_code}: {resp.text}")
                        except Exception as e:
                            st.error(f"Could not reach API: {e}")

    st.divider()
    # ── AI Refresh in sidebar (when connected via API) ───────────
    if st.session_state.connected and st.session_state.get("session_id"):
        st.divider()
        ai_recs  = st.session_state.get("ai_recs", {})
        done_cnt = len([v for v in ai_recs.values() if _ai_layer4_done(v)])
        st.markdown(f'<p style="font-size:0.7rem;color:#4d6a8a;text-align:center;">✨ LLM Explanations: {done_cnt}/{len(ai_recs) if ai_recs else 10} done</p>', unsafe_allow_html=True)
        if st.button("🔄 Refresh AI Insights", use_container_width=True):
            _poll_ai_recs()
            st.rerun()

    st.markdown('<p style="font-size:0.65rem;color:#1a3a5a;text-align:center;">Read-only · No changes made to Snowflake</p>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# LANDING PAGE
# ─────────────────────────────────────────────────────────────────
if not st.session_state.connected:
    st.markdown("""
    <div style='text-align:center;padding:4rem 1rem 2rem;'>
      <div style='font-size:3.5rem;margin-bottom:0.5rem;'>❄️</div>
      <h1 style='font-size:2.8rem;font-weight:800;color:#e8f0fa;letter-spacing:-0.03em;margin:0;'>
        SnowAdvisor</h1>
      <p style='font-size:1.05rem;color:#2d5a8a;margin:0.6rem 0 2.5rem;font-weight:400;'>
        Snowflake Cost Intelligence — Connect, Analyze, Optimize</p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    for col, ico, title, desc in [
        (c1, "🏭", "Warehouse Sizing", "Right-size every warehouse. Detect queue bottlenecks, memory spill, and idle waste."),
        (c2, "🔍", "Query Intelligence", "Find slow queries, poor pruning, and resource-heavy workloads by time and user."),
        (c3, "📈", "Spend Anomaly", "Catch unexpected credit spikes with 7-day rolling baseline comparison."),
        (c4, "🔐", "Security & Users", "MFA gaps, login failures, account lockouts, and inactive accounts."),
    ]:
        col.markdown(f"""
        <div class='sa-card' style='text-align:center;min-height:160px;'>
          <div style='font-size:2rem;margin-bottom:0.6rem;'>{ico}</div>
          <div style='font-size:0.88rem;font-weight:700;color:#c8daf0;margin-bottom:0.4rem;'>{title}</div>
          <div style='font-size:0.75rem;color:#3d6080;line-height:1.5;'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────
# MAIN DASHBOARD
# ─────────────────────────────────────────────────────────────────
ar      = st.session_state.ar
result  = st.session_state.result
health  = ar["health"]
info    = result["account_info"]

# ── Page header ────────────────────────────────────────────────
st.markdown(f"""
<div style='display:flex;align-items:center;justify-content:space-between;
margin-bottom:1.2rem;padding-bottom:1rem;border-bottom:1px solid #0f1e33;'>
  <div>
    <div style='font-size:1.45rem;font-weight:700;color:#e8f0fa;letter-spacing:-0.02em;'>
      Account Intelligence Report</div>
    <div style='font-size:0.75rem;color:#2d5a8a;margin-top:2px;'>
      <span style='color:#60a5fa;font-family:"DM Mono",monospace;'>{info.get("account","")}</span>
      &nbsp;·&nbsp; {info.get("user","")} &nbsp;·&nbsp; {info.get("role","")}
      &nbsp;·&nbsp; Analyzed {datetime.now().strftime("%b %d, %Y %H:%M")}
    </div>
  </div>
  <div style='font-size:0.7rem;color:#1a3a5a;background:#060b14;border:1px solid #0f1e33;
  border-radius:8px;padding:0.4rem 0.8rem;'>Read-only</div>
</div>
""", unsafe_allow_html=True)

# ── Health Score Row ────────────────────────────────────────────
hs = health["overall"]
hc = sc(hs)

col_big, col_dims = st.columns([1, 3], gap="large")

with col_big:
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#060b14,#0a1628);
    border:1px solid #1a2e4a;border-radius:18px;padding:2rem;text-align:center;
    position:relative;overflow:hidden;'>
      <div style='position:absolute;top:0;left:0;right:0;height:3px;
      background:linear-gradient(90deg,{hc},{hc}88);'></div>
      <div style='font-size:0.65rem;color:#2d5a8a;font-weight:700;text-transform:uppercase;
      letter-spacing:0.15em;margin-bottom:0.8rem;'>Account Health Score</div>
      <div style='font-size:5rem;font-weight:900;color:{hc};line-height:1;
      font-family:"DM Mono",monospace;'>{hs}</div>
      <div style='color:#1a3a5a;font-size:0.7rem;margin:4px 0 0.8rem;'>/100</div>
      <div style='display:inline-block;background:{hc}22;color:{hc};
      padding:4px 16px;border-radius:20px;font-size:0.78rem;font-weight:700;'>
      {health["grade"]}</div>
    </div>
    """, unsafe_allow_html=True)

with col_dims:
    dims = [
        ("Query Intelligence", health["scores"].get("query", 0)),
        ("Warehouse Health",   health["scores"].get("warehouse", 0)),
        ("Storage",            health["scores"].get("storage", 0)),
    ]
    d1, d2, d3 = st.columns(3)
    for col_d, (lbl, scr) in zip([d1, d2, d3], dims):
        col_d.markdown(mini_score(lbl, scr), unsafe_allow_html=True)

st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

# ── Issues Bar ──────────────────────────────────────────────────
all_recs = sum([
    ar["warehouse"]["recommendations"], ar["queries"]["recommendations"],
    ar["anomaly"]["recommendations"],   ar["storage"]["recommendations"],
    ar["cost"]["recommendations"],
], [])
hc_recs = [r for r in all_recs if r["severity"]=="HIGH"]
mc_recs = [r for r in all_recs if r["severity"]=="MEDIUM"]
lc_recs = [r for r in all_recs if r["severity"]=="LOW"]

ia, ib, id_ = st.columns(3)
show_high = ia.button(f"🔴 Critical Issues ({len(hc_recs)})", use_container_width=True)
ib.metric("🟡 Warnings", len(mc_recs))
id_.metric("📋 Total Findings",   len(all_recs) - len(lc_recs))  # exclude low priority

if show_high and hc_recs:
    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
    st.markdown("**Critical Issues (HIGH severity)**")
    for rec in hc_recs:
        st.markdown(f"- **{rec.get('title','Issue')}** — {rec.get('detail','')}")

# ── Savings Banner ─────────────────────────────────────────────
_sav = ar.get("savings", {})
if _sav.get("total_usd", 0) > 0:
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='background:linear-gradient(90deg,#052e16,#0a1628);
    border:1px solid #065f46;border-radius:14px;padding:1rem 1.4rem;
    display:flex;align-items:center;justify-content:space-between;'>
      <div>
        <div style='font-size:0.65rem;color:#059669;font-weight:700;
        text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px;'>
        💡 Potential Monthly Savings Identified</div>
        <div style='font-size:2rem;font-weight:800;color:#10b981;
        font-family:"DM Mono",monospace;'>${_sav["total_usd"]:.2f}
        <span style='font-size:0.9rem;color:#065f46;font-weight:400;'>/month</span></div>
      </div>
      <div style='text-align:right;'>
        <div style='font-size:0.7rem;color:#065f46;'>{_sav["item_count"]} optimization opportunities</div>
        <div style='font-size:0.7rem;color:#065f46;'>{_sav["total_credits"]:.4f} credits/month</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# 9 TABS
# ─────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    'Warehouse',
    'Query Intelligence',
    'Spend Anomaly',
    'Cost Breakdown',
    'Storage',
    'Notebooks',
    'Unused Objects',
    'Cloud Services',
    'Savings & History',
])


# ══════════════════════════════════════════════════════════════════
# TAB 1 — WAREHOUSE
# ══════════════════════════════════════════════════════════════════
with tab1:
    wh = ar["warehouse"]

    st.markdown("""<div style='margin-bottom:1rem;'>
    <h3 style='color:#c8daf0;font-size:1.1rem;font-weight:700;margin:0;'>Warehouse Analysis</h3>
    <p style='color:#2d5a8a;font-size:0.75rem;margin:4px 0 0;'>
    Size recommendations · Queue & spill detection · Credit cost · Pruning efficiency — Last 30 days</p>
    </div>""", unsafe_allow_html=True)

    # ── KPIs ──
    k1, k2, k3, k4, k5 = st.columns(5)
    user_whs = wh.get("user_warehouses", [])
    all_whs  = wh.get("warehouses", [])
    upsize_cnt = sum(1 for w in all_whs if w.get("action") in ("UPSIZE","CONSIDER_UPSIZE"))
    spill_cnt  = sum(1 for w in all_whs if w.get("spill_severity") in ("CRITICAL","HIGH"))
    k1.metric("Warehouses", len(all_whs))
    k2.metric("User Warehouses", len(user_whs))
    k3.metric("Total Credits", f"{wh.get('total_credits',0):.4f}")
    k4.metric("Est. Cost (30d)", f"${wh.get('total_cost_usd',0):.2f}")
    k5.metric("Needs Attention", upsize_cnt + spill_cnt)

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    # ── Charts ──
    if all_whs:
        df_wh = pd.DataFrame(all_whs)
        c_left, c_right = st.columns(2, gap="large")

        with c_left:
            st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">Credits by Warehouse</p>', unsafe_allow_html=True)
            wh_sorted = df_wh.sort_values("credits", ascending=True)
            colors = ["#ef4444" if r.get("action")=="UPSIZE"
                      else "#f59e0b" if r.get("action")=="CONSIDER_UPSIZE"
                      else "#2563eb" if r.get("type")=="User Warehouse"
                      else "#1a3a5a"
                      for _, r in wh_sorted.iterrows()]
            # Short warehouse names for display
            short_names = [w[-25:] if len(w) > 25 else w for w in wh_sorted["warehouse"]]
            fig = go.Figure(go.Bar(
                x=wh_sorted["credits"], y=short_names,
                orientation="h", marker_color=colors,
                text=[f"{v:.4f}" for v in wh_sorted["credits"]],
                textposition="outside", textfont=dict(color="#7a9cc0", size=10),
            ))
            fig.update_layout(**PLOTLY_DARK, height=340, showlegend=False)
            fig.update_xaxes(title_text="Credits Used", title_font=dict(size=10), **AXIS_STYLE)
            fig.update_yaxes(tickfont=dict(size=9), **AXIS_STYLE)
            st.plotly_chart(fig, use_container_width=True)

        with c_right:
            st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">Queue % vs Spill Rate %</p>', unsafe_allow_html=True)
            short_names_all = [w[-20:] if len(w) > 20 else w for w in df_wh["warehouse"]]
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                name="Queue %", x=short_names_all, y=df_wh["queue_pct"],
                marker_color="#f59e0b",
                text=[f"{v:.1f}%" for v in df_wh["queue_pct"]],
                textposition="outside", textfont=dict(size=9, color="#7a9cc0"),
            ))
            fig2.add_trace(go.Bar(
                name="Spill %", x=short_names_all, y=df_wh["spill_rate_pct"],
                marker_color="#ef4444",
                text=[f"{v:.1f}%" for v in df_wh["spill_rate_pct"]],
                textposition="outside", textfont=dict(size=9, color="#7a9cc0"),
            ))
            fig2.update_layout(**PLOTLY_DARK, height=340, barmode="group",
                               legend=dict(orientation="h", y=1.15, x=0))
            fig2.update_xaxes(tickangle=-25, tickfont=dict(size=8), **AXIS_STYLE)
            fig2.update_yaxes(title_text="%", **AXIS_STYLE)
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<div style='height:0.3rem;'></div>", unsafe_allow_html=True)

    # ── Warehouse Table ──
    st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;">Warehouse Detail & Recommendations</p>', unsafe_allow_html=True)

    if all_whs:
        rows = []
        for w in all_whs:
            spill_label = "—"
            if w.get("remote_spill_gb", 0) > 0:
                spill_label = f"⚠️ {w['remote_spill_gb']:.3f}GB REMOTE"
            elif w.get("local_spill_gb", 0) > 0:
                spill_label = f"🟡 {w['local_spill_gb']:.3f}GB LOCAL"
            elif w.get("spill_rate_pct", 0) > 0:
                spill_label = f"{w['spill_rate_pct']:.1f}% rate"

            action_icon = {"OK": "✅", "UPSIZE": "🔴", "CONSIDER_UPSIZE": "🟡",
                           "CONSIDER_DOWNSIZE": "🔵", "REVIEW": "⚪", "NO_ACTION": "—"}.get(w.get("action",""), "—")

            rows.append({
                "Warehouse":          w["warehouse"],
                "Type":               "System" if w["type"] != "User Warehouse" else "User",
                "Current Size":       w.get("current_size","—"),
                "Recommendation":     f'{action_icon} {w.get("size_recommendation","—")}',
                "Queries":            w.get("queries", 0),
                "Credits":            f'{w.get("credits",0):.4f}',
                "Est. Cost":          f'${w.get("est_cost_usd",0):.2f}',
                "Queue %":            w.get("queue_pct", 0),
                "Spill":              spill_label,
                "Pruning %":          w.get("pruning_pct", 0),
            })

        df_tbl = pd.DataFrame(rows)

        def color_rec(val):
            if "🔴" in str(val): return "background-color:#200808;color:#fca5a5;"
            if "🟡" in str(val): return "background-color:#201408;color:#fcd34d;"
            if "✅" in str(val): return "background-color:#081a0c;color:#6ee7b7;"
            return "color:#4d7aaa;"

        def color_queue(val):
            if isinstance(val, (int,float)):
                if val > 30: return "color:#fca5a5;font-weight:700;"
                if val > 10: return "color:#fcd34d;"
            return "color:#4d7aaa;"

        styled = (df_tbl.style
                  .applymap(color_rec, subset=["Recommendation"])
                  .applymap(color_queue, subset=["Queue %"]))
        st.dataframe(styled, use_container_width=True, hide_index=True)

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;">Recommendations</p>', unsafe_allow_html=True)
    show_recs(wh["recommendations"])
    render_ai_recs("warehouse")
    render_agent_plan("warehouse")


# ══════════════════════════════════════════════════════════════════
# TAB 2 — QUERY INTELLIGENCE
# ══════════════════════════════════════════════════════════════════
with tab2:
    qry = ar["queries"]

    st.markdown("""<div style='margin-bottom:1rem;'>
    <h3 style='color:#c8daf0;font-size:1.1rem;font-weight:700;margin:0;'>Query Intelligence</h3>
    <p style='color:#2d5a8a;font-size:0.75rem;margin:4px 0 0;'>
    Slowest queries · Time patterns · Problem tagging · Per-warehouse stats — Last 7 days</p>
    </div>""", unsafe_allow_html=True)

    ta = qry.get("time_analysis", {})
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total Queries",    qry.get("total", 0))
    k2.metric("Your Queries",     qry.get("user_query_count", 0))
    k3.metric("System Queries",   qry.get("total",0) - qry.get("user_query_count",0))
    k4.metric("Busiest Hour",     ta.get("busiest_hour_fmt","—"))
    k5.metric("Slowest Avg Hour", ta.get("slowest_hour_fmt","—"))

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

    tag_summary = qry.get("tag_summary", {})
    wh_stats    = qry.get("wh_query_stats", [])

    if tag_summary or wh_stats:
        c_left, c_right = st.columns(2, gap="large")

        with c_left:
            if tag_summary:
                st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">Query Problem Distribution</p>', unsafe_allow_html=True)
                color_map = {"OK":"#10b981","POOR PRUNING":"#f59e0b","HIGH REMOTE SPILL":"#ef4444",
                             "HIGH LOCAL SPILL":"#f97316","QUEUE BOTTLENECK":"#8b5cf6","SLOW QUERY":"#3b82f6"}
                df_tags = pd.DataFrame(list(tag_summary.items()), columns=["Tag","Count"])
                fig = px.pie(df_tags, names="Tag", values="Count", hole=0.6,
                             color="Tag", color_discrete_map=color_map)
                fig.update_traces(textfont=dict(size=10, color="#c8daf0"))
                fig.update_layout(**PLOTLY_DARK, height=280, showlegend=True,
                                  legend=dict(font=dict(size=10, color="#4d7aaa")))
                fig.update_xaxes(**AXIS_STYLE)
                fig.update_yaxes(**AXIS_STYLE)
                st.plotly_chart(fig, use_container_width=True)

        with c_right:
            if wh_stats:
                st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">Avg Execution Time by Warehouse (seconds)</p>', unsafe_allow_html=True)
                df_ws = pd.DataFrame(wh_stats).sort_values("avg_exec_sec", ascending=True)
                short_wh = [w[-22:] if len(w)>22 else w for w in df_ws["warehouse"]]
                fig2 = go.Figure(go.Bar(
                    x=df_ws["avg_exec_sec"], y=short_wh,
                    orientation="h", marker_color="#2563eb",
                    text=[f"{v:.2f}s" for v in df_ws["avg_exec_sec"]],
                    textposition="outside", textfont=dict(color="#7a9cc0", size=10),
                ))
                fig2.update_layout(**PLOTLY_DARK, height=280, showlegend=False)
                fig2.update_xaxes(**AXIS_STYLE)
                fig2.update_yaxes(tickfont=dict(size=9), **AXIS_STYLE)
                st.plotly_chart(fig2, use_container_width=True)

    # ── Hourly Pattern ──
    hourly = ta.get("hourly_stats", [])
    if hourly:
        st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:0.8rem 0 0.4rem;">Query Volume by Hour of Day</p>', unsafe_allow_html=True)
        df_h = pd.DataFrame(hourly)
        if "hour" in df_h.columns and "query_count" in df_h.columns:
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(x=df_h["hour"], y=df_h["query_count"],
                                  marker_color="#2563eb", name="Queries",
                                  marker=dict(opacity=0.8)))
            if "avg_exec" in df_h.columns:
                fig3.add_trace(go.Scatter(x=df_h["hour"], y=df_h["avg_exec"],
                                          mode="lines+markers", name="Avg Exec (s)",
                                          yaxis="y2", line=dict(color="#f59e0b", width=2),
                                          marker=dict(size=5)))
                fig3.update_layout(yaxis2=dict(overlaying="y", side="right",
                                               showgrid=False, color="#f59e0b"))
            fig3.update_layout(**PLOTLY_DARK, height=220, showlegend=True,
                               legend=dict(orientation="h", y=1.2))
            fig3.update_xaxes(tickmode="linear", dtick=1, tickfont=dict(size=9),
                              title_text="Hour (UTC)", **AXIS_STYLE)
            fig3.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig3, use_container_width=True)

    # ── Per-Warehouse Stats Table ──
    if wh_stats:
        st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:0.8rem 0 0.4rem;">Per-Warehouse Query Statistics</p>', unsafe_allow_html=True)
        df_ws2 = pd.DataFrame(wh_stats)
        rename_ws = {"warehouse":"Warehouse","total_queries":"Total","user_queries":"User",
                     "system_queries":"System","avg_exec_sec":"Avg (s)","max_exec_sec":"Max (s)",
                     "p95_exec_sec":"P95 (s)","total_spill_gb":"Spill (GB)","avg_pruning_pct":"Pruning %"}
        cols_ws = [c for c in rename_ws if c in df_ws2.columns]
        st.dataframe(df_ws2[cols_ws].rename(columns=rename_ws),
                     use_container_width=True, hide_index=True)

    # ── Top Slow Queries ──
    q_list = qry.get("queries", [])
    if q_list:
        st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:0.8rem 0 0.4rem;">Top Slow Queries</p>', unsafe_allow_html=True)

        all_tags = sorted(set(q.get("tag","OK") for q in q_list))
        sel_tags = st.multiselect("Filter by tag:", all_tags,
                                  default=[t for t in all_tags if t!="OK"] or all_tags,
                                  key="q_tags")
        filtered = [q for q in q_list if q.get("tag") in sel_tags] if sel_tags else q_list

        if filtered:
            df_q = pd.DataFrame(filtered)
            rename_q = {"tag":"Problem","user":"User","warehouse":"Warehouse",
                        "duration":"Duration","exec_sec":"Exec (s)","queued_sec":"Queue (s)",
                        "spill_gb":"Spill (GB)","pruning_pct":"Pruning %",
                        "start_time":"Start Time","query":"Query Preview"}
            cols_q = [c for c in rename_q if c in df_q.columns]

            def tag_color(val):
                if val in ("HIGH REMOTE SPILL","HIGH LOCAL SPILL"): return "background:#200808;color:#fca5a5;font-weight:700;"
                if val in ("POOR PRUNING","QUEUE BOTTLENECK","SLOW QUERY"): return "background:#201408;color:#fcd34d;"
                if val == "OK": return "color:#10b981;"
                return ""

            st.dataframe(
                df_q[cols_q].rename(columns=rename_q)
                .style.applymap(tag_color, subset=["Problem"]),
                use_container_width=True, hide_index=True,
            )

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;">Recommendations</p>', unsafe_allow_html=True)
    show_recs(qry["recommendations"])
    render_ai_recs("queries")
    render_agent_plan("queries")


# ══════════════════════════════════════════════════════════════════
# TAB 3 — SPEND ANOMALY
# ══════════════════════════════════════════════════════════════════
with tab3:
    anom = ar["anomaly"]

    st.markdown("""<div style='margin-bottom:1rem;'>
    <h3 style='color:#c8daf0;font-size:1.1rem;font-weight:700;margin:0;'>Spend Anomaly Detection</h3>
    <p style='color:#2d5a8a;font-size:0.75rem;margin:4px 0 0;'>
    Daily credits vs 7-day rolling baseline · ANOMALY = 2x+ · WARNING = 1.5x+ — Last 30 days</p>
    </div>""", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Anomaly Score",     f"{anom['score']}/100")
    k2.metric("🔴 Anomalies (2x+)", anom.get("anomaly_count",0))
    k3.metric("🟡 Warnings (1.5x+)",anom.get("warning_count",0))
    k4.metric("Total Flagged Days", anom.get("anomaly_count",0) + anom.get("warning_count",0))

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

    daily = anom.get("daily", [])
    if daily:
        df_d = pd.DataFrame(daily)
        df_d["date"] = pd.to_datetime(df_d["date"], errors="coerce")
        warehouses = sorted(df_d["warehouse"].dropna().unique().tolist())

        if len(warehouses) > 1:
            sel_wh = st.selectbox("Select Warehouse:", warehouses, key="anom_wh")
        else:
            sel_wh = warehouses[0] if warehouses else None

        if sel_wh:
            grp = df_d[df_d["warehouse"]==sel_wh].sort_values("date")

            bar_colors = []
            for s in grp.get("status", pd.Series(["NORMAL"]*len(grp))):
                if s == "ANOMALY": bar_colors.append("#ef4444")
                elif s == "WARNING": bar_colors.append("#f59e0b")
                else: bar_colors.append("#1d4ed8")

            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=grp["date"], y=grp["credits"],
                name="Daily Credits", marker_color=bar_colors,
                text=[f"{v:.4f}" for v in grp["credits"]],
                textposition="outside", textfont=dict(size=9, color="#4d7aaa"),
            ))
            if "avg" in grp.columns:
                fig.add_trace(go.Scatter(
                    x=grp["date"], y=grp["avg"], mode="lines+markers",
                    name="7-day Avg", line=dict(color="#60a5fa", width=2, dash="dash"),
                    marker=dict(size=4),
                ))
                avg_safe = grp["avg"].fillna(0)
                fig.add_trace(go.Scatter(
                    x=grp["date"], y=avg_safe*2,
                    mode="lines", name="Anomaly Threshold (2x)",
                    line=dict(color="#ef4444", width=1, dash="dot"),
                ))
                fig.add_trace(go.Scatter(
                    x=grp["date"], y=avg_safe*1.5,
                    mode="lines", name="Warning Threshold (1.5x)",
                    line=dict(color="#f59e0b", width=1, dash="dot"),
                ))
            fig.update_layout(**PLOTLY_DARK, height=340,
                              title=dict(text=f"{sel_wh} — Daily Credit Spend",
                                         font=dict(size=11, color="#4d7aaa")),
                              legend=dict(orientation="h", y=1.18, font=dict(size=9)))
            fig.update_xaxes(**AXIS_STYLE)
            fig.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig, use_container_width=True)

            # Legend
            lc1, lc2, lc3 = st.columns(3)
            lc1.markdown('<div class="sa-card" style="text-align:center;padding:0.5rem;"><span style="color:#ef4444;font-weight:700;">🔴 ANOMALY</span><br><span style="color:#2d5a8a;font-size:0.7rem;">2x+ above baseline</span></div>', unsafe_allow_html=True)
            lc2.markdown('<div class="sa-card" style="text-align:center;padding:0.5rem;"><span style="color:#f59e0b;font-weight:700;">🟡 WARNING</span><br><span style="color:#2d5a8a;font-size:0.7rem;">1.5x above baseline</span></div>', unsafe_allow_html=True)
            lc3.markdown('<div class="sa-card" style="text-align:center;padding:0.5rem;"><span style="color:#1d4ed8;font-weight:700;">🔵 NORMAL</span><br><span style="color:#2d5a8a;font-size:0.7rem;">Within expected range</span></div>', unsafe_allow_html=True)

        # ── Anomaly Detail Table ──
        anomalies = anom.get("anomalies", [])
        if anomalies:
            st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:0.8rem 0 0.4rem;">Flagged Days — Detail</p>', unsafe_allow_html=True)
            rows_an = []
            for a in anomalies:
                reasons = " · ".join(a.get("possible_reasons",[]))
                rows_an.append({
                    "Date":         a.get("date",""),
                    "Day":          a.get("day_of_week",""),
                    "Warehouse":    a.get("warehouse",""),
                    "Credits Used": f'{a.get("credits",0):.4f}',
                    "7d Average":   f'{a.get("avg_credits",0):.4f}',
                    "Spike Ratio":  f'{a.get("spike_ratio",0):.2f}x',
                    "Est. Cost":    f'${a.get("est_cost_usd",0):.3f}',
                    "Status":       a.get("status",""),
                    "Likely Cause": reasons,
                })
            df_an = pd.DataFrame(rows_an)

            def color_status(val):
                if val=="ANOMALY": return "background:#200808;color:#fca5a5;font-weight:700;"
                if val=="WARNING": return "background:#201408;color:#fcd34d;font-weight:600;"
                return ""

            st.dataframe(df_an.style.applymap(color_status, subset=["Status"]),
                         use_container_width=True, hide_index=True)
    else:
        st.info("No spend data available — ACCOUNT_USAGE has a 45-minute delay. Run some Snowflake queries first, then retry.")

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;">Recommendations</p>', unsafe_allow_html=True)
    show_recs(anom["recommendations"])
    render_ai_recs("anomaly")
    render_agent_plan("anomaly")


# ══════════════════════════════════════════════════════════════════
# TAB 4 — COST BREAKDOWN
# ══════════════════════════════════════════════════════════════════
with tab4:
    cost = ar["cost"]

    st.markdown("""<div style='margin-bottom:1rem;'>
    <h3 style='color:#c8daf0;font-size:1.1rem;font-weight:700;margin:0;'>Cost Breakdown</h3>
    <p style='color:#2d5a8a;font-size:0.75rem;margin:4px 0 0;'>
    Credits by warehouse and user · Execution hours · Query share — Last 30 days</p>
    </div>""", unsafe_allow_html=True)

    k1, k2, k3 = st.columns(3)
    k1.metric("Total Credits (30d)", f"{cost.get('total_credits',0):.4f}")
    k2.metric("Est. Total Cost",     f"${cost.get('total_cost_usd',0):.2f}")
    k3.metric("Active Users",        len([u for u in cost.get("by_user",[]) if not u.get("is_system")]))

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

    by_wh   = cost.get("wh_analysis", [])
    by_user = cost.get("by_user", [])
    by_daily= cost.get("by_warehouse", [])

    cl, cr = st.columns(2, gap="large")

    with cl:
        if by_wh:
            st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">Credits by Warehouse (30 days)</p>', unsafe_allow_html=True)
            df_bw = pd.DataFrame(by_wh)
            df_bw = df_bw.sort_values("total_credits", ascending=True)
            colors_bw = ["#1a3a5a" if r.get("is_system") else "#2563eb"
                         for _, r in df_bw.iterrows()]
            fig = go.Figure(go.Bar(
                x=df_bw["total_credits"], y=df_bw["warehouse"],
                orientation="h", marker_color=colors_bw,
                text=[f'{v:.4f} cr · ${r:.2f}' for v, r in zip(df_bw["total_credits"], df_bw["est_cost_usd"])],
                textposition="outside", textfont=dict(size=9, color="#4d7aaa"),
            ))
            fig.update_layout(**PLOTLY_DARK, height=300, showlegend=False)
            fig.update_xaxes(**AXIS_STYLE)
            fig.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig, use_container_width=True)

            # Daily trend
            if by_daily:
                df_bd = pd.DataFrame(by_daily)
                df_bd["date"] = pd.to_datetime(df_bd["date"], errors="coerce")
                df_bd["credits"] = pd.to_numeric(df_bd["credits"], errors="coerce").fillna(0)
                pivot = df_bd.pivot_table(index="date", columns="warehouse", values="credits", aggfunc="sum").fillna(0)
                if not pivot.empty:
                    fig2 = px.area(pivot, title="")
                    fig2.update_layout(**PLOTLY_DARK, height=200,
                                       legend=dict(orientation="h", y=1.2, font=dict(size=9)))
                    fig2.update_xaxes(**AXIS_STYLE)
                    fig2.update_yaxes(**AXIS_STYLE)
                    st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">Daily Credit Trend</p>', unsafe_allow_html=True)
                    st.plotly_chart(fig2, use_container_width=True)

    with cr:
        if by_user:
            st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.4rem;">Queries by User</p>', unsafe_allow_html=True)
            df_bu = pd.DataFrame(by_user)
            df_bu["queries"] = pd.to_numeric(df_bu["queries"], errors="coerce").fillna(0)
            df_bu_sorted = df_bu.sort_values("queries", ascending=True).tail(15)
            colors_u = ["#1a3a5a" if r.get("is_system") else "#10b981"
                        for _, r in df_bu_sorted.iterrows()]
            fig3 = go.Figure(go.Bar(
                x=df_bu_sorted["queries"], y=df_bu_sorted["user"],
                orientation="h", marker_color=colors_u,
                text=[f'{int(v):,}' for v in df_bu_sorted["queries"]],
                textposition="outside", textfont=dict(size=10, color="#4d7aaa"),
            ))
            fig3.update_layout(**PLOTLY_DARK, height=300, showlegend=False)
            fig3.update_xaxes(**AXIS_STYLE)
            fig3.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig3, use_container_width=True)

    # ── User Detail Table ──
    if by_user:
        st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:0.8rem 0 0.4rem;">User Activity Detail</p>', unsafe_allow_html=True)
        rows_u = []
        for u in by_user:
            rows_u.append({
                "User":          u.get("user",""),
                "Role":          u.get("role",""),
                "Profile":       u.get("profile",""),
                "Queries":       f'{u.get("queries",0):,}',
                "Query Share":   f'{u.get("query_share",0):.1f}%',
                "Avg Exec (s)":  f'{u.get("avg_exec_sec",0):.3f}',
                "Exec Hours":    f'{u.get("exec_hours",0):.4f}',
                "Hour Share":    f'{u.get("hour_share",0):.1f}%',
                "Spill (GB)":    f'{u.get("spill_gb",0):.4f}',
                "Warehouses":    u.get("warehouses_used",0),
                "Databases":     u.get("databases_used",0),
            })
        df_ut = pd.DataFrame(rows_u)

        def color_profile(val):
            if "System" in str(val): return "color:#1a3a5a;"
            if "Admin" in str(val):  return "color:#f59e0b;"
            if "Service" in str(val):return "color:#3b82f6;"
            return "color:#10b981;"

        st.dataframe(df_ut.style.applymap(color_profile, subset=["Profile"]),
                     use_container_width=True, hide_index=True)

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    show_recs(cost["recommendations"])
    render_ai_recs("cost")
    render_agent_plan("cost")


# ══════════════════════════════════════════════════════════════════
# TAB 5 — STORAGE
# ══════════════════════════════════════════════════════════════════
with tab5:
    stor = ar["storage"]

    st.markdown("""<div style='margin-bottom:1rem;'>
    <h3 style='color:#c8daf0;font-size:1.1rem;font-weight:700;margin:0;'>Storage Analysis</h3>
    <p style='color:#2d5a8a;font-size:0.75rem;margin:4px 0 0;'>
    Active data · Time Travel overhead · Failsafe cost · Monthly waste estimate</p>
    </div>""", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Storage Score",      f"{stor['score']}/100")
    k2.metric("Total Active (GB)",  f"{stor.get('total_active_gb',0):.4f}")
    k3.metric("Est. Monthly Waste", f"${stor.get('total_waste_usd',0):.4f}")
    k4.metric("Bloated Tables",     stor.get("bloated_count",0))

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

    show_recs(stor["recommendations"])
    render_ai_recs("storage")
    render_agent_plan("storage")

    tables = stor.get("tables", [])
    if tables:
        real_tables = [t for t in tables if not t.get("is_system") and t.get("active_gb",0) > 0]
        sys_tables  = [t for t in tables if t.get("is_system")]

        if sys_tables and not real_tables:
            st.markdown(f"""
            <div class='sa-card'>
              <p class='sa-title'>ℹ️ Only Snowflake System Tables Found</p>
              <p class='sa-detail'>
              {len(sys_tables)} internal tables detected (SNOWFLAKE.TRUST_CENTER_STATE.*).
              All have ACTIVE_GB = 0 — these are Snowflake metadata tables, not your data.
              Real storage cost = $0.00. Your own tables will appear here once you create them.
              </p>
            </div>
            """, unsafe_allow_html=True)

        if tables:
            st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:0.8rem 0 0.4rem;">All Tracked Tables</p>', unsafe_allow_html=True)
            df_st = pd.DataFrame(tables)
            rename_s = {"database":"Database","schema":"Schema","table":"Table",
                        "active_gb":"Active (GB)","tt_gb":"Time Travel (GB)",
                        "fs_gb":"Failsafe (GB)","bloat_pct":"Overhead %",
                        "waste_usd":"Waste $/mo","is_system":"System"}
            cols_s = [c for c in rename_s if c in df_st.columns]

            def color_bloat(val):
                if isinstance(val, (int,float)):
                    if val > 200: return "background:#200808;color:#fca5a5;font-weight:700;"
                    if val > 100: return "background:#201408;color:#fcd34d;"
                return "color:#4d7aaa;"

            st.dataframe(
                df_st[cols_s].rename(columns=rename_s)
                .style.applymap(color_bloat, subset=["Overhead %"]),
                use_container_width=True, hide_index=True,
            )


# ══════════════════════════════════════════════════════════════════
with tab6:
    nb = ar["notebooks"]

    st.markdown("""<div style='margin-bottom:1rem;'>
    <h3 style='color:#c8daf0;font-size:1.1rem;font-weight:700;margin:0;'>Snowflake Notebooks</h3>
    <p style='color:#2d5a8a;font-size:0.75rem;margin:4px 0 0;'>
    Notebook activity detected via QUERY_TAG filter — Last 30 days</p>
    </div>""", unsafe_allow_html=True)

    notebooks = nb.get("notebooks", [])
    if not notebooks:
        st.markdown(f"""
        <div class='sa-card'>
          <p class='sa-title'>📓 No Notebook Activity Detected</p>
          <p class='sa-detail'>
          {nb.get("note","No activity in last 30 days.")}<br><br>
          Notebooks appear here when QUERY_TAG contains 'notebook', 'jupyter', or 'python'.
          To tag your sessions, run:<br><br>
          <code style='color:#60a5fa;'>ALTER SESSION SET QUERY_TAG = 'notebook';</code>
          </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        k1, k2 = st.columns(2)
        k1.metric("Total Notebook Runs", nb.get("total_runs",0))
        k2.metric("Unique Users", len(set(n.get("user","") for n in notebooks)))

        df_nb = pd.DataFrame(notebooks)
        cl, cr = st.columns(2)
        with cl:
            fig = px.histogram(df_nb, x="date", color="user", nbins=30, title="")
            fig.update_layout(**PLOTLY_DARK, height=260,
                              legend=dict(font=dict(size=9, color="#4d7aaa")))
            fig.update_xaxes(**AXIS_STYLE)
            fig.update_yaxes(**AXIS_STYLE)
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            if "user" in df_nb.columns:
                uc = df_nb["user"].value_counts().reset_index()
                uc.columns = ["User","Runs"]
                fig2 = px.pie(uc, names="User", values="Runs", hole=0.55)
                fig2.update_layout(**PLOTLY_DARK, height=260,
                                   legend=dict(font=dict(size=9, color="#4d7aaa")))
                fig2.update_xaxes(**AXIS_STYLE)
                fig2.update_yaxes(**AXIS_STYLE)
                st.plotly_chart(fig2, use_container_width=True)

        rename_nb = {"user":"User","warehouse":"Warehouse","database":"DB",
                     "exec_sec":"Exec (s)","spill_gb":"Spill (GB)","date":"Date","query":"Query Preview"}
        cols_nb = [c for c in rename_nb if c in df_nb.columns]
        st.dataframe(df_nb[cols_nb].rename(columns=rename_nb),
                     use_container_width=True, hide_index=True)

    render_agent_plan("notebooks")


# ══════════════════════════════════════════════════════════════════
# ——————————————————————————————————————————————————————————————
# TAB 8 — UNUSED OBJECTS
# ——————————————————————————————————————————————————————————————
with tab7:
    unused = ar.get("unused_objects", {})

    st.markdown("""<div style='margin-bottom:1rem;'>
    <h3 style='color:#c8daf0;font-size:1.1rem;font-weight:700;margin:0;'>Unused Objects</h3>
    <p style='color:#2d5a8a;font-size:0.75rem;margin:4px 0 0;'>
    Tables not accessed in the last 30 days · Estimated monthly storage cost & credit equivalent</p>
    </div>""", unsafe_allow_html=True)

    tables = unused.get("tables", [])
    k1, k2, k3 = st.columns(3)
    k1.metric("Unused Tables", len(tables))
    k2.metric("Stale Storage", f"{unused.get('total_stale_gb',0):.2f} GB")
    k3.metric("Est. Monthly Cost", f"${unused.get('total_stale_usd',0):.2f} · {unused.get('total_stale_credits_est',0):.4f} cr")

    if tables:
        df_unused = pd.DataFrame(tables)
        rename_u = {
            "FULL_TABLE_NAME": "Table",
            "SIZE_GB": "Size (GB)",
            "cost_usd": "Est. Cost $/mo",
            "est_credits": "Est. Credits/mo",
            "ROW_COUNT": "Rows",
        }
        cols_u = [c for c in rename_u if c in df_unused.columns]
        st.dataframe(df_unused[cols_u].rename(columns=rename_u),
                     use_container_width=True, hide_index=True)
    else:
        st.info("No unused tables detected in the last 30 days.")

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("**AI Insights**")
    render_ai_recs("unused_objects")
    render_agent_plan("unused_objects")


# ——————————————————————————————————————————————————————————————
# TAB 9 — CLOUD SERVICES
# ——————————————————————————————————————————————————————————————
with tab8:
    cloud = ar.get("cloud_services", {})

    st.markdown("""<div style='margin-bottom:1rem;'>
    <h3 style='color:#c8daf0;font-size:1.1rem;font-weight:700;margin:0;'>Cloud Services Credits</h3>
    <p style='color:#2d5a8a;font-size:0.75rem;margin:4px 0 0;'>
    Cloud services allowance is 10% of compute credits per day · Highlight warehouses exceeding allowance</p>
    </div>""", unsafe_allow_html=True)

    totals = cloud.get("totals", {})
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Cloud Services Credits", f"{totals.get('cloud_credits',0):.4f}")
    k2.metric("Compute Credits",        f"{totals.get('compute_credits',0):.4f}")
    k3.metric("Billed CS (over 10%)",   f"{totals.get('billed_cs',0):.4f}")
    k4.metric("Free CS",                f"{totals.get('free_cs',0):.4f}")

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
    show_recs(cloud.get("recommendations", []))
    render_ai_recs("cloud_services")

    wh_rows = cloud.get("warehouses", [])
    if wh_rows:
        df_cs = pd.DataFrame(wh_rows)
        rename_c = {
            "WAREHOUSE_NAME": "Warehouse",
            "CLOUD_CREDITS": "Cloud Services",
            "COMPUTE_CREDITS": "Compute",
            "TOTAL_CREDITS": "Total",
            "cs_allowance": "Allowance (10%)",
            "billed_cs": "Billed CS",
            "free_cs": "Free CS",
            "cs_pct_of_total": "CS % of Total",
        }
        cols_c = [c for c in rename_c if c in df_cs.columns]
        st.dataframe(df_cs[cols_c].rename(columns=rename_c),
                     use_container_width=True, hide_index=True)
    else:
        st.info("No cloud services usage detected in the selected window.")

    anomalies = cloud.get("anomalies", [])
    if anomalies:
        st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin:0.6rem 0 0.3rem;">Anomalies (over 10% allowance)</p>', unsafe_allow_html=True)
        df_an = pd.DataFrame(anomalies)
        st.dataframe(df_an, use_container_width=True, hide_index=True)

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    st.markdown("**AI Insights**")
    render_ai_recs("cloud_services")
    render_agent_plan("cloud_services")


# TAB 10 — SAVINGS & HISTORY
# ══════════════════════════════════════════════════════════════════
with tab9:
    sav = ar.get("savings", {})
    aus = ar.get("auto_suspend", {})

    st.markdown("""<div style='margin-bottom:1rem;'>
    <h3 style='color:#c8daf0;font-size:1.1rem;font-weight:700;margin:0;'>💡 Savings Estimator & Advisor</h3>
    <p style='color:#2d5a8a;font-size:0.75rem;margin:4px 0 0;'>
    Concrete dollar savings per recommendation · Auto-suspend timing · Historical trend</p>
    </div>""", unsafe_allow_html=True)

    # ── Savings KPIs ──────────────────────────────────────────────
    total_usd   = sav.get("total_usd", 0)
    items       = sav.get("items", [])
    high_conf   = [i for i in items if i.get("confidence") == "High"]

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("💰 Total Potential Savings", f"${total_usd:.2f}/mo")
    k2.metric("High Confidence Savings",
              f"${sum(i['saving_usd'] for i in high_conf):.2f}/mo")
    k3.metric("Saving Opportunities",      len(items))
    k4.metric("Credits Saveable",          f"{sav.get('total_credits',0):.4f}")

    render_agent_plan("savings")

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    # ── Big savings box ───────────────────────────────────────────
    if total_usd > 0:
        st.markdown(f"""
        <div style='background:linear-gradient(135deg,#081a10,#0d2818);
        border:1px solid #065f46;border-radius:16px;padding:1.5rem;
        text-align:center;margin-bottom:1rem;position:relative;overflow:hidden;'>
          <div style='position:absolute;top:0;left:0;right:0;height:3px;
          background:linear-gradient(90deg,#10b981,#059669);'></div>
          <div style='font-size:0.7rem;color:#065f46;font-weight:700;
          text-transform:uppercase;letter-spacing:0.15em;margin-bottom:0.5rem;'>
          Estimated Monthly Savings If All Recommendations Applied</div>
          <div style='font-size:3.5rem;font-weight:900;color:#10b981;
          font-family:"DM Mono",monospace;'>${total_usd:.2f}</div>
          <div style='font-size:0.75rem;color:#065f46;margin-top:4px;'>per month</div>
        </div>
        """, unsafe_allow_html=True)

    # ── Savings Items ─────────────────────────────────────────────
    if items:
        st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;">Savings Breakdown</p>', unsafe_allow_html=True)

        for itm in items:
            conf  = itm.get("confidence","")
            conf_color = {"High":"#10b981","Medium":"#f59e0b","Low":"#3b82f6"}.get(conf,"#4d7aaa")
            conf_bg    = {"High":"#083b1a","Medium":"#3b2008","Low":"#082838"}.get(conf,"#0b1220")
            usd   = itm.get("saving_usd", 0)

            st.markdown(f"""
            <div class='sa-card' style='border-left:4px solid {conf_color};
            background:linear-gradient(90deg,{conf_bg},#0d1829);'>
              <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                <div>
                  <span class='sa-label' style='background:{conf_bg};color:{conf_color};
                  margin-bottom:4px;display:inline-block;'>{itm.get("category","")}</span>
                  <p class='sa-title' style='margin:4px 0;'>{itm.get("detail","")}</p>
                  <p class='sa-detail'>Confidence: {conf} &nbsp;·&nbsp; Period: {itm.get("period","monthly")}</p>
                </div>
                <div style='text-align:right;flex-shrink:0;margin-left:1rem;'>
                  <div style='font-size:1.4rem;font-weight:800;color:{conf_color};
                  font-family:"DM Mono",monospace;'>${usd:.2f}</div>
                  <div style='font-size:0.65rem;color:#2d5a8a;'>per month</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            if itm.get("fix_sql"):
                with st.expander("View Fix SQL"):
                    st.code(itm["fix_sql"], language="sql")

    elif total_usd == 0:
        st.markdown("""
        <div class='sa-card' style='border-left:4px solid #10b981;text-align:center;'>
          <p class='sa-title'>✅ No obvious savings opportunities found</p>
          <p class='sa-detail'>Your account appears well-optimized. Check back after more activity.</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    # ── Auto-Suspend Timing ───────────────────────────────────────
    st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;">⏱️ Auto-Suspend Timing Recommendations</p>', unsafe_allow_html=True)

    aus_whs = aus.get("warehouses", [])
    if aus_whs:
        rows_aus = []
        for w in aus_whs:
            rows_aus.append({
                "Warehouse":        w["warehouse"],
                "Total Queries":    w["total_queries"],
                "Peak Window":      w["peak_window"],
                "Weekend Activity": "Yes" if not w["weekday_only"] else "Weekdays Only",
                "Recommended Suspend": f'{w["recommended_suspend_min"]} min',
                "Current SQL":      f'AUTO_SUSPEND = {w["recommended_suspend_min"]*60}',
                "Note":             w["suspend_note"],
            })
        df_aus = pd.DataFrame(rows_aus)
        st.dataframe(df_aus, use_container_width=True, hide_index=True)
        st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
        show_recs(aus.get("recommendations", []))
    else:
        st.info("Not enough query pattern data for auto-suspend recommendations. Run more queries first.")

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    # Historical trend removed per request
    st.markdown('<p style="color:#4d7aaa;font-size:0.75rem;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:0.6rem;">📊 Historical Trend (from MongoDB)</p>', unsafe_allow_html=True)

    sid = st.session_state.get("session_id")

    if not sid:
        # Fallback to local JSON files if no API session
        acct_slug = info.get("account","").lower().replace(".","").replace("-","")
        hist      = analysis.analyze_historical_trend("data", acct_slug)
        if not hist.get("has_trend"):
            st.markdown(f"""
            <div class='sa-card'>
              <p class='sa-title'>📊 {hist.get("note","Run the tool again to build trend data.")}</p>
              <p class='sa-detail'>Connect via FastAPI to enable MongoDB-backed trend history across sessions.
              Currently showing local file history only.</p>
            </div>""", unsafe_allow_html=True)
        runs_for_chart = hist.get("runs", [])
    else:
        # Load history from MongoDB via API
        try:
            hist_resp = _req.get(f"{API_URL}/session/{sid}/history", timeout=10)
            if hist_resp.status_code == 200:
                hist_data  = hist_resp.json()
                runs_api   = hist_data.get("runs", [])
                run_count  = hist_data.get("run_count", 0)
                # Normalize API runs to match local format
                runs_for_chart = [{
                    "timestamp":      r.get("analyzed_at","")[:19].replace("T"," "),
                    "health_overall": r.get("health_score", 0),
                    "health_grade":   r.get("health_grade","—"),
                    "total_credits":  0,
                    "total_cost":     r.get("total_cost_usd", 0),
                    "anomaly_count":  r.get("anomaly_count", 0),
                    "high_issues":    0,
                } for r in runs_api]

                if run_count < 2:
                    st.markdown(f"""
                    <div class='sa-card'>
                      <p class='sa-title'>📊 {run_count} run(s) in MongoDB — need 2+ for trend</p>
                      <p class='sa-detail'>Each time you connect and analyze, a snapshot is saved to MongoDB.
                      Connect again tomorrow to see your health trend over time.</p>
                    </div>""", unsafe_allow_html=True)
                else:
                    first_r = runs_for_chart[0]
                    last_r  = runs_for_chart[-1]
                    hc      = last_r["health_overall"] - first_r["health_overall"]
                    hc_ic   = "↑" if hc > 0 else ("↓" if hc < 0 else "→")
                    cc      = last_r["total_cost"] - first_r["total_cost"]
                    cc_ic   = "↑" if cc > 0 else ("↓" if cc < 0 else "→")

                    t1, t2, t3 = st.columns(3)
                    t1.metric("Total Runs in MongoDB", run_count)
                    t2.metric("Health Change",  f"{hc_ic} {abs(hc)} pts", delta=int(hc), delta_color="normal")
                    t3.metric("Cost Change",    f"${abs(cc):.2f}", delta=round(cc,2), delta_color="inverse")

                    st.markdown(f"""<div class='sa-card'>
                    <p class='sa-title'>📈 MongoDB Trend: {run_count} runs</p>
                    <p class='sa-detail'>First run: {first_r['timestamp']} &nbsp;·&nbsp;
                    Latest: {last_r['timestamp']}</p>
                    </div>""", unsafe_allow_html=True)
            else:
                runs_for_chart = []
                st.info("Could not load history from MongoDB.")
        except Exception as e:
            runs_for_chart = []
            st.warning(f"History API error: {e}")

    # Chart (works for both local and MongoDB data)
    if len(runs_for_chart) >= 2:
        df_hist = pd.DataFrame(runs_for_chart)
        fig_h = go.Figure()
        fig_h.add_trace(go.Scatter(
            x=df_hist["timestamp"], y=df_hist["health_overall"],
            mode="lines+markers+text", name="Health Score",
            line=dict(color="#2563eb", width=2),
            marker=dict(size=8, color="#2563eb"),
            text=[str(v) for v in df_hist["health_overall"]],
            textposition="top center", textfont=dict(size=10, color="#7a9cc0"),
        ))
        if "total_cost" in df_hist.columns:
            fig_h.add_trace(go.Bar(
                x=df_hist["timestamp"], y=df_hist["total_cost"],
                name="Est. Cost ($)", yaxis="y2",
                marker_color="#10b981", opacity=0.4,
            ))
            fig_h.update_layout(yaxis2=dict(overlaying="y", side="right",
                                            showgrid=False, color="#10b981"))
        fig_h.update_layout(**PLOTLY_DARK, height=280,
                            legend=dict(orientation="h", y=1.2, font=dict(size=9)))
        fig_h.update_xaxes(**AXIS_STYLE, tickangle=-20, tickfont=dict(size=9))
        fig_h.update_yaxes(**AXIS_STYLE, title_text="Health Score")
        st.plotly_chart(fig_h, use_container_width=True)

        disp_cols = ["timestamp","health_overall","health_grade","anomaly_count"]
        avail     = [c for c in disp_cols if c in df_hist.columns]
        rename_h  = {"timestamp":"Run Time","health_overall":"Health",
                     "health_grade":"Grade","anomaly_count":"Anomalies"}
        st.dataframe(df_hist[avail].rename(columns=rename_h),
                     use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────────────────────────
# AI JSON EXPORT
# ─────────────────────────────────────────────────────────────────
st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
st.divider()

with st.expander("🤖 AI Insights File — Export for LLM Analysis"):
    st.markdown('<p style="color:#2d5a8a;font-size:0.8rem;">Download this structured JSON and feed it to any AI model (Claude, ChatGPT, etc.) for additional insights and recommendations.</p>', unsafe_allow_html=True)
    from datetime import datetime as _dt
    ai_json_str = json.dumps(ar.get("ai_json", {}), indent=2, default=str)
    _acct = info.get("account","account")
    _ts   = _dt.now().strftime("%Y%m%d_%H%M%S")
    st.download_button(
        label="⬇️ Download AI_Insights_file.json",
        data=ai_json_str,
        file_name=f"AI_Insights_file_{_acct}_{_ts}.json",
        mime="application/json",
        use_container_width=True,
    )
    st.markdown('<p style="color:#1a3a5a;font-size:0.72rem;">Preview (first 1500 chars):</p>', unsafe_allow_html=True)
    st.code(ai_json_str[:1500] + ("\n... (truncated)" if len(ai_json_str) > 1500 else ""), language="json")

# ─────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div style='text-align:center;color:#1a3a5a;font-size:0.7rem;
margin-top:2rem;padding-top:1rem;border-top:1px solid #0a1220;'>
  ❄️ SnowAdvisor &nbsp;·&nbsp;
  <span style='color:#2d5a8a;font-family:"DM Mono",monospace;'>{info.get("account","")}</span>
  &nbsp;·&nbsp; {info.get("user","")} &nbsp;·&nbsp;
  Saved: <span style='font-family:"DM Mono",monospace;'>{result.get("filename","")}</span>
  &nbsp;·&nbsp; Read-only — no changes made to your Snowflake account
</div>
""", unsafe_allow_html=True)
