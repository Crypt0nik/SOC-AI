"""Reversible PII tokeniser for SOC-AI.

Replaces IP addresses, e-mail addresses, and known usernames with stable
tokens (``IP_1``, ``EMAIL_1``, ``USER_1``, …) before the text is sent to a
cloud LLM.  The original values are stored in the ``pii_mapping`` table so
that the dashboard can reconstruct the clear-text view.
"""

import logging
import re
import sqlite3
from datetime import UTC, datetime

logger = logging.getLogger(__name__)

_IP_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
_EMAIL_RE = re.compile(r"\b[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}\b")


def anonymize(
    text: str,
    conn: sqlite3.Connection,
    alert_id: int,
    known_ips: list[str] | None = None,
    known_users: list[str] | None = None,
) -> tuple[str, dict[str, str]]:
    """Tokenise PII in *text* and persist the mapping to the database.

    Processing order: emails first (most specific), then IPs, then usernames.
    Longest values are replaced first to avoid partial-match collisions.
    The same original value always receives the same token within one alert.

    Args:
        text: The raw text to anonymise.
        conn: Open SQLite connection.
        alert_id: FK to the ``alerts`` table row this mapping belongs to.
        known_ips: Explicit IP values to tokenise (e.g. from ``alerts.source_ip``).
        known_users: Explicit username values to tokenise (e.g. from ``alerts.user``).

    Returns:
        Tuple of ``(anonymised_text, token_to_original_dict)``.
    """
    val_to_info: dict[str, tuple[str, str]] = {}  # original -> (token, kind)
    counters: dict[str, int] = {"ip": 0, "email": 0, "user": 0}

    def _token(original: str, kind: str) -> str:
        if original in val_to_info:
            return val_to_info[original][0]
        counters[kind] += 1
        tok = f"{kind.upper()}_{counters[kind]}"
        val_to_info[original] = (tok, kind)
        return tok

    result = text

    # 1. Emails (most specific — run before IP to avoid false IP matches in domains)
    emails = sorted(set(_EMAIL_RE.findall(result)), key=len, reverse=True)
    for email in emails:
        tok = _token(email, "email")
        result = result.replace(email, tok)

    # 2. IPs (from regex + explicit context)
    ip_candidates: set[str] = set(_IP_RE.findall(result))
    if known_ips:
        ip_candidates.update(ip for ip in known_ips if ip)
    for ip in sorted(ip_candidates, key=len, reverse=True):
        tok = _token(ip, "ip")
        result = result.replace(ip, tok)

    # 3. Known usernames (not regex-detectable without prior knowledge)
    if known_users:
        for user in sorted((u for u in known_users if u), key=len, reverse=True):
            tok = _token(user, "user")
            result = result.replace(user, tok)

    # Persist mapping
    if val_to_info:
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        try:
            conn.executemany(
                "INSERT OR IGNORE INTO pii_mapping "
                "(token, original, kind, alert_id, created_at) VALUES (?, ?, ?, ?, ?)",
                [(tok, orig, kind, alert_id, now) for orig, (tok, kind) in val_to_info.items()],
            )
            conn.commit()
        except sqlite3.Error as exc:
            logger.error("Failed to persist pii_mapping for alert %d: %s", alert_id, exc)

    return result, {tok: orig for orig, (tok, _) in val_to_info.items()}


def deanonymize(text: str, conn: sqlite3.Connection, alert_id: int) -> str:
    """Replace tokens in *text* with their original values from ``pii_mapping``.

    Args:
        text: Tokenised text (e.g. a triage summary).
        conn: Open SQLite connection.
        alert_id: The alert whose mapping to use.

    Returns:
        Text with all known tokens substituted back to original values.
    """
    try:
        rows = conn.execute(
            "SELECT token, original FROM pii_mapping WHERE alert_id=?", (alert_id,)
        ).fetchall()
    except sqlite3.Error as exc:
        logger.error("Failed to read pii_mapping for alert %d: %s", alert_id, exc)
        return text
    for row in rows:
        text = text.replace(row["token"] if hasattr(row, "__getitem__") else row[0],
                            row["original"] if hasattr(row, "__getitem__") else row[1])
    return text
