"""SQLite helpers for the notifications module."""

import logging
import os
import sqlite3

logger = logging.getLogger(__name__)

_SEV_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}


def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection to the shared SOC-AI database.

    Returns:
        Connection with row_factory and WAL mode enabled.
    """
    db_path = os.environ.get("DB_PATH", "/data/soc.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_notifications_table(conn: sqlite3.Connection) -> None:
    """Create the notifications table if it does not exist.

    Args:
        conn: Open SQLite connection.
    """
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id  INTEGER UNIQUE NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
                channel   TEXT    NOT NULL,
                sent_at   TEXT    NOT NULL,
                status    TEXT    NOT NULL
            )
            """
        )
        conn.commit()
    except sqlite3.Error as exc:
        logger.error("init_notifications_table failed: %s", exc)


def fetch_alerts_to_notify(
    conn: sqlite3.Connection,
    min_severity: str,
    since_id: int,
) -> list[dict]:
    """Return triaged alerts not yet notified whose severity meets the threshold.

    Args:
        conn: Open SQLite connection.
        min_severity: Minimum severity to notify on (e.g. ``"HIGH"``).
        since_id: Only consider alerts with id > since_id.

    Returns:
        List of row dicts with alert + triage fields.
    """
    min_rank = _SEV_ORDER.get(min_severity, 3)
    try:
        rows = conn.execute(
            "SELECT a.id, a.rule_id, a.rule_name, a.severity, a.source_ip, "
            "a.matched_count, a.timestamp, "
            "t.severity AS triage_severity, t.attack_type, t.mitre_id, "
            "t.confidence, t.summary, t.false_positive_risk "
            "FROM alerts a "
            "JOIN triage t ON t.alert_id = a.id "
            "LEFT JOIN notifications n ON n.alert_id = a.id "
            "WHERE a.id > ? AND n.id IS NULL "
            "ORDER BY a.id ASC",
            (since_id,),
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("fetch_alerts_to_notify failed: %s", exc)
        return []

    result = []
    for r in rows:
        eff_sev = r["triage_severity"] or r["severity"]
        if _SEV_ORDER.get(eff_sev, 0) >= min_rank:
            result.append(dict(r))
    return result


def mark_notified(
    conn: sqlite3.Connection,
    alert_id: int,
    channel: str,
    status: str,
    sent_at: str,
) -> None:
    """Record that a notification was sent (or failed) for an alert.

    Args:
        conn: Open SQLite connection.
        alert_id: The alert that was notified.
        channel: Channel used (``"slack"`` or ``"teams"``).
        status: ``"sent"`` or ``"error"``.
        sent_at: ISO-8601 timestamp of the attempt.
    """
    try:
        conn.execute(
            "INSERT OR REPLACE INTO notifications (alert_id, channel, sent_at, status) "
            "VALUES (?, ?, ?, ?)",
            (alert_id, channel, sent_at, status),
        )
        conn.commit()
    except sqlite3.Error as exc:
        logger.error("mark_notified(%d) failed: %s", alert_id, exc)
