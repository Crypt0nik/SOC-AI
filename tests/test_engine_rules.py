"""Per-rule tests for the Sigma engine (one trigger + one non-trigger per rule)."""

from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from engine.db import insert_alert
from engine.matcher import evaluate_rule
from engine.rules_loader import load_rules
from parser.db import insert_event
from parser.models import Event

RULES_DIR = Path(__file__).parent.parent / "engine" / "rules"


@pytest.fixture(scope="module")
def all_rules():
    """Load all engine rules once for the test session."""
    return load_rules(str(RULES_DIR))


def _get_rule(all_rules, rule_id):
    return next(r for r in all_rules if r.id == rule_id)


def _ts() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _insert(conn, **kwargs) -> Event:
    """Insert an event and return it with its DB id."""
    defaults = {
        "timestamp": _ts(),
        "source_ip": "1.2.3.4",
        "user": None,
        "action": "generic",
        "raw_log": "raw",
        "source_type": "json",
    }
    defaults.update(kwargs)
    event = Event(**defaults)
    event.id = insert_event(conn, event)
    return event


# ── SSH-001: Brute Force SSH ──────────────────────────────────────────────────

def test_ssh_001_triggers_on_threshold(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "SSH-001")
    ip = "192.168.1.45"
    for _ in range(5):
        _insert(conn, source_ip=ip, action="ssh_failed_auth", source_type="ssh", raw_log="Failed")
    sixth = _insert(
        conn, source_ip=ip, action="ssh_failed_auth", source_type="ssh", raw_log="Failed"
    )
    alert = evaluate_rule(conn, sixth, rule)
    assert alert is not None
    assert alert.rule_id == "SSH-001"
    assert alert.severity == "HIGH"
    assert alert.source_ip == ip
    assert alert.matched_count >= 5


def test_ssh_001_no_trigger_below_threshold(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "SSH-001")
    ip = "10.10.10.10"
    for _ in range(4):
        _insert(conn, source_ip=ip, action="ssh_failed_auth", source_type="ssh", raw_log="Failed")
    fourth = _insert(
        conn, source_ip=ip, action="ssh_failed_auth", source_type="ssh", raw_log="Failed"
    )
    assert evaluate_rule(conn, fourth, rule) is None


def test_ssh_001_dedup_no_double_alert(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "SSH-001")
    ip = "99.99.99.99"
    for _ in range(7):
        _insert(conn, source_ip=ip, action="ssh_failed_auth", source_type="ssh", raw_log="Failed")
    # Trigger first alert
    trigger = _insert(
        conn, source_ip=ip, action="ssh_failed_auth", source_type="ssh", raw_log="Failed"
    )
    first = evaluate_rule(conn, trigger, rule)
    assert first is not None
    insert_alert(conn, first)
    # Same IP again — should be deduplicated within the window
    trigger2 = _insert(
        conn, source_ip=ip, action="ssh_failed_auth", source_type="ssh", raw_log="Failed"
    )
    second = evaluate_rule(conn, trigger2, rule)
    assert second is None


# ── SSH-002: Direct SSH Root Login ────────────────────────────────────────────

def test_ssh_002_triggers_root_login(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "SSH-002")
    evt = _insert(conn, user="root", action="ssh_accepted_auth", source_type="ssh",
                  raw_log="Accepted publickey for root from 1.2.3.4 port 22 ssh2")
    alert = evaluate_rule(conn, evt, rule)
    assert alert is not None
    assert alert.rule_id == "SSH-002"
    assert alert.severity == "HIGH"


def test_ssh_002_no_trigger_regular_user(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "SSH-002")
    evt = _insert(conn, user="alice", action="ssh_accepted_auth", source_type="ssh",
                  raw_log="Accepted publickey for alice from 1.2.3.4 port 22 ssh2")
    assert evaluate_rule(conn, evt, rule) is None


# ── SSH-003: SSH Login from External IP ───────────────────────────────────────

def test_ssh_003_triggers_external_ip(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "SSH-003")
    evt = _insert(conn, source_ip="203.0.113.7", user="alice",
                  action="ssh_accepted_auth", source_type="ssh",
                  raw_log="Accepted password for alice from 203.0.113.7 port 22 ssh2")
    alert = evaluate_rule(conn, evt, rule)
    assert alert is not None
    assert alert.rule_id == "SSH-003"
    assert alert.severity == "MEDIUM"


