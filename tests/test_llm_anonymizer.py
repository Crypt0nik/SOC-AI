"""Tests for the PII anonymiser (tokenise / deanonymise round-trip)."""

from datetime import UTC, datetime

from llm_agent.anonymizer import anonymize, deanonymize


def _ts() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _make_alert(conn, alert_id: int = 1) -> int:
    """Insert a minimal event + alert row so pii_mapping FK is satisfied."""
    conn.execute(
        "INSERT INTO events (id, timestamp, source_ip, user, action, raw_log, source_type) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (alert_id, _ts(), "1.2.3.4", None, "test_action", "raw", "json"),
    )
    conn.execute(
        "INSERT INTO alerts (id, event_id, rule_id, rule_name, severity, "
        "source_ip, matched_count, timestamp) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (alert_id, alert_id, "TEST-001", "Test Rule", "LOW", "1.2.3.4", 1, _ts()),
    )
    conn.commit()
    return alert_id


def test_ip_in_text_is_tokenised(tmp_db):
    _, conn = tmp_db
    _make_alert(conn, 1)
    text = "Connection from 192.168.1.100 failed"
    result, mapping = anonymize(text, conn, alert_id=1)
    assert "192.168.1.100" not in result
    assert "IP_1" in result
    assert mapping["IP_1"] == "192.168.1.100"


def test_email_in_text_is_tokenised(tmp_db):
    _, conn = tmp_db
    _make_alert(conn, 2)
    text = "User admin@example.com attempted login"
    result, mapping = anonymize(text, conn, alert_id=2)
    assert "admin@example.com" not in result
    assert "EMAIL_1" in result
    assert mapping["EMAIL_1"] == "admin@example.com"


def test_known_ip_in_text_is_tokenised(tmp_db):
    _, conn = tmp_db
    _make_alert(conn, 3)
    text = "Brute force from 10.0.0.5 detected"
    result, mapping = anonymize(text, conn, alert_id=3, known_ips=["10.0.0.5"])
    assert "10.0.0.5" not in result
    assert "IP_1" in result
    assert mapping["IP_1"] == "10.0.0.5"


def test_known_ip_not_in_text_still_in_mapping(tmp_db):
    # When source_ip isn't in the raw text, the token goes into mapping but not result
    _, conn = tmp_db
    _make_alert(conn, 4)
    text = "Brute force detected"
    result, mapping = anonymize(text, conn, alert_id=4, known_ips=["10.0.0.5"])
    assert result == text  # text unchanged — IP wasn't present
    assert mapping.get("IP_1") == "10.0.0.5"


def test_known_user_in_text_is_tokenised(tmp_db):
    _, conn = tmp_db
    _make_alert(conn, 5)
    text = "Failed password for alice from 1.2.3.4"
    result, mapping = anonymize(
        text, conn, alert_id=5, known_ips=["1.2.3.4"], known_users=["alice"]
    )
    assert "alice" not in result
    assert "1.2.3.4" not in result
    assert "USER_1" in result
    assert "IP_1" in result


def test_same_ip_gets_same_token(tmp_db):
    _, conn = tmp_db
    _make_alert(conn, 6)
    text = "1.2.3.4 connected then 1.2.3.4 again"
    result, mapping = anonymize(text, conn, alert_id=6)
    assert result.count("IP_1") == 2
    assert "IP_2" not in result


def test_multiple_different_ips_get_distinct_tokens(tmp_db):
    _, conn = tmp_db
    _make_alert(conn, 7)
    text = "From 10.0.0.1 and from 10.0.0.2"
    result, mapping = anonymize(text, conn, alert_id=7)
    assert "10.0.0.1" not in result
    assert "10.0.0.2" not in result
    assert len(mapping) == 2


def test_no_pii_text_unchanged(tmp_db):
    _, conn = tmp_db
    _make_alert(conn, 8)
    text = "Normal log message with no PII here"
    result, mapping = anonymize(text, conn, alert_id=8)
    assert result == text
    assert mapping == {}


def test_mapping_persisted_to_pii_mapping_table(tmp_db):
    _, conn = tmp_db
    _make_alert(conn, 9)
    text = "From 1.2.3.4 port 22"
    anonymize(text, conn, alert_id=9)
    rows = conn.execute(
        "SELECT token, original, kind FROM pii_mapping WHERE alert_id=9"
    ).fetchall()
    assert len(rows) == 1
    assert rows[0]["token"] == "IP_1"
    assert rows[0]["original"] == "1.2.3.4"
    assert rows[0]["kind"] == "ip"


def test_deanonymize_round_trip(tmp_db):
    _, conn = tmp_db
    _make_alert(conn, 10)
    original = "Login from 203.0.113.5 for user bob@corp.com"
    anon, _ = anonymize(original, conn, alert_id=10, known_users=["bob@corp.com"])
    assert "203.0.113.5" not in anon
    restored = deanonymize(anon, conn, alert_id=10)
    assert "203.0.113.5" in restored
    assert "bob@corp.com" in restored


def test_deanonymize_empty_mapping(tmp_db):
    _, conn = tmp_db
    _make_alert(conn, 11)
    text = "No tokens here"
    result = deanonymize(text, conn, alert_id=11)
    assert result == text
