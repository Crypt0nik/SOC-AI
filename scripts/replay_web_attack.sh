#!/usr/bin/env bash
# scripts/replay_web_attack.sh
# ─────────────────────────────────────────────────────────────
# Simulate a web attack chain: reconnaissance scanner → SQL injection
# → path traversal. Triggers WEB-001, WEB-002, WEB-003.
#
# Usage:
#   bash scripts/replay_web_attack.sh [TARGET_LOG_DIR]
# ─────────────────────────────────────────────────────────────

set -euo pipefail

TARGET_DIR="${1:-./sample_logs}"
LOG_FILE="$TARGET_DIR/access.log"
ATTACKER="198.51.100.42"

echo "🔵  SOC-AI — Web Attack Replay"
echo "   Target log : $LOG_FILE"
echo "   Attacker IP: $ATTACKER"
echo ""

mkdir -p "$TARGET_DIR"

ts() { date -u +"%d/%b/%Y:%H:%M:%S +0000"; }

inject() {
    local method="$1" path="$2" status="$3" ua="$4"
    local line="$ATTACKER - - [$(ts)] \"$method $path HTTP/1.1\" $status 1024 \"-\" \"$ua\""
    echo "$line" >> "$LOG_FILE"
    echo "   → $method $path  [$status]"
    sleep 0.3
}

echo "🔍  Phase 1 — Reconnaissance with nikto scanner (WEB-003)..."
inject "GET" "/" 200 "Mozilla/5.0 (nikto/2.1.6)"
inject "GET" "/admin" 403 "nikto/2.1.6"
inject "GET" "/phpinfo.php" 404 "nikto/2.1.6"
inject "GET" "/.env" 404 "nikto/2.1.6"
echo ""

echo "💉  Phase 2 — SQL Injection attempts (WEB-001)..."
inject "GET" "/login?user=admin'%20OR%20'1'='1&pass=x" 200 "python-requests/2.31"
inject "GET" "/search?q=1'%20UNION%20SELECT%20*%20FROM%20users--" 500 "python-requests/2.31"
inject "POST" "/api/users?id=1;DROP%20TABLE%20sessions--" 400 "python-requests/2.31"
inject "GET" "/products?cat=1%20AND%20information_schema.tables" 200 "sqlmap/1.7"
echo ""

echo "📁  Phase 3 — Path Traversal attempts (WEB-002)..."
inject "GET" "/download?file=../../../etc/passwd" 403 "curl/7.88.1"
inject "GET" "/static/%2e%2e%2f%2e%2e%2fetc%2fshadow" 403 "curl/7.88.1"
inject "GET" "/img/..%2f..%2f..%2fvar%2fwww%2f.env" 404 "curl/7.88.1"
echo ""

echo "✅  Done — 11 events injected. Check alerts within ~10s:"
echo "   curl http://localhost:8000/alerts | jq ."
echo "   open http://localhost:3000"