def test_ssh_003_no_trigger_private_ip(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "SSH-003")
    evt = _insert(conn, source_ip="10.0.0.5", user="alice",
                  action="ssh_accepted_auth", source_type="ssh",
                  raw_log="Accepted publickey for alice from 10.0.0.5 port 22 ssh2")
    assert evaluate_rule(conn, evt, rule) is None


# ── WEB-001: SQL Injection ────────────────────────────────────────────────────

def test_web_001_triggers_sql_injection(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "WEB-001")
    raw = (
        '192.168.1.100 - - [29/Jun/2026:10:05:01 +0000]'
        ' "GET /page.php?id=1\' OR \'1\'=\'1 HTTP/1.1" 200 512 "-" "Mozilla/5.0"'
    )
    evt = _insert(conn, source_ip="192.168.1.100", action="http_request",
                  source_type="web", raw_log=raw)
    alert = evaluate_rule(conn, evt, rule)
    assert alert is not None
    assert alert.rule_id == "WEB-001"
    assert alert.severity == "HIGH"


def test_web_001_no_trigger_normal_request(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "WEB-001")
    raw = (
        '192.168.1.5 - - [29/Jun/2026:10:00:00 +0000]'
        ' "GET /dashboard HTTP/1.1" 200 4096 "-" "Chrome"'
    )
    evt = _insert(conn, source_ip="192.168.1.5", action="http_request",
                  source_type="web", raw_log=raw)
    assert evaluate_rule(conn, evt, rule) is None


# ── WEB-002: Path Traversal ───────────────────────────────────────────────────

def test_web_002_triggers_path_traversal(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "WEB-002")
    raw = (
        '192.168.1.100 - - [29/Jun/2026:10:05:05 +0000]'
        ' "GET /admin/../../../etc/passwd HTTP/1.1" 403 210 "-" "curl/7.88"'
    )
    evt = _insert(conn, source_ip="192.168.1.100", action="http_request",
                  source_type="web", raw_log=raw)
    alert = evaluate_rule(conn, evt, rule)
    assert alert is not None
    assert alert.rule_id == "WEB-002"
    assert alert.severity == "MEDIUM"


def test_web_002_no_trigger_normal_path(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "WEB-002")
    raw = (
        '10.0.0.1 - - [29/Jun/2026:11:00:00 +0000]'
        ' "GET /api/data HTTP/1.1" 200 128 "-" "Python/3.11"'
    )
    evt = _insert(conn, source_ip="10.0.0.1", action="http_request",
                  source_type="web", raw_log=raw)
    assert evaluate_rule(conn, evt, rule) is None


# ── WEB-003: HTTP Scanner ─────────────────────────────────────────────────────

def test_web_003_triggers_scanner_ua(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "WEB-003")
    raw = (
        '198.51.100.22 - - [29/Jun/2026:10:05:10 +0000]'
        ' "GET /robots.txt HTTP/1.1" 200 64 "-" "sqlmap/1.7.12"'
    )
    evt = _insert(conn, source_ip="198.51.100.22", action="http_request",
                  source_type="web", raw_log=raw)
    alert = evaluate_rule(conn, evt, rule)
    assert alert is not None
    assert alert.rule_id == "WEB-003"
    assert alert.severity == "LOW"


def test_web_003_no_trigger_normal_ua(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "WEB-003")
    raw = '10.0.0.1 - - [29/Jun/2026:10:00:00 +0000] "GET / HTTP/1.1" 200 1024 "-" "Mozilla/5.0"'
    evt = _insert(conn, source_ip="10.0.0.1", action="http_request",
                  source_type="web", raw_log=raw)
    assert evaluate_rule(conn, evt, rule) is None


# ── WIN-001: Privilege Escalation (Event 4672) ───────────────────────────────

def test_win_001_triggers_privilege_assigned(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "WIN-001")
    raw = "<Event><System><EventID>4672</EventID></System></Event>"
    evt = _insert(conn, source_ip=None, user="jdupont",
                  action="privilege_assigned", source_type="windows", raw_log=raw)
    alert = evaluate_rule(conn, evt, rule)
    assert alert is not None
    assert alert.rule_id == "WIN-001"
    assert alert.severity == "CRITICAL"


def test_win_001_no_trigger_regular_action(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "WIN-001")
    evt = _insert(conn, user="user", action="logon_success",
                  source_type="windows", raw_log="<Event/>")
    assert evaluate_rule(conn, evt, rule) is None


# ── WIN-002: User Account Created (Event 4720) ───────────────────────────────

