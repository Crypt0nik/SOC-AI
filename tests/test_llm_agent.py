"""Tests for the LLM triage agent (backend mocked)."""

import json
from unittest.mock import MagicMock

from engine.db import insert_alert
from llm_agent.agent import process_alert
from llm_agent.backends.base import LLMBackend
from llm_agent.db import fetch_untriaged_alerts
from parser.db import insert_event
from parser.models import Event

# ── Helpers ───────────────────────────────────────────────────────────────────

_SYSTEM = "system prompt"

_VALID_JSON = json.dumps({
    "severity": "HIGH",
    "attack_type": "SSH Brute Force",
    "mitre_id": "T1110",
    "confidence": 90,
    "summary": "Multiple failed logins detected from a single external IP.",
    "recommendation": "Block source IP at the firewall immediately.",
    "false_positive_risk": "LOW",
})


def _make_backend(response: str, raises: Exception | None = None) -> LLMBackend:
    """Return a mock LLMBackend that returns *response* or raises *raises*."""
    backend = MagicMock(spec=LLMBackend)
    backend.name = "mock"
    if raises:
        backend.triage.side_effect = raises
    else:
        backend.triage.return_value = response
    return backend


def _seed_alert(conn):
    """Insert a minimal event + alert and return the alert row."""
    from datetime import UTC, datetime

    ts = datetime.now(UTC).isoformat().replace("+00:00", "Z")
    event = Event(
        timestamp=ts,
        source_ip="1.2.3.4",
        user=None,
        action="ssh_failed_auth",
        raw_log="Failed password for root from 1.2.3.4 port 22 ssh2",
        source_type="ssh",
    )
    event.id = insert_event(conn, event)

    from engine.models import Alert
    alert = Alert(
        event_id=event.id,
        rule_id="SSH-001",
        rule_name="SSH Brute Force",
        severity="HIGH",
        source_ip="1.2.3.4",
        matched_count=6,
        timestamp=ts,
    )
    insert_alert(conn, alert)
    rows = fetch_untriaged_alerts(conn)
    assert rows, "Expected at least one untriaged alert"
    return rows[0]


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_valid_json_marks_alert_triaged(tmp_db):
    _, conn = tmp_db
    row = _seed_alert(conn)
    backend = _make_backend(_VALID_JSON)
    success = process_alert(conn, row, backend, _SYSTEM, anonymize_pii=False)
    assert success is True
    status = conn.execute(
        "SELECT status FROM alerts WHERE id=?", (row["id"],)
    ).fetchone()["status"]
    assert status == "triaged"


def test_valid_json_inserts_triage_row(tmp_db):
    _, conn = tmp_db
    row = _seed_alert(conn)
    backend = _make_backend(_VALID_JSON)
    process_alert(conn, row, backend, _SYSTEM, anonymize_pii=False)
    triage = conn.execute(
        "SELECT * FROM triage WHERE alert_id=?", (row["id"],)
    ).fetchone()
    assert triage is not None
    assert triage["severity"] == "HIGH"
    assert triage["confidence"] == 90
    assert triage["backend"] == "mock"


def test_invalid_json_both_attempts_marks_error(tmp_db):
    _, conn = tmp_db
    row = _seed_alert(conn)
    backend = _make_backend("this is not json {{{")
    success = process_alert(conn, row, backend, _SYSTEM, anonymize_pii=False)
    assert success is False
    status = conn.execute(
        "SELECT status FROM alerts WHERE id=?", (row["id"],)
    ).fetchone()["status"]
    assert status == "error"
    assert backend.triage.call_count == 2


def test_backend_exception_marks_error(tmp_db):
    _, conn = tmp_db
    row = _seed_alert(conn)
    backend = _make_backend("", raises=ConnectionError("Ollama unreachable"))
    success = process_alert(conn, row, backend, _SYSTEM, anonymize_pii=False)
    assert success is False
    status = conn.execute(
        "SELECT status FROM alerts WHERE id=?", (row["id"],)
    ).fetchone()["status"]
    assert status == "error"


def test_retry_succeeds_on_second_attempt(tmp_db):
    _, conn = tmp_db
    row = _seed_alert(conn)
    # First call returns garbage, second call returns valid JSON
    backend = MagicMock(spec=LLMBackend)
    backend.name = "mock"
    backend.triage.side_effect = ["not json", _VALID_JSON]
    success = process_alert(conn, row, backend, _SYSTEM, anonymize_pii=False)
    assert success is True
    assert backend.triage.call_count == 2
    status = conn.execute(
        "SELECT status FROM alerts WHERE id=?", (row["id"],)
    ).fetchone()["status"]
    assert status == "triaged"


def test_process_alert_with_pii_anonymization(tmp_db):
    _, conn = tmp_db
    row = _seed_alert(conn)
    backend = _make_backend(_VALID_JSON)
    success = process_alert(conn, row, backend, _SYSTEM, anonymize_pii=True)
    assert success is True
    # PII mapping should have been stored
    mapping_count = conn.execute(
        "SELECT COUNT(*) FROM pii_mapping WHERE alert_id=?", (row["id"],)
    ).fetchone()[0]
    assert mapping_count >= 1


def test_retry_prompt_appends_json_reminder(tmp_db):
    _, conn = tmp_db
    row = _seed_alert(conn)
    # Both fail so we see both prompts
    backend = _make_backend("bad json")
    process_alert(conn, row, backend, _SYSTEM, anonymize_pii=False)
    first_call_user = backend.triage.call_args_list[0][0][1]
    second_call_user = backend.triage.call_args_list[1][0][1]
    assert "JSON" in second_call_user
    assert len(second_call_user) > len(first_call_user)


def test_no_triage_row_on_error(tmp_db):
    _, conn = tmp_db
    row = _seed_alert(conn)
    backend = _make_backend("bad")
    process_alert(conn, row, backend, _SYSTEM, anonymize_pii=False)
    count = conn.execute(
        "SELECT COUNT(*) FROM triage WHERE alert_id=?", (row["id"],)
    ).fetchone()[0]
    assert count == 0
