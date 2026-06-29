"""Unit tests for the SSH auth.log parser."""

from parser.formats.ssh import parse_ssh_line

_FAIL_INVALID = (  # noqa: E501
    "Jun 29 10:01:01 webserver sshd[12340]: Failed password for invalid user admin"
    " from 192.168.1.45 port 55001 ssh2"
)
_FAIL_ROOT = (
    "Jun 29 10:02:00 webserver sshd[12350]: Failed password for root"
    " from 203.0.113.7 port 22234 ssh2"
)
_ACCEPTED_PK = (
    "Jun 29 10:01:15 webserver sshd[12346]: Accepted publickey for arthur"
    " from 10.0.0.5 port 43201 ssh2"
)
_ACCEPTED_PW = (
    "Jun 29 10:03:00 webserver sshd[12360]: Accepted password for alice"
    " from 10.0.0.6 port 43202 ssh2"
)
_FAIL_DIGIT = (
    "Jun  1 09:00:00 webserver sshd[9999]: Failed password for invalid user test"
    " from 1.2.3.4 port 1000 ssh2"
)


def test_failed_password_invalid_user():
    event = parse_ssh_line(_FAIL_INVALID)
    assert event is not None
    assert event.source_ip == "192.168.1.45"
    assert event.user == "admin"
    assert event.action == "ssh_failed_auth"
    assert event.source_type == "ssh"
    assert _FAIL_INVALID == event.raw_log
    assert "T" in event.timestamp  # ISO-8601 contains T


def test_failed_password_root_no_invalid_user_prefix():
    event = parse_ssh_line(_FAIL_ROOT)
    assert event is not None
    assert event.user == "root"
    assert event.source_ip == "203.0.113.7"
    assert event.action == "ssh_failed_auth"


def test_accepted_publickey():
    event = parse_ssh_line(_ACCEPTED_PK)
    assert event is not None
    assert event.user == "arthur"
    assert event.source_ip == "10.0.0.5"
    assert event.action == "ssh_accepted_auth"
    assert event.source_type == "ssh"


def test_accepted_password():
    event = parse_ssh_line(_ACCEPTED_PW)
    assert event is not None
    assert event.action == "ssh_accepted_auth"
    assert event.user == "alice"


def test_single_digit_day():
    event = parse_ssh_line(_FAIL_DIGIT)
    assert event is not None
    assert event.user == "test"
    assert event.source_ip == "1.2.3.4"


def test_malformed_returns_none():
    assert parse_ssh_line("not a valid ssh log line") is None


def test_non_sshd_process_returns_none():
    line = "Jun 29 10:00:00 webserver kernel: some kernel message here"
    assert parse_ssh_line(line) is None


def test_empty_string_returns_none():
    assert parse_ssh_line("") is None
