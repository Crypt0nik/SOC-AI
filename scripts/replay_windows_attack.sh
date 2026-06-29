#!/usr/bin/env bash
# scripts/replay_windows_attack.sh
# ─────────────────────────────────────────────────────────────
# Simulate a Windows post-exploitation sequence:
#   1. Privilege escalation via special privileges (Event 4672) → WIN-001 CRITICAL
#   2. New local account created (Event 4720)         → WIN-002
#   3. SAM registry hive access / credential dump     → WIN-003 CRITICAL
#
# Usage:
#   bash scripts/replay_windows_attack.sh [TARGET_LOG_DIR]
# ─────────────────────────────────────────────────────────────

set -euo pipefail

TARGET_DIR="${1:-./sample_logs}"
LOG_FILE="$TARGET_DIR/security.xml"
COMPUTER="WORKSTATION-7B"

echo "🔵  SOC-AI — Windows Post-Exploitation Replay"
echo "   Target log : $LOG_FILE"
echo "   Host       : $COMPUTER"
echo ""

mkdir -p "$TARGET_DIR"

NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "🔐  Event 4672 — Special privileges assigned (WIN-001 CRITICAL)..."
cat >> "$LOG_FILE" << EOF
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <EventID>4672</EventID>
    <TimeCreated SystemTime="$NOW"/>
    <Computer>$COMPUTER</Computer>
  </System>
  <EventData>
    <Data Name="SubjectUserName">svc_backup</Data>
    <Data Name="SubjectDomainName">CORP</Data>
    <Data Name="PrivilegeList">SeDebugPrivilege SeImpersonatePrivilege SeTcbPrivilege</Data>
  </EventData>
</Event>
EOF
echo "   → SeDebugPrivilege + SeImpersonatePrivilege assigned to svc_backup"
sleep 1

echo ""
echo "👤  Event 4720 — New user account created (WIN-002)..."
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cat >> "$LOG_FILE" << EOF
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <EventID>4720</EventID>
    <TimeCreated SystemTime="$NOW"/>
    <Computer>$COMPUTER</Computer>
  </System>
  <EventData>
    <Data Name="TargetUserName">backdoor_user</Data>
    <Data Name="SubjectUserName">svc_backup</Data>
    <Data Name="SubjectDomainName">CORP</Data>
  </EventData>
</Event>
EOF
echo "   → backdoor_user account created by svc_backup"
sleep 1

echo ""
echo "🗝️   Event 4657 — SAM registry hive access (WIN-003 CRITICAL)..."
NOW=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
cat >> "$LOG_FILE" << EOF
<Event xmlns="http://schemas.microsoft.com/win/2004/08/events/event">
  <System>
    <EventID>4657</EventID>
    <TimeCreated SystemTime="$NOW"/>
    <Computer>$COMPUTER</Computer>
  </System>
  <EventData>
    <Data Name="SubjectUserName">svc_backup</Data>
    <Data Name="ObjectName">\REGISTRY\MACHINE\SECURITY\SAM</Data>
    <Data Name="ObjectValueName">SAM</Data>
    <Data Name="OperationType">%%1904</Data>
  </EventData>
</Event>
EOF
echo "   → SAM hive accessed — credential dump in progress"
echo ""

echo "✅  Done — 3 Windows events injected (2x CRITICAL). Check alerts within ~10s:"
echo "   curl http://localhost:8000/alerts | jq ."
echo "   open http://localhost:3000"
