"""Parser for SSH auth.log lines (OpenSSH syslog format)."""

import logging
import re
from datetime import UTC, datetime

from parser.models import Event

logger = logging.getLogger(__name__)

# Matches both "Failed password for invalid user X" and "Failed password for X"
_FAILED_RE = re.compile(
    r"(?P<ts>\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+\S+\s+sshd\[\d+\]:\s+"
    r"Failed\s+password\s+for\s+(?:invalid\s+user\s+)?(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+\d+"
)

_ACCEPTED_RE = re.compile(
    r"(?P<ts>\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})\s+\S+\s+sshd\[\d+\]:\s+"
    r"Accepted\s+\S+\s+for\s+(?P<user>\S+)\s+from\s+(?P<ip>\S+)\s+port\s+\d+"
)


def _parse_syslog_ts(ts_raw: str) -> str:
    """Convert a syslog timestamp (no year) to an ISO-8601 UTC string.

    Args:
        ts_raw: Raw syslog timestamp, e.g. ``"Jun 29 10:01:01"`` or ``"Jun  1 09:00:00"``.

    Returns:
        ISO-8601 UTC string, e.g. ``"2026-06-29T10:01:01Z"``.
    """
    year = datetime.now(UTC).year
    # Normalise whitespace: "Jun  1 ..." → "Jun 1 ..."
    normalised = " ".join(ts_raw.split())
    try:
        dt = datetime.strptime(f"{year} {normalised}", "%Y %b %d %H:%M:%S")
        return dt.replace(tzinfo=UTC).isoformat().replace("+00:00", "Z")
    except ValueError:
        logger.warning("Could not parse syslog timestamp: %r", ts_raw)
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def parse_ssh_line(line: str) -> Event | None:
    """Parse a single SSH auth.log line into a normalised Event.

    Handles:
    - ``Failed password for [invalid user] <user> from <ip>``
    - ``Accepted (publickey|password) for <user> from <ip>``

    Args:
        line: Raw auth.log line.

    Returns:
        A normalised :class:`~parser.models.Event`, or ``None`` if the line
        does not match any known SSH pattern.
    """
    if not line:
        return None

    m = _FAILED_RE.search(line)
    if m:
        return Event(
            timestamp=_parse_syslog_ts(m.group("ts")),
            source_ip=m.group("ip"),
            user=m.group("user"),
            action="ssh_failed_auth",
            raw_log=line,
            source_type="ssh",
        )

    m = _ACCEPTED_RE.search(line)
    if m:
        return Event(
            timestamp=_parse_syslog_ts(m.group("ts")),
            source_ip=m.group("ip"),
            user=m.group("user"),
            action="ssh_accepted_auth",
            raw_log=line,
            source_type="ssh",
        )

    return None
