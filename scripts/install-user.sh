#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN_HOME="$HOME/.local/bin"
APP_DIR="$DATA_HOME/sentinelux"
APPLICATIONS_DIR="$DATA_HOME/applications"
LAUNCHER="$BIN_HOME/sentinelux"
DESKTOP_FILE="$APPLICATIONS_DIR/io.matt88.Sentinelux.desktop"

mkdir -p "$BIN_HOME" "$APPLICATIONS_DIR"
rm -rf "$APP_DIR.tmp"
mkdir -p "$APP_DIR.tmp"
cp -R "$ROOT_DIR/src" "$APP_DIR.tmp/src"
cp "$ROOT_DIR/README.md" "$ROOT_DIR/LICENSE" "$APP_DIR.tmp/"
rm -rf "$APP_DIR"
mv "$APP_DIR.tmp" "$APP_DIR"

cat > "$LAUNCHER" <<EOF_LAUNCHER
#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$APP_DIR/src\${PYTHONPATH:+:\$PYTHONPATH}"
export SENTINELUX_AUTOSTART_EXEC="$LAUNCHER"
exec python3 -m sentinelux "\$@"
EOF_LAUNCHER
chmod 0755 "$LAUNCHER"

sed "s|@EXEC@|$LAUNCHER|g" \
  "$ROOT_DIR/data/io.matt88.Sentinelux.desktop.in" \
  > "$DESKTOP_FILE"
chmod 0644 "$DESKTOP_FILE"

printf 'Sentinelux installed for %s\n' "$USER"
printf 'Launcher: %s\n' "$LAUNCHER"
printf 'Desktop entry: %s\n' "$DESKTOP_FILE"
case ":$PATH:" in
  *":$BIN_HOME:"*) ;;
  *) printf 'Note: add %s to PATH or run the absolute launcher path.\n' "$BIN_HOME" ;;
esac
