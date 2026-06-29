"""Abstract base class for LLM triage backends."""

from abc import ABC, abstractmethod


class LLMBackend(ABC):
    """Interface that all LLM backends must implement."""

    name: str = "unknown"

    @abstractmethod
    def triage(self, system: str, user: str) -> str:
        """Send a triage request to the LLM and return the raw response string.

        Args:
            system: System prompt (persona + JSON schema instructions).
            user: User message (alert context, optionally anonymised).

        Returns:
            Raw string response from the LLM (expected to be valid JSON).

        Raises:
            Exception: On API/network error; callers must handle and retry.
        """
