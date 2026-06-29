# Contributing to SOC-AI

Thank you for your interest in contributing to SOC-AI! 🎉

## Development setup

```bash
git clone https://github.com/your-org/soc-ai.git
cd soc-ai
python -m venv .venv && source .venv/bin/activate
pip install -r parser/requirements.txt -r engine/requirements.txt \
            -r llm_agent/requirements.txt -r api/requirements.txt
pip install pytest ruff
cp .env.example .env
```

## Workflow

1. Fork the repo and create a branch from `dev` (not `main`).
2. Write tests first (TDD) for parser and engine modules.
3. Implement until tests pass: `pytest tests/ -v`
4. Lint: `ruff check .` — must be clean.
5. Open a PR against `dev`.

## Commit conventions

```
<type>(<scope>): <short description>
```
Types: `feat | fix | test | docs | chore | refactor | ci`
Scopes: `parser | engine | llm_agent | api | dashboard | db | ci | docs | all`

## Scope guard — COMMUNITY ONLY

v1.0 implements only the **Community tier**. Do **not** add:
- Slack/Teams/PagerDuty alerts
- Sigma premium rules (50+)
- Advanced temporal correlation
- Auto-response (IP block, quarantine)
- Multi-tenant, SSO/SAML/OIDC
- NIS2/ISO27001 reports
- SOAR / SIEM connectors

Everything above belongs in the README Roadmap only.

## RGPD / PII requirements

Any code handling user data **must**:
- Respect `ANONYMIZE_PII` environment variable.
- Never log or transmit raw PII to a cloud LLM when anonymisation is enabled.
- Document data flows in PR description.

## Code style

- Python 3.11, PEP8, Google-style docstrings on all public functions.
- `try/except` on every LLM and DB call; use `logging`, not `print()`.
- No secrets in code — use `.env`.

## Reporting vulnerabilities

See [SECURITY.md](SECURITY.md).
