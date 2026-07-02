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


def delete_alert(conn: sqlite3.Connection, alert_id: int) -> bool:
    """Delete a single alert and its triage record.

    Args:
        conn: Open SQLite connection.
        alert_id: Primary key to delete.

    Returns:
        True if an alert was deleted, False if not found.
    """
    try:
        conn.execute("DELETE FROM triage WHERE alert_id = ?", (alert_id,))
        cur = conn.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
        conn.commit()
        return cur.rowcount > 0
    except sqlite3.Error as exc:
        logger.error("delete_alert(%d) failed: %s", alert_id, exc)
        return False


def delete_all_alerts(conn: sqlite3.Connection) -> int:
    """Delete all alerts and triage records.

    Args:
        conn: Open SQLite connection.

    Returns:
        Number of alerts deleted.
    """
    try:
        conn.execute("DELETE FROM triage")
        cur = conn.execute("DELETE FROM alerts")
        conn.commit()
        return cur.rowcount
    except sqlite3.Error as exc:
        logger.error("delete_all_alerts failed: %s", exc)
        return 0


def fetch_compliance_stats(
    conn: sqlite3.Connection, window_days: int = 30
) -> dict:
    """Fetch aggregated metrics for compliance reporting.

    Args:
        conn: Open SQLite connection.
        window_days: Look-back window in days.

    Returns:
        Dict with total_alerts, by_severity, mean_triage_seconds,
        false_positive_count, top_attack_types, mitre_coverage,
        triaged_pct, error_pct.
    """
    cutoff = (
        datetime.now(UTC) - timedelta(days=window_days)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        total_row = conn.execute(
            "SELECT COUNT(*) FROM alerts WHERE created_at >= ?", (cutoff,)
        ).fetchone()
        total = total_row[0] if total_row else 0

        sev_rows = conn.execute(
            "SELECT COALESCE(t.severity, a.severity) AS eff_sev, COUNT(*) AS cnt "
            "FROM alerts a LEFT JOIN triage t ON t.alert_id = a.id "
            "WHERE a.created_at >= ? GROUP BY eff_sev",
            (cutoff,),
        ).fetchall()

        status_rows = conn.execute(
            "SELECT status, COUNT(*) AS cnt FROM alerts "
            "WHERE created_at >= ? GROUP BY status",
            (cutoff,),
        ).fetchall()
        status_map = {r["status"]: r["cnt"] for r in status_rows}

        mtta_row = conn.execute(
            "SELECT AVG((julianday(t.created_at) - julianday(a.created_at)) * 86400) "
            "FROM alerts a JOIN triage t ON t.alert_id = a.id "
            "WHERE a.created_at >= ?",
            (cutoff,),
        ).fetchone()

        fp_row = conn.execute(
            "SELECT COUNT(*) FROM triage t JOIN alerts a ON a.id = t.alert_id "
            "WHERE t.false_positive_risk = 'HIGH' AND a.created_at >= ?",
            (cutoff,),
        ).fetchone()

        attack_rows = conn.execute(
            "SELECT t.attack_type, COUNT(*) AS cnt "
            "FROM triage t JOIN alerts a ON a.id = t.alert_id "
            "WHERE t.attack_type IS NOT NULL AND a.created_at >= ? "
            "GROUP BY t.attack_type ORDER BY cnt DESC LIMIT 5",
            (cutoff,),
        ).fetchall()

        mitre_rows = conn.execute(
            "SELECT DISTINCT t.mitre_id FROM triage t "
            "JOIN alerts a ON a.id = t.alert_id "
            "WHERE t.mitre_id IS NOT NULL AND a.created_at >= ?",
            (cutoff,),
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("fetch_compliance_stats failed: %s", exc)
        return {}

    triaged = status_map.get("triaged", 0)
    errors = status_map.get("error", 0)
    return {
        "total_alerts": total,
        "window_days": window_days,
        "by_severity": {r["eff_sev"]: r["cnt"] for r in sev_rows},
        "mean_triage_seconds": round(mtta_row[0] or 0, 1),
        "false_positive_count": fp_row[0] if fp_row else 0,
        "top_attack_types": [
            {"type": r["attack_type"], "count": r["cnt"]} for r in attack_rows
        ],
        "mitre_coverage": [r["mitre_id"] for r in mitre_rows],
        "triaged_pct": round(triaged / total * 100, 1) if total else 0,
        "error_pct": round(errors / total * 100, 1) if total else 0,
    }


def fetch_ip_timeline(
    conn: sqlite3.Connection, source_ip: str, limit: int = 50
) -> list[dict]:
    """Fetch alert history for a specific source IP.

    Args:
        conn: Open SQLite connection.
        source_ip: IP address to look up.
        limit: Maximum rows to return.

    Returns:
        List of alert dicts ordered by timestamp descending.
    """
    try:
        rows = conn.execute(
            "SELECT a.id, a.rule_id, a.rule_name, a.severity, a.matched_count, "
            "a.timestamp, a.status, "
            "COALESCE(t.severity, a.severity) AS eff_severity, t.attack_type, t.mitre_id "
            "FROM alerts a LEFT JOIN triage t ON t.alert_id = a.id "
            "WHERE a.source_ip = ? "
            "ORDER BY a.timestamp DESC LIMIT ?",
            (source_ip, limit),
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("fetch_ip_timeline(%s) failed: %s", source_ip, exc)
        return []
    return [dict(r) for r in rows]


def fetch_note(conn: sqlite3.Connection, alert_id: int) -> str | None:
    """Fetch analyst note for an alert.

    Args:
        conn: Open SQLite connection.
        alert_id: Alert primary key.

    Returns:
        Note text or None if no note exists.
    """
    try:
        row = conn.execute(
            "SELECT note FROM alert_notes WHERE alert_id = ?", (alert_id,)
        ).fetchone()
    except sqlite3.Error as exc:
        logger.error("fetch_note(%d) failed: %s", alert_id, exc)
        return None
    return row["note"] if row else None


def upsert_note(conn: sqlite3.Connection, alert_id: int, note: str) -> bool:
    """Save or update an analyst note for an alert.

    Args:
        conn: Open SQLite connection.
        alert_id: Alert primary key.
        note: Note text to save.

    Returns:
        True on success, False on error.
    """
    try:
        conn.execute(
            "INSERT INTO alert_notes(alert_id, note) VALUES(?, ?) "
            "ON CONFLICT(alert_id) DO UPDATE SET note=excluded.note, "
            "created_at=strftime('%Y-%m-%dT%H:%M:%SZ','now')",
            (alert_id, note),
        )
        conn.commit()
        return True
    except sqlite3.Error as exc:
        logger.error("upsert_note(%d) failed: %s", alert_id, exc)
        return False


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
