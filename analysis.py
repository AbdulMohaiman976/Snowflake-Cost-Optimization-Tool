# analysis.py
# ─────────────────────────────────────────────────────────────────
# Pure Python — koi Snowflake connection nahi.
# dashboard.py call karta hai:  analysis.run_analysis(data)
# Har function ek self-contained dict return karta hai.
# Sab results ek structured JSON mein bhi export hota hai AI layer ke liye.
# ─────────────────────────────────────────────────────────────────

import pandas as pd
from datetime import datetime


# ══════════════════════════════════════════════════════════════════
# UTILS
# ══════════════════════════════════════════════════════════════════

def _to_df(table: dict) -> pd.DataFrame:
    if not table or table.get("error") or not table.get("rows"):
        return pd.DataFrame()
    df = pd.DataFrame(table["rows"])
    df.columns = [c.upper() for c in df.columns]
    return df

def _n(df, *cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    return df

def _safe_dt(val):
    try:
        return str(val)[:19].replace("T"," ")
    except Exception:
        return ""

def _fmt_hour(h):
    """Convert 0-23 hour to 12-hour AM/PM format e.g. 14 -> 2:00 PM"""
    if h is None: return "N/A"
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12
    if h12 == 0: h12 = 12
    return f"{h12}:00 {suffix}"

# Snowflake credit price — configurable
CREDIT_PRICE_USD = 3.0   # $3 per credit (standard)


# ══════════════════════════════════════════════════════════════════
# 1. WAREHOUSE ANALYSIS
#    Input:  warehouse_advisor table
#    Output: per-warehouse decision + size recommendation
# ══════════════════════════════════════════════════════════════════

# Snowflake warehouse size hierarchy
_WH_SIZES = ["X-Small","Small","Medium","Large","X-Large","2X-Large","3X-Large","4X-Large"]
_WH_CREDITS = {"X-Small":1,"Small":2,"Medium":4,"Large":8,"X-Large":16,
               "2X-Large":32,"3X-Large":64,"4X-Large":128}

def _next_size(current: str) -> str:
    try:
        idx = _WH_SIZES.index(current)
        return _WH_SIZES[min(idx+1, len(_WH_SIZES)-1)]
    except ValueError:
        return "Medium"

def _prev_size(current: str) -> str:
    try:
        idx = _WH_SIZES.index(current)
        return _WH_SIZES[max(idx-1, 0)]
    except ValueError:
        return "X-Small"

def analyze_warehouses(data: dict) -> dict:
    df = _to_df(data.get("warehouse_advisor", {}))
    if df.empty:
        return _empty_wh()

    df = _n(df,"QUEUE_RATIO_PCT","SPILL_RATE_PCT","AVG_PRUNING_PCT",
              "TOTAL_CREDITS","TOTAL_QUERIES","REMOTE_SPILL_GB","LOCAL_SPILL_GB","AVG_EXEC_SEC")

    # ── Aggregate: same warehouse, multiple size rows → merge ──
    agg = df.groupby("WAREHOUSE_NAME", as_index=False).agg(
        total_queries = ("TOTAL_QUERIES",   "sum"),
        total_credits = ("TOTAL_CREDITS",   "sum"),
        queue_pct     = ("QUEUE_RATIO_PCT",  "max"),
        spill_pct     = ("SPILL_RATE_PCT",   "max"),
        pruning_pct   = ("AVG_PRUNING_PCT",  "min"),   # worst-case pruning
        remote_spill  = ("REMOTE_SPILL_GB",  "sum"),
        local_spill   = ("LOCAL_SPILL_GB",   "sum"),
        avg_exec_sec  = ("AVG_EXEC_SEC",     "mean"),
    )

    # Pick warehouse size from highest-query row
    size_map = {}
    for _, row in df.sort_values("TOTAL_QUERIES", ascending=False).iterrows():
        wh = row["WAREHOUSE_NAME"]
        sz = str(row.get("WAREHOUSE_SIZE","")).strip()
        if sz and sz.lower() not in ("","none","nan") and wh not in size_map:
            size_map[wh] = sz

    warehouses   = []
    recs         = []
    total_credits_all = float(agg["total_credits"].sum())

    for _, row in agg.iterrows():
        wh         = row["WAREHOUSE_NAME"]
        is_sys     = wh.startswith("COMPUTE_SERVICE_WH")
        credits    = float(row["total_credits"])
        queries    = int(row["total_queries"])
        queue      = float(row["queue_pct"])
        spill      = float(row["spill_pct"])
        pruning    = float(row["pruning_pct"])
        remote_gb  = float(row["remote_spill"])
        local_gb   = float(row["local_spill"])
        avg_exec   = float(row["avg_exec_sec"])
        current_sz = size_map.get(wh, "Unknown")
        credit_pct = round(credits/total_credits_all*100, 1) if total_credits_all > 0 else 0
        est_cost   = round(credits * CREDIT_PRICE_USD, 2)

        # ── Size Recommendation Logic ──────────────────────────
        # UPSIZE if: queue > 20% OR remote spill > 0 OR spill_rate > 15%
        # DOWNSIZE if: very low usage + queue=0 + spill=0
        # RIGHT-SIZE if: optimal

        total_spill_gb = remote_gb + local_gb

        if is_sys:
            size_rec  = "Managed by Snowflake"
            action    = "NO_ACTION"
            action_why = "Internal Snowflake service warehouse — not billed to you"
        elif queue > 40 or (spill > 20 and remote_gb > 0):
            rec_size  = _next_size(current_sz)
            size_rec  = f"UPSIZE → {rec_size}"
            action    = "UPSIZE"
            action_why = f"Queue={queue:.1f}% + Remote Spill={remote_gb:.3f}GB — warehouse overwhelmed"
        elif queue > 10 or spill > 10:
            rec_size  = _next_size(current_sz)
            size_rec  = f"CONSIDER UPSIZE → {rec_size}"
            action    = "CONSIDER_UPSIZE"
            action_why = f"Queue={queue:.1f}%, Spill={spill:.1f}% — monitor closely"
        elif queries > 0 and queue == 0 and spill == 0 and credits > 0:
            prev_sz   = _prev_size(current_sz)
            if prev_sz != current_sz and credits < 0.5 and queries < 50:
                size_rec  = f"CONSIDER DOWNSIZE → {prev_sz}"
                action    = "CONSIDER_DOWNSIZE"
                action_why = f"Only {queries} queries, {credits:.4f} credits — may be oversized"
            else:
                size_rec  = "RIGHT-SIZED ✅"
                action    = "OK"
                action_why = "No queue, no spill, healthy pruning"
        elif queries == 0 and credits == 0:
            size_rec  = "IDLE / NO USAGE"
            action    = "REVIEW"
            action_why = "No activity detected — consider suspending or dropping"
        else:
            size_rec  = "RIGHT-SIZED ✅"
            action    = "OK"
            action_why = "Performance metrics within normal range"

        # ── Spill Analysis ──────────────────────────────────────
        # Spill types: LOCAL = memory → disk (slow), REMOTE = disk → S3 (very slow)
        spill_severity = "NONE"
        spill_reason   = ""
        spill_fix      = ""
        if remote_gb > 0.1:
            spill_severity = "CRITICAL"
            spill_reason   = (f"Remote spill {remote_gb:.3f}GB — queries exceeded both memory AND local disk. "
                              f"This is 10-100x slower than normal execution.")
            spill_fix      = (f"1. Upsize {wh} to {_next_size(current_sz)}\n"
                              f"2. Check for large JOINs or GROUP BYs without filters\n"
                              f"3. Break large queries into smaller CTEs\n"
                              f"ALTER WAREHOUSE {wh} SET WAREHOUSE_SIZE = '{_next_size(current_sz)}';")
        elif local_gb > 0.1:
            spill_severity = "HIGH"
            spill_reason   = (f"Local spill {local_gb:.3f}GB — queries exceeded warehouse memory "
                              f"and spilled to local SSD. 2-5x slower than normal.")
            spill_fix      = (f"Upsize {wh} or add query filters to reduce data scanned.\n"
                              f"ALTER WAREHOUSE {wh} SET WAREHOUSE_SIZE = '{_next_size(current_sz)}';")
        elif spill > 10:
            spill_severity = "MEDIUM"
            spill_reason   = f"{spill:.1f}% of queries had some memory pressure"
            spill_fix      = f"Monitor — if trend continues, upsize {wh}"

        # ── Pruning Analysis ────────────────────────────────────
        pruning_note = ""
        if pruning < 50 and not is_sys:
            pruning_note = (f"Only {pruning:.1f}% of partitions pruned — queries scanning most of the table. "
                            f"Add cluster keys on columns used in WHERE clauses.")
        elif pruning < 80 and not is_sys:
            pruning_note = f"{pruning:.1f}% pruning — room for improvement with better WHERE clause filters."
        else:
            pruning_note = f"{pruning:.1f}% pruning — good partition elimination."

        # ── Issues for recommendations ──────────────────────────
        issues = []
        if action in ("UPSIZE","CONSIDER_UPSIZE"):
            sev = "HIGH" if action=="UPSIZE" else "MEDIUM"
            issues.append({"severity":sev,
                "title": f"{wh} ({current_sz}): {size_rec}",
                "detail": action_why,
                "fix_sql": f"ALTER WAREHOUSE {wh} SET WAREHOUSE_SIZE = '{_next_size(current_sz)}';"})
        if spill_severity in ("CRITICAL","HIGH"):
            issues.append({"severity":"HIGH" if spill_severity=="CRITICAL" else "MEDIUM",
                "title": f"{wh}: Memory Spill Detected — {spill_severity}",
                "detail": spill_reason,
                "fix_sql": spill_fix})
        if pruning < 50 and not is_sys and queries > 20:
            issues.append({"severity":"MEDIUM",
                "title": f"{wh}: Poor Partition Pruning ({pruning:.1f}%)",
                "detail": pruning_note,
                "fix_sql": "ALTER TABLE your_large_table CLUSTER BY (date_column, key_column);"})
        if action == "REVIEW":
            issues.append({"severity":"LOW",
                "title": f"{wh}: No Activity — Review Needed",
                "detail": "Warehouse exists but had zero queries and zero credits.",
                "fix_sql": f"-- If truly unused:\nDROP WAREHOUSE IF EXISTS {wh};\n-- Or just suspend:\nALTER WAREHOUSE {wh} SUSPEND;"})

        # ── Auto-Suspend Timing ─────────────────────────────────
        # Based on query volume: kitni queries hain → kitna suspend time sahi hai
        if not is_sys:
            if queries == 0:
                rec_suspend_min = 1
                suspend_reason  = "No activity — suspend immediately when idle"
            elif queries < 20:
                rec_suspend_min = 1
                suspend_reason  = f"Only {queries} queries in 7 days — suspend after 1 min idle"
            elif queries < 100:
                rec_suspend_min = 5
                suspend_reason  = f"{queries} queries — suspend after 5 min idle"
            elif queries < 500:
                rec_suspend_min = 10
                suspend_reason  = f"{queries} queries — suspend after 10 min idle"
            else:
                rec_suspend_min = 15
                suspend_reason  = f"Active warehouse ({queries} queries) — 15 min idle suspend"

            if rec_suspend_min <= 5 and queries < 100:
                issues.append({"severity":"LOW",
                    "title": f"{wh}: Set AUTO_SUSPEND = {rec_suspend_min} min to reduce idle waste",
                    "detail": suspend_reason,
                    "fix_sql": (f"ALTER WAREHOUSE {wh} SET AUTO_SUSPEND = {rec_suspend_min * 60};\n"
                                f"ALTER WAREHOUSE {wh} SET AUTO_RESUME = TRUE;")})
        else:
            rec_suspend_min = None
            suspend_reason  = "Managed by Snowflake"

        wh_obj = {
            "warehouse":     wh,
            "type":          "System (Snowflake)" if is_sys else "User Warehouse",
            "current_size":  current_sz,
            "size_recommendation": size_rec,
            "action":        action,
            "action_reason": action_why,
            "queries":       queries,
            "credits":       round(credits, 4),
            "credit_share":  credit_pct,
            "est_cost_usd":  est_cost,
            "avg_exec_sec":  round(avg_exec, 2),
            "queue_pct":     round(queue, 2),
            "spill_rate_pct":round(spill, 2),
            "local_spill_gb":round(local_gb, 4),
            "remote_spill_gb":round(remote_gb, 4),
            "spill_severity":spill_severity,
            "spill_detail":  spill_reason,
            "pruning_pct":   round(pruning, 1),
            "pruning_note":  pruning_note,
            "rec_suspend_min": rec_suspend_min,
            "suspend_reason":  suspend_reason,
            "issues":        issues,
        }
        warehouses.append(wh_obj)
        recs.extend(issues)

    high_c   = sum(1 for r in recs if r["severity"]=="HIGH")
    medium_c = sum(1 for r in recs if r["severity"]=="MEDIUM")
    score    = max(0, 100 - high_c*20 - medium_c*8)

    return {
        "warehouses":         warehouses,
        "recommendations":    sorted(recs, key=lambda x: {"HIGH":0,"MEDIUM":1,"LOW":2}[x["severity"]]),
        "score":              score,
        "total_credits":      round(total_credits_all, 4),
        "total_cost_usd":     round(total_credits_all * CREDIT_PRICE_USD, 2),
        "user_warehouses":    [w for w in warehouses if w["type"]=="User Warehouse"],
        "system_warehouses":  [w for w in warehouses if w["type"]!="User Warehouse"],
    }

def _empty_wh():
    return {"warehouses":[],"recommendations":[],"score":100,"total_credits":0,
            "total_cost_usd":0,"user_warehouses":[],"system_warehouses":[]}


# ══════════════════════════════════════════════════════════════════
# 2. QUERY INTELLIGENCE
#    Input:  query_intelligence table
#    Output: slow queries, time patterns, resource usage, idle gaps
# ══════════════════════════════════════════════════════════════════

def analyze_queries(data: dict) -> dict:
    df = _to_df(data.get("query_intelligence", {}))
    if df.empty:
        return {"queries":[],"tag_summary":{},"recommendations":[],"score":100,
                "total":0,"problem_count":0,"time_analysis":{},"user_query_count":0}

    df = _n(df,"EXEC_SECONDS","QUEUED_SECONDS","SPILL_LOCAL_GB","SPILL_REMOTE_GB",
              "PRUNING_PCT","SCAN_PCT","PARTITIONS_SCANNED","PARTITIONS_TOTAL")

    if "START_TIME" in df.columns:
        df["START_DT"] = pd.to_datetime(df["START_TIME"], errors="coerce", utc=True)
    else:
        df["START_DT"] = pd.NaT

    # Split system vs user
    is_system = df["USER_NAME"]=="SYSTEM" if "USER_NAME" in df.columns else pd.Series([False]*len(df))
    sys_df    = df[is_system]
    usr_df    = df[~is_system]

    # ── Tag Summary ──────────────────────────────────────────────
    tag_summary = df["PROBLEM_TAG"].value_counts().to_dict() if "PROBLEM_TAG" in df.columns else {}

    # ── Time Pattern Analysis ────────────────────────────────────
    time_analysis = {}
    if not df["START_DT"].isna().all():
        df["hour"]     = df["START_DT"].dt.hour
        df["weekday"]  = df["START_DT"].dt.day_name()

        # Busiest hours
        hour_counts    = df.groupby("hour")["EXEC_SECONDS"].agg(["count","mean","max"]).reset_index()
        hour_counts.columns = ["hour","query_count","avg_exec","max_exec"]
        busiest_hour   = int(hour_counts.loc[hour_counts["query_count"].idxmax(),"hour"]) if len(hour_counts) > 0 else None
        slowest_hour   = int(hour_counts.loc[hour_counts["avg_exec"].idxmax(),"hour"]) if len(hour_counts) > 0 else None

        # Date range
        valid_dt = df["START_DT"].dropna()
        if len(valid_dt) > 0:
            date_from = _safe_dt(valid_dt.min())
            date_to   = _safe_dt(valid_dt.max())
        else:
            date_from = date_to = "N/A"

        # Warehouse-hour heatmap data
        if "WAREHOUSE_NAME" in df.columns:
            wh_hour = (df.groupby(["WAREHOUSE_NAME","hour"])["EXEC_SECONDS"]
                       .count().reset_index()
                       .rename(columns={"EXEC_SECONDS":"count"}))
            wh_hour_list = wh_hour.to_dict("records")
        else:
            wh_hour_list = []

        time_analysis = {
            "date_from":       date_from,
            "date_to":         date_to,
            "busiest_hour":    busiest_hour,
            "busiest_hour_fmt": _fmt_hour(busiest_hour),
            "slowest_hour":    slowest_hour,
            "slowest_hour_fmt": _fmt_hour(slowest_hour),
            "hourly_stats":    hour_counts.to_dict("records"),
            "wh_hour_heatmap": wh_hour_list,
        }

    # ── Top Slow Queries (user only) ─────────────────────────────
    queries_list = []
    display_df = df.sort_values("EXEC_SECONDS", ascending=False).head(100)
    for _, row in display_df.iterrows():
        dt      = _safe_dt(row.get("START_DT",""))
        exec_s  = float(row.get("EXEC_SECONDS",0))
        q_text  = str(row.get("QUERY_TEXT",""))[:150].strip()
        user    = row.get("USER_NAME","")
        wh      = row.get("WAREHOUSE_NAME","")
        tag     = row.get("PROBLEM_TAG","OK")
        prune   = float(row.get("PRUNING_PCT",100))
        spill   = float(row.get("SPILL_LOCAL_GB",0)) + float(row.get("SPILL_REMOTE_GB",0))
        queued  = float(row.get("QUEUED_SECONDS",0))

        # Human readable duration
        if exec_s >= 60:
            duration = f"{int(exec_s//60)}m {int(exec_s%60)}s"
        else:
            duration = f"{exec_s:.1f}s"

        # Resource grade
        if exec_s > 60 or spill > 0.1:   grade = "⚠️ Heavy"
        elif exec_s > 10:                  grade = "🟡 Moderate"
        else:                              grade = "✅ Light"

        queries_list.append({
            "query_id":    str(row.get("QUERY_ID",""))[:20],
            "user":        user,
            "warehouse":   wh,
            "exec_sec":    exec_s,
            "duration":    duration,
            "queued_sec":  queued,
            "spill_gb":    round(spill, 4),
            "pruning_pct": round(prune, 1),
            "tag":         tag,
            "grade":       grade,
            "start_time":  dt,
            "query":       q_text if q_text else "(system internal)",
        })

    # ── Per-Warehouse Query Stats ────────────────────────────────
    wh_query_stats = []
    if "WAREHOUSE_NAME" in df.columns:
        for wh_name, grp in df.groupby("WAREHOUSE_NAME"):
            user_grp = grp[grp["USER_NAME"]!="SYSTEM"] if "USER_NAME" in grp.columns else grp
            wh_query_stats.append({
                "warehouse":        wh_name,
                "total_queries":    len(grp),
                "user_queries":     len(user_grp),
                "system_queries":   len(grp) - len(user_grp),
                "avg_exec_sec":     round(float(grp["EXEC_SECONDS"].mean()), 2),
                "max_exec_sec":     round(float(grp["EXEC_SECONDS"].max()), 2),
                "p95_exec_sec":     round(float(grp["EXEC_SECONDS"].quantile(0.95)), 2),
                "total_spill_gb":   round(float(grp.get("SPILL_LOCAL_GB",pd.Series([0])).sum()) +
                                         float(grp.get("SPILL_REMOTE_GB",pd.Series([0])).sum()), 4),
                "avg_pruning_pct":  round(float(grp["PRUNING_PCT"].mean()), 1),
            })

    # ── Recommendations ──────────────────────────────────────────
    recommendations = []

    sys_pct = round(len(sys_df)/max(len(df),1)*100, 1)
    if sys_pct > 70:
        recommendations.append({"severity":"LOW",
            "title": f"{sys_pct:.0f}% queries are internal Snowflake system tasks — normal",
            "detail": ("SYSTEM user runs background maintenance: upgrades, task scheduling, "
                       "metadata sync. These run on COMPUTE_SERVICE_WH warehouses which are "
                       "billed by Snowflake, not charged to your account credits."),
            "fix_sql": ""})

    # Slow user queries
    slow_usr = usr_df[usr_df["EXEC_SECONDS"] > 30] if not usr_df.empty and "EXEC_SECONDS" in usr_df.columns else pd.DataFrame()
    if len(slow_usr) > 0:
        worst = slow_usr.sort_values("EXEC_SECONDS", ascending=False).iloc[0]
        recommendations.append({"severity":"MEDIUM",
            "title": f"{len(slow_usr)} of your queries took >30 seconds",
            "detail": (f"Slowest: {float(worst['EXEC_SECONDS']):.1f}s on {worst.get('WAREHOUSE_NAME','')} "
                       f"at {_safe_dt(worst.get('START_DT',''))}. "
                       f"User: {worst.get('USER_NAME','')}"),
            "fix_sql": ("-- Find your slow queries:\n"
                        "SELECT USER_NAME, WAREHOUSE_NAME,\n"
                        "       ROUND(EXECUTION_TIME/1000,1) AS exec_sec,\n"
                        "       LEFT(QUERY_TEXT,200)\n"
                        "FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY\n"
                        "WHERE EXECUTION_TIME > 30000\n"
                        "  AND USER_NAME != 'SYSTEM'\n"
                        "ORDER BY EXECUTION_TIME DESC LIMIT 20;")})

    # Queue time in user queries
    queued_usr = usr_df[usr_df["QUEUED_SECONDS"] > 1] if not usr_df.empty and "QUEUED_SECONDS" in usr_df.columns else pd.DataFrame()
    if len(queued_usr) > 0:
        recommendations.append({"severity":"MEDIUM",
            "title": f"{len(queued_usr)} user queries had significant queue wait (>1s)",
            "detail": "Queries waiting in queue — warehouse may be busy or undersized during peak hours.",
            "fix_sql": ("-- Check peak usage time and consider scaling up:\n"
                        "-- Admin → Warehouses → [select warehouse] → Query Activity")})

    # Poor pruning in user queries
    poor_prune_usr = usr_df[usr_df["PRUNING_PCT"] < 70] if not usr_df.empty and "PRUNING_PCT" in usr_df.columns else pd.DataFrame()
    if len(poor_prune_usr) > 2:
        recommendations.append({"severity":"MEDIUM",
            "title": f"{len(poor_prune_usr)} user queries have poor partition pruning (<70%)",
            "detail": "Queries scanning too many micro-partitions — missing cluster keys or WHERE filters.",
            "fix_sql": ("-- Find tables needing clustering:\n"
                        "SELECT TABLE_NAME, CLUSTERING_KEY, ROW_COUNT\n"
                        "FROM INFORMATION_SCHEMA.TABLES\n"
                        "WHERE TABLE_SCHEMA = 'your_schema'\n"
                        "  AND CLUSTERING_KEY IS NULL\n"
                        "  AND ROW_COUNT > 1000000;\n\n"
                        "ALTER TABLE big_table CLUSTER BY (date_col);" )})

    total = len(df)
    ok_c  = tag_summary.get("OK", 0)
    score = max(0, 100 - int((total-ok_c)/max(total,1)*80))

    return {
        "queries":          queries_list,
        "tag_summary":      tag_summary,
        "wh_query_stats":   wh_query_stats,
        "time_analysis":    time_analysis,
        "recommendations":  recommendations,
        "score":            score,
        "total":            total,
        "problem_count":    total - ok_c,
        "user_query_count": len(usr_df),
        "system_pct":       sys_pct,
    }


# ══════════════════════════════════════════════════════════════════
# 3. SPEND ANOMALY
#    Input:  spend_anomaly table
#    Output: daily spend, spikes, possible reasons
# ══════════════════════════════════════════════════════════════════

def analyze_anomalies(data: dict) -> dict:
    df = _to_df(data.get("spend_anomaly", {}))
    if df.empty:
        return {"daily":[],"anomalies":[],"recommendations":[],"score":100,
                "anomaly_count":0,"warning_count":0}

    df = _n(df,"DAILY_CREDITS","ROLLING_7D_AVG","SPIKE_RATIO")

    if "DT" in df.columns:
        df["DT_parsed"] = pd.to_datetime(df["DT"], errors="coerce", utc=True)
        df["DATE_LABEL"] = df["DT_parsed"].dt.strftime("%b %d, %Y").fillna("Unknown")
        df["DAY_OF_WEEK"] = df["DT_parsed"].dt.day_name().fillna("")
        df["HOUR"]        = df["DT_parsed"].dt.hour.fillna(0).astype(int)
    else:
        df["DATE_LABEL"] = "Unknown"
        df["DAY_OF_WEEK"] = ""
        df["HOUR"]        = 0

    anomalies = []
    if "ALERT_STATUS" in df.columns:
        for _, row in df[df["ALERT_STATUS"].isin(["ANOMALY","WARNING"])].iterrows():
            cred    = float(row.get("DAILY_CREDITS",0))
            avg_c   = float(row.get("ROLLING_7D_AVG",0))
            spike   = float(row.get("SPIKE_RATIO",0))
            wh      = row.get("WAREHOUSE_NAME","")
            dt_str  = row.get("DATE_LABEL","")
            dow     = row.get("DAY_OF_WEEK","")
            status  = row.get("ALERT_STATUS","")

            # ── Possible Reason ────────────────────────────────
            reasons = []
            if spike > 5:
                reasons.append("Very large spike — likely a bulk load, full-table scan, or runaway query")
            elif spike > 2:
                reasons.append("Unusual workload — possibly a new ETL job or larger-than-usual dataset")
            if dow in ("Saturday","Sunday"):
                reasons.append("Weekend anomaly — unexpected activity on non-business day")
            if avg_c < 0.01 and cred > 0.1:
                reasons.append("Account normally almost idle — this day had unusually high activity")
            if not reasons:
                reasons.append("Workload higher than 7-day rolling average")

            anomalies.append({
                "date":          dt_str,
                "day_of_week":   dow,
                "warehouse":     wh,
                "credits":       round(cred, 4),
                "avg_credits":   round(avg_c, 4),
                "spike_ratio":   round(spike, 3),
                "status":        status,
                "est_cost_usd":  round(cred * CREDIT_PRICE_USD, 3),
                "possible_reasons": reasons,
            })

    high_a   = [a for a in anomalies if a["status"]=="ANOMALY"]
    warnings = [a for a in anomalies if a["status"]=="WARNING"]

    recommendations = []
    for a in sorted(high_a, key=lambda x: x["spike_ratio"], reverse=True):
        reasons_txt = " | ".join(a["possible_reasons"])
        recommendations.append({"severity":"HIGH",
            "title": f"🔴 ANOMALY on {a['date']} ({a['day_of_week']}) — {a['warehouse']}: {a['spike_ratio']:.2f}x spike",
            "detail": (f"Used {a['credits']:.4f} credits (${a['est_cost_usd']:.3f}) vs "
                       f"7-day avg of {a['avg_credits']:.4f} credits. "
                       f"Possible cause: {reasons_txt}"),
            "fix_sql": (f"-- Investigate what ran on this day:\n"
                        f"SELECT USER_NAME,\n"
                        f"       LEFT(QUERY_TEXT, 300) AS query,\n"
                        f"       ROUND(EXECUTION_TIME/1000, 1) AS exec_sec,\n"
                        f"       ROUND(BYTES_SCANNED/1e9, 2) AS gb_scanned,\n"
                        f"       START_TIME\n"
                        f"FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY\n"
                        f"WHERE WAREHOUSE_NAME = '{a['warehouse']}'\n"
                        f"  AND DATE_TRUNC('day', START_TIME) = (SELECT MIN(DT)\n"
                        f"      FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY\n"
                        f"      WHERE CREDITS_USED = {a['credits']})\n"
                        f"ORDER BY EXECUTION_TIME DESC\n"
                        f"LIMIT 25;")})

    for a in sorted(warnings, key=lambda x: x["spike_ratio"], reverse=True):
        recommendations.append({"severity":"MEDIUM",
            "title": f"🟡 WARNING on {a['date']}: {a['warehouse']} {a['spike_ratio']:.2f}x above normal",
            "detail": f"Credits: {a['credits']:.4f} vs avg {a['avg_credits']:.4f}. {' | '.join(a['possible_reasons'])}",
            "fix_sql": ""})

    if not anomalies and len(df) > 0:
        recommendations.append({"severity":"LOW",
            "title": "✅ No spend anomalies — all days within normal range",
            "detail": "Daily credit usage is consistent with historical 7-day average.",
            "fix_sql": ""})

    # Daily list for charts
    daily_list = []
    for _, row in df.iterrows():
        daily_list.append({
            "date":      str(row.get("DT",""))[:10],
            "label":     row.get("DATE_LABEL",""),
            "day":       row.get("DAY_OF_WEEK",""),
            "warehouse": row.get("WAREHOUSE_NAME",""),
            "credits":   float(row.get("DAILY_CREDITS",0)),
            "avg":       float(row.get("ROLLING_7D_AVG",0)),
            "spike":     float(row.get("SPIKE_RATIO",0)),
            "status":    row.get("ALERT_STATUS","NORMAL"),
            "est_cost":  round(float(row.get("DAILY_CREDITS",0))*CREDIT_PRICE_USD, 3),
        })

    score = max(0, 100 - len(high_a)*20 - len(warnings)*8)
    return {"daily":daily_list,"anomalies":anomalies,"recommendations":recommendations,
            "score":score,"anomaly_count":len(high_a),"warning_count":len(warnings)}


# ══════════════════════════════════════════════════════════════════
# 4. COST BREAKDOWN
#    Input:  warehouse_metering + cost_by_user
#    Output: per-user analytics + warehouse trend
# ══════════════════════════════════════════════════════════════════

def analyze_cost(data: dict) -> dict:
    wm_df  = _to_df(data.get("warehouse_metering", {}))
    usr_df = _to_df(data.get("cost_by_user", {}))

    # ── Warehouse daily ──────────────────────────────────────────
    by_warehouse = []
    wh_totals    = {}
    if not wm_df.empty:
        wm_df = _n(wm_df,"TOTAL_CREDITS","COMPUTE_CREDITS","CLOUD_CREDITS")
        for _, row in wm_df.iterrows():
            cred = float(row.get("TOTAL_CREDITS",0))
            wh   = row.get("WAREHOUSE_NAME","")
            wh_totals[wh] = wh_totals.get(wh,0) + cred
            by_warehouse.append({
                "warehouse": wh,
                "date":      str(row.get("USAGE_DATE",""))[:10],
                "credits":   round(cred,4),
                "compute":   round(float(row.get("COMPUTE_CREDITS",0)),4),
                "cloud":     round(float(row.get("CLOUD_CREDITS",0)),4),
                "est_cost":  round(cred*CREDIT_PRICE_USD,3),
            })

    total_credits = sum(wh_totals.values())

    # ── User analytics ───────────────────────────────────────────
    by_user = []
    if not usr_df.empty:
        usr_df = _n(usr_df,"TOTAL_QUERIES","AVG_EXEC_SEC","TOTAL_EXEC_HOURS","TOTAL_SPILL_GB",
                    "WAREHOUSES_USED","DATABASES_USED")
        total_q = float(usr_df["TOTAL_QUERIES"].sum())
        total_h = float(usr_df["TOTAL_EXEC_HOURS"].sum())

        for _, row in usr_df.iterrows():
            uname   = row.get("USER_NAME","")
            role    = row.get("ROLE_NAME","")
            queries = int(row.get("TOTAL_QUERIES",0))
            avg_sec = float(row.get("AVG_EXEC_SEC",0))
            hrs     = float(row.get("TOTAL_EXEC_HOURS",0))
            spill   = float(row.get("TOTAL_SPILL_GB",0))
            whs     = int(row.get("WAREHOUSES_USED",0))
            dbs     = int(row.get("DATABASES_USED",0))
            is_sys  = uname == "SYSTEM"

            q_share  = round(queries/max(total_q,1)*100,1)
            h_share  = round(hrs/max(total_h,1)*100,1)

            # User profile
            if is_sys:
                profile = "Snowflake Internal"
                note    = "Background system tasks — not user activity"
            elif "ADMIN" in role.upper():
                profile = "Admin / DBA"
                note    = f"Admin user — {queries} queries, {avg_sec:.2f}s avg"
            elif "SERVICE" in uname.upper() or "TOOL" in uname.upper():
                profile = "Service Account"
                note    = f"Automated service — {queries} queries"
            else:
                profile = "Analyst / Developer"
                note    = f"{queries} queries across {whs} warehouse(s), {dbs} database(s)"

            by_user.append({
                "user":          uname,
                "role":          role,
                "profile":       profile,
                "note":          note,
                "queries":       queries,
                "query_share":   q_share,
                "avg_exec_sec":  round(avg_sec,3),
                "exec_hours":    round(hrs,4),
                "hour_share":    h_share,
                "spill_gb":      round(spill,4),
                "warehouses_used":whs,
                "databases_used":dbs,
                "is_system":     is_sys,
            })

    # ── Warehouse usage analysis ─────────────────────────────────
    wh_analysis = []
    if wh_totals:
        sorted_wh = sorted(wh_totals.items(), key=lambda x: x[1], reverse=True)
        for wh, cred in sorted_wh:
            is_sys = wh.startswith("COMPUTE_SERVICE_WH") or wh == "CLOUD_SERVICES_ONLY"
            wh_analysis.append({
                "warehouse":    wh,
                "total_credits":round(cred,4),
                "credit_share": round(cred/max(total_credits,0.0001)*100,1),
                "est_cost_usd": round(cred*CREDIT_PRICE_USD,2),
                "is_system":    is_sys,
                "note":         "Snowflake-managed (not billed to your credits)" if is_sys else "",
            })

    recommendations = []
    real_user_wh = [w for w in wh_analysis if not w["is_system"]]
    if real_user_wh and len(real_user_wh) == 1:
        recommendations.append({"severity":"LOW",
            "title": f"All user credit spend on single warehouse: {real_user_wh[0]['warehouse']}",
            "detail": f"Total: {real_user_wh[0]['total_credits']:.4f} credits (${real_user_wh[0]['est_cost_usd']:.2f}). "
                      f"Normal for small accounts — separate ETL and reporting workloads as you scale.",
            "fix_sql": ""})

    sys_users = [u for u in by_user if u["is_system"]]
    real_users= [u for u in by_user if not u["is_system"]]
    if sys_users:
        sys_q_pct = sum(u["query_share"] for u in sys_users)
        if sys_q_pct > 80:
            recommendations.append({"severity":"LOW",
                "title": f"SYSTEM user runs {sys_q_pct:.0f}% of queries — this is normal",
                "detail": "Snowflake internal background tasks dominate query count. Your real user activity is smaller.",
                "fix_sql": ""})

    return {"by_warehouse":by_warehouse,"by_user":by_user,"wh_analysis":wh_analysis,
            "recommendations":recommendations,"total_credits":round(total_credits,4),
            "total_cost_usd":round(total_credits*CREDIT_PRICE_USD,2)}


# ══════════════════════════════════════════════════════════════════
# 5. STORAGE OPTIMIZER
# ══════════════════════════════════════════════════════════════════

def analyze_storage(data: dict) -> dict:
    df = _to_df(data.get("storage", {}))
    if df.empty:
        return {"tables":[],"recommendations":[],"score":100,"total_waste_usd":0,
                "bloated_count":0,"system_table_count":0,"total_active_gb":0}

    df = _n(df,"ACTIVE_GB","TIME_TRAVEL_GB","FAILSAFE_GB","BLOAT_PCT","EST_MONTHLY_WASTE_USD")

    tables = []
    for _, row in df.iterrows():
        active = float(row.get("ACTIVE_GB",0))
        tt     = float(row.get("TIME_TRAVEL_GB",0))
        fs     = float(row.get("FAILSAFE_GB",0))
        db     = str(row.get("DATABASE_NAME","") or "")
        schema = str(row.get("SCHEMA_NAME","")  or "")
        tbl    = row.get("TABLE_NAME","")
        is_sys = db.upper() in ("SNOWFLAKE","") or schema.upper().startswith("TRUST_CENTER")

        # Recalculate — BLOAT_PCT meaningless when active=0
        if active > 0:
            bloat = round((tt+fs)/active*100, 1)
            waste = round((tt+fs)/1024*23, 4)   # $23/TB/month
        else:
            bloat = 0
            waste = 0

        tables.append({
            "database":  db,"schema":schema,"table":tbl,
            "active_gb": round(active,4),"tt_gb":round(tt,4),"fs_gb":round(fs,4),
            "bloat_pct": bloat,"waste_usd":waste,"is_system":is_sys,
            "overhead_gb":round(tt+fs,4),
        })

    real_tables = [t for t in tables if not t["is_system"] and t["active_gb"] > 0]
    sys_tables  = [t for t in tables if t["is_system"]]
    bad_tables  = [t for t in real_tables if t["bloat_pct"] > 100]
    real_waste  = round(sum(t["waste_usd"] for t in real_tables), 4)
    total_active= round(sum(t["active_gb"] for t in real_tables), 4)

    recommendations = []
    if all(t["active_gb"] == 0 for t in tables):
        recommendations.append({"severity":"LOW",
            "title": "All tracked tables are Snowflake internal system tables (ACTIVE_GB = 0)",
            "detail": (f"{len(sys_tables)} system tables found (SNOWFLAKE.TRUST_CENTER_STATE.*). "
                       "These are Snowflake's own metadata tables — zero user data. "
                       "Real storage waste: $0. Your own tables will appear here once created."),
            "fix_sql": ("-- See your own tables:\n"
                        "SELECT TABLE_CATALOG, TABLE_SCHEMA, TABLE_NAME,\n"
                        "       ACTIVE_BYTES/1e9 AS active_gb\n"
                        "FROM SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS\n"
                        "WHERE TABLE_CATALOG != 'SNOWFLAKE'\n"
                        "  AND ACTIVE_BYTES > 0\n"
                        "ORDER BY ACTIVE_BYTES DESC;")})
    else:
        for t in sorted(bad_tables, key=lambda x: x["waste_usd"], reverse=True)[:5]:
            recommendations.append({"severity":"HIGH" if t["waste_usd"] > 100 else "MEDIUM",
                "title": f"{t['table']}: {t['bloat_pct']:.0f}% overhead (${t['waste_usd']:.2f}/mo)",
                "detail": (f"Active: {t['active_gb']:.3f}GB | "
                           f"Time Travel: {t['tt_gb']:.3f}GB | "
                           f"Failsafe: {t['fs_gb']:.3f}GB"),
                "fix_sql": f"ALTER TABLE {t['table']} SET DATA_RETENTION_TIME_IN_DAYS = 1;"})

    score = 100 if real_waste == 0 else (80 if real_waste < 100 else 60)
    return {"tables":tables,"recommendations":recommendations,"score":score,
            "total_waste_usd":real_waste,"bloated_count":len(bad_tables),
            "system_table_count":len(sys_tables),"total_active_gb":total_active}


# ══════════════════════════════════════════════════════════════════
# 6. USER SECURITY
# ══════════════════════════════════════════════════════════════════

def analyze_users(data: dict) -> dict:
    users_df = _to_df(data.get("users", {}))
    login_df = _to_df(data.get("login_history", {}))

    if users_df.empty:
        return {"users":[],"login_events":[],"security_events":[],"recommendations":[],
                "score":100,"inactive_count":0,"no_mfa_count":0,"admin_no_mfa":0,
                "failed_logins":0,"lock_events":0}

    users_df = _n(users_df,"DAYS_INACTIVE")
    users = []
    for _, row in users_df.iterrows():
        uname = row.get("USERNAME","")
        days  = int(float(row.get("DAYS_INACTIVE",0)))
        has_m = str(row.get("HAS_MFA","FALSE")).upper()=="TRUE"
        dis   = str(row.get("DISABLED","FALSE")).upper()=="TRUE"
        last  = str(row.get("LAST_SUCCESS_LOGIN","")).strip()
        if not last or last.lower() in ("none","nan",""):
            last = "Never logged in"
        else:
            last = last[:19].replace("T"," ")

        risk  = "LOW"
        if not has_m and "ADMIN" in str(row.get("DEFAULT_ROLE","")).upper(): risk = "HIGH"
        elif not has_m: risk = "MEDIUM"
        if days > 90 and not dis: risk = max(risk, "MEDIUM", key=lambda x: {"LOW":0,"MEDIUM":1,"HIGH":2}[x])

        users.append({"username":uname,"role":row.get("DEFAULT_ROLE",""),
            "has_mfa":has_m,"disabled":dis,"days_inactive":days,"last_login":last,
            "email":row.get("EMAIL",""),"risk":risk})

    inactive_90  = [u for u in users if u["days_inactive"]>90 and not u["disabled"]]
    no_mfa       = [u for u in users if not u["has_mfa"] and not u["disabled"]]
    admin_no_mfa = [u for u in no_mfa if "ADMIN" in u["role"].upper()]

    # Login security
    security_events = []
    login_events    = []
    failed_count    = 0

    if not login_df.empty:
        login_df = _n(login_df,"LOGIN_COUNT")
        for _, row in login_df.iterrows():
            ok    = str(row.get("IS_SUCCESS","NO")).upper() == "YES"
            err   = str(row.get("ERROR_MESSAGE","") or "").strip()
            count = int(float(row.get("LOGIN_COUNT",0)))
            dt    = str(row.get("LOGIN_DATE",""))[:10]
            user  = row.get("USER_NAME","")

            login_events.append({"user":user,"date":dt,"success":ok,"error":err,"count":count})
            if not ok:
                failed_count += count
                if "LOCKED" in err.upper():
                    security_events.append({"severity":"HIGH","date":dt,"user":user,
                        "event":"Account temporarily locked",
                        "detail":f"Too many failed attempts — account locked on {dt}"})
                elif "INCORRECT" in err.upper() and count >= 3:
                    security_events.append({"severity":"MEDIUM","date":dt,"user":user,
                        "event":f"{count} incorrect password attempts",
                        "detail":f"Repeated wrong password on {dt} — verify it was you"})
                elif "OVERFLOW" in err.upper():
                    security_events.append({"severity":"MEDIUM","date":dt,"user":user,
                        "event":"Login failure overflow",
                        "detail":f"Volume of failed attempts too high to fully log on {dt}"})

    lock_evts = [e for e in security_events if e["severity"]=="HIGH"]
    recommendations = []

    if lock_evts:
        recommendations.append({"severity":"HIGH",
            "title": f"🔐 Account lockout on {lock_evts[0]['date']} — {failed_count} total failed logins",
            "detail": (f"User {lock_evts[0]['user']} locked after repeated wrong password attempts. "
                       f"If this was not you — change password immediately and enable MFA."),
            "fix_sql": ("SELECT USER_NAME, ERROR_MESSAGE, EVENT_TIMESTAMP\n"
                        "FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY\n"
                        "WHERE IS_SUCCESS = 'NO'\n"
                        "ORDER BY EVENT_TIMESTAMP DESC LIMIT 50;\n\n"
                        "-- Reset password if suspicious:\n"
                        "ALTER USER <username> SET PASSWORD = 'NewSecurePassword123!';\n"
                        "ALTER USER <username> MUST_CHANGE_PASSWORD = TRUE;")})

    if admin_no_mfa:
        recommendations.append({"severity":"HIGH",
            "title": f"CRITICAL: {len(admin_no_mfa)} admin account(s) without MFA",
            "detail": (f"Users: {', '.join(u['username'] for u in admin_no_mfa)}. "
                       f"Admin accounts without MFA + recent login failures = high risk."),
            "fix_sql": ("-- Enable MFA: Snowflake UI → Profile → Multi-Factor Authentication → Enroll\n\n"
                        "-- Enforce MFA for all admins:\n"
                        "CREATE AUTHENTICATION POLICY require_mfa_policy\n"
                        "  MFA_AUTHENTICATION_METHODS = ('PASSWORD')\n"
                        "  MFA_ENROLLMENT = REQUIRED;\n"
                        "ALTER ACCOUNT SET AUTHENTICATION POLICY require_mfa_policy;")})

    elif no_mfa:
        recommendations.append({"severity":"MEDIUM",
            "title": f"{len(no_mfa)} user(s) without MFA enabled",
            "detail": f"Users: {', '.join(u['username'] for u in no_mfa)}. Enable MFA for all accounts.",
            "fix_sql": "-- Snowflake UI: Profile → Multi-Factor Authentication → Enroll"})

    if failed_count > 5 and not lock_evts:
        recommendations.append({"severity":"MEDIUM",
            "title": f"{failed_count} failed login attempts in last 30 days",
            "detail": "Review login history to check for unauthorized access attempts.",
            "fix_sql": ("SELECT USER_NAME, ERROR_MESSAGE, COUNT(*)\n"
                        "FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY\n"
                        "WHERE IS_SUCCESS='NO'\nGROUP BY 1,2 ORDER BY 3 DESC;")})

    for u in users:
        if ("SERVICE" in u["username"].upper() or "TOOL" in u["username"].upper()):
            if "Never" in u["last_login"]:
                recommendations.append({"severity":"LOW",
                    "title": f"Service account '{u['username']}' has never logged in",
                    "detail": "Review if this service account is still needed.",
                    "fix_sql": f"ALTER USER {u['username']} SET DISABLED = TRUE;"})

    if inactive_90:
        recommendations.append({"severity":"MEDIUM",
            "title": f"{len(inactive_90)} user(s) inactive 90+ days",
            "detail": f"Users: {', '.join(u['username'] for u in inactive_90)}",
            "fix_sql": "\n".join(f"ALTER USER {u['username']} SET DISABLED = TRUE;" for u in inactive_90)})

    score = 100
    score -= len(lock_evts)*25
    score -= len([e for e in security_events if e["severity"]=="MEDIUM"])*10
    score -= len(admin_no_mfa)*20
    score -= len(no_mfa)*8
    score -= len(inactive_90)*5
    score = max(0, score)

    return {"users":users,"login_events":login_events,"security_events":security_events,
            "recommendations":recommendations,"score":score,"inactive_count":len(inactive_90),
            "no_mfa_count":len(no_mfa),"admin_no_mfa":len(admin_no_mfa),
            "failed_logins":failed_count,"lock_events":len(lock_evts)}


# ══════════════════════════════════════════════════════════════════
# 7. NOTEBOOKS
# ══════════════════════════════════════════════════════════════════

def analyze_notebooks(data: dict) -> dict:
    df = _to_df(data.get("notebooks", {}))
    if df.empty:
        return {"notebooks":[],"note":"No notebook activity detected in last 30 days.","total_runs":0}
    return {"notebooks":[{"user":r.get("USER_NAME",""),"warehouse":r.get("WAREHOUSE_NAME",""),
        "database":r.get("DATABASE_NAME",""),"exec_sec":float(r.get("EXEC_SECONDS",0)),
        "spill_gb":float(r.get("SPILL_GB",0)),"date":str(r.get("RUN_DATE",""))[:10],
        "query":str(r.get("QUERY_PREVIEW",""))[:100]} for _,r in df.head(50).iterrows()],
        "total_runs":len(df)}


# ══════════════════════════════════════════════════════════════════
# 8. UNUSED OBJECTS
# ══════════════════════════════════════════════════════════════════

def analyze_unused_objects(data: dict) -> dict:
    df = _to_df(data.get("unused_objects", {}))
    if df.empty:
        return {"tables": [], "recommendations": [], "total_size_gb": 0, "potential_savings_usd": 0}
    
    df = _n(df, "SIZE_GB", "ROW_COUNT")
    tables = []
    total_size = 0
    for _, row in df.iterrows():
        size = float(row.get("SIZE_GB", 0))
        total_size += size
        tables.append({
            "name": row.get("FULL_TABLE_NAME", ""),
            "type": row.get("TABLE_TYPE", ""),
            "rows": int(row.get("ROW_COUNT", 0)),
            "size_gb": round(size, 3),
            "created": _safe_dt(row.get("CREATED", "")),
            "last_altered": _safe_dt(row.get("LAST_ALTERED", ""))
        })
    
    # $23 per TB per month = $0.023 per GB per month
    potential_savings = round(total_size * 0.023, 2)
    
    recs = []
    if tables:
        recs.append({
            "severity": "MEDIUM",
            "title": f"Found {len(tables)} unused tables in last 30 days",
            "detail": f"Total size: {total_size:.2f} GB. Potential savings: ${potential_savings:.2f}/month by dropping or archiving these.",
            "fix_sql": f"-- Example: Drop the largest unused table\nDROP TABLE {tables[0]['name']};"
        })
        
    return {
        "tables": tables,
        "recommendations": recs,
        "total_size_gb": round(total_size, 2),
        "potential_savings_usd": potential_savings
    }


# ══════════════════════════════════════════════════════════════════
# 9. CLOUD SERVICES
# ══════════════════════════════════════════════════════════════════

def analyze_cloud_services(data: dict) -> dict:
    df = _to_df(data.get("cloud_services", {}))
    if df.empty:
        return {"warehouses": [], "recommendations": [], "total_cloud_credits": 0}
    
    df = _n(df, "CLOUD_SERVICES_CREDITS", "COMPUTE_CREDITS", "TOTAL_CREDITS", "CLOUD_SERVICES_PCT")
    warehouses = []
    total_cloud = 0
    for _, row in df.iterrows():
        cloud = float(row.get("CLOUD_SERVICES_CREDITS", 0))
        total_cloud += cloud
        warehouses.append({
            "warehouse": row.get("WAREHOUSE_NAME", ""),
            "cloud_credits": round(cloud, 4),
            "compute_credits": round(float(row.get("COMPUTE_CREDITS", 0)), 4),
            "total_credits": round(float(row.get("TOTAL_CREDITS", 0)), 4),
            "cloud_pct": round(float(row.get("CLOUD_SERVICES_PCT", 0)), 2)
        })
    
    recs = []
    high_cloud = [w for w in warehouses if w["cloud_pct"] > 10 and w["total_credits"] > 1]
    for w in high_cloud:
        recs.append({
            "severity": "MEDIUM",
            "title": f"High Cloud Services ratio on {w['warehouse']} ({w['cloud_pct']:.1f}%)",
            "detail": f"Cloud Services: {w['cloud_credits']:.2f} credits. This usually indicates high metadata operations or many small queries.",
            "fix_sql": f"-- Check for many small queries:\nSELECT QUERY_TEXT, EXECUTION_TIME\nFROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY\nWHERE WAREHOUSE_NAME = '{w['warehouse']}'\nAND EXECUTION_TIME < 100\nORDER BY START_TIME DESC LIMIT 100;"
        })
        
    return {
        "warehouses": warehouses,
        "recommendations": recs,
        "total_cloud_credits": round(total_cloud, 4)
    }


# ══════════════════════════════════════════════════════════════════
# HEALTH SCORE
# ══════════════════════════════════════════════════════════════════

def calculate_health_score(wh, qry, anomaly, storage, users) -> dict:
    scores = {
        "query":    qry.get("score",100),
        "warehouse":wh.get("score",100),
        "storage":  storage.get("score",100),
        "users":    users.get("score",100),
        "anomaly":  anomaly.get("score",100),
    }
    weighted = (scores["query"]*0.35 + scores["warehouse"]*0.30 +
                scores["storage"]*0.15 + scores["users"]*0.20)
    anomaly_penalty = min(15, (100-scores["anomaly"])*0.15)
    final = max(0, round(weighted - anomaly_penalty))

    if final>=80:   grade,color,emoji = "Excellent",   "#16a34a","🟢"
    elif final>=65: grade,color,emoji = "Healthy",     "#22c55e","✅"
    elif final>=50: grade,color,emoji = "Fair",        "#f59e0b","🟡"
    elif final>=35: grade,color,emoji = "Poor",        "#ef4444","🔴"
    else:           grade,color,emoji = "Critical",    "#991b1b","🚨"

    return {"overall":final,"grade":grade,"color":color,"emoji":emoji,
            "scores":scores,"anomaly_penalty":round(anomaly_penalty,1)}


# ══════════════════════════════════════════════════════════════════
# AI-READY JSON EXPORT
#    Structured output for any AI layer (GPT, Claude, etc.)
#    Contains: account summary + all findings + all recommendations
# ══════════════════════════════════════════════════════════════════

def build_ai_json(account_info: dict, health: dict, wh, qry, anomaly,
                  cost, storage, users, notebooks, unused, cloud, raw_data: dict) -> dict:
    """
    AI layer ke liye structured JSON.
    Yeh format directly kisi bhi LLM ko de sakte hain — woh apni insights dega.
    """
    all_recs = []
    for module_name, module in [("warehouse",wh),("queries",qry),("anomaly",anomaly),
                                  ("storage",storage),("users",users),("cost",cost),
                                  ("unused",unused),("cloud",cloud)]:
        for r in module.get("recommendations",[]):
            all_recs.append({**r, "module": module_name})

    return {
        "schema_version": "1.0",
        "exported_at":    datetime.now().isoformat(),
        "tool":           "SnowAdvisor",

        # ── Account ──────────────────────────────────────────────
        "account": {
            "name":      account_info.get("account",""),
            "user":      account_info.get("user",""),
            "role":      account_info.get("role",""),
            "warehouse": account_info.get("warehouse",""),
        },

        # ── Health ───────────────────────────────────────────────
        "health_score": {
            "overall":     health["overall"],
            "grade":       health["grade"],
            "breakdown":   health["scores"],
            "anomaly_penalty": health["anomaly_penalty"],
        },

        # ── Overall Findings ─────────────────────────────────────
        "summary": {
            "total_credits_30d":    cost.get("total_credits", 0),
            "total_cost_usd_30d":   cost.get("total_cost_usd", 0),
            "anomalies_30d":        anomaly.get("anomaly_count", 0),
            "stale_storage_usd":    unused.get("total_stale_usd", 0),
            "billed_cloud_credits": cloud.get("billed_cs_credits", 0),
            "total_users":          len(users.get("users", [])),
        },

        # ── Summary Stats ────────────────────────────────────────
        "summary": {
            "total_credits_30d":    cost.get("total_credits", 0),
            "total_cost_usd_30d":   cost.get("total_cost_usd", 0),
            "warehouses_count":     len(wh.get("warehouses",[])),
            "user_warehouses":      len(wh.get("user_warehouses",[])),
            "total_queries_7d":     qry.get("total",0),
            "user_queries_7d":      qry.get("user_query_count",0),
            "anomalies_30d":        anomaly.get("anomaly_count",0),
            "warnings_30d":         anomaly.get("warning_count",0),
            "total_users":          len(users.get("users",[])),
            "users_without_mfa":    users.get("no_mfa_count",0),
            "failed_logins_30d":    users.get("failed_logins",0),
            "storage_waste_usd":    storage.get("total_waste_usd",0),
        },

        # ── All Recommendations (sorted by severity) ─────────────
        "recommendations": sorted(all_recs,
            key=lambda x: {"HIGH":0,"MEDIUM":1,"LOW":2}.get(x.get("severity","LOW"),3)),

        # ── Module Details ────────────────────────────────────────
        "warehouse_analysis": {
            "warehouses":      wh.get("warehouses",[]),
            "total_credits":   wh.get("total_credits",0),
            "user_warehouses": wh.get("user_warehouses",[]),
        },

        "query_analysis": {
            "tag_distribution":   qry.get("tag_summary",{}),
            "wh_query_stats":     qry.get("wh_query_stats",[]),
            "time_analysis":      qry.get("time_analysis",{}),
            "top_slow_queries":   [q for q in qry.get("queries",[]) if q["exec_sec"] > 5][:20],
        },

        "spend_analysis": {
            "anomalies":      anomaly.get("anomalies",[]),
            "daily_trend":    anomaly.get("daily",[]),
        },

        "cost_analysis": {
            "by_user":        cost.get("by_user",[]),
            "wh_totals":      cost.get("wh_analysis",[]),
        },

        "storage_analysis": {
            "total_active_gb": storage.get("total_active_gb",0),
            "total_waste_usd": storage.get("total_waste_usd",0),
            "bloated_tables":  [t for t in storage.get("tables",[]) if t.get("bloat_pct",0) > 50],
        },

        "security_analysis": {
            "security_events":  users.get("security_events",[]),
            "users_at_risk":    [u for u in users.get("users",[]) if u.get("risk") in ("HIGH","MEDIUM")],
            "login_summary": {
                "failed_logins": users.get("failed_logins",0),
                "lock_events":   users.get("lock_events",0),
                "no_mfa_count":  users.get("no_mfa_count",0),
            },
        },

        "notebook_activity": notebooks,

        "unused_objects": unused,
        "cloud_services": cloud,
    }


# ══════════════════════════════════════════════════════════════════
# 8. SAVINGS ESTIMATOR
#    Har recommendation ke liye concrete $ savings calculate karo
# ══════════════════════════════════════════════════════════════════

_WH_CREDITS_PER_HR = {
    "X-Small": 1, "Small": 2, "Medium": 4, "Large": 8,
    "X-Large": 16, "2X-Large": 32, "3X-Large": 64, "4X-Large": 128
}

def _downsize_credits(current_size: str) -> float:
    sizes = list(_WH_CREDITS_PER_HR.keys())
    try:
        idx = sizes.index(current_size)
        return _WH_CREDITS_PER_HR[sizes[max(0, idx - 1)]]
    except (ValueError, IndexError):
        return _WH_CREDITS_PER_HR.get(current_size, 1)

def estimate_savings(wh_result: dict, storage_result: dict,
                     cost_result: dict, anomaly_result: dict) -> dict:
    """
    Har category mein potential monthly savings calculate karo.
    Formula: credits x $3/credit x hours_used
    """
    CREDIT_PRICE = 3.0
    STORAGE_RATE = 23.0   # $23 per TB per month
    items        = []
    total_saving = 0.0

    # ── 1. Warehouse Downsize Savings ────────────────────────────
    for wh in wh_result.get("user_warehouses", []):
        action       = wh.get("action", "")
        current_sz   = wh.get("current_size", "")
        credits_used = wh.get("credits", 0)          # 30-day credits
        wh_name      = wh.get("warehouse", "")

        if action == "CONSIDER_DOWNSIZE" and credits_used > 0 and current_sz in _WH_CREDITS_PER_HR:
            current_cr  = _WH_CREDITS_PER_HR.get(current_sz, 1)
            smaller_cr  = _downsize_credits(current_sz)
            # saving ratio = (current - smaller) / current
            save_ratio  = (current_cr - smaller_cr) / current_cr
            saved_cr    = round(credits_used * save_ratio, 4)
            saved_usd   = round(saved_cr * CREDIT_PRICE, 2)
            if saved_usd > 0:
                items.append({
                    "category":    "Warehouse Downsize",
                    "warehouse":   wh_name,
                    "detail":      f"Downsize {wh_name} from {current_sz} → smaller size",
                    "saving_cr":   saved_cr,
                    "saving_usd":  saved_usd,
                    "period":      "monthly",
                    "confidence":  "Medium",
                    "fix_sql":     f"ALTER WAREHOUSE {wh_name} SET WAREHOUSE_SIZE = '{_WH_SIZES[max(0,_WH_SIZES.index(current_sz)-1)]}';"
                                   if current_sz in _WH_SIZES else "",
                })
                total_saving += saved_usd

        # Idle warehouse — can be suspended (save 100% of idle credits)
        if action == "REVIEW" and credits_used > 0:
            saved_usd = round(credits_used * CREDIT_PRICE, 2)
            items.append({
                "category":   "Idle Warehouse",
                "warehouse":  wh_name,
                "detail":     f"{wh_name} had {credits_used:.4f} credits with zero useful queries — suspend it",
                "saving_cr":  credits_used,
                "saving_usd": saved_usd,
                "period":     "monthly",
                "confidence": "High",
                "fix_sql":    f"ALTER WAREHOUSE {wh_name} SUSPEND;\n-- Or drop if truly unused:\nDROP WAREHOUSE IF EXISTS {wh_name};",
            })
            total_saving += saved_usd

    # ── 2. Storage Savings ───────────────────────────────────────
    for tbl in storage_result.get("tables", []):
        if tbl.get("active_gb", 0) > 0 and tbl.get("bloat_pct", 0) > 100:
            overhead_gb  = tbl.get("overhead_gb", 0)
            # Reducing DATA_RETENTION to 1 day saves most of Time Travel
            tt_gb        = tbl.get("tt_gb", 0)
            saved_tb     = tt_gb / 1024
            saved_usd    = round(saved_tb * STORAGE_RATE, 2)
            if saved_usd > 0.01:
                items.append({
                    "category":   "Storage Optimization",
                    "warehouse":  "—",
                    "detail":     f"Reduce Time Travel on {tbl['table']} (currently {tbl['tt_gb']:.3f}GB TT overhead)",
                    "saving_cr":  0,
                    "saving_usd": saved_usd,
                    "period":     "monthly",
                    "confidence": "High",
                    "fix_sql":    f"ALTER TABLE {tbl['table']} SET DATA_RETENTION_TIME_IN_DAYS = 1;",
                })
                total_saving += saved_usd

    # ── 3. Anomaly Prevention Savings ───────────────────────────
    # If anomalies happened, estimate how much was "wasted" above baseline
    for a in anomaly_result.get("anomalies", []):
        if a.get("status") == "ANOMALY":
            extra_credits = max(0, a.get("credits", 0) - a.get("avg_credits", 0))
            saved_usd     = round(extra_credits * CREDIT_PRICE, 2)
            if saved_usd > 0.01:
                items.append({
                    "category":   "Anomaly Prevention",
                    "warehouse":  a.get("warehouse", ""),
                    "detail":     f"Anomaly on {a.get('date','')} — {extra_credits:.4f} extra credits above baseline",
                    "saving_cr":  round(extra_credits, 4),
                    "saving_usd": saved_usd,
                    "period":     "one-time (past)",
                    "confidence": "Medium",
                    "fix_sql":    (f"-- Set resource monitor to alert at 2x baseline:\n"
                                   f"CREATE RESOURCE MONITOR snowadvisor_guard\n"
                                   f"  WITH CREDIT_QUOTA = {max(1, round(a.get('avg_credits',0)*2, 1))}\n"
                                   f"  TRIGGERS ON 100 PERCENT DO NOTIFY;"),
                })
                # Don't add to total — it's past, not future saving

    # ── 4. Auto-Suspend Saving (if warehouses have long suspend times)
    by_wh = cost_result.get("by_warehouse", [])
    wh_active_days = {}
    for row in by_wh:
        wh  = row.get("warehouse", "")
        crd = row.get("credits", 0)
        if crd > 0:
            wh_active_days[wh] = wh_active_days.get(wh, 0) + 1

    for wh in wh_result.get("user_warehouses", []):
        wh_name  = wh.get("warehouse", "")
        credits  = wh.get("credits", 0)
        days     = wh_active_days.get(wh_name, 1)
        # If credits per active day > 0.5 but queries are low — probably not auto-suspending fast
        if credits > 0 and wh.get("queries", 0) < 100 and credits / max(days, 1) > 0.1:
            # Estimate 20% saving from faster auto-suspend
            saved_usd = round(credits * 0.20 * CREDIT_PRICE, 2)
            if saved_usd > 0.10:
                items.append({
                    "category":   "Auto-Suspend Tuning",
                    "warehouse":  wh_name,
                    "detail":     f"Faster auto-suspend on {wh_name} could save ~20% of idle runtime credits",
                    "saving_cr":  round(credits * 0.20, 4),
                    "saving_usd": saved_usd,
                    "period":     "monthly (estimated)",
                    "confidence": "Low",
                    "fix_sql":    f"ALTER WAREHOUSE {wh_name} SET AUTO_SUSPEND = 60;  -- 1 minute",
                })
                total_saving += saved_usd

    # Sort by saving desc
    items = sorted(items, key=lambda x: x["saving_usd"], reverse=True)

    return {
        "items":         items,
        "total_usd":     round(total_saving, 2),
        "total_credits": round(sum(i["saving_cr"] for i in items), 4),
        "item_count":    len(items),
        "high_confidence": [i for i in items if i["confidence"] == "High"],
    }


# ══════════════════════════════════════════════════════════════════
# 9. AUTO-SUSPEND TIMING ADVISOR
#    Query patterns se optimal auto-suspend time recommend karo
# ══════════════════════════════════════════════════════════════════

def analyze_auto_suspend(data: dict) -> dict:
    """
    QUERY_HISTORY ke hourly patterns se warehouse ke liye
    optimal AUTO_SUSPEND time calculate karo.
    """
    df = _to_df(data.get("query_intelligence", {}))
    if df.empty or "START_DT" not in df.columns:
        return {"warehouses": [], "recommendations": []}

    df["START_DT"] = pd.to_datetime(df["START_DT"], errors="coerce", utc=True)
    df = df.dropna(subset=["START_DT"])

    if df.empty:
        return {"warehouses": [], "recommendations": []}

    df["hour"]    = df["START_DT"].dt.hour
    df["weekday"] = df["START_DT"].dt.dayofweek   # 0=Mon, 6=Sun

    results = []
    recs    = []

    wh_col = "WAREHOUSE_NAME" if "WAREHOUSE_NAME" in df.columns else None
    if not wh_col:
        return {"warehouses": [], "recommendations": []}

    for wh_name, grp in df.groupby(wh_col):
        if wh_name.startswith("COMPUTE_SERVICE_WH"):
            continue   # skip system warehouses

        hour_counts = grp.groupby("hour").size()
        total_q     = len(grp)

        # Peak hours — hours with > 5% of total queries
        peak_hours  = sorted([h for h, c in hour_counts.items() if c / max(total_q, 1) > 0.05])
        quiet_hours = [h for h in range(24) if h not in peak_hours]

        # Weekday vs weekend activity
        weekday_q   = len(grp[grp["weekday"] < 5])
        weekend_q   = len(grp[grp["weekday"] >= 5])
        is_weekday_only = (weekend_q == 0 and weekday_q > 0)

        # Gap analysis — find longest gap between queries (in hours)
        if len(peak_hours) >= 2:
            gaps = []
            sorted_hours = sorted(peak_hours)
            for i in range(1, len(sorted_hours)):
                gaps.append(sorted_hours[i] - sorted_hours[i-1])
            max_gap = max(gaps) if gaps else 0
        else:
            max_gap = 0

        # Recommend suspend time based on gap
        if total_q < 20:
            suspend_min  = 1
            suspend_note = "Very low usage — suspend immediately after use (1 min)"
        elif max_gap >= 4:
            suspend_min  = 5
            suspend_note = f"Large gaps between usage detected — 5 min suspend recommended"
        elif max_gap >= 2:
            suspend_min  = 10
            suspend_note = "Moderate gaps in usage — 10 min suspend works well"
        else:
            suspend_min  = 15
            suspend_note = "Continuous usage pattern — 15 min suspend to avoid frequent cold starts"

        # Peak window description
        if peak_hours:
            peak_start = min(peak_hours)
            peak_end   = max(peak_hours)
            ps = _fmt_hour(peak_start)
            pe = _fmt_hour(peak_end + 1)
            peak_desc = f"{ps} – {pe}"
        else:
            peak_desc = "No clear peak"

        wh_obj = {
            "warehouse":         wh_name,
            "total_queries":     total_q,
            "peak_hours":        peak_hours,
            "peak_window":       peak_desc,
            "quiet_hours":       quiet_hours[:6],   # first 6 quiet hours
            "weekday_only":      is_weekday_only,
            "weekend_queries":   weekend_q,
            "recommended_suspend_min": suspend_min,
            "suspend_note":      suspend_note,
        }
        results.append(wh_obj)

        # Build recommendation
        current_note = ""
        if is_weekday_only:
            current_note = " Weekend activity = 0 — consider a schedule to suspend on weekends."

        recs.append({
            "severity": "LOW",
            "title":    f"{wh_name}: Set AUTO_SUSPEND = {suspend_min} min (peak: {peak_desc})",
            "detail":   f"{suspend_note}.{current_note} {total_q} queries analyzed.",
            "fix_sql":  (f"-- Set auto-suspend to {suspend_min} minute(s):\n"
                         f"ALTER WAREHOUSE {wh_name} SET AUTO_SUSPEND = {suspend_min * 60};\n"
                         f"ALTER WAREHOUSE {wh_name} SET AUTO_RESUME = TRUE;\n"
                         + (f"\n-- Optional: suspend on weekends via task:\n"
                            f"CREATE TASK suspend_{wh_name.lower()}_weekend\n"
                            f"  SCHEDULE = 'USING CRON 0 0 * * 6 UTC'\n"
                            f"  AS ALTER WAREHOUSE {wh_name} SUSPEND;"
                            if is_weekday_only else ""))
        })

    return {"warehouses": results, "recommendations": recs}


# ══════════════════════════════════════════════════════════════════
# 10. HISTORICAL TRENDING
#     data/ folder mein saved JSONs se trend read karo
# ══════════════════════════════════════════════════════════════════

import os
import glob

def load_historical_runs(data_dir: str = "data", account_slug: str = "") -> list:
    """
    data/ folder mein saved JSON files dhundo aur unse
    historical health scores + key metrics nikalo.

    Returns list of dicts sorted by timestamp (oldest first).
    """
    pattern = os.path.join(data_dir, f"account_{account_slug}*.json") if account_slug \
              else os.path.join(data_dir, "account_*.json")

    files   = sorted(glob.glob(pattern))   # alphabetical = chronological (timestamp in name)
    history = []

    for fp in files:
        try:
            with open(fp, "r") as f:
                raw = json.load(f)

            # Re-run analysis on this historical data
            hist_ar = run_analysis(raw.get("data", {}))
            h       = hist_ar["health"]
            cost    = hist_ar["cost"]
            wh      = hist_ar["warehouse"]
            anom    = hist_ar["anomaly"]

            # Extract timestamp from filename: account_slug_YYYYMMDD_HHMMSS.json
            fname   = os.path.basename(fp)
            parts   = fname.replace(".json","").split("_")
            # Last two parts should be date + time
            try:
                date_str = parts[-2]
                time_str = parts[-1]
                dt_str   = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}"
            except Exception:
                dt_str   = fname

            history.append({
                "filename":      fname,
                "timestamp":     dt_str,
                "health_overall":h["overall"],
                "health_grade":  h["grade"],
                "query_score":   h["scores"]["query"],
                "wh_score":      h["scores"]["warehouse"],
                "storage_score": h["scores"]["storage"],
                "user_score":    h["scores"]["users"],
                "total_credits": wh.get("total_credits", 0),
                "total_cost":    wh.get("total_cost_usd", 0),
                "anomaly_count": anom.get("anomaly_count", 0),
                "high_issues":   sum(1 for r in (hist_ar["warehouse"]["recommendations"] +
                                                  hist_ar["queries"]["recommendations"] +
                                                  hist_ar["users"]["recommendations"])
                                     if r.get("severity") == "HIGH"),
            })
        except Exception:
            continue   # skip corrupted files silently

    return history


