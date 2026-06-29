"""Sigma rule loader for the SOC-AI engine.

Loads ``*.yml`` files from a directory using PyYAML.
The ``soc_ai:`` extension block is read for engine-specific metadata
(rule_id, severity, source_types, aggregation config).
"""

import logging
from pathlib import Path

import yaml

from engine.models import Rule

logger = logging.getLogger(__name__)

# Standard Sigma level → SOC-AI severity (fallback when soc_ai.severity absent)
_LEVEL_MAP = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
    "informational": "INFO",
}


def load_rules(rules_dir: str) -> list[Rule]:
    """Load all Sigma rule YAML files from a directory.

    Each file must contain a ``detection`` block and a ``soc_ai`` extension
    block with at least ``rule_id``, ``severity``, and ``source_types``.

    Args:
        rules_dir: Path to the directory containing ``*.yml`` rule files.

    Returns:
        List of parsed :class:`~engine.models.Rule` objects.  Files that
        fail to parse are skipped with an ERROR log.
    """
    path = Path(rules_dir)
    rules: list[Rule] = []

    for rule_file in sorted(path.glob("*.yml")):
        try:
            rule = _load_one(rule_file)
            rules.append(rule)
            logger.info("Loaded rule %s (%s)", rule.id, rule.name)
        except Exception as exc:
            logger.error("Skipping invalid rule file %s: %s", rule_file.name, exc)

    if not rules:
        logger.warning("No rules loaded from %s", rules_dir)
    return rules


def _load_one(rule_file: Path) -> Rule:
    """Parse a single Sigma YAML file into a Rule.

    Args:
        rule_file: Path to the ``.yml`` file.

    Returns:
        A :class:`~engine.models.Rule` instance.

    Raises:
        ValueError: If required fields are missing.
        yaml.YAMLError: If the file is not valid YAML.
    """
    data = yaml.safe_load(rule_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Rule file is not a YAML mapping")

    soc_ai = data.get("soc_ai", {})
    if not isinstance(soc_ai, dict):
        raise ValueError("soc_ai block must be a mapping")

    rule_id = soc_ai.get("rule_id")
    if not rule_id:
        raise ValueError("soc_ai.rule_id is required")

    severity_raw = soc_ai.get("severity", "")
    if severity_raw not in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        # Fallback: map standard Sigma level
        sigma_level = str(data.get("level", "medium")).lower()
        severity_raw = _LEVEL_MAP.get(sigma_level, "MEDIUM")

    source_types = soc_ai.get("source_types", [])
    if not source_types:
        raise ValueError("soc_ai.source_types must list at least one source type")

    detection = data.get("detection")
    if not detection or not isinstance(detection, dict):
        raise ValueError("detection block is required")

    return Rule(
        id=rule_id,
        name=str(data.get("title", rule_id)),
        severity=severity_raw,
        source_types=list(source_types),
        detection=detection,
        aggregation=soc_ai.get("aggregation"),
    )
