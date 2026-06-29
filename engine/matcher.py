"""Sigma field matcher and rule evaluator for the SOC-AI engine.

Implements a subset of the Sigma detection language sufficient for all
10 built-in rules:
- Field modifiers: (none) exact, ``contains``, ``startswith``, ``endswith``, ``re``
- Value types: scalar or list (list = OR across values)
- Conditions: ``selection``, ``selection and not filter``, ``not X``, ``X and Y``
- Aggregation: time-window count via SQLite query
"""

import logging
import re
from datetime import UTC, datetime, timedelta

from engine.models import Alert, Rule
from parser.models import Event

logger = logging.getLogger(__name__)


# ── Low-level field matching ──────────────────────────────────────────────────


def match_field_value(
    value: str | None, pattern: object, modifiers: list[str]
) -> bool:
    """Test whether an event field value matches a pattern with optional modifiers.

    Args:
        value: The event field value (may be ``None``).
        pattern: Scalar string or list of strings from the Sigma YAML.
        modifiers: List of Sigma modifier names (e.g. ``["contains"]``).

    Returns:
        ``True`` if the value matches according to the modifiers.
    """
    if value is None:
        return False

    patterns: list[str] = (
        [str(pattern)] if not isinstance(pattern, list) else [str(p) for p in pattern]
    )

    if "contains" in modifiers:
        val_lower = value.lower()
        return any(p.lower() in val_lower for p in patterns)

    if "startswith" in modifiers:
        return any(value.startswith(p) for p in patterns)

    if "endswith" in modifiers:
        return any(value.endswith(p) for p in patterns)

    if "re" in modifiers:
        return any(bool(re.search(p, value, re.IGNORECASE)) for p in patterns)

    # Exact match (no modifiers); list = OR
    return value in patterns


def match_selection(event: Event, selection: dict) -> bool:
    """Return ``True`` if ALL field conditions in the selection match the event.

    Field names in ``selection`` may include Sigma modifiers separated by ``|``
    (e.g. ``raw_log|contains``).

    Args:
        event: The normalised event to test.
        selection: Sigma detection group dict.

    Returns:
        ``True`` when every field in the selection matches.
    """
    for field_spec, pattern in selection.items():
        parts = field_spec.split("|")
        field_name = parts[0]
        modifiers = parts[1:]
        value = getattr(event, field_name, None)
        if not match_field_value(value, pattern, modifiers):
            return False
    return True


# ── Condition parser ──────────────────────────────────────────────────────────


def _eval_condition(cond: str, groups: dict[str, dict], event: Event) -> bool:
    """Recursively evaluate a Sigma condition string against named detection groups.

    Supports: ``X``, ``not X``, ``X and Y``, ``X or Y``, ``X and not Y``.

    Args:
        cond: Condition expression (lowercased).
        groups: Dict of group name → field-condition dict.
        event: The event being evaluated.

    Returns:
        Boolean result of the condition.
    """
    cond = cond.strip()

    if cond in groups:
        return match_selection(event, groups[cond])

    if " and not " in cond:
        pos, neg = cond.split(" and not ", 1)
        return (
            _eval_condition(pos.strip(), groups, event)
            and not _eval_condition(neg.strip(), groups, event)
        )

    if cond.startswith("not "):
        return not _eval_condition(cond[4:].strip(), groups, event)

    if " and " in cond:
        parts = cond.split(" and ")
        return all(_eval_condition(p.strip(), groups, event) for p in parts)

    if " or " in cond:
        parts = cond.split(" or ")
        return any(_eval_condition(p.strip(), groups, event) for p in parts)

    logger.warning("Unrecognised Sigma condition: %r", cond)
    return False


def evaluate_detection(event: Event, detection: dict) -> bool:
    """Evaluate the full Sigma detection block against an event.

    Args:
        event: The event to test.
        detection: Complete Sigma detection block including ``condition`` key.

    Returns:
        ``True`` if the detection matches.
    """
    condition = str(detection.get("condition", "selection")).strip().lower()
    groups = {k: v for k, v in detection.items() if k != "condition"}
    return _eval_condition(condition, groups, event)


# ── Aggregation helpers ───────────────────────────────────────────────────────


def _count_by_source_ip_in_window(
    conn, source_ip: str, action: str, source_type: str, timeframe_seconds: int
) -> int:
    """Count events from ``source_ip`` matching ``action``/``source_type`` in the time window.

    Uses lexicographic ISO-8601 timestamp comparison (all timestamps are UTC).

    Args:
        conn: Open SQLite connection.
        source_ip: The IP to group by.
        action: Event action to filter on.
        source_type: Event source_type to filter on.
        timeframe_seconds: Look-back window in seconds.

    Returns:
        Count of matching events.
    """
    cutoff = (
        (datetime.now(UTC) - timedelta(seconds=timeframe_seconds))
        .isoformat()
        .replace("+00:00", "Z")
    )
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM events "
            "WHERE source_ip=? AND action=? AND source_type=? AND timestamp >= ?",
            (source_ip, action, source_type, cutoff),
        ).fetchone()
        return int(row[0])
    except Exception as exc:
        logger.error("DB error in count window: %s", exc)
        return 0


