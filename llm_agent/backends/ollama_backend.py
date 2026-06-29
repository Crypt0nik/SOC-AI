"""Ollama local LLM backend for SOC-AI triage."""

import json
import logging
import os
import urllib.error
import urllib.request

from llm_agent.backends.base import LLMBackend

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 120


class OllamaBackend(LLMBackend):
    """Calls a local Ollama instance via its REST API (``/api/generate``).

    Uses ``format: "json"`` to coerce Ollama into returning a JSON object.
    Requires no API key — just a running Ollama server accessible at
    ``OLLAMA_HOST`` (default ``http://ollama:11434``).
    """

    name = "ollama"

    def __init__(self) -> None:
        """Initialise from ``OLLAMA_HOST`` and ``OLLAMA_MODEL`` env vars."""
        self._host = os.environ.get("OLLAMA_HOST", "http://ollama:11434").rstrip("/")
        self._model = os.environ.get("OLLAMA_MODEL", "llama3.1")
        logger.info("OllamaBackend initialised: host=%s model=%s", self._host, self._model)

    def triage(self, system: str, user: str) -> str:
        """POST to ``/api/generate`` and return the ``response`` field.

        The system prompt and user message are concatenated (Ollama's generate
        API does not natively support separate system/user turns in all models).

        Args:
            system: System prompt string.
            user: User message string (alert context).

        Returns:
            The ``response`` field from Ollama's JSON reply.

        Raises:
            urllib.error.URLError: On network/connection errors.
            KeyError: If the response JSON is missing the ``response`` field.
        """
        payload = json.dumps({
            "model": self._model,
            "prompt": f"{system}\n\n{user}",
            "format": "json",
            "stream": False,
        }).encode()

        url = f"{self._host}/api/generate"
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=_DEFAULT_TIMEOUT) as resp:
                data = json.loads(resp.read().decode())
            return data["response"]
        except urllib.error.URLError as exc:
            logger.error("Ollama unreachable at %s: %s", url, exc)
            raise
        except (KeyError, json.JSONDecodeError) as exc:
            logger.error("Unexpected Ollama response format: %s", exc)
            raise
