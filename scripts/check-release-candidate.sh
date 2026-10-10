#!/usr/bin/env bash
# Read-only source validation gate: execute on the local Dell workstation.
# Run via: bash scripts/check-release-candidate.sh
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

EXPECTED_BRANCH="work/first-prerelease-v0.1.0-alpha.1"
BRANCH="$(git branch --show-current)"
if [[ "$BRANCH" != "$EXPECTED_BRANCH" ]]; then
  printf 'ERROR: expected branch %s; got %s\n' "$EXPECTED_BRANCH" "$BRANCH" >&2
  exit 2
fi
if [[ -n "$(git status --porcelain)" ]]; then
  printf 'ERROR: working tree is not clean. Review git status --short.\n' >&2
  git status --short
  exit 2
fi

printf 'Candidate branch: %s\n' "$BRANCH"
printf 'Candidate SHA: %s\n' "$(git rev-parse HEAD)"
printf 'Local time: %s\n' "$(date --iso-8601=seconds)"
printf '\n[1/5] Unit tests\n'
PYTHONPATH=src python3 -m unittest discover -s tests -v

printf '\n[2/5] Byte compilation\n'
PYTHONPATH=src python3 -m compileall -q src tests

printf '\n[3/5] CLI version contract\n'
ACTUAL_VERSION="$(PYTHONPATH=src python3 -m sentinelux --version)"
if [[ "$ACTUAL_VERSION" != "0.1.0a1" ]]; then
  printf 'ERROR: CLI returned unexpected version: %s\n' "$ACTUAL_VERSION" >&2
  exit 2
fi
printf 'Version: %s\n' "$ACTUAL_VERSION"

printf '\n[4/5] JSON snapshot (no GUI)\n'
PYTHONPATH=src python3 -m sentinelux --once |
  python3 -c 'import json,sys; data=json.load(sys.stdin); assert isinstance(data,dict) and bool(data); print("JSON snapshot valid")'

printf '\n[5/5] Commit whitespace check against origin/main\n'
git diff --check origin/main...HEAD

printf '\nSOURCE GATE PASS (GUI/install/sensor/alerts smoke still required)\n'
printf 'Validated commit: %s\n' "$(git rev-parse HEAD)"