def _alert_exists_in_window(
    conn, rule_id: str, source_ip: str | None, timeframe_seconds: int
) -> bool:
    """Check if an alert for this rule+source_ip was already created in the window.

    Used to suppress repeated alerts during the same aggregation window.

    Args:
        conn: Open SQLite connection.
        rule_id: Rule identifier.
        source_ip: Source IP (or None).
        timeframe_seconds: Deduplication window in seconds.

    Returns:
        ``True`` if a duplicate alert exists.
    """
    cutoff = (
        (datetime.now(UTC) - timedelta(seconds=timeframe_seconds))
        .isoformat()
        .replace("+00:00", "Z")
    )
    try:
        if source_ip is None:
            row = conn.execute(
                "SELECT COUNT(*) FROM alerts "
                "WHERE rule_id=? AND source_ip IS NULL AND created_at >= ?",
                (rule_id, cutoff),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) FROM alerts "
                "WHERE rule_id=? AND source_ip=? AND created_at >= ?",
                (rule_id, source_ip, cutoff),
            ).fetchone()
        return int(row[0]) > 0
    except Exception as exc:
        logger.error("DB error in alert dedup check: %s", exc)
        return False


# ── Rule evaluation ───────────────────────────────────────────────────────────


def _evaluate_aggregation(conn, event: Event, rule: Rule) -> Alert | None:
    """Evaluate an aggregation rule (time-window count threshold).

    Args:
        conn: Open SQLite connection.
        event: The triggering event (must have ``id`` set).
        rule: Rule with a non-None ``aggregation`` block.

    Returns:
        An :class:`~engine.models.Alert` if the threshold is exceeded and
        no duplicate exists, else ``None``.
    """
    agg = rule.aggregation
    count_by: str = agg.get("count_by", "source_ip")
    timeframe: int = int(agg.get("timeframe_seconds", 60))
    threshold: int = int(agg.get("threshold", 5))

    group_value: str | None = getattr(event, count_by, None)
    if group_value is None:
        return None

    # The event must itself match the selection first
    if not evaluate_detection(event, rule.detection):
        return None

    # Get the action filter from the detection selection
    selection = rule.detection.get("selection", {})
    action = str(selection.get("action", ""))
    source_type = event.source_type

    count = _count_by_source_ip_in_window(conn, group_value, action, source_type, timeframe)
    # Spec: "> N events" means strictly more than threshold, not >= threshold
    if count <= threshold:
        return None

    # Deduplication: suppress repeated alerts within the same window
    if _alert_exists_in_window(conn, rule.id, group_value, timeframe):
        return None

    return Alert(
        event_id=event.id,
        rule_id=rule.id,
        rule_name=rule.name,
        severity=rule.severity,
        source_ip=group_value,
        matched_count=count,
        timestamp=event.timestamp,
    )


def _evaluate_field_match(event: Event, rule: Rule) -> Alert | None:
    """Evaluate a field-match rule (no aggregation).

    Args:
        event: The event to evaluate (must have ``id`` set).
        rule: Rule without an ``aggregation`` block.

    Returns:
        An :class:`~engine.models.Alert` if the detection matches, else ``None``.
    """
    if not evaluate_detection(event, rule.detection):
        return None
    return Alert(
        event_id=event.id,
        rule_id=rule.id,
        rule_name=rule.name,
        severity=rule.severity,
        source_ip=event.source_ip,
        matched_count=1,
        timestamp=event.timestamp,
    )


def evaluate_rule(conn, event: Event, rule: Rule) -> Alert | None:
    """Evaluate a rule against an event and return an Alert if triggered.

    Dispatches to aggregation or field-match evaluation based on whether
    ``rule.aggregation`` is set.  Returns ``None`` if the event's source_type
    is not in the rule's target source_types.

    Args:
        conn: Open SQLite connection.
        event: The event to evaluate.  ``event.id`` must be set.
        rule: The rule to evaluate.

    Returns:
        An :class:`~engine.models.Alert`, or ``None`` if no match.
    """
    if event.source_type not in rule.source_types:
        return None

    if rule.aggregation:
        return _evaluate_aggregation(conn, event, rule)
    return _evaluate_field_match(event, rule)
