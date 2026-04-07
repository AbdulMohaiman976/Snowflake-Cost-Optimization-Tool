# backend.py
# Snowflake se connect karo, ACCOUNT_USAGE se data nikalo.
# dashboard.py yahan se sirf run_full_pipeline() call karta hai.

import json, os, logging
from datetime import datetime

import pandas as pd
import snowflake.connector
from snowflake.connector import DictCursor

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(levelname)s  %(message)s")
log = logging.getLogger("backend")

DATA_FOLDER = None


# ══════════════════════════════════════════════════════════════════
# A — CONNECT
# ══════════════════════════════════════════════════════════════════

def connect(account, username, password, warehouse="COMPUTE_WH", role="ACCOUNTADMIN"):
    account = (account
               .replace("https://", "")
               .replace(".snowflakecomputing.com", "")
               .strip().lower())
    log.info(f"Connecting: account={account} user={username}")
    try:
        conn = snowflake.connector.connect(
            account=account, user=username, password=password,
            warehouse=warehouse, role=role,
            database="SNOWFLAKE", schema="ACCOUNT_USAGE",
            login_timeout=20, network_timeout=30,
        )
        log.info("Connection SUCCESS")
        return conn, None
    except Exception as e:
        log.error(f"Connection FAILED: {e}")
        return None, str(e)


# ══════════════════════════════════════════════════════════════════
# B — VERIFY -- Test
# ══════════════════════════════════════════════════════════════════

def verify(conn) -> dict:
    cur = conn.cursor()
    cur.execute("SELECT CURRENT_ACCOUNT(), CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE()")
    row = cur.fetchone()
    cur.close()
    info = {"account": row[0], "user": row[1], "role": row[2], "warehouse": row[3]}
    log.info(f"Verified: {info}")
    return info


# ══════════════════════════════════════════════════════════════════
# C — ACCESS CHECK
# ══════════════════════════════════════════════════════════════════

def check_access(conn):
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY "
            "WHERE START_TIME > DATEADD('hour',-1,CURRENT_TIMESTAMP()) LIMIT 1"
        )
        cur.fetchone()
        cur.close()
        log.info("ACCOUNT_USAGE: OK")
        return True, "Access confirmed"
    except Exception as e:
        fix = "GRANT IMPORTED PRIVILEGES ON DATABASE SNOWFLAKE TO ROLE ACCOUNTADMIN;"
        log.warning(f"ACCOUNT_USAGE: DENIED — {e}")
        return False, f"Access denied — {e}\n\nFix:\n{fix}"


# ══════════════════════════════════════════════════════════════════
# D — QUERY RUNNER
# ══════════════════════════════════════════════════════════════════

def _q(conn, name, sql):
    try:
        cur = conn.cursor(DictCursor)
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        cur.close()
        log.info(f"  {name}: {len(rows)} rows")
        return rows, cols, None
    except Exception as e:
        log.warning(f"  {name}: ERROR — {e}")
        return [], [], str(e)


# ══════════════════════════════════════════════════════════════════
# E — ALL QUERIES
# ══════════════════════════════════════════════════════════════════

