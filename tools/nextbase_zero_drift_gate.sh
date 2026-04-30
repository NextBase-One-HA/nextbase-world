#!/bin/bash
set -euo pipefail

TASK_TEXT="${1:-}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "STATE: NEXTBASE_ZERO_DRIFT_GATE"
echo "PWD: $(pwd)"
echo "TIME_UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

echo "---- canonical files ----"
test -f canonical/NEXTBASE_IMMUTABLE_CANONICAL.md || { echo "STOP: missing immutable canonical"; exit 1; }
test -f canonical/NEXTBASE_DYNAMIC_CANONICAL.md || { echo "STOP: missing dynamic canonical"; exit 1; }
test -f canonical/NEXTBASE_SELF_OPTIMIZATION_LAYER_V2.md || { echo "STOP: missing self optimization v2"; exit 1; }
test -f canonical/STELLA_LAYER_V1_0_5_ENHANCED.yaml || { echo "STOP: missing STELLA layer"; exit 1; }

echo "OK: canonical files exist"

echo "---- git state ----"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "STOP: not a git repository"; exit 1; }
git branch --show-current || true
git status --short

echo "---- preflight ----"
bash tools/tomori_preflight.sh >/tmp/tomori_preflight.out
cat /tmp/tomori_preflight.out

echo "---- drift detector ----"
if [ -z "$TASK_TEXT" ]; then
  TASK_TEXT="STATE: HOLD
GOAL: Run NextBase zero drift gate
BLOCKER: none
NEXT_ACTION: verify canonical and continue
EVIDENCE: canonical files and git state
IRREVERSIBLE: none
OUTPUT: HOLD"
fi
printf '%s' "$TASK_TEXT" | python3 tools/tomori_drift_detector.py

echo "---- response gate ----"
printf '%s' "$TASK_TEXT" | python3 tools/tomori_response_gate.py

echo "ZERO_DRIFT_GATE_OK"
