#!/usr/bin/env bash
set -euo pipefail

CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
TARGET="$CONFIG_HOME/autostart/io.matt88.Sentinelux.desktop"
rm -f "$TARGET"
printf 'Sentinelux autostart disabled.\n'
