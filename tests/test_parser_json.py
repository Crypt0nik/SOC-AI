"""Unit tests for the generic JSON log parser."""

import json

from parser.formats.generic_json import parse_json_line


def test_full_json_event():
    payload = {
        "timestamp": "2026-06-29T10:00:00Z",
        "source_ip": "10.1.2.3",
        "user": "svcaccount",
        "action": "login_attempt",
        "raw_log": "svcaccount attempted login from 10.1.2.3",
    }
    event = parse_json_line(json.dumps(payload))
    assert event is not None
    assert event.source_ip == "10.1.2.3"
    assert event.user == "svcaccount"
    assert event.action == "login_attempt"
    assert event.source_type == "json"
    assert event.timestamp == "2026-06-29T10:00:00Z"


def test_missing_optional_fields():
    payload = {"action": "generic_event", "raw_log": "some log"}
    event = parse_json_line(json.dumps(payload))
    assert event is not None
    assert event.source_ip is None
    assert event.user is None
    assert event.action == "generic_event"


def test_missing_action_uses_fallback():
    payload = {"source_ip": "1.2.3.4", "raw_log": "raw entry"}
    event = parse_json_line(json.dumps(payload))
    assert event is not None
    assert event.action == "json_event"


def test_raw_log_generated_if_absent():
    payload = {"source_ip": "5.6.7.8", "action": "test"}
    event = parse_json_line(json.dumps(payload))
    assert event is not None
    assert event.raw_log != ""  # fallback to serialised JSON


def test_invalid_json_returns_none():
    assert parse_json_line("{not valid json}") is None


def test_empty_string_returns_none():
    assert parse_json_line("") is None


def test_non_object_json_returns_none():
    assert parse_json_line('["a", "b"]') is None
