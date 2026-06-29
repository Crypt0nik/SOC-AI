"""Pydantic model for the LLM triage JSON response."""

from typing import Literal

from pydantic import BaseModel, field_validator


class TriageResult(BaseModel):
    """Validated output from the LLM triage backend.

    All fields are required. The LLM must return strict JSON conforming to
    this schema; any deviation triggers a retry then ``status=error``.
    """

    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]
    attack_type: str
    mitre_id: str
    confidence: int
    summary: str
    recommendation: str
    false_positive_risk: Literal["LOW", "MEDIUM", "HIGH"]

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: int) -> int:
        """Ensure confidence is an integer between 0 and 100."""
        if not 0 <= v <= 100:
            raise ValueError(f"confidence must be 0-100, got {v}")
        return v

    @field_validator("attack_type", "mitre_id", "summary", "recommendation")
    @classmethod
    def not_empty(cls, v: str) -> str:
        """Reject blank or whitespace-only string fields."""
        if not v or not v.strip():
            raise ValueError("field must not be empty or whitespace")
        return v
