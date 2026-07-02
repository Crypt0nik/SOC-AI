"""Tests for the OpenAI Codex backend."""

import sys
import types

from llm_agent.backends.codex_backend import CodexBackend


class _FakeResponses:
    def __init__(self, response):
        self._response = response
        self.last_payload = None

    def create(self, **payload):
        self.last_payload = payload
        return self._response


class _FakeClient:
    def __init__(self, response):
        self.responses = _FakeResponses(response)


def _install_fake_openai(monkeypatch, response):
    created = {}

    class FakeOpenAI:
        def __init__(self, api_key):
            created["api_key"] = api_key
            created["client"] = _FakeClient(response)

        @property
        def responses(self):
            return created["client"].responses

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=FakeOpenAI))
    return created


def test_codex_backend_returns_output_text(monkeypatch):
    response = types.SimpleNamespace(output_text='{"severity":"LOW"}')
    created = _install_fake_openai(monkeypatch, response)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("CODEX_MODEL", "test-model")

    backend = CodexBackend()

    assert backend.triage("system", "user") == '{"severity":"LOW"}'
    assert created["api_key"] == "test-key"
    payload = created["client"].responses.last_payload
    assert payload["model"] == "test-model"
    assert payload["instructions"] == "system"
    assert payload["input"] == "user"
    assert payload["text"]["format"]["type"] == "json_schema"


def test_codex_backend_falls_back_to_output_content(monkeypatch):
    content = types.SimpleNamespace(text='{"severity":"MEDIUM"}')
    item = types.SimpleNamespace(content=[content])
    response = types.SimpleNamespace(output=[item])
    _install_fake_openai(monkeypatch, response)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    backend = CodexBackend()

    assert backend.triage("system", "user") == '{"severity":"MEDIUM"}'


def test_codex_backend_requires_openai_api_key(monkeypatch):
    _install_fake_openai(monkeypatch, types.SimpleNamespace(output_text="{}"))
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    try:
        CodexBackend()
    except ValueError as exc:
        assert "OPENAI_API_KEY" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
