"""Unit tests for the Sigma field matcher (engine/matcher.py)."""

from datetime import UTC, datetime

from engine.matcher import evaluate_detection, match_field_value, match_selection
from parser.models import Event


def _event(**kwargs) -> Event:
    defaults = {
        "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "source_ip": "192.168.1.1",
        "user": "admin",
        "action": "ssh_failed_auth",
        "raw_log": "raw log line",
        "source_type": "ssh",
    }
    defaults.update(kwargs)
    return Event(**defaults)


# ── match_field_value ─────────────────────────────────────────────────────────

def test_exact_match_hits():
    assert match_field_value("ssh_failed_auth", "ssh_failed_auth", []) is True


def test_exact_match_miss():
    assert match_field_value("ssh_accepted_auth", "ssh_failed_auth", []) is False


def test_exact_match_list_any():
    assert match_field_value("B", ["A", "B", "C"], []) is True


def test_exact_match_list_none():
    assert match_field_value("D", ["A", "B", "C"], []) is False


def test_contains_modifier_hit():
    assert match_field_value("SELECT * FROM users", "SELECT", ["contains"]) is True


def test_contains_modifier_case_insensitive():
    assert match_field_value("select * from users", "SELECT", ["contains"]) is True


def test_contains_modifier_miss():
    assert match_field_value("normal log line", "DROP TABLE", ["contains"]) is False


def test_contains_list_any_hit():
    assert match_field_value("../etc/passwd", ["../", "%2e%2e"], ["contains"]) is True


def test_startswith_hit():
    assert match_field_value("10.0.0.1", "10.", ["startswith"]) is True


def test_startswith_miss():
    assert match_field_value("192.168.1.1", "10.", ["startswith"]) is False


def test_startswith_list_any_hit():
    assert match_field_value("192.168.1.1", ["10.", "192.168."], ["startswith"]) is True


def test_null_value_no_match():
    assert match_field_value(None, "anything", []) is False


def test_null_value_with_modifier():
    assert match_field_value(None, "something", ["contains"]) is False


# ── match_selection ───────────────────────────────────────────────────────────

def test_selection_all_fields_match():
    evt = _event(action="ssh_failed_auth", source_type="ssh")
    sel = {"action": "ssh_failed_auth", "source_type": "ssh"}
    assert match_selection(evt, sel) is True


def test_selection_one_field_miss():
    evt = _event(action="ssh_accepted_auth", source_type="ssh")
    sel = {"action": "ssh_failed_auth", "source_type": "ssh"}
    assert match_selection(evt, sel) is False


def test_selection_with_contains_modifier():
    evt = _event(raw_log="/admin/../../../etc/passwd HTTP/1.1")
    sel = {"raw_log|contains": "../"}
    assert match_selection(evt, sel) is True


def test_empty_selection_matches_any():
    evt = _event()
    assert match_selection(evt, {}) is True


# ── evaluate_detection ────────────────────────────────────────────────────────

def test_condition_selection():
    evt = _event(action="ssh_failed_auth")
    detection = {"selection": {"action": "ssh_failed_auth"}, "condition": "selection"}
    assert evaluate_detection(evt, detection) is True


def test_condition_selection_and_not_filter_passes():
    evt = _event(action="ssh_accepted_auth", source_ip="203.0.113.7")
    detection = {
        "selection": {"action": "ssh_accepted_auth"},
        "filter": {"source_ip|startswith": ["10.", "192.168.", "172.", "127."]},
        "condition": "selection and not filter",
    }
    assert evaluate_detection(evt, detection) is True


def test_condition_selection_and_not_filter_blocked():
    evt = _event(action="ssh_accepted_auth", source_ip="10.0.0.5")
    detection = {
        "selection": {"action": "ssh_accepted_auth"},
        "filter": {"source_ip|startswith": ["10.", "192.168.", "172.", "127."]},
        "condition": "selection and not filter",
    }
    assert evaluate_detection(evt, detection) is False


def test_condition_selection_miss():
    evt = _event(action="ssh_accepted_auth")
    detection = {"selection": {"action": "ssh_failed_auth"}, "condition": "selection"}
    assert evaluate_detection(evt, detection) is False
