"""Data models for the SOC-AI Sigma engine."""

from dataclasses import dataclass, field


@dataclass
class Rule:
    """A loaded and parsed Sigma rule ready for evaluation.

    Attributes:
        id: SOC-AI friendly identifier (e.g. ``SSH-001``).
        name: Human-readable rule title.
        severity: Alert severity string — CRITICAL | HIGH | MEDIUM | LOW | INFO.
        source_types: Event ``source_type`` values this rule applies to.
        detection: Raw Sigma detection block (dict of named groups + condition).
        aggregation: Optional time-window aggregation config from ``soc_ai`` block.
    """

    id: str
    name: str
    severity: str
    source_types: list[str]
    detection: dict
    aggregation: dict | None = field(default=None)


@dataclass
class Alert:
    """An alert raised by the Sigma engine for a matching event.

    Attributes:
        event_id: Foreign key to the triggering ``events`` row.
        rule_id: SOC-AI rule identifier (e.g. ``SSH-001``).
        rule_name: Human-readable rule name.
        severity: Alert severity — CRITICAL | HIGH | MEDIUM | LOW | INFO.
        source_ip: Source IP from the triggering event (may be None).
        matched_count: 1 for field-match rules; N for aggregation rules.
        timestamp: ISO-8601 UTC timestamp of the triggering event.
    """

    event_id: int
    rule_id: str
    rule_name: str
    severity: str
    source_ip: str | None
    matched_count: int
    timestamp: str
