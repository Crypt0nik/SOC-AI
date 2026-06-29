"""Pydantic response models for the SOC-AI REST API."""

from pydantic import BaseModel


class TriageSummary(BaseModel):
    """Triage fields included in the alert list (no full text fields)."""

    severity: str | None = None
    attack_type: str | None = None
    mitre_id: str | None = None
    confidence: int | None = None
    false_positive_risk: str | None = None
    backend: str | None = None


class AlertItem(BaseModel):
    """One alert row as returned in the list endpoint."""

    id: int
    rule_id: str
    rule_name: str
    severity: str
    source_ip: str | None
    matched_count: int
    timestamp: str
    status: str
    created_at: str
    triage: TriageSummary | None = None


class AlertListResponse(BaseModel):
    """Paginated alert list response."""

    items: list[AlertItem]
    total: int
    page: int
    page_size: int


class TriageDetail(BaseModel):
    """Full triage data included in the alert detail endpoint."""

    severity: str
    attack_type: str
    mitre_id: str | None
    confidence: int
    summary: str
    recommendation: str
    false_positive_risk: str
    backend: str
    raw_llm_json: str


class AlertDetail(BaseModel):
    """Full alert with raw log and optional triage detail."""

    id: int
    rule_id: str
    rule_name: str
    severity: str
    source_ip: str | None
    matched_count: int
    timestamp: str
    status: str
    created_at: str
    raw_log: str
    triage: TriageDetail | None = None


class StatsResponse(BaseModel):
    """Alert counts for the last N hours, keyed by effective severity."""

    window_hours: int = 24
    counts: dict[str, int]
    total: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    db: str
