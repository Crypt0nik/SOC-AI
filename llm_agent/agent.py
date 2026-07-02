"""SOC-AI LLM triage agent.

Polls ``alerts(status=untriaged)``, anonymises PII if enabled, calls the
configured LLM backend, validates the JSON response, and writes triage results.
On persistent JSON failures the alert is marked ``error`` so the pipeline
never stalls.
"""

import logging
import os
import time
from pathlib import Path

from db.init_db import init_db
from llm_agent.anonymizer import anonymize
from llm_agent.backends.base import LLMBackend
from llm_agent.db import fetch_untriaged_alerts, insert_triage, mark_alert_status
from llm_agent.schema import TriageResult

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("soc_ai.llm_agent")

_SYSTEM_PROMPT_PATH = Path(__file__).parent / "prompts" / "triage_system.txt"
_JSON_RETRY_SUFFIX = (
    "\n\nIMPORTANT: Your previous response could not be parsed as JSON. "
    "Respond with the JSON object ONLY — no markdown, no explanation."
)


def _load_system_prompt() -> str:
    """Read the system prompt from the prompts directory."""
    return _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()


def _build_context(row) -> str:
    """Construct the alert context string sent to the LLM.

    Args:
        row: SQLite row with alert fields and ``event_raw_log``.

    Returns:
        Multi-line string summarising the alert for the LLM.
    """
    lines = [
        f"Alert ID: {row['id']}",
        f"Rule: {row['rule_name']} ({row['rule_id']})",
        f"Detection Severity: {row['severity']}",
        f"Source IP: {row['source_ip'] or 'N/A'}",
        f"Matched Count: {row['matched_count']}",
        f"Timestamp: {row['timestamp']}",
        f"Raw Log: {row['event_raw_log'] or ''}",
    ]
    return "\n".join(lines)


def process_alert(
    conn,
    row,
    backend: LLMBackend,
    system_prompt: str,
    anonymize_pii: bool,
) -> bool:
    """Triage a single untriaged alert row.

    Builds the LLM context, optionally anonymises PII, calls the backend
    with up to 2 attempts, validates the JSON, and writes the result.

    Args:
        conn: Open SQLite connection.
        row: SQLite row from ``fetch_untriaged_alerts``.
        backend: Configured LLM backend instance.
        system_prompt: System prompt string.
        anonymize_pii: Whether to tokenise PII before sending to the LLM.

    Returns:
        ``True`` if the alert was successfully triaged, ``False`` otherwise.
    """
    alert_id: int = row["id"]
    context = _build_context(row)

    if anonymize_pii:
        known_ips = [row["source_ip"]] if row["source_ip"] else []
        context, _ = anonymize(context, conn, alert_id, known_ips=known_ips)

    for attempt in range(2):
        prompt = context if attempt == 0 else context + _JSON_RETRY_SUFFIX
        try:
            raw_json = backend.triage(system_prompt, prompt)
            result = TriageResult.model_validate_json(raw_json)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Triage attempt %d/%d failed for alert %d: %s",
                attempt + 1, 2, alert_id, exc,
            )
            continue

        # Success path
        insert_triage(conn, alert_id, result, backend.name, raw_json)
        mark_alert_status(conn, alert_id, "triaged")
        logger.info(
            "Alert %d triaged: severity=%s confidence=%d backend=%s",
            alert_id, result.severity, result.confidence, backend.name,
        )
        return True

    # Both attempts failed
    mark_alert_status(conn, alert_id, "error")
    logger.error("Alert %d could not be triaged after 2 attempts — marked error", alert_id)
    return False


def get_backend(env: dict | None = None) -> LLMBackend:
    """Instantiate the LLM backend from the ``LLM_BACKEND`` environment variable.

    Args:
        env: Optional dict to use instead of ``os.environ`` (for testing).

    Returns:
        Configured :class:`~llm_agent.backends.base.LLMBackend` instance.

    Raises:
        ValueError: If ``LLM_BACKEND`` is not a supported backend.
    """
    backend_name = (env or os.environ).get("LLM_BACKEND", "ollama").lower().strip()
    if backend_name == "claude":
        from llm_agent.backends.claude_backend import ClaudeBackend
        return ClaudeBackend()
    if backend_name == "codex":
        from llm_agent.backends.codex_backend import CodexBackend
        return CodexBackend()
    if backend_name == "ollama":
        from llm_agent.backends.ollama_backend import OllamaBackend
        return OllamaBackend()
    raise ValueError(
        f"Unknown LLM_BACKEND={backend_name!r}. "
        "Supported values: 'claude', 'codex', 'ollama'."
    )


def main() -> None:
    """Entry point — poll untriaged alerts and send them for LLM triage."""
    poll_interval = int(os.environ.get("POLL_INTERVAL", "2"))
    db_path = os.environ.get("DB_PATH", "/data/soc.db")
    anonymize_pii = os.environ.get("ANONYMIZE_PII", "true").lower() == "true"

    conn = init_db(db_path)
    try:
        backend = get_backend()
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to initialise LLM backend: %s", exc)
        raise

    system_prompt = _load_system_prompt()
    logger.info(
        "LLM agent started: backend=%s anonymize_pii=%s polling every %ds",
        backend.name, anonymize_pii, poll_interval,
    )

    while True:
        try:
            rows = fetch_untriaged_alerts(conn)
            for row in rows:
                try:
                    process_alert(conn, row, backend, system_prompt, anonymize_pii)
                except Exception as exc:  # noqa: BLE001
                    logger.error("Unexpected error processing alert %d: %s", row["id"], exc)
                    mark_alert_status(conn, row["id"], "error")
        except Exception as exc:  # noqa: BLE001
            logger.error("Agent loop error: %s", exc)
        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
