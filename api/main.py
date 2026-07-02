"""SOC-AI FastAPI backend.

Exposes a REST API consumed by the dashboard:
- GET  /health              → service + DB status
- GET  /plan                → current plan + enabled features
- GET  /alerts              → paginated alert list (joined with triage)
- GET  /alerts/{id}         → alert detail with raw log + full triage
- DELETE /alerts            → clear all alerts (for testing)
- DELETE /alerts/{id}       → delete a single alert
- GET  /stats               → per-severity counts for the last 24 h
- GET  /export              → full JSON download (optional severity filter)
- GET  /pro/mitre-stats     → MITRE technique frequency [Pro]
- GET  /pro/risk-scores     → top IPs by cumulative risk score [Pro]
"""

import json
import logging
import os
import sqlite3
from collections.abc import Generator

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from api import config as cfg
from api.db import (
    delete_alert,
    delete_all_alerts,
    fetch_alert_by_id,
    fetch_alerts,
    fetch_all_alerts_for_export,
    fetch_compliance_stats,
    fetch_ip_timeline,
    fetch_note,
    fetch_stats,
    get_connection,
    upsert_note,
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
    version="1.5.0",
    description="Community + Pro Edition — lightweight LLM-powered SOC triage API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "DELETE", "POST"],
    allow_headers=["*", "X-Admin-Token"],
)

_VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
_SEVERITY_PATTERN = "^(CRITICAL|HIGH|MEDIUM|LOW|INFO)$"
_SEV_WEIGHT = {"CRITICAL": 10, "HIGH": 5, "MEDIUM": 2, "LOW": 1, "INFO": 0}


# ── Dependencies ──────────────────────────────────────────────────────────────


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI dependency: yield a per-request SQLite connection, close on exit."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def require_pro(x_admin_token: str | None = Header(default=None)) -> None:
    """Dependency that enforces Pro plan (or valid admin token).

    Args:
        x_admin_token: Optional ``X-Admin-Token`` header for admin bypass.

    Raises:
        HTTPException: 403 when neither Pro plan nor valid admin token is present.
    """
    if cfg.is_pro():
        return
    if x_admin_token and cfg.ADMIN_TOKEN and x_admin_token == cfg.ADMIN_TOKEN:
        return
    raise HTTPException(
        status_code=403,
        detail="This endpoint requires a Pro or Enterprise plan.",
    )


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


# ── Community routes ──────────────────────────────────────────────────────────


@app.get("/health", response_model=HealthResponse)
def health(db: sqlite3.Connection = Depends(get_db)) -> HealthResponse:
    """Return service and database health status."""
    try:
        db.execute("SELECT 1").fetchone()
        db_status = "ok"
    except Exception:  # noqa: BLE001
        db_status = "error"
    return HealthResponse(status="ok", db=db_status)


@app.get("/plan")
def plan_info() -> dict:
    """Return the current plan and list of enabled Pro/Enterprise features.

    Returns:
        Dict with plan name, feature list, and boolean flags.
    """
    return {
        "plan": cfg.PLAN,
        "features": cfg.enabled_features(),
        "isPro": cfg.is_pro(),
        "isEnterprise": cfg.is_enterprise(),
    }


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


@app.delete("/alerts")
def clear_all_alerts(db: sqlite3.Connection = Depends(get_db)) -> dict:
    """Delete all alerts and their triage records.

    Args:
        db: Injected SQLite connection.

    Returns:
        Dict with count of deleted alerts.
    """
    count = delete_all_alerts(db)
    logger.info("Cleared %d alerts", count)
    return {"deleted": count}


