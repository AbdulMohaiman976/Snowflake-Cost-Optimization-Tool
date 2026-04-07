from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def _median(xs: list[float]) -> float:
    if not xs:
        return 0.0
    xs2 = sorted(xs)
    mid = len(xs2) // 2
    if len(xs2) % 2 == 1:
        return xs2[mid]
    return (xs2[mid - 1] + xs2[mid]) / 2.0


def _mad(xs: list[float]) -> float:
    if not xs:
        return 0.0
    m = _median(xs)
    return _median([abs(x - m) for x in xs])


def _outliers_mad(
    items: list[dict],
    value_key: str,
    id_key: str,
    z_threshold: float = 3.5,
    max_items: int = 5,
) -> list[dict]:
    """
    Returns robust outliers using modified Z-score based on MAD.
    Output items: {id_key: ..., value_key: ..., score: ...}
    """
    vals = []
    for it in items:
        v = _safe_float(it.get(value_key))
        vals.append(v)
    if len(vals) < 6:
        return []

    m = _median(vals)
    mad = _mad(vals)
    if mad <= 1e-9:
        return []

    out = []
    for it in items:
        v = _safe_float(it.get(value_key))
        mz = 0.6745 * (v - m) / mad
        if mz >= z_threshold:
            out.append(
                {
                    id_key: it.get(id_key),
                    value_key: v,
                    "mz": round(mz, 2),
                }
            )
    out.sort(key=lambda x: x.get("mz", 0), reverse=True)
    return out[:max_items]


@dataclass(frozen=True)
class LayeredInsights:
    module_key: str
    generated_at: str
    layer1: dict
    layer2: dict
    layer3: dict
    layer4: dict

    def to_dict(self) -> dict:
        return {
            "module_key": self.module_key,
            "generated_at": self.generated_at,
            "layer1": self.layer1,
            "layer2": self.layer2,
            "layer3": self.layer3,
            "layer4": self.layer4,
        }


def should_generate_llm(insights: dict) -> bool:
    """
    Always trigger LLM review to ensure the 'No issues detected' or 'Issue/Fix' 
    logic is applied consistently to all tabs.
    """
    return True


def build_base_insights(module_key: str, data: dict, *, llm_enabled: bool) -> dict:
    """
    Layer 1-3 are deterministic (local) and instant.
    Layer 4 is optional and filled asynchronously by the AI service.
    """
    generated_at = _utc_now_iso()
    layer1 = _layer1_rule_based(module_key, data)
    layer2 = _layer2_statistical(module_key, data)
    layer3 = _layer3_forecast(module_key, data)

    layer4_status = "pending" if llm_enabled and should_generate_llm(
        {
            "layer1": layer1,
            "layer2": layer2,
            "layer3": layer3,
        }
    ) else "skipped"

    layer4 = {
        "enabled": bool(llm_enabled),
        "status": layer4_status,  # pending|complete|skipped|error|rate_limited
        "provider": "groq",
        "model": None,
        "recommendations_md": "",
        "error": "",
        "updated_at": generated_at,
    }

    return LayeredInsights(
        module_key=module_key,
        generated_at=generated_at,
        layer1=layer1,
        layer2=layer2,
        layer3=layer3,
        layer4=layer4,
    ).to_dict()


