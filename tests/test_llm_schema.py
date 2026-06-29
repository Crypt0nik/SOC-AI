"""Tests for TriageResult pydantic schema validation."""

import pytest
from pydantic import ValidationError

from llm_agent.schema import TriageResult

_VALID = {
    "severity": "HIGH",
    "attack_type": "SSH Brute Force",
    "mitre_id": "T1110",
    "confidence": 85,
    "summary": "Multiple failed SSH login attempts from a single external IP.",
    "recommendation": "Block source IP at the firewall and review auth logs.",
    "false_positive_risk": "LOW",
}


def test_valid_triage_result():
    r = TriageResult.model_validate(_VALID)
    assert r.severity == "HIGH"
    assert r.confidence == 85
    assert r.false_positive_risk == "LOW"


def test_all_severity_values_accepted():
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"):
        r = TriageResult.model_validate({**_VALID, "severity": sev})
        assert r.severity == sev


def test_invalid_severity_rejected():
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**_VALID, "severity": "EXTREME"})


def test_confidence_zero_accepted():
    r = TriageResult.model_validate({**_VALID, "confidence": 0})
    assert r.confidence == 0


def test_confidence_hundred_accepted():
    r = TriageResult.model_validate({**_VALID, "confidence": 100})
    assert r.confidence == 100


def test_confidence_above_100_rejected():
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**_VALID, "confidence": 101})


def test_confidence_negative_rejected():
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**_VALID, "confidence": -1})


def test_empty_summary_rejected():
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**_VALID, "summary": "   "})


def test_empty_recommendation_rejected():
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**_VALID, "recommendation": ""})


def test_empty_attack_type_rejected():
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**_VALID, "attack_type": ""})


def test_empty_mitre_id_rejected():
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**_VALID, "mitre_id": ""})


def test_invalid_false_positive_risk_rejected():
    with pytest.raises(ValidationError):
        TriageResult.model_validate({**_VALID, "false_positive_risk": "NONE"})


def test_all_false_positive_risk_values_accepted():
    for risk in ("LOW", "MEDIUM", "HIGH"):
        r = TriageResult.model_validate({**_VALID, "false_positive_risk": risk})
        assert r.false_positive_risk == risk


def test_model_validate_json_roundtrip():
    import json
    raw = json.dumps(_VALID)
    r = TriageResult.model_validate_json(raw)
    assert r.severity == "HIGH"
    assert r.mitre_id == "T1110"


def test_invalid_json_string_raises():
    from pydantic import ValidationError as PydanticError
    with pytest.raises(PydanticError):
        TriageResult.model_validate_json("not valid json {")


def test_missing_required_field_raises():
    data = {k: v for k, v in _VALID.items() if k != "mitre_id"}
    with pytest.raises(ValidationError):
        TriageResult.model_validate(data)
