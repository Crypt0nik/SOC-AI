"""Microsoft Teams webhook notifications for SOC-AI alerts."""

import logging

import httpx

logger = logging.getLogger(__name__)

_SEVERITY_COLOR = {
    "CRITICAL": "FF0000",
    "HIGH": "FF6600",
    "MEDIUM": "FFB300",
    "LOW": "0066CC",
    "INFO": "666666",
}
_SEVERITY_EMOJI = {
    "CRITICAL": "🔴",
    "HIGH": "🟠",
    "MEDIUM": "🟡",
    "LOW": "🔵",
    "INFO": "⚪",
}


def send_teams_notification(
    alert: dict,
    webhook_url: str,
) -> bool:
    """Send an alert notification to a Microsoft Teams channel via webhook.

    Uses the legacy Incoming Webhook (MessageCard) format compatible with
    all Teams versions without needing an Azure app registration.

    Args:
        alert: Row dict containing alert + triage fields.
        webhook_url: Teams incoming webhook URL.

    Returns:
        True on success, False on any error.
    """
    eff_sev = alert.get("triage_severity") or alert.get("severity", "INFO")
    color = _SEVERITY_COLOR.get(eff_sev, "666666")
    emoji = _SEVERITY_EMOJI.get(eff_sev, "⚪")

    facts = [
        {"name": "Rule", "value": f"{alert.get('rule_id')} — {alert.get('rule_name')}"},
        {"name": "Severity", "value": f"{emoji} {eff_sev}"},
    ]
    if alert.get("source_ip"):
        facts.append({"name": "Source IP", "value": alert["source_ip"]})
    if alert.get("mitre_id"):
        facts.append({"name": "MITRE ATT&CK", "value": alert["mitre_id"]})
    if alert.get("confidence") is not None:
        facts.append({"name": "Confidence", "value": f"{alert['confidence']}%"})

    sections = [{"facts": facts}]
    if alert.get("summary"):
        sections.append({"text": f"**Analysis:** {alert['summary']}"})

    payload = {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": color,
        "summary": f"SOC-AI Alert — {eff_sev}: {alert.get('rule_name')}",
        "title": f"{emoji} SOC-AI Alert — {eff_sev}",
        "sections": sections,
    }

    try:
        resp = httpx.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        logger.info("Teams notification sent for alert %d", alert["id"])
        return True
    except httpx.HTTPError as exc:
        logger.warning("Teams notification failed for alert %d: %s", alert.get("id"), exc)
        return False
