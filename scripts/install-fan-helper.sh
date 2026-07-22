#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE="$ROOT_DIR/src/sentinelux/fan_helper.py"
TARGET="/usr/libexec/sentinelux-fan-helper"

sudo install -o root -g root -m 0755 "$SOURCE" "$TARGET"
printf 'Sentinelux fan helper installed at %s\n' "$TARGET"
