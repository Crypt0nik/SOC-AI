"""OpenAI Codex backend for SOC-AI triage."""

import logging
import os
from typing import Any

from llm_agent.backends.base import LLMBackend

logger = logging.getLogger(__name__)

_TRIAGE_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "severity": {
            "type": "string",
            "enum": ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"],
        },
        "attack_type": {"type": "string", "minLength": 1},
        "mitre_id": {"type": "string", "minLength": 1},
        "confidence": {"type": "integer", "minimum": 0, "maximum": 100},
        "summary": {"type": "string", "minLength": 1},
        "recommendation": {"type": "string", "minLength": 1},
        "false_positive_risk": {
            "type": "string",
            "enum": ["LOW", "MEDIUM", "HIGH"],
        },
    },
    "required": [
        "severity",
        "attack_type",
        "mitre_id",
        "confidence",
        "summary",
        "recommendation",
        "false_positive_risk",
    ],
}


class CodexBackend(LLMBackend):
    """Calls OpenAI's Responses API with a Codex-compatible model.

    Requires ``OPENAI_API_KEY`` environment variable.
    The model is overridable via ``CODEX_MODEL``.
    """

    name = "codex"

    def __init__(self) -> None:
        """Initialise the OpenAI client from environment variables."""
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise ImportError("openai package required: pip install openai") from exc

        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self._client = OpenAI(api_key=api_key)
        self._model = os.environ.get("CODEX_MODEL", "gpt-5.4-mini")
        logger.info("CodexBackend initialised with model=%s", self._model)

    def triage(self, system: str, user: str) -> str:
        """Call OpenAI Responses API and return the JSON text response.

        Args:
            system: System prompt string.
            user: User message string (alert context).

        Returns:
            Raw JSON response text.

        Raises:
            openai.APIError: On API-level errors (rate limit, auth, etc.).
            ValueError: If the response does not contain text output.
        """
        response = self._client.responses.create(
            model=self._model,
            instructions=system,
            input=user,
            max_output_tokens=1024,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "soc_ai_triage_result",
                    "schema": _TRIAGE_JSON_SCHEMA,
                    "strict": True,
                }
            },
        )

        output_text = getattr(response, "output_text", None)
        if output_text:
            return output_text

        for item in getattr(response, "output", []) or []:
            for content in getattr(item, "content", []) or []:
                text = getattr(content, "text", None)
                if text:
                    return text

        raise ValueError("OpenAI response did not contain output text")
