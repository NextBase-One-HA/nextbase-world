#!/usr/bin/env python3
"""
Append a structured execution record to canonical/NEXTBASE_EXECUTION_LEDGER.md.

Usage:
  python3 tools/append_execution_ledger.py \
    --action "Verify AI Router endpoint" \
    --target "nextbase-gateway-v1" \
    --owner "NORI-san / TOMORI" \
    --before "endpoint unknown" \
    --after "probe executed" \
    --evidence "tools/probe_ai_router_endpoints.sh output" \
    --result "HOLD" \
    --next-action "restore /gateway or update translate path"
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "canonical" / "NEXTBASE_EXECUTION_LEDGER.md"
VALID_RESULTS = {
    "HOLD",
    "STOP",
    "INVALID",
    "LOCAL_PASS",
    "LIVE_PASS",
    "RELEASE_READY",
    "GO_CANDIDATE",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--action", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--before", required=True)
    parser.add_argument("--after", required=True)
    parser.add_argument("--evidence", required=True)
    parser.add_argument("--result", required=True, choices=sorted(VALID_RESULTS))
    parser.add_argument("--next-action", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not LEDGER.exists():
        raise SystemExit(f"STOP: missing ledger {LEDGER}")

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    entry = f"""

## Execution Record - {now}

```text
DATE: {now}
ACTION: {args.action}
TARGET: {args.target}
OWNER: {args.owner}
BEFORE: {args.before}
AFTER: {args.after}
EVIDENCE: {args.evidence}
RESULT: {args.result}
NEXT_ACTION: {args.next_action}
```
"""
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(entry)
    print(f"LEDGER_APPEND_OK: {LEDGER}")


if __name__ == "__main__":
    main()