@app.delete("/alerts/{alert_id}")
def remove_alert(alert_id: int, db: sqlite3.Connection = Depends(get_db)) -> dict:
    """Delete a single alert and its triage record.

    Args:
        alert_id: Alert primary key.
        db: Injected SQLite connection.

    Returns:
        Dict with deleted id.

    Raises:
        HTTPException: 404 if the alert does not exist.
    """
    ok = delete_alert(db, alert_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")
    logger.info("Deleted alert %d", alert_id)
    return {"deleted": alert_id}


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


# ── Pro routes ────────────────────────────────────────────────────────────────


@app.get("/pro/mitre-stats")
def mitre_stats(
    db: sqlite3.Connection = Depends(get_db),
    _: None = Depends(require_pro),
) -> dict:
    """Return MITRE technique frequency for the ATT&CK heatmap.

    Args:
        db: Injected SQLite connection.

    Returns:
        Dict with list of ``{id, count}`` technique objects.
    """
    try:
        rows = db.execute(
            "SELECT mitre_id, COUNT(*) AS cnt "
            "FROM triage WHERE mitre_id IS NOT NULL "
            "GROUP BY mitre_id ORDER BY cnt DESC"
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("mitre_stats failed: %s", exc)
        rows = []
    return {"techniques": [{"id": r["mitre_id"], "count": r["cnt"]} for r in rows]}


@app.get("/pro/risk-scores")
def risk_scores(
    limit: int = Query(10, ge=1, le=50),
    db: sqlite3.Connection = Depends(get_db),
    _: None = Depends(require_pro),
) -> dict:
    """Return top source IPs ranked by cumulative risk score.

    Score = SUM(severity_weight × matched_count) per source_ip.
    Weights: CRITICAL=10, HIGH=5, MEDIUM=2, LOW=1, INFO=0.

    Args:
        limit: Maximum number of IPs to return (1–50).
        db: Injected SQLite connection.

    Returns:
        Dict with list of ``{source_ip, score, alert_count, top_severity}`` objects.
    """
    try:
        rows = db.execute(
            "SELECT a.source_ip, "
            "SUM(CASE COALESCE(t.severity, a.severity) "
            "    WHEN 'CRITICAL' THEN 10 * a.matched_count "
            "    WHEN 'HIGH'     THEN  5 * a.matched_count "
            "    WHEN 'MEDIUM'   THEN  2 * a.matched_count "
            "    WHEN 'LOW'      THEN  1 * a.matched_count "
            "    ELSE 0 END) AS score, "
            "COUNT(*) AS alert_count, "
            "MAX(CASE COALESCE(t.severity, a.severity) "
            "    WHEN 'CRITICAL' THEN 5 "
            "    WHEN 'HIGH'     THEN 4 "
            "    WHEN 'MEDIUM'   THEN 3 "
            "    WHEN 'LOW'      THEN 2 "
            "    ELSE 1 END) AS sev_rank, "
            "COALESCE(t.severity, a.severity) AS top_sev "
            "FROM alerts a LEFT JOIN triage t ON t.alert_id = a.id "
            "WHERE a.source_ip IS NOT NULL "
            "GROUP BY a.source_ip "
            "ORDER BY score DESC LIMIT ?",
            (limit,),
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("risk_scores failed: %s", exc)
        rows = []

    sev_names = {5: "CRITICAL", 4: "HIGH", 3: "MEDIUM", 2: "LOW", 1: "INFO"}
    return {
        "scores": [
            {
                "source_ip": r["source_ip"],
                "score": r["score"] or 0,
                "alert_count": r["alert_count"],
                "top_severity": sev_names.get(r["sev_rank"], "INFO"),
            }
            for r in rows
        ]
    }


@app.get("/pro/ip-timeline/{source_ip}")
def ip_timeline(
    source_ip: str,
    db: sqlite3.Connection = Depends(get_db),
    _: None = Depends(require_pro),
) -> dict:
    """Return alert history for a specific source IP (last 50 alerts).

    Args:
        source_ip: IP address to look up.
        db: Injected SQLite connection.

    Returns:
        Dict with ip, alerts list, and severity summary.
    """
    rows = fetch_ip_timeline(db, source_ip)
    return {"ip": source_ip, "alerts": rows, "total": len(rows)}


# ── Enterprise routes ─────────────────────────────────────────────────────────


@app.get("/enterprise/compliance")
def compliance_report(
    window_days: int = Query(30, ge=1, le=365),
    db: sqlite3.Connection = Depends(get_db),
    _: None = Depends(require_pro),
) -> dict:
    """Return compliance metrics for NIS2/ISO27001 reporting.

    Args:
        window_days: Look-back window in days (1–365).
        db: Injected SQLite connection.

    Returns:
        Compliance metrics dict.
    """
    return fetch_compliance_stats(db, window_days)


# ── Notes routes (Community) ──────────────────────────────────────────────────


@app.get("/alerts/{alert_id}/note")
def get_note_endpoint(
    alert_id: int,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    """Fetch analyst note for a single alert.

    Args:
        alert_id: Alert primary key.
        db: Injected SQLite connection.

    Returns:
        Dict with note text (empty string if none).
    """
    note = fetch_note(db, alert_id)
    return {"alert_id": alert_id, "note": note or ""}


@app.post("/alerts/{alert_id}/note")
def set_note_endpoint(
    alert_id: int,
    body: dict,
    db: sqlite3.Connection = Depends(get_db),
) -> dict:
    """Save or update analyst note for an alert.

    Args:
        alert_id: Alert primary key.
        body: JSON body containing ``note`` string.
        db: Injected SQLite connection.

    Returns:
        Dict confirming saved alert_id.

    Raises:
        HTTPException: 400 if note text is missing.
    """
    note = body.get("note", "")
    if not isinstance(note, str):
        raise HTTPException(status_code=400, detail="note must be a string")
    ok = upsert_note(db, alert_id, note)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to save note")
    return {"alert_id": alert_id, "saved": True}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("API_PORT", "8000"))
    uvicorn.run("api.main:app", host="0.0.0.0", port=port, reload=False)
