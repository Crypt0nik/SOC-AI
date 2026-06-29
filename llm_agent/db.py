"""Database helpers for the SOC-AI LLM triage agent."""

import logging
import sqlite3

from llm_agent.schema import TriageResult

logger = logging.getLogger(__name__)


def fetch_untriaged_alerts(conn: sqlite3.Connection, limit: int = 50) -> list[sqlite3.Row]:
    """Fetch untriaged alerts joined with their source event's raw log.

    Args:
        conn: Open SQLite connection.
        limit: Maximum number of alerts to return per call.

    Returns:
        List of rows with all ``alerts`` columns plus ``event_raw_log``.
    """
    try:
        return conn.execute(
            "SELECT a.*, e.raw_log AS event_raw_log "
            "FROM alerts a "
            "JOIN events e ON a.event_id = e.id "
            "WHERE a.status = 'untriaged' "
            "ORDER BY a.created_at ASC "
            "LIMIT ?",
            (limit,),
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("Failed to fetch untriaged alerts: %s", exc)
        return []


def mark_alert_status(conn: sqlite3.Connection, alert_id: int, status: str) -> None:
    """Update an alert's status column.

    Args:
        conn: Open SQLite connection.
        alert_id: Primary key of the alert.
        status: New status string (``triaged`` or ``error``).
    """
    try:
        conn.execute("UPDATE alerts SET status=? WHERE id=?", (status, alert_id))
        conn.commit()
    except sqlite3.Error as exc:
        logger.error("Failed to update alert %d status to %s: %s", alert_id, status, exc)


def insert_triage(
    conn: sqlite3.Connection,
    alert_id: int,
    result: TriageResult,
    backend: str,
    raw_llm_json: str,
) -> int:
    """Insert a validated triage result into the ``triage`` table.

    Args:
        conn: Open SQLite connection.
        alert_id: FK to ``alerts.id``.
        result: Validated :class:`~llm_agent.schema.TriageResult`.
        backend: Name of the LLM backend used (e.g. ``"claude"`` or ``"ollama"``).
        raw_llm_json: The raw JSON string returned by the LLM (stored for audit).

    Returns:
        The ``id`` of the newly inserted triage row, or ``-1`` on error.
    """
    try:
        cur = conn.execute(
            "INSERT INTO triage "
            "(alert_id, severity, attack_type, mitre_id, confidence, summary, "
            "recommendation, false_positive_risk, backend, raw_llm_json) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                alert_id,
                result.severity,
                result.attack_type,
                result.mitre_id,
                result.confidence,
                result.summary,
                result.recommendation,
                result.false_positive_risk,
                backend,
                raw_llm_json,
            ),
        )
        conn.commit()
        logger.debug(
            "Triage inserted id=%d alert_id=%d severity=%s",
            cur.lastrowid, alert_id, result.severity,
        )
        return cur.lastrowid
    except sqlite3.Error as exc:
        logger.error("Failed to insert triage for alert %d: %s", alert_id, exc)
        return -1
