"""SOC-AI notification dispatcher — polls triaged alerts and forwards to Slack/Teams.

Pro feature: requires PLAN=pro or PLAN=enterprise.
Runs as a standalone service in Docker Compose (profile: pro).
"""

import logging
import os
import time
from datetime import UTC, datetime

from notifications.db import (
    fetch_alerts_to_notify,
    get_connection,
    init_notifications_table,
    mark_notified,
)
from notifications.slack import send_slack_notification
from notifications.teams import send_teams_notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("soc_ai.notifications")

_POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "10"))
_MIN_SEVERITY = os.environ.get("NOTIFY_MIN_SEVERITY", "HIGH").upper()
_SLACK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
_TEAMS_URL = os.environ.get("TEAMS_WEBHOOK_URL", "")
_PLAN = os.environ.get("PLAN", "community").lower()


def _dispatch(alert: dict) -> None:
    """Send alert to all configured channels and mark as notified.

    Args:
        alert: Alert row dict with triage fields merged in.
    """
    conn = get_connection()
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    sent_any = False

    if _SLACK_URL:
        ok = send_slack_notification(alert, _SLACK_URL)
        mark_notified(conn, alert["id"], "slack", "sent" if ok else "error", now)
        sent_any = True

    if _TEAMS_URL:
        ok = send_teams_notification(alert, _TEAMS_URL)
        mark_notified(conn, alert["id"], "teams", "sent" if ok else "error", now)
        sent_any = True

    if not sent_any:
        # No channels configured — mark as sent to avoid reprocessing
        mark_notified(conn, alert["id"], "none", "sent", now)

    conn.close()


def run() -> None:
    """Main polling loop — dispatches new triaged alerts to configured channels."""
    if _PLAN not in ("pro", "enterprise"):
        logger.warning(
            "PLAN=%s — notifications require Pro or Enterprise. Exiting.", _PLAN
        )
        return

    if not _SLACK_URL and not _TEAMS_URL:
        logger.warning(
            "No webhook URLs configured (SLACK_WEBHOOK_URL / TEAMS_WEBHOOK_URL). "
            "Notifications will be recorded but not sent."
        )

    logger.info(
        "Notification dispatcher started — plan=%s min_severity=%s slack=%s teams=%s",
        _PLAN,
        _MIN_SEVERITY,
        bool(_SLACK_URL),
        bool(_TEAMS_URL),
    )

    conn = get_connection()
    init_notifications_table(conn)
    conn.close()

    last_id = 0
    while True:
        try:
            conn = get_connection()
            alerts = fetch_alerts_to_notify(conn, _MIN_SEVERITY, last_id)
            conn.close()

            for alert in alerts:
                logger.info(
                    "Dispatching alert %d (%s — %s)",
                    alert["id"],
                    alert.get("triage_severity") or alert.get("severity"),
                    alert.get("rule_name"),
                )
                try:
                    _dispatch(alert)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Dispatch failed for alert %d: %s", alert["id"], exc)
                last_id = max(last_id, alert["id"])

        except Exception as exc:  # noqa: BLE001
            logger.error("Dispatcher poll error: %s", exc)

        time.sleep(_POLL_INTERVAL)


if __name__ == "__main__":
    run()
