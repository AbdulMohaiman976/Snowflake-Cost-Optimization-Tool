# SnowAdvisor: Cost Optimization Analysis & Proposals

This document provides a deep dive into the business logic, data usage, and use cases of the SnowAdvisor application, along with proposals for new cost-saving insights.

## Existing Dashboard Analysis

| Tab | Key Metric / Insight | Data Source (`ACCOUNT_USAGE`) | Use Case / Problem Solved |
| :--- | :--- | :--- | :--- |
| **Warehouse** | Sizing, Queue %, Spill Rate %, Pruning % | `QUERY_HISTORY`, `WAREHOUSE_METERING_HISTORY` | Identifies over/under-sized warehouses and performance bottlenecks. |
| **Query Intelligence** | Slow Queries, Error Tags (Spill, Pruning) | `QUERY_HISTORY` | Pinpoints specific inefficient queries for targeted tuning. |
| **Spend Anomaly** | 7-day Rolling Avg, 2x+ Spikes | `WAREHOUSE_METERING_HISTORY` | Detects runaway queries or "sticker shock" events early. |
| **Cost Breakdown** | Credits by Wh/User, User Profiles | `WAREHOUSE_METERING_HISTORY`, `QUERY_HISTORY` | Cost attribution and identifying high-usage teams/roles. |
| **Storage** | Table Bloat (TT+FS vs Active) | `TABLE_STORAGE_METRICS` | Reduces storage costs by optimizing Time Travel retention. |
| **Security & Users** | MFA Gaps, Inactive Users, Login Failures | `USERS`, `LOGIN_HISTORY` | Security hygiene and reducing risk of administrative breaches. |
| **Notebooks** | Notebook/Python activity | `QUERY_HISTORY` (via `QUERY_TAG`) | Monitors costs associated with interactive data science tools. |

---

## Proposed New Optimization Insights

Based on research into extended `ACCOUNT_USAGE` and `ACCESS_HISTORY` views, the following high-impact insights are proposed:

### 1. Unused Object Detection (`ACCESS_HISTORY`)
- **Insight**: Identify tables, views, and columns that have not been accessed in the last 30, 60, or 90 days.
- **Value**: Directly reduce storage costs by archiving or dropping unused data.
- **Metadata**: `SNOWFLAKE.ACCOUNT_USAGE.ACCESS_HISTORY`.

### 2. Cloud Services Credit Monitoring
- **Insight**: Flag warehouses or account-level usage where Cloud Services credits exceed 10% of total credits.
- **Value**: High cloud services fees often indicate "death by a thousand cuts" (too many small queries) or metadata-heavy operations that can be optimized.
- **Metadata**: `SNOWFLAKE.ACCOUNT_USAGE.WAREHOUSE_METERING_HISTORY`.

### 3. Materialized View ROI Analysis
- **Insight**: Compare the cost of Materialized View (MV) refreshes against the frequency and performance benefit of queries hitting those MVs.
- **Value**: Prevents "zombie" MVs that cost more to maintain than they save in query time.
- **Metadata**: `SNOWFLAKE.ACCOUNT_USAGE.MATERIALIZED_VIEW_REFRESH_HISTORY`.

### 4. Automatic Clustering Efficiency
- **Insight**: Track credits spent on Automatic Clustering vs. the improvement in Partition Pruning for the target tables.
- **Value**: Ensures clustering is providing a positive ROI.
- **Metadata**: `SNOWFLAKE.ACCOUNT_USAGE.AUTOMATIC_CLUSTERING_HISTORY`.

### 5. Idle Data in Stages
- **Insight**: Identify files left in internal stages for long periods.
- **Value**: Internal stages often become "hidden" storage costs.
- **Metadata**: `SNOWFLAKE.ACCOUNT_USAGE.STAGE_STORAGE_USAGE_HISTORY`.
