"""SOC-AI Sigma detection engine.

Polls the ``events`` SQLite table for new normalised log events, evaluates
them against the loaded Sigma rules, and writes alerts to the ``alerts``
table for subsequent LLM triage.
"""

import logging
import os
import time
from pathlib import Path

from db.init_db import init_db
from engine.db import fetch_new_events, insert_alert, mark_event_processed
from engine.matcher import evaluate_rule
from engine.rules_loader import load_rules

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("soc_ai.engine")


def run_once(conn, rules: list) -> int:
    """Process all new events against all rules in a single pass.

    Args:
        conn: Open SQLite connection (WAL mode).
        rules: List of loaded :class:`~engine.models.Rule` objects.

    Returns:
        Number of alerts created during this pass.
    """
    events = fetch_new_events(conn)
    alerts_created = 0

    for event in events:
        applicable = [r for r in rules if event.source_type in r.source_types]
        for rule in applicable:
            try:
                alert = evaluate_rule(conn, event, rule)
                if alert:
                    alert_id = insert_alert(conn, alert)
                    if alert_id > 0:
                        alerts_created += 1
                        logger.info(
                            "Alert %d raised: rule=%s severity=%s ip=%s",
                            alert_id, rule.id, rule.severity, event.source_ip,
                        )
            except Exception as exc:  # noqa: BLE001
                logger.error(
                    "Rule %s failed for event %d: %s", rule.id, event.id or -1, exc
                )
        mark_event_processed(conn, event.id)

    return alerts_created


def main() -> None:
    """Entry point — poll events table and evaluate Sigma rules continuously."""
    poll_interval = int(os.environ.get("POLL_INTERVAL", "2"))
    db_path = os.environ.get("DB_PATH", "/data/soc.db")
    rules_dir = Path(__file__).parent / "rules"

    conn = init_db(db_path)
    rules = load_rules(str(rules_dir))
    logger.info("Engine started: %d rules loaded, polling every %ds", len(rules), poll_interval)

    while True:
        try:
            n = run_once(conn, rules)
            if n:
                logger.info("%d alert(s) created this cycle", n)
        except Exception as exc:  # noqa: BLE001
            logger.error("Engine loop error: %s", exc)
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