def analyze_historical_trend(data_dir: str = "data", account_slug: str = "") -> dict:
    """
    Historical runs se trend analysis:
    - Health score improving ya worsening?
    - Cost trend
    - Issue count trend
    """
    runs = load_historical_runs(data_dir, account_slug)

    if len(runs) < 2:
        return {
            "runs":        runs,
            "has_trend":   False,
            "note":        "At least 2 analysis runs needed for trend. Run the tool again tomorrow.",
            "trend":       {},
        }

    first = runs[0]
    last  = runs[-1]

    health_change = last["health_overall"] - first["health_overall"]
    cost_change   = last["total_cost"] - first["total_cost"]
    issue_change  = last["high_issues"] - first["high_issues"]

    # Trend direction
    health_trend  = "improving" if health_change > 2 else ("worsening" if health_change < -2 else "stable")
    cost_trend    = "increasing" if cost_change > 0.5 else ("decreasing" if cost_change < -0.5 else "stable")
    issue_trend   = "fewer issues" if issue_change < 0 else ("more issues" if issue_change > 0 else "same")

    return {
        "runs":      runs,
        "has_trend": True,
        "run_count": len(runs),
        "first_run": first["timestamp"],
        "last_run":  last["timestamp"],
        "trend": {
            "health_change":  health_change,
            "health_trend":   health_trend,
            "cost_change":    round(cost_change, 4),
            "cost_trend":     cost_trend,
            "issue_change":   issue_change,
            "issue_trend":    issue_trend,
        },
        "summary": (f"Over {len(runs)} runs, health score went from "
                    f"{first['health_overall']} to {last['health_overall']} "
                    f"({health_trend}). Cost is {cost_trend}."),
        "note": "",
    }



