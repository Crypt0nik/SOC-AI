"""Integration tests for the SOC-AI FastAPI endpoints."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from api.main import app
from engine.db import insert_alert
from engine.models import Alert
from llm_agent.db import insert_triage
from llm_agent.schema import TriageResult
from parser.db import insert_event
from parser.models import Event

# ── Seed helpers ──────────────────────────────────────────────────────────────


def _ts() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _event(conn, source_ip="1.2.3.4", source_type="ssh") -> int:
    e = Event(
        timestamp=_ts(),
        source_ip=source_ip,
        user=None,
        action="ssh_failed_auth",
        raw_log=f"Failed password for root from {source_ip} port 22 ssh2",
        source_type=source_type,
    )
    e.id = insert_event(conn, e)
    return e.id


def _alert(conn, event_id: int, severity: str = "HIGH") -> int:
    a = Alert(
        event_id=event_id,
        rule_id="SSH-001",
        rule_name="SSH Brute Force",
        severity=severity,
        source_ip="1.2.3.4",
        matched_count=6,
        timestamp=_ts(),
    )
    return insert_alert(conn, a)


_VALID_TRIAGE = TriageResult(
    severity="HIGH",
    attack_type="SSH Brute Force",
    mitre_id="T1110",
    confidence=88,
    summary="Repeated SSH failures from external IP detected.",
    recommendation="Block source IP at the firewall.",
    false_positive_risk="LOW",
)


def _triage(conn, alert_id: int, sev: str = "HIGH") -> None:
    result = _VALID_TRIAGE.model_copy(update={"severity": sev})
    insert_triage(conn, alert_id, result, "mock", result.model_dump_json())


# ── Health ────────────────────────────────────────────────────────────────────


def test_health_ok(tmp_db):
    with TestClient(app) as client:
        r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"


# ── /alerts list ──────────────────────────────────────────────────────────────


def test_list_alerts_empty(tmp_db):
    with TestClient(app) as client:
        r = client.get("/alerts")
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["page"] == 1
    assert body["page_size"] == 20


def test_list_alerts_returns_inserted_alert(tmp_db):
    _, conn = tmp_db
    eid = _event(conn)
    _alert(conn, eid, severity="HIGH")
    with TestClient(app) as client:
        r = client.get("/alerts")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    item = body["items"][0]
    assert item["rule_id"] == "SSH-001"
    assert item["severity"] == "HIGH"
    assert item["triage"] is None  # untriaged


def test_list_alerts_includes_triage_summary(tmp_db):
    _, conn = tmp_db
    eid = _event(conn)
    aid = _alert(conn, eid)
    _triage(conn, aid)
    with TestClient(app) as client:
        r = client.get("/alerts")
    item = r.json()["items"][0]
    assert item["triage"] is not None
    assert item["triage"]["severity"] == "HIGH"
    assert item["triage"]["confidence"] == 88
    assert item["triage"]["backend"] == "mock"


def test_list_alerts_severity_filter_matches(tmp_db):
    _, conn = tmp_db
    eid1 = _event(conn)
    _alert(conn, eid1, severity="CRITICAL")
    eid2 = _event(conn, source_ip="2.2.2.2")
    _alert(conn, eid2, severity="LOW")
    with TestClient(app) as client:
        r = client.get("/alerts?severity=CRITICAL")
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["severity"] == "CRITICAL"


def test_list_alerts_severity_filter_no_match(tmp_db):
    _, conn = tmp_db
    eid = _event(conn)
    _alert(conn, eid, severity="HIGH")
    with TestClient(app) as client:
        r = client.get("/alerts?severity=CRITICAL")
    assert r.json()["total"] == 0


def test_list_alerts_invalid_severity_returns_422(tmp_db):
    with TestClient(app) as client:
        r = client.get("/alerts?severity=EXTREME")
    assert r.status_code == 422


def test_list_alerts_page_zero_returns_422(tmp_db):
    with TestClient(app) as client:
        r = client.get("/alerts?page=0")
    assert r.status_code == 422


def test_list_alerts_page_size_too_large_returns_422(tmp_db):
    with TestClient(app) as client:
        r = client.get("/alerts?page_size=101")
    assert r.status_code == 422


def test_list_alerts_pagination(tmp_db):
    _, conn = tmp_db
    for _ in range(5):
        eid = _event(conn)
        _alert(conn, eid)
    with TestClient(app) as client:
        r1 = client.get("/alerts?page=1&page_size=3")
        r2 = client.get("/alerts?page=2&page_size=3")
    assert r1.json()["total"] == 5
    assert len(r1.json()["items"]) == 3
    assert len(r2.json()["items"]) == 2


# ── /alerts/{id} detail ───────────────────────────────────────────────────────


def test_alert_detail_untriaged(tmp_db):
    _, conn = tmp_db
    eid = _event(conn)
    aid = _alert(conn, eid, severity="MEDIUM")
    with TestClient(app) as client:
        r = client.get(f"/alerts/{aid}")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == aid
    assert body["severity"] == "MEDIUM"
    assert "raw_log" in body
    assert "Failed password" in body["raw_log"]
    assert body["triage"] is None


def test_alert_detail_with_triage(tmp_db):
    _, conn = tmp_db
    eid = _event(conn)
    aid = _alert(conn, eid)
    _triage(conn, aid, sev="CRITICAL")
    with TestClient(app) as client:
        r = client.get(f"/alerts/{aid}")
    body = r.json()
    assert body["triage"] is not None
    assert body["triage"]["severity"] == "CRITICAL"
    assert body["triage"]["mitre_id"] == "T1110"
    assert "summary" in body["triage"]
    assert "recommendation" in body["triage"]
    assert "raw_llm_json" in body["triage"]


def test_alert_detail_not_found(tmp_db):
    with TestClient(app) as client:
        r = client.get("/alerts/99999")
    assert r.status_code == 404


# ── /stats ────────────────────────────────────────────────────────────────────


def test_stats_empty(tmp_db):
    with TestClient(app) as client:
        r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["window_hours"] == 24
    assert body["total"] == 0
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        assert sev in body["counts"]
        assert body["counts"][sev] == 0


def test_stats_counts_by_severity(tmp_db):
    _, conn = tmp_db
    for sev in ("CRITICAL", "HIGH", "HIGH", "LOW"):
        eid = _event(conn)
        _alert(conn, eid, severity=sev)
    with TestClient(app) as client:
        r = client.get("/stats")
    body = r.json()
    assert body["total"] == 4
    assert body["counts"]["CRITICAL"] == 1
    assert body["counts"]["HIGH"] == 2
    assert body["counts"]["LOW"] == 1
    assert body["counts"]["MEDIUM"] == 0


def test_stats_uses_triage_severity_when_available(tmp_db):
    _, conn = tmp_db
    eid = _event(conn)
    aid = _alert(conn, eid, severity="HIGH")
    _triage(conn, aid, sev="CRITICAL")  # LLM escalated severity
    with TestClient(app) as client:
        r = client.get("/stats")
    body = r.json()
    # Effective severity is triage.severity = CRITICAL, not alerts.severity = HIGH
    assert body["counts"]["CRITICAL"] == 1
    assert body["counts"]["HIGH"] == 0


# ── /export ───────────────────────────────────────────────────────────────────


def test_export_returns_json_attachment(tmp_db):
    _, conn = tmp_db
    eid = _event(conn)
    _alert(conn, eid, severity="HIGH")
    with TestClient(app) as client:
        r = client.get("/export")
    assert r.status_code == 200
    assert "attachment" in r.headers.get("content-disposition", "")
    body = r.json()
    assert "alerts" in body
    assert body["count"] == 1


def test_export_severity_filter(tmp_db):
    _, conn = tmp_db
    eid1 = _event(conn)
    _alert(conn, eid1, severity="HIGH")
    eid2 = _event(conn, source_ip="5.5.5.5")
    _alert(conn, eid2, severity="LOW")
    with TestClient(app) as client:
        r = client.get("/export?severity=HIGH")
    body = r.json()
    assert body["count"] == 1
    assert body["alerts"][0]["severity"] == "HIGH"


def test_export_invalid_severity_returns_422(tmp_db):
    with TestClient(app) as client:
        r = client.get("/export?severity=UNKNOWN")
    assert r.status_code == 422


def test_export_empty_db(tmp_db):
    with TestClient(app) as client:
        r = client.get("/export")
    body = r.json()
    assert body["count"] == 0
    assert body["alerts"] == []