def pull_account_usage(conn) -> dict:
    queries = {

        # ── 1. Warehouse Advisor ─────────────────────────────────────────
        "warehouse_advisor": """
            WITH wh_query_stats AS (
                SELECT
                    WAREHOUSE_NAME,
                    WAREHOUSE_SIZE,
                    COUNT(*)                                                        AS total_queries,
                    ROUND(AVG(EXECUTION_TIME)/1000.0, 2)                           AS avg_exec_sec,
                    ROUND(
                        AVG(COALESCE(QUEUED_OVERLOAD_TIME,0))
                        / NULLIF(AVG(EXECUTION_TIME),0) * 100.0
                    , 2)                                                            AS queue_ratio_pct,
                    ROUND(
                        SUM(CASE WHEN COALESCE(BYTES_SPILLED_TO_LOCAL_STORAGE,0)
                                    + COALESCE(BYTES_SPILLED_TO_REMOTE_STORAGE,0) > 0
                                 THEN 1 ELSE 0 END)::FLOAT / NULLIF(COUNT(*),0) * 100.0
                    , 2)                                                            AS spill_rate_pct,
                    ROUND(
                        AVG(CASE WHEN COALESCE(PARTITIONS_TOTAL,0) > 0
                                 THEN (1.0 - PARTITIONS_SCANNED::FLOAT
                                       / PARTITIONS_TOTAL) * 100.0
                                 ELSE 100.0 END)
                    , 2)                                                            AS avg_pruning_pct,
                    ROUND(SUM(COALESCE(BYTES_SPILLED_TO_REMOTE_STORAGE,0))/1e9, 3) AS remote_spill_gb,
                    ROUND(SUM(COALESCE(BYTES_SPILLED_TO_LOCAL_STORAGE,0))/1e9, 3)  AS local_spill_gb
                FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
                WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
                  AND WAREHOUSE_NAME IS NOT NULL
                  AND EXECUTION_STATUS = 'SUCCESS'
                GROUP BY 1, 2
            ),
            wh_credits AS (
                SELECT
                    WAREHOUSE_NAME,
                    SUM(CREDITS_USED) AS total_credits
                FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
                WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
                GROUP BY 1
            )
            SELECT
                q.*,
                ROUND(COALESCE(c.total_credits, 0), 4) AS total_credits
            FROM wh_query_stats q
            LEFT JOIN wh_credits c ON q.WAREHOUSE_NAME = c.WAREHOUSE_NAME
            ORDER BY total_credits DESC
        """,

        # ── 2. Query Intelligence ────────────────────────────────────────
        "query_intelligence": """
            SELECT
                QUERY_ID,
                LEFT(QUERY_TEXT, 400)                                           AS query_text,
                USER_NAME,
                ROLE_NAME,
                WAREHOUSE_NAME,
                DATABASE_NAME,
                ROUND(EXECUTION_TIME/1000.0, 2)                                 AS exec_seconds,
                ROUND(COALESCE(QUEUED_OVERLOAD_TIME,0)/1000.0, 2)              AS queued_seconds,
                ROUND(COALESCE(BYTES_SPILLED_TO_LOCAL_STORAGE,0)/1e9, 4)       AS spill_local_gb,
                ROUND(COALESCE(BYTES_SPILLED_TO_REMOTE_STORAGE,0)/1e9, 4)      AS spill_remote_gb,
                COALESCE(PARTITIONS_SCANNED, 0)                                 AS partitions_scanned,
                COALESCE(PARTITIONS_TOTAL, 0)                                   AS partitions_total,
                CASE WHEN COALESCE(PARTITIONS_TOTAL,0) > 0
                     THEN ROUND(PARTITIONS_SCANNED::FLOAT/PARTITIONS_TOTAL*100.0, 1)
                     ELSE 0 END                                                 AS scan_pct,
                CASE WHEN COALESCE(PARTITIONS_TOTAL,0) > 0
                     THEN ROUND((1.0 - PARTITIONS_SCANNED::FLOAT/PARTITIONS_TOTAL)*100.0, 1)
                     ELSE 100.0 END                                             AS pruning_pct,
                CASE
                    WHEN COALESCE(BYTES_SPILLED_TO_REMOTE_STORAGE,0) > 1e9  THEN 'HIGH REMOTE SPILL'
                    WHEN COALESCE(BYTES_SPILLED_TO_LOCAL_STORAGE,0)  > 1e9  THEN 'HIGH LOCAL SPILL'
                    WHEN COALESCE(PARTITIONS_TOTAL,0) > 0
                     AND PARTITIONS_SCANNED::FLOAT/PARTITIONS_TOTAL > 0.8    THEN 'POOR PRUNING'
                    WHEN COALESCE(QUEUED_OVERLOAD_TIME,0) > EXECUTION_TIME   THEN 'QUEUE BOTTLENECK'
                    WHEN EXECUTION_TIME > 300000                              THEN 'SLOW QUERY'
                    ELSE 'OK'
                END                                                             AS problem_tag,
                START_TIME
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD('day', -7, CURRENT_TIMESTAMP())
              AND EXECUTION_STATUS = 'SUCCESS'
              AND EXECUTION_TIME > 1000
            ORDER BY EXECUTION_TIME DESC
            LIMIT 200
        """,

        # ── 3. Spend Anomaly ─────────────────────────────────────────────
        "spend_anomaly": """
            WITH daily AS (
                SELECT
                    DATE_TRUNC('day', START_TIME)   AS dt,
                    WAREHOUSE_NAME,
                    SUM(CREDITS_USED)               AS daily_credits
                FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
                WHERE START_TIME >= DATEADD('day', -37, CURRENT_TIMESTAMP())
                GROUP BY 1, 2
            ),
            with_avg AS (
                SELECT
                    dt, WAREHOUSE_NAME, daily_credits,
                    AVG(daily_credits) OVER (
                        PARTITION BY WAREHOUSE_NAME
                        ORDER BY dt
                        ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
                    ) AS rolling_7d_avg
                FROM daily
            )
            SELECT
                dt,
                WAREHOUSE_NAME,
                ROUND(daily_credits, 4)                                  AS daily_credits,
                ROUND(rolling_7d_avg, 4)                                 AS rolling_7d_avg,
                ROUND(daily_credits / NULLIF(rolling_7d_avg,0), 3)      AS spike_ratio,
                CASE
                    WHEN daily_credits > rolling_7d_avg * 2.0 THEN 'ANOMALY'
                    WHEN daily_credits > rolling_7d_avg * 1.5 THEN 'WARNING'
                    ELSE 'NORMAL'
                END AS alert_status
            FROM with_avg
            WHERE dt >= DATEADD('day', -30, CURRENT_TIMESTAMP())
            ORDER BY dt DESC, spike_ratio DESC NULLS LAST
        """,

        # ── 4. Cost by User ──────────────────────────────────────────────
        "cost_by_user": """
            SELECT
                USER_NAME,
                ROLE_NAME,
                COUNT(*)                                                        AS total_queries,
                ROUND(AVG(EXECUTION_TIME)/1000.0, 2)                           AS avg_exec_sec,
                ROUND(SUM(EXECUTION_TIME)/1000.0/3600.0, 4)                    AS total_exec_hours,
                ROUND(SUM(COALESCE(BYTES_SPILLED_TO_LOCAL_STORAGE,0)
                        + COALESCE(BYTES_SPILLED_TO_REMOTE_STORAGE,0))/1e9, 3) AS total_spill_gb,
                COUNT(DISTINCT WAREHOUSE_NAME)                                  AS warehouses_used,
                COUNT(DISTINCT DATABASE_NAME)                                   AS databases_used
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
              AND EXECUTION_STATUS = 'SUCCESS'
              AND USER_NAME IS NOT NULL
            GROUP BY 1, 2
            ORDER BY total_queries DESC
            LIMIT 50
        """,

        # ── 5. Warehouse Metering (daily) ────────────────────────────────
        "warehouse_metering": """
            SELECT
                WAREHOUSE_NAME,
                DATE_TRUNC('day', START_TIME)           AS usage_date,
                ROUND(SUM(CREDITS_USED), 4)             AS total_credits,
                ROUND(SUM(CREDITS_USED_COMPUTE), 4)     AS compute_credits,
                ROUND(SUM(CREDITS_USED_CLOUD_SERVICES), 4) AS cloud_credits
            FROM SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY
            WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
            GROUP BY 1, 2
            ORDER BY usage_date DESC, total_credits DESC
        """,

        # ── 6. Storage ───────────────────────────────────────────────────
        "storage": """
            SELECT
                TABLE_CATALOG                                               AS database_name,
                TABLE_SCHEMA                                                AS schema_name,
                TABLE_NAME,
                ROUND(COALESCE(ACTIVE_BYTES,0)/1e9, 4)                     AS active_gb,
                ROUND(COALESCE(TIME_TRAVEL_BYTES,0)/1e9, 4)                AS time_travel_gb,
                ROUND(COALESCE(FAILSAFE_BYTES,0)/1e9, 4)                   AS failsafe_gb,
                ROUND(
                    (COALESCE(TIME_TRAVEL_BYTES,0)+COALESCE(FAILSAFE_BYTES,0))
                    / NULLIF(ACTIVE_BYTES,0)*100.0
                ,2)                                                         AS bloat_pct,
                ROUND(
                    (COALESCE(TIME_TRAVEL_BYTES,0)+COALESCE(FAILSAFE_BYTES,0))
                    /1e12*23.0
                ,4)                                                         AS est_monthly_waste_usd
            FROM SNOWFLAKE.ACCOUNT_USAGE.TABLE_STORAGE_METRICS
            WHERE ACTIVE_BYTES > 0
            ORDER BY bloat_pct DESC NULLS LAST
            LIMIT 100
        """,

        # ── 7. Login History ─────────────────────────────────────────────
        "login_history": """
            SELECT
                USER_NAME,
                IS_SUCCESS,
                ERROR_MESSAGE,
                DATE_TRUNC('day', EVENT_TIMESTAMP) AS login_date,
                COUNT(*) AS login_count
            FROM SNOWFLAKE.ACCOUNT_USAGE.LOGIN_HISTORY
            WHERE EVENT_TIMESTAMP >= DATEADD('day', -30, CURRENT_TIMESTAMP())
            GROUP BY 1, 2, 3, 4
            ORDER BY login_date DESC
            LIMIT 300
        """,

        # ── 8. Users ─────────────────────────────────────────────────────
        "users": """
            SELECT
                NAME                    AS username,
                LOGIN_NAME,
                EMAIL,
                DEFAULT_ROLE,
                HAS_MFA,
                CREATED_ON,
                LAST_SUCCESS_LOGIN,
                DISABLED,
                DATEDIFF('day',
                    COALESCE(LAST_SUCCESS_LOGIN, CREATED_ON),
                    CURRENT_TIMESTAMP())                        AS days_inactive
            FROM SNOWFLAKE.ACCOUNT_USAGE.USERS
            WHERE DELETED_ON IS NULL
            ORDER BY days_inactive DESC NULLS LAST
            LIMIT 100
        """,

        # ── 9. Notebooks ─────────────────────────────────────────────────
        # CLIENT_APPLICATION_ID column older versions mein nahi hoti
        # QUERY_TAG se detect karte hain jo user set karta hai
        "notebooks": """
            SELECT
                USER_NAME,
                WAREHOUSE_NAME,
                DATABASE_NAME,
                LEFT(QUERY_TEXT, 300)                               AS query_preview,
                ROUND(EXECUTION_TIME/1000.0, 2)                    AS exec_seconds,
                ROUND(
                    (COALESCE(BYTES_SPILLED_TO_LOCAL_STORAGE,0)
                    + COALESCE(BYTES_SPILLED_TO_REMOTE_STORAGE,0))
                    /1e9, 3)                                        AS spill_gb,
                START_TIME,
                DATE_TRUNC('day', START_TIME)                      AS run_date,
                COALESCE(QUERY_TAG, '')                            AS query_tag
            FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY
            WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
              AND EXECUTION_STATUS = 'SUCCESS'
              AND (UPPER(QUERY_TAG) LIKE '%NOTEBOOK%' OR UPPER(QUERY_TAG) LIKE '%PYTHON%' OR UPPER(QUERY_TAG) LIKE '%JUPYTER%')
            ORDER BY START_TIME DESC
            LIMIT 200
        """,

        # ── 10. Unused Object Detection (ACCESS_HISTORY) ─────────────────
        "unused_objects": """
            WITH accessed AS (
                SELECT DISTINCT 
                    f.value:objName::string as table_name,
                    f.value:objDomain::string as table_domain
                FROM SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY,
                LATERAL FLATTEN(input => BASE_OBJECTS_ACCESSED) f
                WHERE QUERY_START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP())
            )
            SELECT 
                t.TABLE_CATALOG || '.' || t.TABLE_SCHEMA || '.' || t.TABLE_NAME as full_table_name,
                t.TABLE_TYPE,
                t.ROW_COUNT,
                ROUND(t.BYTES / 1e9, 3) as size_gb,
                t.CREATED,
                t.LAST_ALTERED
            FROM SNOWFLAKE.ACCOUNT_USAGE.TABLES t
            LEFT JOIN accessed a 
                ON t.TABLE_NAME = SPLIT_PART(a.table_name, '.', 3)
                AND t.TABLE_SCHEMA = SPLIT_PART(a.table_name, '.', 2)
                AND t.TABLE_CATALOG = SPLIT_PART(a.table_name, '.', 1)
            WHERE t.DELETED IS NULL
              AND a.table_name IS NULL
              AND t.TABLE_SCHEMA != 'INFORMATION_SCHEMA'
              AND t.TABLE_CATALOG != 'SNOWFLAKE'
              AND t.TABLE_TYPE = 'BASE TABLE'
            ORDER BY size_gb DESC
            LIMIT 100
        """,

    }

    log.info("Pulling 10 ACCOUNT_USAGE tables...")
    result = {}
    for name, sql in queries.items():
        rows, cols, error = _q(conn, name, sql)
        result[name] = {"rows": rows, "columns": cols, "count": len(rows), "error": error}
    return result


