# api/models.py
# ─────────────────────────────────────────────────────────────────
# Pydantic models — request bodies + response shapes
# ─────────────────────────────────────────────────────────────────

from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime


# ══════════════════════════════════════════════════════════════════
# REQUEST MODELS
# ══════════════════════════════════════════════════════════════════

class ConnectRequest(BaseModel):
    account:   str = Field(..., example="abc12345.us-east-1")
    username:  str = Field(..., example="my_user")
    password:  str = Field(..., example="my_pass")
    warehouse: str = Field("COMPUTE_WH", example="COMPUTE_WH")
    role:      str = Field("ACCOUNTADMIN", example="ACCOUNTADMIN")

    class Config:
        # Prevent password from showing up in logs/responses
        json_schema_extra = {
            "example": {
                "account":   "abc12345.us-east-1",
                "username":  "my_user",
                "password":  "***",
                "warehouse": "COMPUTE_WH",
                "role":      "ACCOUNTADMIN",
            }
        }


# ══════════════════════════════════════════════════════════════════
# RESPONSE MODELS
# ══════════════════════════════════════════════════════════════════

class ConnectResponse(BaseModel):
    session_id:   str           # Fernet-encrypted token — send this to client
    account_info: dict
    analyzed_at:  str
    health:       dict
    warehouse:    dict
    queries:      dict
    anomaly:      dict
    cost:         dict
    storage:      dict
    savings:      dict
    unused_objects: dict
    cloud_services: dict
    notebooks:      dict
    auto_suspend:   dict
    ai_json:        Optional[dict] = None
    ai_recommendations: Optional[dict] = None


class HistoryEntry(BaseModel):
    analyzed_at: str
    health_score: int
    health_grade: str
    total_cost_usd: float
    anomaly_count: int
    grade:         Optional[str] = "Healthy"


class HistoryResponse(BaseModel):
    session_id: str
    account:    str
    runs:       list[HistoryEntry]


class HealthResponse(BaseModel):
    status:  str = "ok"
    service: str = "SnowAdvisor API"
    version: str = "1.0.0"


# Agent
class AgentRequest(BaseModel):
    token: str
    mode:  str = Field("steps", pattern="^(steps|auto)$")


class AgentResponse(BaseModel):
    status:  str
    plan:    str
    took_ms: int