# ══════════════════════════════════════════════════════════════════
# 11. UNUSED OBJECT DETECTION
# ══════════════════════════════════════════════════════════════════

def analyze_unused_objects(data: dict) -> dict:
    """
    ACCESS_HISTORY based unused objects analysis.
    - Tables not accessed in 30 days
    - Large stale tables = high savings
    """
    df = _to_df(data.get("unused_objects", {}))
    if df.empty:
        return {"tables": [], "total_stale_gb": 0, "total_stale_usd": 0, "recommendations": []}

    df = _n(df, "SIZE_GB", "ROW_COUNT")
    
    # Calculate monthly storage cost for each stale table ($23/TB -> $0.022/GB)
    df["cost_usd"] = df["SIZE_GB"] * (23.0 / 1024.0)
    
    stale_tables = df.to_dict("records")
    total_gb     = round(df["SIZE_GB"].sum(), 2)
    total_usd    = round(df["cost_usd"].sum(), 2)
    
    recs = []
    if total_usd > 10.0:
        recs.append({
            "severity": "HIGH",
            "title":    f"Found {len(df)} unused tables ({total_gb} GB)",
            "detail":   f"These tables haven't been accessed in 30 days. Deleting them could save ~${total_usd}/month in storage costs.",
            "fix_sql":  "-- Review and drop largest unused tables:\n" + \
                       "\n".join([f"DROP TABLE IF EXISTS {r['FULL_TABLE_NAME']};" for r in df.head(5).to_dict("records")])
        })
    
    return {
        "tables":           stale_tables,
        "total_stale_gb":   total_gb,
        "total_stale_usd":  total_usd,
        "recommendations":  recs,
    }


