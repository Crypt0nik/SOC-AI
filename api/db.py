"""SQLite query helpers for the SOC-AI API layer."""

import logging
import os
import sqlite3
from datetime import UTC, datetime, timedelta

logger = logging.getLogger(__name__)

_STATS_WINDOW_HOURS = 24


def get_connection() -> sqlite3.Connection:
    """Open an SQLite connection using the ``DB_PATH`` environment variable.

    Returns:
        A connection with ``row_factory = sqlite3.Row`` and FK enforcement enabled.
    """
    db_path = os.environ.get("DB_PATH", "/data/soc.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def fetch_alerts(
    conn: sqlite3.Connection,
    severity: str | None,
    page: int,
    page_size: int,
) -> tuple[list[dict], int]:
    """Query paginated alerts joined with optional triage data.

    Args:
        conn: Open SQLite connection.
        severity: Optional severity filter (applied on ``alerts.severity``).
        page: 1-based page number.
        page_size: Number of items per page.

    Returns:
        Tuple of ``(rows_as_dicts, total_count)``.
    """
    where = "WHERE COALESCE(t.severity, a.severity) = ?" if severity else ""
    base: list = [severity] if severity else []
    join = "LEFT JOIN triage t ON t.alert_id = a.id"

    try:
        total: int = conn.execute(
            f"SELECT COUNT(*) FROM alerts a {join} {where}", base
        ).fetchone()[0]

        rows = conn.execute(
            "SELECT a.id, a.rule_id, a.rule_name, a.severity, a.source_ip, "
            "a.matched_count, a.timestamp, a.status, a.created_at, "
            "t.severity AS triage_severity, t.attack_type, t.mitre_id, "
            "t.confidence, t.false_positive_risk, t.backend "
            f"FROM alerts a {join} "
            f"{where} "
            "ORDER BY a.timestamp DESC "
            "LIMIT ? OFFSET ?",
            base + [page_size, (page - 1) * page_size],
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("fetch_alerts failed: %s", exc)
        return [], 0

    return [dict(r) for r in rows], total


def fetch_alert_by_id(conn: sqlite3.Connection, alert_id: int) -> dict | None:
    """Fetch a single alert with its raw log and full triage data.

    Args:
        conn: Open SQLite connection.
        alert_id: Primary key to look up.

    Returns:
        Row dict, or ``None`` if not found.
    """
    try:
        row = conn.execute(
            "SELECT a.id, a.rule_id, a.rule_name, a.severity, a.source_ip, "
            "a.matched_count, a.timestamp, a.status, a.created_at, "
            "e.raw_log, "
            "t.severity AS triage_severity, t.attack_type, t.mitre_id, "
            "t.confidence, t.summary, t.recommendation, t.false_positive_risk, "
            "t.backend, t.raw_llm_json "
            "FROM alerts a "
            "JOIN events e ON e.id = a.event_id "
            "LEFT JOIN triage t ON t.alert_id = a.id "
            "WHERE a.id = ?",
            (alert_id,),
        ).fetchone()
    except sqlite3.Error as exc:
        logger.error("fetch_alert_by_id(%d) failed: %s", alert_id, exc)
        return None
    return dict(row) if row else None


def fetch_stats(
    conn: sqlite3.Connection, window_hours: int = _STATS_WINDOW_HOURS
) -> dict[str, int]:
    """Count alerts per effective severity within the last *window_hours*.

    Effective severity is ``triage.severity`` when available, falling back to
    ``alerts.severity`` for untriaged alerts.

    Args:
        conn: Open SQLite connection.
        window_hours: Look-back window in hours (default 24).

    Returns:
        Dict mapping severity label → count.
    """
    cutoff = (
        datetime.now(UTC) - timedelta(hours=window_hours)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        rows = conn.execute(
            "SELECT COALESCE(t.severity, a.severity) AS eff_sev, COUNT(*) AS cnt "
            "FROM alerts a "
            "LEFT JOIN triage t ON t.alert_id = a.id "
            "WHERE a.created_at >= ? "
            "GROUP BY eff_sev",
            (cutoff,),
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("fetch_stats failed: %s", exc)
        return {}
    return {row["eff_sev"]: row["cnt"] for row in rows}


def fetch_all_alerts_for_export(
    conn: sqlite3.Connection, severity: str | None
) -> list[dict]:
    """Fetch all alerts (no pagination) for the export endpoint.

    Args:
        conn: Open SQLite connection.
        severity: Optional severity filter.

    Returns:
        List of row dicts ordered by timestamp descending.
    """
    where = "WHERE COALESCE(t.severity, a.severity) = ?" if severity else ""
    base: list = [severity] if severity else []
    try:
        rows = conn.execute(
            "SELECT a.id, a.rule_id, a.rule_name, a.severity, a.source_ip, "
            "a.matched_count, a.timestamp, a.status, a.created_at, "
            "t.severity AS triage_severity, t.attack_type, t.mitre_id, "
            "t.confidence, t.summary, t.recommendation, t.false_positive_risk, "
            "t.backend "
            "FROM alerts a "
            "LEFT JOIN triage t ON t.alert_id = a.id "
            f"{where} "
            "ORDER BY a.timestamp DESC",
            base,
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("fetch_all_alerts_for_export failed: %s", exc)
        return []
    return [dict(r) for r in rows]
