#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="$ROOT_DIR/src${PYTHONPATH:+:$PYTHONPATH}"
export SENTINELUX_AUTOSTART_EXEC="$ROOT_DIR/scripts/run-dev.sh"
exec python3 -m sentinelux "$@"
