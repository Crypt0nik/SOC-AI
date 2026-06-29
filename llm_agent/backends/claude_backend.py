"""Anthropic Claude backend for SOC-AI triage."""

import logging
import os

from llm_agent.backends.base import LLMBackend

logger = logging.getLogger(__name__)


class ClaudeBackend(LLMBackend):
    """Calls the Anthropic Messages API (claude-sonnet-4-6 by default).

    Requires ``ANTHROPIC_API_KEY`` environment variable.
    The model is overridable via ``CLAUDE_MODEL``.
    """

    name = "claude"

    def __init__(self) -> None:
        """Initialise the Anthropic client from environment variables."""
        try:
            import anthropic
        except ImportError as exc:
            raise ImportError("anthropic package required: pip install anthropic") from exc

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6")
        logger.info("ClaudeBackend initialised with model=%s", self._model)

    def triage(self, system: str, user: str) -> str:
        """Call the Anthropic Messages API and return the text response.

        Args:
            system: System prompt string.
            user: User message string (alert context).

        Returns:
            Raw text content from the first content block.

        Raises:
            anthropic.APIError: On API-level errors (rate limit, auth, etc.).
        """
        message = self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return message.content[0].text
