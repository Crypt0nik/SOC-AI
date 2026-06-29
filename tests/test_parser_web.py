"""Unit tests for the Apache/Nginx access log parser."""

from parser.formats.web import parse_web_line

_SQLI = (
    '192.168.1.100 - - [29/Jun/2026:10:05:01 +0000]'
    ' "GET /index.php?id=1\' OR \'1\'=\'1 HTTP/1.1" 200 512 "-" "Mozilla/5.0"'
)
_TRAVERSAL = (
    '192.168.1.100 - - [29/Jun/2026:10:05:05 +0000]'
    ' "GET /admin/../../../etc/passwd HTTP/1.1" 403 210 "-" "Mozilla/5.0"'
)
_SCANNER = (
    '198.51.100.22 - - [29/Jun/2026:10:05:10 +0000]'
    ' "GET /robots.txt HTTP/1.1" 200 64 "-" "sqlmap/1.7.12"'
)
_AUTHED = (
    '10.0.0.1 - jdoe [29/Jun/2026:11:00:00 +0000]'
    ' "GET /dashboard HTTP/1.1" 200 4096 "-" "Firefox/126.0"'
)


def test_sql_injection_in_url():
    event = parse_web_line(_SQLI)
    assert event is not None
    assert event.source_ip == "192.168.1.100"
    assert event.action == "http_request"
    assert event.source_type == "web"
    assert event.raw_log == _SQLI
    assert "T" in event.timestamp


def test_path_traversal():
    event = parse_web_line(_TRAVERSAL)
    assert event is not None
    assert event.source_ip == "192.168.1.100"
    assert event.action == "http_request"


def test_scanner_user_agent():
    event = parse_web_line(_SCANNER)
    assert event is not None
    assert event.source_ip == "198.51.100.22"
    assert event.user is None  # unauthenticated → "-" mapped to None


def test_authenticated_user():
    event = parse_web_line(_AUTHED)
    assert event is not None
    assert event.source_ip == "10.0.0.1"
    assert event.user == "jdoe"


def test_malformed_returns_none():
    assert parse_web_line("not an apache log line") is None


def test_empty_returns_none():
    assert parse_web_line("") is None
