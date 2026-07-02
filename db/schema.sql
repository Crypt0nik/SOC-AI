-- SOC-AI v1.0 — SQLite schema
-- Created by db/init.py (called at first run of each module).
-- WAL mode is enabled at runtime via PRAGMA journal_mode=WAL;

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ── events ──────────────────────────────────────────────────
-- Normalised log lines written by parser/, consumed by engine/.
CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT    NOT NULL,                  -- ISO-8601 UTC
    source_ip   TEXT,                              -- nullable (e.g. Windows local events)
    user        TEXT,                              -- nullable
    action      TEXT,                              -- human-readable action label
    raw_log     TEXT    NOT NULL,                  -- original log line (verbatim)
    source_type TEXT    NOT NULL,                  -- ssh | web | windows | json
    status      TEXT    NOT NULL DEFAULT 'new',    -- new | processed
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_ts     ON events(timestamp);
CREATE INDEX IF NOT EXISTS idx_events_ip     ON events(source_ip);

-- ── alerts ──────────────────────────────────────────────────
-- Sigma rule matches produced by engine/, consumed by llm_agent/.
CREATE TABLE IF NOT EXISTS alerts (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id      INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    rule_id       TEXT    NOT NULL,                -- e.g. SSH-001
    rule_name     TEXT    NOT NULL,
    severity      TEXT    NOT NULL,                -- rule severity: CRITICAL|HIGH|MEDIUM|LOW|INFO
    source_ip     TEXT,
    matched_count INTEGER NOT NULL DEFAULT 1,      -- number of events matched (aggregation)
    timestamp     TEXT    NOT NULL,
    status        TEXT    NOT NULL DEFAULT 'untriaged', -- untriaged | triaged | error
    created_at    TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_alerts_status   ON alerts(status);
CREATE INDEX IF NOT EXISTS idx_alerts_ts       ON alerts(timestamp);
CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);

-- ── triage ──────────────────────────────────────────────────
-- LLM qualification produced by llm_agent/, read by api/.
CREATE TABLE IF NOT EXISTS triage (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id            INTEGER NOT NULL UNIQUE REFERENCES alerts(id) ON DELETE CASCADE,
    severity            TEXT    NOT NULL,           -- LLM-qualified severity (authoritative for UI)
    attack_type         TEXT    NOT NULL,
    mitre_id            TEXT,                       -- e.g. T1110.001 or NULL
    confidence          INTEGER NOT NULL,           -- 0-100
    summary             TEXT    NOT NULL,           -- FR, ≤2 sentences
    recommendation      TEXT    NOT NULL,           -- FR, ≤2 sentences
    false_positive_risk TEXT    NOT NULL,           -- LOW | MEDIUM | HIGH
    backend             TEXT    NOT NULL,           -- claude | ollama
    raw_llm_json        TEXT    NOT NULL,           -- raw JSON string from LLM (archival)
    created_at          TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_triage_alert_id ON triage(alert_id);
CREATE INDEX IF NOT EXISTS idx_triage_severity ON triage(severity);

-- ── notifications ────────────────────────────────────────────
-- Tracks alerts dispatched to Slack/Teams (Pro feature).
CREATE TABLE IF NOT EXISTS notifications (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id  INTEGER UNIQUE NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    channel   TEXT    NOT NULL,                 -- slack | teams | none
    sent_at   TEXT    NOT NULL,                 -- ISO-8601 UTC
    status    TEXT    NOT NULL                  -- sent | error
);
CREATE INDEX IF NOT EXISTS idx_notifications_alert_id ON notifications(alert_id);

-- ── alert_notes ─────────────────────────────────────────────
-- Analyst notes attached to alerts (Community feature).
CREATE TABLE IF NOT EXISTS alert_notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_id   INTEGER NOT NULL UNIQUE REFERENCES alerts(id) ON DELETE CASCADE,
    note       TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);
CREATE INDEX IF NOT EXISTS idx_alert_notes_alert_id ON alert_notes(alert_id);

-- ── pii_mapping ──────────────────────────────────────────────
-- Reversible PII tokenisation map (local only, never sent to cloud LLM).
-- Tokens: IP_1, USER_1, EMAIL_1 … scoped per alert.
CREATE TABLE IF NOT EXISTS pii_mapping (
    token       TEXT    NOT NULL,                  -- e.g. IP_1
    original    TEXT    NOT NULL,                  -- e.g. 192.168.1.45
    kind        TEXT    NOT NULL,                  -- ip | user | email
    alert_id    INTEGER REFERENCES alerts(id) ON DELETE CASCADE,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    PRIMARY KEY (token, alert_id)
);