# ══════════════════════════════════════════════════════════════════
# 12. CLOUD SERVICES ANALYSIS
# ══════════════════════════════════════════════════════════════════

def analyze_cloud_services(data: dict) -> dict:
    """
    Analyze cloud services credits.
    Snowflake takes credits for cloud services if they exceed 10% of DAILY compute credits.
    """
    df = _to_df(data.get("warehouse_metering", {}))
    if df.empty:
        return {"total_cs_credits": 0, "billed_cs_credits": 0, "free_cs_credits": 0, "recommendations": []}

    df = _n(df, "COMPUTE_CREDITS", "CLOUD_CREDITS")
    
    # Daily aggregation (CS billing logic is daily)
    daily = df.groupby("USAGE_DATE").agg({
        "COMPUTE_CREDITS": "sum",
        "CLOUD_CREDITS":   "sum"
    })
    
    # 10% allowance
    daily["cs_allowance"] = daily["COMPUTE_CREDITS"] * 0.1
    daily["billed_cs"]    = (daily["CLOUD_CREDITS"] - daily["cs_allowance"]).clip(lower=0)
    daily["free_cs"]      = daily["CLOUD_CREDITS"] - daily["billed_cs"]
    
    total_cs    = round(daily["CLOUD_CREDITS"].sum(), 4)
    billed_cs   = round(daily["billed_cs"].sum(), 4)
    free_cs     = round(daily["free_cs"].sum(), 4)
    
    recs = []
    if billed_cs > total_cs * 0.2:
        recs.append({
            "severity": "MEDIUM",
            "title":    "High Cloud Services Billing",
            "detail":   f"Your cloud services are {billed_cs} credits over the 10% allowance. Likely cause: high metadata churn (copy, delete, list).",
            "fix_sql":  "-- Check for high frequency COPY/INSERT commands:\n" + \
                       "SELECT QUERY_TEXT, USER_NAME, COUNT(*) \n" + \
                       "FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY \n" + \
                       "WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP()) \n" + \
                       "GROUP BY 1, 2 ORDER BY 3 DESC LIMIT 10;"
        })
        
    return {
        "total_cs_credits":  total_cs,
        "billed_cs_credits": billed_cs,
        "free_cs_credits":   free_cs,
        "recommendations":   recs,
    }