# ══════════════════════════════════════════════════════════════════
# F — SAVE JSON (disabled: MongoDB Atlas is the source of truth)
# ══════════════════════════════════════════════════════════════════

def save_json(account_info: dict, data: dict) -> tuple:
    raise RuntimeError("Local JSON storage is disabled. Use MongoDB Atlas.")


# ══════════════════════════════════════════════════════════════════
# G — MAIN PIPELINE
# ══════════════════════════════════════════════════════════════════

def run_full_pipeline(account, username, password,
                      warehouse="COMPUTE_WH", role="ACCOUNTADMIN") -> dict:
    result = {
        "success": False, "account_info": {},
        "access_ok": False, "access_msg": "",
        "data": {}, "filepath": None, "filename": None, "error": None,
    }
    conn, err = connect(account, username, password, warehouse, role)
    if err:
        result["error"] = err
        return result
    try:
        result["account_info"] = verify(conn)
        ok, msg = check_access(conn)
        result["access_ok"], result["access_msg"] = ok, msg
        if not ok:
            result["error"] = msg
            return result
        data = pull_account_usage(conn)
        result["data"] = data
        result["success"]  = True
    except Exception as e:
        log.error(f"Pipeline error: {e}", exc_info=True)
        result["error"] = str(e)
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return result
