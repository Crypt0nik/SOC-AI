#!/usr/bin/env bash
# scripts/replay_full_scenario.sh
# ─────────────────────────────────────────────────────────────
# Full APT-style attack scenario — runs all attack vectors in sequence:
#
#   Phase 1 — External reconnaissance (web scanner)
#   Phase 2 — SSH brute force + root login
#   Phase 3 — Web exploitation (SQLi + path traversal)
#   Phase 4 — Windows post-exploitation (privesc + credential dump)
#
# Triggers: WEB-003, SSH-001, SSH-002, SSH-003, WEB-001, WEB-002,
#           WIN-001 (CRITICAL), WIN-002, WIN-003 (CRITICAL)
#
# Usage:
#   bash scripts/replay_full_scenario.sh [TARGET_LOG_DIR]
# ─────────────────────────────────────────────────────────────

set -euo pipefail

TARGET_DIR="${1:-./sample_logs}"
SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "╔══════════════════════════════════════════════════════════╗"
echo "║       SOC-AI — Full APT Scenario Demo                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "Target log dir : $TARGET_DIR"
echo "This will inject ~25 events across 4 attack phases."
echo ""

mkdir -p "$TARGET_DIR"

# ── Phase 1 — SSH Brute Force ───────────────────────────────
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PHASE 1/4 — SSH Brute Force (SSH-001)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash "$SCRIPTS_DIR/replay_bruteforce.sh" "$TARGET_DIR"

echo ""
echo "⏳  Waiting 5s before next phase..."
sleep 5

# ── Phase 2 — SSH Root Login + External IP ─────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PHASE 2/4 — SSH Lateral Movement (SSH-002 + SSH-003)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

LOG_SSH="$TARGET_DIR/auth.log"
NOW=$(date -u +"%b %d %H:%M:%S")

echo "   → Root login from internal pivot"
echo "$NOW prod-server sshd[2001]: Accepted password for root from 10.0.0.55 port 44444 ssh2" >> "$LOG_SSH"
sleep 0.5

echo "   → External IP login (C2 callback)"
echo "$NOW prod-server sshd[2002]: Accepted password for deploy from 203.0.113.77 port 55555 ssh2" >> "$LOG_SSH"
sleep 0.5

echo "   → Second external connection"
echo "$NOW prod-server sshd[2003]: Accepted password for admin from 198.51.100.10 port 33333 ssh2" >> "$LOG_SSH"
echo ""

echo "⏳  Waiting 5s before next phase..."
sleep 5

# ── Phase 3 — Web Exploitation ─────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PHASE 3/4 — Web Exploitation (WEB-001/002/003)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash "$SCRIPTS_DIR/replay_web_attack.sh" "$TARGET_DIR"

echo ""
echo "⏳  Waiting 5s before next phase..."
sleep 5

# ── Phase 4 — Windows Post-Exploitation ────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  PHASE 4/4 — Windows Post-Exploitation (WIN-001/002/003)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
bash "$SCRIPTS_DIR/replay_windows_attack.sh" "$TARGET_DIR"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Scenario complete — ~25 events across 4 attack phases  ║"
echo "║                                                          ║"
echo "║  Expected alerts:                                        ║"
echo "║    CRITICAL  WIN-001 Privilege Escalation                ║"
echo "║    CRITICAL  WIN-003 SAM Credential Dump                 ║"
echo "║    HIGH      SSH-001 Brute Force                         ║"
echo "║    HIGH      SSH-002 Root Login                          ║"
echo "║    HIGH      WEB-001 SQL Injection                       ║"
echo "║    MEDIUM    SSH-003 External IP Login                   ║"
echo "║    MEDIUM    WEB-002 Path Traversal                      ║"
echo "║    LOW       WEB-003 Scanner Detected                    ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "   curl http://localhost:8000/alerts | jq ."
echo "   open http://localhost:3000"
