"""SOC-AI FastAPI backend.

Exposes a REST API consumed by the dashboard:
- GET /health            → service + DB status
- GET /alerts            → paginated alert list (joined with triage)
- GET /alerts/{id}       → alert detail with raw log + full triage
- GET /stats             → per-severity counts for the last 24 h
- GET /export            → full JSON download (optional severity filter)
"""

import json
import logging
import os
import sqlite3
from collections.abc import Generator

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from api.db import (
    fetch_alert_by_id,
    fetch_alerts,
    fetch_all_alerts_for_export,
    fetch_stats,
    get_connection,
)
from api.models import (
    AlertDetail,
    AlertItem,
    AlertListResponse,
    HealthResponse,
    StatsResponse,
    TriageDetail,
    TriageSummary,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("soc_ai.api")

app = FastAPI(
    title="SOC-AI API",
    version="1.0.0",
    description="Community Edition — lightweight LLM-powered SOC triage API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

_VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
_SEVERITY_PATTERN = "^(CRITICAL|HIGH|MEDIUM|LOW|INFO)$"


# ── Dependency ────────────────────────────────────────────────────────────────


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency: yield a per-request SQLite connection, close on exit."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


# ── Helpers ───────────────────────────────────────────────────────────────────


def _build_triage_summary(row: dict) -> TriageSummary | None:
    """Extract a :class:`TriageSummary` from a flat alert+triage row dict."""
    if row.get("triage_severity") is None:
        return None
    return TriageSummary(
        severity=row.get("triage_severity"),
        attack_type=row.get("attack_type"),
        mitre_id=row.get("mitre_id"),
        confidence=row.get("confidence"),
        false_positive_risk=row.get("false_positive_risk"),
        backend=row.get("backend"),
    )


def _build_triage_detail(row: dict) -> TriageDetail | None:
    """Extract a :class:`TriageDetail` from a flat alert+triage row dict."""
    if row.get("triage_severity") is None:
        return None
    return TriageDetail(
        severity=row["triage_severity"],
        attack_type=row["attack_type"],
        mitre_id=row.get("mitre_id"),
        confidence=row["confidence"],
        summary=row["summary"],
        recommendation=row["recommendation"],
        false_positive_risk=row["false_positive_risk"],
        backend=row["backend"],
        raw_llm_json=row["raw_llm_json"],
    )


# ── Routes ────────────────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse)
def health(db: sqlite3.Connection = Depends(get_db)) -> HealthResponse:
    """Return service and database health status."""
    try:
        db.execute("SELECT 1").fetchone()
        db_status = "ok"
    except Exception:  # noqa: BLE001
        db_status = "error"
    return HealthResponse(status="ok", db=db_status)


@app.get("/alerts", response_model=AlertListResponse)
def list_alerts(
    severity: str | None = Query(None, pattern=_SEVERITY_PATTERN),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: sqlite3.Connection = Depends(get_db),
) -> AlertListResponse:
    """Return a paginated list of alerts sorted by timestamp descending.

    Args:
        severity: Optional filter — one of CRITICAL, HIGH, MEDIUM, LOW, INFO.
        page: 1-based page index.
        page_size: Items per page (1–100).
        db: Injected SQLite connection.

    Returns:
        Paginated alert list with optional triage summaries.
    """
    rows, total = fetch_alerts(db, severity, page, page_size)
    items = [
        AlertItem(
            id=r["id"],
            rule_id=r["rule_id"],
            rule_name=r["rule_name"],
            severity=r["severity"],
            source_ip=r.get("source_ip"),
            matched_count=r["matched_count"],
            timestamp=r["timestamp"],
            status=r["status"],
            created_at=r["created_at"],
            triage=_build_triage_summary(r),
        )
        for r in rows
    ]
    return AlertListResponse(items=items, total=total, page=page, page_size=page_size)


@app.get("/alerts/{alert_id}", response_model=AlertDetail)
def get_alert(
    alert_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> AlertDetail:
    """Return full detail for a single alert including raw log and triage.

    Args:
        alert_id: Alert primary key.
        db: Injected SQLite connection.

    Returns:
        Full alert detail.

    Raises:
        HTTPException: 404 if the alert does not exist.
    """
    row = fetch_alert_by_id(db, alert_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    return AlertDetail(
        id=row["id"],
        rule_id=row["rule_id"],
        rule_name=row["rule_name"],
        severity=row["severity"],
        source_ip=row.get("source_ip"),
        matched_count=row["matched_count"],
        timestamp=row["timestamp"],
        status=row["status"],
        created_at=row["created_at"],
        raw_log=row["raw_log"],
        triage=_build_triage_detail(row),
    )


@app.get("/stats", response_model=StatsResponse)
def stats(db: sqlite3.Connection = Depends(get_db)) -> StatsResponse:
    """Return per-severity alert counts for the last 24 hours.

    Uses the LLM-qualified triage severity when available, falling back to
    the Sigma rule severity for untriaged alerts.

    Args:
        db: Injected SQLite connection.

    Returns:
        Stats with window_hours, counts dict, and total.
    """
    counts = fetch_stats(db, window_hours=24)
    # Ensure all severity levels are present (zero if none)
    full_counts = {sev: counts.get(sev, 0) for sev in _VALID_SEVERITIES}
    return StatsResponse(
        window_hours=24,
        counts=full_counts,
        total=sum(full_counts.values()),
    )


@app.get("/export")
def export_alerts(
    severity: str | None = Query(None, pattern=_SEVERITY_PATTERN),
    db: sqlite3.Connection = Depends(get_db),
) -> Response:
    """Download all matching alerts as a JSON file attachment.

    Args:
        severity: Optional severity filter.
        db: Injected SQLite connection.

    Returns:
        JSON file response with ``Content-Disposition: attachment``.
    """
    rows = fetch_all_alerts_for_export(db, severity)
    payload = {"alerts": rows, "count": len(rows)}
    content = json.dumps(payload, indent=2, default=str)
    filename = f"alerts{'_' + severity if severity else ''}.json"
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("API_PORT", "8000"))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=False)
