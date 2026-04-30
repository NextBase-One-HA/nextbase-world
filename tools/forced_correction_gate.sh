#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "STATE: FORCED_CORRECTION_GATE"
echo "TIME_UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "---- load canonical ----"
test -f canonical/NEXTBASE_IMMUTABLE_CANONICAL.md || { echo "STOP: missing immutable"; exit 1; }
test -f canonical/NEXTBASE_DYNAMIC_CANONICAL.md || { echo "STOP: missing dynamic"; exit 1; }
test -f canonical/NEXTBASE_SELF_OPTIMIZATION_LAYER_V2.md || { echo "STOP: missing self opt"; exit 1; }
test -f canonical/STELLA_LAYER_V1_0_5_ENHANCED.yaml || { echo "STOP: missing STELLA"; exit 1; }

echo "OK: canonical loaded"

echo "---- drift check ----"
printf '%s' "STATE: HOLD
GOAL: forced correction gate check
BLOCKER: none
NEXT_ACTION: continue
EVIDENCE: canonical load
IRREVERSIBLE: none
OUTPUT: HOLD" | python3 tools/tomori_drift_detector.py

echo "---- response gate ----"
printf '%s' "STATE: HOLD
GOAL: forced correction gate check
BLOCKER: none
NEXT_ACTION: continue
EVIDENCE: canonical load
IRREVERSIBLE: none
OUTPUT: HOLD" | python3 tools/tomori_response_gate.py

echo "FORCED_CORRECTION_READY"