def _layer1_rule_based(module_key: str, data: dict) -> dict:
    alerts: list[dict] = []

    if module_key == "warehouse":
        for wh in (data.get("warehouses") or []):
            if wh.get("type", "").lower().startswith("system"):
                continue
            queue_pct = _safe_float(wh.get("queue_pct"))
            spill_pct = _safe_float(wh.get("spill_rate_pct"))
            credits = _safe_float(wh.get("credits"))
            if queue_pct >= 10:
                alerts.append(
                    {
                        "severity": "HIGH" if queue_pct >= 25 else "MEDIUM",
                        "title": f"Queue buildup on {wh.get('warehouse')}",
                        "detail": f"Queued overload ratio is {queue_pct:.2f}% — queries may wait due to undersized warehouse.",
                        "fix_sql": f"ALTER WAREHOUSE {wh.get('warehouse')} SET WAREHOUSE_SIZE = '{wh.get('size_recommendation','Medium')}';",
                    }
                )
            if spill_pct > 0:
                alerts.append(
                    {
                        "severity": "MEDIUM" if spill_pct < 10 else "HIGH",
                        "title": f"Spillage detected on {wh.get('warehouse')}",
                        "detail": f"Spill rate is {spill_pct:.2f}% — memory pressure causing local/remote spillage.",
                        "fix_sql": f"ALTER WAREHOUSE {wh.get('warehouse')} SET WAREHOUSE_SIZE = '{wh.get('size_recommendation','Medium')}';",
                    }
                )
            if credits >= 500:
                alerts.append(
                    {
                        "severity": "MEDIUM",
                        "title": f"High credit burn on {wh.get('warehouse')}",
                        "detail": f"Warehouse used {credits:.2f} credits in the analysis window — verify autosuspend and workload.",
                        "fix_sql": "",
                    }
                )

    elif module_key == "queries":
        for q in (data.get("queries") or [])[:25]:
            exec_sec = _safe_float(q.get("exec_sec"))
            spill_gb = _safe_float(q.get("spill_gb"))
            pruning = _safe_float(q.get("pruning_pct"), default=100.0)
            if exec_sec >= 60:
                alerts.append(
                    {
                        "severity": "HIGH" if exec_sec >= 300 else "MEDIUM",
                        "title": f"Very slow query ({q.get('duration','')})",
                        "detail": f"exec_sec={exec_sec:.2f}s on warehouse {q.get('warehouse')}, user={q.get('user')}.",
                        "fix_sql": "/* Add filters, enable pruning, or rewrite joins; use QUERY_TAG to track. */\nALTER SESSION SET QUERY_TAG = 'snowadvisor_investigate';",
                    }
                )
            if spill_gb > 0:
                alerts.append(
                    {
                        "severity": "MEDIUM",
                        "title": "Query spillage detected",
                        "detail": f"spill_gb={spill_gb:.2f} GB — likely memory pressure or large joins/sorts.",
                        "fix_sql": "",
                    }
                )
            if pruning < 60:
                alerts.append(
                    {
                        "severity": "LOW",
                        "title": "Poor pruning (scan-heavy)",
                        "detail": f"pruning_pct={pruning:.1f}% — consider clustering or better predicates.",
                        "fix_sql": "",
                    }
                )

    
    elif module_key == "anomaly":
        cnt = _safe_int(data.get("anomaly_count"))
        anomalies = data.get("anomalies") or []
        if cnt > 0 and anomalies:
            a = anomalies[0]
            wh = a.get("warehouse", "WAREHOUSE")
            date = a.get("date", "DATE")
            credits = _safe_float(a.get("credits"))
            spike = a.get("spike_ratio")
            alerts.append(
                {
                    "severity": "HIGH",
                    "title": f"Spend spike {spike}x on {date} ({wh})",
                    "detail": f"Used {credits} credits vs 7-day baseline; contain and remediate immediately.",
                    "fix_sql": (
                        f"""-- Investigate heavy queries on the spike day\nSELECT USER_NAME,\n       LEFT(QUERY_TEXT, 300) AS query,\n       ROUND(EXECUTION_TIME/1000, 1) AS exec_sec,\n       ROUND(BYTES_SCANNED/1e9, 2) AS gb_scanned,\n       START_TIME\nFROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY\nWHERE WAREHOUSE_NAME = '{wh}'\n  AND DATE_TRUNC('day', START_TIME) = '{date}'\nORDER BY EXECUTION_TIME DESC\nLIMIT 25;\n\n-- Contain runaway spend with a resource monitor\nCREATE RESOURCE MONITOR IF NOT EXISTS rm_{wh}_protect\n  WITH CREDIT_QUOTA = 2 * (\n    SELECT COALESCE(AVG(CREDITS_USED),1)\n    FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY\n    WHERE WAREHOUSE_NAME = '{wh}'\n      AND START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())\n  )\n  TRIGGERS ON 100 PERCENT DO NOTIFY\n           ON 150 PERCENT DO SUSPEND\n           ON 200 PERCENT DO SUSPEND_IMMEDIATE;\n\n-- Tag further investigation queries\nALTER SESSION SET QUERY_TAG = 'snowadvisor_spike_{wh}';"""
                    ),
                }
            )
        elif _safe_int(data.get("warning_count")) > 0:
            alerts.append(
                {
                    "severity": "LOW",
                    "title": "Spend warning(s) detected",
                    "detail": "Warnings exceed baseline but below anomaly threshold; monitor with notifications.",
                    "fix_sql": (
                        "CREATE RESOURCE MONITOR IF NOT EXISTS rm_warning_guard\n"
                        "  WITH CREDIT_QUOTA = 50\n"
                        "  TRIGGERS ON 100 PERCENT DO NOTIFY;"
                    ),
                }
            )
    elif module_key == "cost":
        total = _safe_float(data.get("total_credits"))
        by_wh = data.get("by_warehouse") or []
        if total > 0 and by_wh:
            top = max(by_wh, key=lambda x: _safe_float(x.get("credits")))
            share = _safe_float(top.get("credit_share"))
            if share >= 60:
                alerts.append(
                    {
                        "severity": "MEDIUM",
                        "title": "Cost concentrated in one warehouse",
                        "detail": f"{top.get('warehouse')} accounts for ~{share:.1f}% of credits.",
                        "fix_sql": "",
                    }
                )

    elif module_key == "storage":
        bloated = _safe_int(data.get("bloated_count"))
        if bloated > 0:
            alerts.append(
                {
                    "severity": "MEDIUM",
                    "title": "Storage waste detected",
                    "detail": f"{bloated} bloated table(s) detected — time travel/failsafe overhead may be high.",
                    "fix_sql": "",
                }
            )

    elif module_key == "users":
        no_mfa = _safe_int(data.get("no_mfa_count"))
        failed = _safe_int(data.get("failed_logins"))
        if no_mfa > 0:
            alerts.append(
                {
                    "severity": "HIGH",
                    "title": "MFA not enabled for some users",
                    "detail": f"{no_mfa} user(s) have MFA disabled — security risk.",
                    "fix_sql": "",
                }
            )
        if failed >= 10:
            alerts.append(
                {
                    "severity": "MEDIUM",
                    "title": "Elevated login failures",
                    "detail": f"{failed} failed login(s) detected — investigate potential brute-force or misconfigured automation.",
                    "fix_sql": "",
                }
            )

    elif module_key == "unused_objects":
        tables = data.get("tables") or []
        stale_usd = _safe_float(data.get("total_stale_usd"))
        if tables or stale_usd > 0:
            alerts.append(
                {
                    "severity": "LOW",
                    "title": "Stale/unused objects detected",
                    "detail": f"Estimated stale storage waste: ${stale_usd:.2f}.",
                    "fix_sql": "",
                }
            )

    elif module_key == "notebooks":
        runs = _safe_int(data.get("total_runs"))
        if runs <= 0:
            alerts.append(
                {
                    "severity": "LOW",
                    "title": "No notebook activity detected",
                    "detail": "No notebook runs found — if you use notebooks, ensure query tagging and warehouse sizing are tracked.",
                    "fix_sql": "ALTER SESSION SET QUERY_TAG = 'notebook';",
                }
            )

    elif module_key == "savings":
        total_usd = _safe_float(data.get("total_usd"))
        if total_usd > 0:
            alerts.append(
                {
                    "severity": "LOW",
                    "title": "Savings opportunities available",
                    "detail": f"Estimated total savings: ${total_usd:.2f} across {data.get('item_count',0)} item(s).",
                    "fix_sql": "",
                }
            )

    return {
        "summary": f"{len(alerts)} alert(s) generated.",
        "alerts": alerts[:12],
    }



