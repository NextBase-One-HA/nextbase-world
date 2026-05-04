#!/usr/bin/env bash
# Run from repo root:  bash billing_api/cloudshell-git-fix.sh
# Removes manual canonical copies and local Dockerfile edits so `git pull` can merge.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
rm -rf billing_api/canonical
git checkout -- billing_api/Dockerfile 2>/dev/null || true
git pull
echo "OK: billing_api/canonical is now from git (no manual cp needed for deploy)."