# ══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════

def run_analysis(data: dict, account_info: dict = None) -> dict:
    """
    dashboard.py call karta hai:
        ar = analysis.run_analysis(result["data"], result["account_info"])

    Returns full analysis dict + ai_json for export.
    """
    wh          = analyze_warehouses(data)
    qry         = analyze_queries(data)
    anomaly     = analyze_anomalies(data)
    cost        = analyze_cost(data)
    storage     = analyze_storage(data)
    users       = analyze_users(data)
    notebooks   = analyze_notebooks(data)
    unused      = analyze_unused_objects(data)
    cloud       = analyze_cloud_services(data)
    health      = calculate_health_score(wh, qry, anomaly, storage, users)
    savings     = estimate_savings(wh, storage, cost, anomaly)
    auto_sus    = analyze_auto_suspend(data)

    ai_json     = build_ai_json(
        account_info or {}, health, wh, qry, anomaly, cost, storage, users, notebooks,
        unused, cloud, data
    )

    return {
        "health":         health,
        "warehouse":      wh,
        "queries":        qry,
        "anomaly":        anomaly,
        "cost":           cost,
        "storage":        storage,
        "users":          users,
        "notebooks":      notebooks,
        "unused_objects": unused,
        "cloud_services": cloud,
        "savings":        savings,
        "auto_suspend":   auto_sus,
        "ai_json":        ai_json,
    }