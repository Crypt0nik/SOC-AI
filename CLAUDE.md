# CLAUDE.md — SOC-AI v1.0

> This file guides Claude Code on conventions, scope, and commands for this project.

## Project summary
SOC-AI is a **Community Edition** (MIT, open source) lightweight SOC powered by an LLM.
It automates L1 alert triage for SMEs.

## Architecture at a glance
```
[Logs] → parser/ → SQLite(events) → engine/ → SQLite(alerts) → llm_agent/ → SQLite(triage)
                                                                       ↓
                                                             api/ (FastAPI) ← dashboard/ (React)
```
All modules communicate via **SQLite (WAL mode, polling ~2s)** — no message broker.

## Scope guard — COMMUNITY ONLY
v1.0 implements ONLY the Community tier. Never add:
- Slack/Teams/PagerDuty alerts, Sigma premium (50+), temporal correlation,
  auto-response (IP block / quarantine), multi-tenant, SSO/SAML/OIDC,
  NIS2/ISO27001 reports, SOAR connectors, SIEM connectors.
All of the above go in the README Roadmap section only.

## Tech stack
| Module | Stack |
|--------|-------|
| parser, engine, llm_agent, api | Python 3.11, SQLite, pySigma, FastAPI |
| llm_agent backends | Anthropic Claude Sonnet (`claude-sonnet-4-6`) · Ollama (llama3.1) |
| dashboard | React 18 + Vite + TailwindCSS 3 |
| CI | GitHub Actions (ruff, pytest, docker compose build) |
| Containers | Docker + Docker Compose |

## Severity colour palette (exact — dashboard and tests must use these)
| Severity | Hex | CSS class |
|----------|-----|-----------|
| CRITICAL | `#FF0000` | `text-[#FF0000]` / `bg-[#FF0000]` |
| HIGH | `#FF6600` | `text-[#FF6600]` |
| MEDIUM | `#FFB300` | `text-[#FFB300]` |
| LOW | `#0066CC` | `text-[#0066CC]` |
| INFO | `#666666` | `text-[#666666]` |

## Database schema
See `db/schema.sql`.
Key tables: `events`, `alerts`, `triage`, `pii_mapping`.

## RGPD / PII rules
- `ANONYMIZE_PII=true` → IPs, usernames, emails are tokenised before LLM cloud call.
- Mapping stored in `pii_mapping` (local only, never sent to cloud).
- Dashboard shows original values (resolved from mapping).
- Retention: `RETENTION_DAYS=90` (configurable).

## Quality rules
- PEP8 via `ruff check .` (CI enforced). Zero warnings before committing.
- Docstrings on all public functions (Google style).
- `try/except` on every LLM and DB call; use `logging.WARNING/ERROR`, never `print()`.
- No secrets in code — use `.env` / environment variables.
- TDD for parser/ and engine/ (write tests before implementation in those phases).

## Sigma rules
`engine/rules/{id}.yml` — standard Sigma format + optional `soc_ai:` extension block for
time-window aggregation. PyYAML loads at runtime; pySigma validates in tests.

## Key commands
```bash
# Start everything (Claude API mode)
LLM_BACKEND=claude docker compose up

# Start with local Ollama
docker compose --profile ollama up

# Run all tests
pytest tests/ -v

# Lint
ruff check .

# Inject a sample brute-force for demo
bash scripts/replay_bruteforce.sh

# Query alerts via API
curl http://localhost:8000/alerts | jq .
```

## Commit conventions
```
<type>(<scope>): <short description>

Types: feat | fix | test | docs | chore | refactor | ci
Scopes: parser | engine | llm_agent | api | dashboard | db | ci | docs | all
```
One phase = one atomic commit. Work on `dev`, merge to `main` after tests pass.
