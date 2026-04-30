#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

LOG_DIR="/tmp/nextbase_forced_read"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/forced_read_$(date -u +%Y%m%dT%H%M%SZ).log"

record_read() {
  local file="$1"
  test -f "$file" || { echo "STOP: missing $file"; exit 1; }
  local hash
  hash="$(sha256sum "$file" | awk '{print $1}')"
  local bytes
  bytes="$(wc -c < "$file")"
  echo "READ file=$file sha256=$hash bytes=$bytes" | tee -a "$LOG_FILE"
  # Force an actual read without dumping canonical contents to stdout.
  cat "$file" >/dev/null
}

echo "STATE: FORCED_CORRECTION_GATE"
echo "TIME_UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
echo "READ_LOG: $LOG_FILE"

echo "---- forced canonical read ----"
record_read canonical/NEXTBASE_IMMUTABLE_CANONICAL.md
record_read canonical/NEXTBASE_DYNAMIC_CANONICAL.md
record_read canonical/NEXTBASE_SELF_OPTIMIZATION_LAYER_V2.md
record_read canonical/STELLA_LAYER_V1_0_5_ENHANCED.yaml
record_read canonical/NEXTBASE_PROOF_MODE_120_CONTEXT.md
record_read canonical/EXTERNAL_FORCED_CORRECTION_LAYER_V1.md
record_read canonical/SOLS_RUNTIME_CONTROL_V1.md
record_read canonical/NEXTBASE_EXECUTION_LEDGER.md

echo "OK: forced canonical read completed with log"

echo "---- drift check ----"
printf '%s' "STATE: HOLD
GOAL: forced correction gate check with SOLS runtime control
BLOCKER: none
NEXT_ACTION: continue after canonical forced read
EVIDENCE: $LOG_FILE
IRREVERSIBLE: none
OUTPUT: HOLD" | python3 tools/tomori_drift_detector.py

echo "---- response gate ----"
printf '%s' "STATE: HOLD
GOAL: forced correction gate check with SOLS runtime control
BLOCKER: none
NEXT_ACTION: continue after canonical forced read
EVIDENCE: $LOG_FILE
IRREVERSIBLE: none
OUTPUT: HOLD" | python3 tools/tomori_response_gate.py

echo "FORCED_CORRECTION_READY"
