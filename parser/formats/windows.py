"""Parser for Windows Event Log XML blocks (Security / System events)."""

import logging
import xml.etree.ElementTree as ET
from datetime import UTC, datetime

from parser.models import Event

logger = logging.getLogger(__name__)

_NS = "http://schemas.microsoft.com/win/2004/08/events/event"
_NS_MAP = {"e": _NS}

# Map EventID → action label
_EVENT_ID_ACTIONS: dict[str, str] = {
    "4624": "logon_success",
    "4625": "logon_failure",
    "4657": "registry_value_modified",  # WIN-003: SAM registry access
    "4672": "privilege_assigned",       # WIN-001: privilege escalation
    "4720": "user_account_created",     # WIN-002: new account
    "4726": "user_account_deleted",
    "4732": "group_member_added",
}


def _normalize_ts(ts_raw: str) -> str:
    """Convert a Windows Event ``SystemTime`` value to ISO-8601 UTC.

    Args:
        ts_raw: SystemTime attribute, e.g. ``"2026-06-29T10:10:00.000Z"``.

    Returns:
        ISO-8601 UTC string with milliseconds stripped.
    """
    if not ts_raw:
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")
    # Handle both "2026-06-29T10:10:00Z" and "2026-06-29T10:10:00.000Z"
    ts_clean = ts_raw.rstrip("Z").split(".")[0] + "Z"
    try:
        dt = datetime.strptime(ts_clean, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC)
        return dt.isoformat().replace("+00:00", "Z")
    except ValueError:
        logger.warning("Could not parse Windows timestamp: %r", ts_raw)
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def parse_windows_xml(block: str) -> Event | None:
    """Parse a complete Windows Event XML block into a normalised Event.

    Args:
        block: A single ``<Event>…</Event>`` XML string.

    Returns:
        A normalised :class:`~parser.models.Event`, or ``None`` on parse failure.
    """
    if not block or not block.strip():
        return None

    try:
        root = ET.fromstring(block)
    except ET.ParseError as exc:
        logger.warning("Windows XML parse error: %s", exc)
        return None

    event_id_el = root.find("e:System/e:EventID", _NS_MAP)
    event_id = event_id_el.text.strip() if event_id_el is not None and event_id_el.text else ""

    time_el = root.find("e:System/e:TimeCreated", _NS_MAP)
    ts_raw = time_el.get("SystemTime", "") if time_el is not None else ""

    # Collect EventData fields by Name attribute
    data: dict[str, str] = {}
    for d in root.findall("e:EventData/e:Data", _NS_MAP):
        name = d.get("Name", "")
        data[name] = d.text or ""

    # For account-creation events, prefer TargetUserName (the created account)
    if event_id == "4720":
        user = data.get("TargetUserName") or data.get("SubjectUserName") or None
    else:
        user = data.get("SubjectUserName") or data.get("TargetUserName") or None

    action = _EVENT_ID_ACTIONS.get(event_id, f"windows_event_{event_id}")

    return Event(
        timestamp=_normalize_ts(ts_raw),
        source_ip=None,  # Windows Security events carry no source IP in this context
        user=user if user else None,
        action=action,
        raw_log=block,
        source_type="windows",
    )
