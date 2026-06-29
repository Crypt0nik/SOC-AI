"""Unit tests for the parser DB helper (insert_event)."""


from parser.db import insert_event
from parser.models import Event


def _make_event(**kwargs) -> Event:
    defaults = {
        "timestamp": "2026-06-29T10:00:00Z",
        "source_ip": "192.168.1.1",
        "user": "testuser",
        "action": "ssh_failed_auth",
        "raw_log": (
            "Jun 29 10:00:00 host sshd[1]: Failed password for testuser"
            " from 192.168.1.1 port 22 ssh2"
        ),
        "source_type": "ssh",
    }
    defaults.update(kwargs)
    return Event(**defaults)


def test_insert_event_returns_id(tmp_db):
    _, conn = tmp_db
    event_id = insert_event(conn, _make_event())
    assert isinstance(event_id, int)
    assert event_id > 0


def test_inserted_event_is_readable(tmp_db):
    _, conn = tmp_db
    evt = _make_event(source_ip="10.0.0.1", user="alice", action="ssh_accepted_auth")
    event_id = insert_event(conn, evt)

    row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    assert row is not None
    assert row["source_ip"] == "10.0.0.1"
    assert row["user"] == "alice"
    assert row["action"] == "ssh_accepted_auth"
    assert row["source_type"] == "ssh"
    assert row["status"] == "new"


def test_insert_event_null_ip_and_user(tmp_db):
    _, conn = tmp_db
    evt = _make_event(source_ip=None, user=None, source_type="windows", action="privilege_assigned")
    event_id = insert_event(conn, evt)
    row = conn.execute("SELECT source_ip, user FROM events WHERE id = ?", (event_id,)).fetchone()
    assert row["source_ip"] is None
    assert row["user"] is None


def test_multiple_inserts_increment_id(tmp_db):
    _, conn = tmp_db
    id1 = insert_event(conn, _make_event())
    id2 = insert_event(conn, _make_event())
    assert id2 > id1
