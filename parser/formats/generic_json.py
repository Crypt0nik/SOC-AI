"""Parser for generic JSON log lines (one JSON object per line)."""

import json
import logging
from datetime import UTC, datetime

from parser.models import Event

logger = logging.getLogger(__name__)


def parse_json_line(line: str) -> Event | None:
    """Parse a single JSON log line into a normalised Event.

    Expected keys (all optional except at least one must make the result useful):
    - ``timestamp``: ISO-8601 string; defaults to current UTC time.
    - ``source_ip``: string; defaults to ``None``.
    - ``user``: string; defaults to ``None``.
    - ``action``: string; defaults to ``"json_event"``.
    - ``raw_log``: string; defaults to the raw JSON serialisation.

    Args:
        line: A single-line JSON string representing one log entry.

    Returns:
        A normalised :class:`~parser.models.Event`, or ``None`` if the line
        is empty, not valid JSON, or not a JSON object.
    """
    if not line or not line.strip():
        return None

    try:
        obj = json.loads(line)
    except json.JSONDecodeError as exc:
        logger.warning("JSON parse error: %s — line: %.80r", exc, line)
        return None

    if not isinstance(obj, dict):
        logger.warning("JSON log line is not an object: %.80r", line)
        return None

    timestamp = obj.get("timestamp") or datetime.now(UTC).isoformat().replace("+00:00", "Z")
    source_ip = obj.get("source_ip") or None
    user = obj.get("user") or None
    action = obj.get("action") or "json_event"
    raw_log = obj.get("raw_log") or line

    return Event(
        timestamp=str(timestamp),
        source_ip=str(source_ip) if source_ip else None,
        user=str(user) if user else None,
        action=str(action),
        raw_log=str(raw_log),
        source_type="json",
    )
