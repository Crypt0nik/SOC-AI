"""Shared data models for the SOC-AI parser module."""

from dataclasses import dataclass


@dataclass
class Event:
    """Normalised representation of a single log line.

    Attributes:
        timestamp: ISO-8601 UTC timestamp of the event.
        source_ip: Source IP address, or None if unavailable.
        user: Username involved, or None if unavailable.
        action: Human-readable action label (e.g. ``ssh_failed_auth``).
        raw_log: Original log line verbatim.
        source_type: Format tag — one of ``ssh``, ``web``, ``windows``, ``json``.
    """

    timestamp: str
    source_ip: str | None
    user: str | None
    action: str
    raw_log: str
    source_type: str
    id: int | None = None  # set after DB insertion; required for engine evaluation
