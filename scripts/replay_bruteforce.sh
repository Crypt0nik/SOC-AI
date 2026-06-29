#!/usr/bin/env bash
# scripts/replay_bruteforce.sh
# ─────────────────────────────────────────────────────────────
# Inject a synthetic SSH brute-force into the watched log directory.
# Triggers rule SSH-001 (>5 failures in 60s) → engine → llm_agent → triage.
#
# Usage:
#   bash scripts/replay_bruteforce.sh [TARGET_LOG_DIR]
#
# Default TARGET_LOG_DIR: ./sample_logs (for local dev without Docker).
# Inside Docker: mount point is /logs — set TARGET_LOG_DIR=/logs.
# ─────────────────────────────────────────────────────────────

set -euo pipefail

TARGET_DIR="${1:-./sample_logs}"
LOG_FILE="$TARGET_DIR/auth.log"
ATTACKER_IP="192.168.100.99"

echo "🔵  SOC-AI — SSH Brute-Force Replay"
echo "   Target log : $LOG_FILE"
echo "   Attacker IP: $ATTACKER_IP"
echo ""

mkdir -p "$TARGET_DIR"

NOW=$(date -u +"%b %d %H:%M:%S")
HOST="webserver"

inject() {
    local user="$1"
    local port="$2"
    echo "$NOW $HOST sshd[$$]: Failed password for invalid user $user from $ATTACKER_IP port $port ssh2" >> "$LOG_FILE"
    echo "   → injected: Failed password for $user from $ATTACKER_IP"
    sleep 0.5
}

echo "⚡  Injecting 8 failed SSH attempts (triggers SSH-001 threshold of 5)..."
inject "admin"  55100
inject "root"   55101
inject "deploy" 55102
inject "ubuntu" 55103
inject "pi"     55104
inject "test"   55105
inject "guest"  55106
inject "oracle" 55107

echo ""
echo "✅  Done. Check alerts within ~10s:"
echo "   curl http://localhost:8000/alerts | jq ."
echo ""
echo "📊  Or open the dashboard: http://localhost:3000"
