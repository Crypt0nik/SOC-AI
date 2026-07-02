"""Slack incoming-webhook notifications for SOC-AI alerts."""

import logging

import httpx

logger = logging.getLogger(__name__)

_SEVERITY_COLOR = {
    "CRITICAL": "#FF0000",
    "HIGH": "#FF6600",
    "MEDIUM": "#FFB300",
    "LOW": "#0066CC",
    "INFO": "#666666",
}
_SEVERITY_EMOJI = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🔵",
    "INFO": "⚪",
}


def send_slack_notification(
    alert: dict,
    webhook_url: str,
) -> bool:
    """Send an alert notification to a Slack channel via incoming webhook.

    Args:
        alert: Row dict containing alert + triage fields.
        webhook_url: Slack incoming webhook URL.

    Returns:
        True on success, False on any error.
    """
    eff_sev = alert.get("triage_severity") or alert.get("severity", "INFO")
    color = _SEVERITY_COLOR.get(eff_sev, "#666666")
    emoji = _SEVERITY_EMOJI.get(eff_sev, "⚪")

    fields = [
        {"title": "Rule", "value": f"`{alert.get('rule_id')}` — {alert.get('rule_name')}", "short": False},
        {"title": "Severity", "value": f"{emoji} {eff_sev}", "short": True},
    ]
    if alert.get("source_ip"):
        fields.append({"title": "Source IP", "value": alert["source_ip"], "short": True})
    if alert.get("mitre_id"):
        fields.append({"title": "MITRE ATT&CK", "value": alert["mitre_id"], "short": True})
    if alert.get("confidence") is not None:
        fields.append({"title": "Confidence", "value": f"{alert['confidence']}%", "short": True})
    if alert.get("summary"):
        fields.append({"title": "Analysis", "value": alert["summary"], "short": False})

    payload = {
        "attachments": [
            {
                "color": color,
                "pretext": f"{emoji} *SOC-AI Alert — {eff_sev}*",
                "title": alert.get("rule_name", "Unknown rule"),
                "fields": fields,
                "footer": "SOC-AI Pro",
                "ts": alert.get("timestamp", ""),
            }
        ]
    }

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("Slack notification sent for alert %d", alert["id"])
        return True
    except httpx.HTTPError as exc:
        logger.warning("Slack notification failed for alert %d: %s", alert.get("id"), exc)
        return False
