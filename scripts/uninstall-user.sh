#!/usr/bin/env bash
set -euo pipefail

DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"

rm -rf "$DATA_HOME/sentinelux"
rm -f "$HOME/.local/bin/sentinelux"
rm -f "$DATA_HOME/applications/io.matt88.Sentinelux.desktop"
rm -f "$CONFIG_HOME/autostart/io.matt88.Sentinelux.desktop"

printf 'Sentinelux user installation removed.\n'
printf 'Configuration retained at %s/sentinelux\n' "$CONFIG_HOME"
