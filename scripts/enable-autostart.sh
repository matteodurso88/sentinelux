#!/usr/bin/env bash
set -euo pipefail

DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
SOURCE="$DATA_HOME/applications/io.matt88.Sentinelux.desktop"
TARGET_DIR="$CONFIG_HOME/autostart"
TARGET="$TARGET_DIR/io.matt88.Sentinelux.desktop"

if [[ ! -f "$SOURCE" ]]; then
  printf 'Desktop entry not found: %s\n' "$SOURCE" >&2
  printf 'Run scripts/install-user.sh first.\n' >&2
  exit 1
fi

mkdir -p "$TARGET_DIR"
cp "$SOURCE" "$TARGET"
printf 'Sentinelux autostart enabled: %s\n' "$TARGET"
