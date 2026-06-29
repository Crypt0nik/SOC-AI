"""Format detection and dispatch for the SOC-AI parser."""

import logging
from pathlib import Path

from parser.formats.generic_json import parse_json_line
from parser.formats.ssh import parse_ssh_line
from parser.formats.web import parse_web_line
from parser.models import Event

logger = logging.getLogger(__name__)

# Filename substring → source_type mappings (checked in order)
_FILENAME_RULES: list[tuple[str, str]] = [
    ("auth", "ssh"),
    ("secure", "ssh"),        # RHEL/CentOS equivalent of auth.log
    ("access", "web"),
    ("nginx", "web"),
    ("apache", "web"),
    ("httpd", "web"),
    ("error.log", "web"),     # nginx/apache error logs also follow CLF-like format
]


def detect_source_type(filepath: str) -> str:
    """Infer the log source type from the file name.

    Args:
        filepath: Absolute or relative path to the log file.

    Returns:
        One of ``"ssh"``, ``"web"``, ``"windows"``, ``"json"``.
        Defaults to ``"json"`` when no rule matches.
    """
    name = Path(filepath).name.lower()

    if name.endswith(".xml"):
        return "windows"
    if name.endswith(".json") or name.endswith(".jsonl") or name.endswith(".ndjson"):
        return "json"

    for substring, source_type in _FILENAME_RULES:
        if substring in name:
            return source_type

    return "json"  # safe default for unrecognised files


def parse_line(line: str, source_type: str) -> Event | None:
    """Dispatch a log line to the appropriate format parser.

    Note: ``"windows"`` source type is handled at the observer level (buffered
    XML blocks), so this function does not route to the Windows parser.

    Args:
        line: Raw log line (stripped).
        source_type: One of ``"ssh"``, ``"web"``, ``"json"``.

    Returns:
        A normalised :class:`~parser.models.Event`, or ``None`` if the line
        does not match the expected format.
    """
    if source_type == "ssh":
        return parse_ssh_line(line)
    if source_type == "web":
        return parse_web_line(line)
    if source_type == "json":
        return parse_json_line(line)
    logger.warning("No parser for source_type=%r — skipping line", source_type)
    return None