def test_win_002_triggers_account_created(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "WIN-002")
    raw = "<Event><System><EventID>4720</EventID></System></Event>"
    evt = _insert(conn, user="hackeruser",
                  action="user_account_created", source_type="windows", raw_log=raw)
    alert = evaluate_rule(conn, evt, rule)
    assert alert is not None
    assert alert.rule_id == "WIN-002"
    assert alert.severity == "MEDIUM"


# ── WIN-003: SAM Registry Access (Event 4657) ────────────────────────────────

def test_win_003_triggers_sam_access(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "WIN-003")
    raw = (
        "<Event><System><EventID>4657</EventID></System>"
        "<EventData><Data>\\REGISTRY\\MACHINE\\SAM\\SAM\\Domains</Data></EventData></Event>"
    )
    evt = _insert(conn, user="SYSTEM",
                  action="registry_value_modified", source_type="windows", raw_log=raw)
    alert = evaluate_rule(conn, evt, rule)
    assert alert is not None
    assert alert.rule_id == "WIN-003"
    assert alert.severity == "CRITICAL"


def test_win_003_no_trigger_unrelated_registry(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "WIN-003")
    raw = "<Event><EventData><Data>\\HKLM\\SOFTWARE\\MyApp\\Config</Data></EventData></Event>"
    evt = _insert(conn, user="appuser",
                  action="registry_value_modified", source_type="windows", raw_log=raw)
    assert evaluate_rule(conn, evt, rule) is None


# ── NET-001: Port Scan ───────────────────────────────────────────────────────

def test_net_001_triggers_port_scan(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "NET-001")
    ip = "45.33.32.156"
    for _ in range(21):
        _insert(conn, source_ip=ip, action="net_connection", source_type="json",
                raw_log='{"action":"net_connection"}')
    last = _insert(conn, source_ip=ip, action="net_connection", source_type="json",
                   raw_log='{"action":"net_connection"}')
    alert = evaluate_rule(conn, last, rule)
    assert alert is not None
    assert alert.rule_id == "NET-001"
    assert alert.severity == "HIGH"


def test_net_001_no_trigger_below_threshold(tmp_db, all_rules):
    _, conn = tmp_db
    rule = _get_rule(all_rules, "NET-001")
    ip = "8.8.8.8"
    for _ in range(10):
        _insert(conn, source_ip=ip, action="net_connection", source_type="json",
                raw_log='{"action":"net_connection"}')
    last = _insert(conn, source_ip=ip, action="net_connection", source_type="json",
                   raw_log='{"action":"net_connection"}')
    assert evaluate_rule(conn, last, rule) is None


# ── pySigma validation ───────────────────────────────────────────────────────

def test_all_sigma_rules_parse_as_valid_yaml():
    """All rule YAML files must be valid YAML and contain required Sigma fields."""
    required_fields = {"title", "logsource", "detection"}
    rule_files = list(RULES_DIR.glob("*.yml"))
    assert len(rule_files) == 10, f"Expected 10 rules, found {len(rule_files)}"
    for rule_file in sorted(rule_files):
        data = yaml.safe_load(rule_file.read_text())
        assert isinstance(data, dict), f"{rule_file.name}: not a YAML dict"
        missing = required_fields - data.keys()
        assert not missing, f"{rule_file.name}: missing fields {missing}"
        soc_ai = data.get("soc_ai", {})
        assert "rule_id" in soc_ai, f"{rule_file.name}: missing soc_ai.rule_id"
        assert "severity" in soc_ai, f"{rule_file.name}: missing soc_ai.severity"
        assert "source_types" in soc_ai, f"{rule_file.name}: missing soc_ai.source_types"


def test_all_sigma_rules_parseable_by_pysigma():
    """All rules must pass pySigma structural validation (soc_ai block stripped)."""
    try:
        from sigma.rule import SigmaRule
    except ImportError:
        pytest.skip("pySigma not installed")

    rule_files = list(RULES_DIR.glob("*.yml"))
    for rule_file in sorted(rule_files):
        data = yaml.safe_load(rule_file.read_text())
        data.pop("soc_ai", None)  # strip custom block
        # Replace friendly ID with a valid UUID placeholder for pySigma
        data["id"] = "00000000-0000-0000-0000-000000000000"
        rule_yaml = yaml.dump(data)
        try:
            sigma_rule = SigmaRule.from_yaml(rule_yaml)
            assert sigma_rule.title is not None, f"{rule_file.name}: title is None"
        except Exception as exc:
            pytest.fail(f"pySigma rejected {rule_file.name}: {exc}")
