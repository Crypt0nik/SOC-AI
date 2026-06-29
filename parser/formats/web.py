"""Parser for Apache / Nginx access log lines (Combined Log Format)."""

import logging
import re
from datetime import UTC, datetime

from parser.models import Event

logger = logging.getLogger(__name__)

# Combined Log Format:
#   <ip> - <user> [<date>] "<method> <path> <proto>" <status> <size> "<ref>" "<ua>"
# <user> is "-" for unauthenticated requests.
_COMBINED_RE = re.compile(
    r'^(?P<ip>\S+)\s+-\s+(?P<user>\S+)\s+\[(?P<ts>[^\]]+)\]\s+'
    r'"(?P<request>[^"]*?)"\s+(?P<status>\d{3})\s+(?P<size>\S+)'
)


def _parse_apache_ts(ts_raw: str) -> str:
    """Convert an Apache Combined Log timestamp to ISO-8601 UTC.

    Args:
        ts_raw: Timestamp string, e.g. ``"29/Jun/2026:10:05:01 +0000"``.

    Returns:
        ISO-8601 UTC string, e.g. ``"2026-06-29T10:05:01Z"``.
    """
    try:
        dt = datetime.strptime(ts_raw, "%d/%b/%Y:%H:%M:%S %z")
        return dt.astimezone(UTC).isoformat().replace("+00:00", "Z")
    except ValueError:
        logger.warning("Could not parse Apache timestamp: %r", ts_raw)
        return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def parse_web_line(line: str) -> Event | None:
    """Parse a single Apache/Nginx Combined Log Format line into an Event.

    Args:
        line: Raw access log line.

    Returns:
        A normalised :class:`~parser.models.Event`, or ``None`` if the line
        does not match the Combined Log Format.
    """
    if not line:
        return None

    m = _COMBINED_RE.match(line.strip())
    if not m:
        return None

    user_field = m.group("user")
    user = None if user_field == "-" else user_field

    return Event(
        timestamp=_parse_apache_ts(m.group("ts")),
        source_ip=m.group("ip"),
        user=user,
        action="http_request",
        raw_log=line,
        source_type="web",
    )