def _layer2_statistical(module_key: str, data: dict) -> dict:
    """Statistical detection disabled (rule-based + optional forecast only)."""
    return {"summary": "Statistical detection disabled", "anomalies": []}
def _layer3_forecast(module_key: str, data: dict) -> dict:
    if module_key != "anomaly":
        return {
            "summary": "Forecast not applicable for this tab.",
            "forecast": {"available": False},
        }

    daily = data.get("daily") or []
    if not daily:
        return {
            "summary": "No daily spend data available to forecast.",
            "forecast": {"available": False},
        }

    # Use last N points (sorted by date string)
    pts = []
    for d in daily:
        pts.append(
            {
                "date": d.get("date") or "",
                "credits": _safe_float(d.get("credits")),
                "est_cost": _safe_float(d.get("est_cost")),
                "warehouse": d.get("warehouse") or "",
            }
        )
    pts = [p for p in pts if p["date"]]
    pts.sort(key=lambda x: x["date"])

    credits_series = [p["credits"] for p in pts if p["credits"] > 0]
    if len(credits_series) < 5:
        return {
            "summary": "Not enough daily points to forecast reliably.",
            "forecast": {"available": False},
        }

    window = credits_series[-7:]
    baseline = sum(window) / len(window)
    # crude trend: compare first half vs second half of window
    half = max(1, len(window) // 2)
    a = sum(window[:half]) / half
    b = sum(window[-half:]) / half
    trend = b - a  # credits per day (approx)

    # cost-per-credit from observed points if possible
    cpc_vals = []
    for p in pts[-10:]:
        if p["credits"] > 0 and p["est_cost"] > 0:
            cpc_vals.append(p["est_cost"] / p["credits"])
    cost_per_credit = (sum(cpc_vals) / len(cpc_vals)) if cpc_vals else 3.0

    horizon = 7
    forecast_daily = []
    for i in range(1, horizon + 1):
        pred = max(0.0, baseline + trend * (i / horizon))
        forecast_daily.append(
            {
                "day_offset": i,
                "pred_credits": round(pred, 4),
                "pred_cost_usd": round(pred * cost_per_credit, 2),
            }
        )

    total_pred_credits = sum(x["pred_credits"] for x in forecast_daily)
    total_pred_cost = sum(x["pred_cost_usd"] for x in forecast_daily)

    risk_level = "LOW"
    if trend >= baseline * 0.5:
        risk_level = "HIGH"
    elif trend >= baseline * 0.2:
        risk_level = "MEDIUM"

    return {
        "summary": f"7-day forecast built from last {len(window)} day(s); trend={trend:.4f} credits/day.",
        "forecast": {
            "available": True,
            "horizon_days": horizon,
            "baseline_credits_per_day": round(baseline, 4),
            "trend_credits_per_day": round(trend, 4),
            "risk_level": risk_level,
            "predicted_total_credits": round(total_pred_credits, 4),
            "predicted_total_cost_usd": round(total_pred_cost, 2),
            "daily": forecast_daily,
        },
    }
