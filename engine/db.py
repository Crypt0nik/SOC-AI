"""Database helpers for the SOC-AI Sigma engine."""

import logging
import sqlite3

from engine.models import Alert
from parser.models import Event

logger = logging.getLogger(__name__)


def fetch_new_events(conn: sqlite3.Connection) -> list[Event]:
    """Fetch all events with status ``new``, ordered by creation time.

    Args:
        conn: Open SQLite connection.

    Returns:
        List of :class:`~parser.models.Event` objects with ``id`` set.
    """
    try:
        rows = conn.execute(
            "SELECT * FROM events WHERE status='new' ORDER BY created_at ASC"
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("Failed to fetch new events: %s", exc)
        return []
    return [_row_to_event(row) for row in rows]


def mark_event_processed(conn: sqlite3.Connection, event_id: int) -> None:
    """Mark an event as processed so the engine does not re-evaluate it.

    Args:
        conn: Open SQLite connection.
        event_id: Primary key of the event row.
    """
    try:
        conn.execute("UPDATE events SET status='processed' WHERE id=?", (event_id,))
        conn.commit()
    except sqlite3.Error as exc:
        logger.error("Failed to mark event %d as processed: %s", event_id, exc)


def insert_alert(conn: sqlite3.Connection, alert: Alert) -> int:
    """Persist an alert to the ``alerts`` table.

    Args:
        conn: Open SQLite connection.
        alert: The alert to insert.

    Returns:
        The ``id`` of the newly inserted alert row.
    """
    try:
        cur = conn.execute(
            "INSERT INTO alerts "
            "(event_id, rule_id, rule_name, severity, source_ip, matched_count, timestamp) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (alert.event_id, alert.rule_id, alert.rule_name, alert.severity,
             alert.source_ip, alert.matched_count, alert.timestamp),
        )
        conn.commit()
        logger.debug(
            "Alert inserted id=%d rule=%s ip=%s", cur.lastrowid, alert.rule_id, alert.source_ip
        )
        return cur.lastrowid
    except sqlite3.Error as exc:
        logger.error("Failed to insert alert for rule %s: %s", alert.rule_id, exc)
        return -1


def _row_to_event(row: sqlite3.Row) -> Event:
    """Convert a SQLite row from the ``events`` table to an Event.

    Args:
        row: A ``sqlite3.Row`` from the ``events`` table.

    Returns:
        An :class:`~parser.models.Event` with ``id`` set.
    """
    return Event(
        id=row["id"],
        timestamp=row["timestamp"],
        source_ip=row["source_ip"],
        user=row["user"],
        action=row["action"],
        raw_log=row["raw_log"],
        source_type=row["source_type"],
    )
