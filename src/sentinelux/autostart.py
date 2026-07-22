"""XDG autostart management for Sentinelux."""

from __future__ import annotations

import os
import shutil
from pathlib import Path


DESKTOP_FILENAME = "io.matt88.Sentinelux.desktop"


class AutostartError(RuntimeError):
    """Raised when the autostart entry cannot be created."""


def autostart_path() -> Path:
    """Return the XDG autostart desktop-entry path."""

    config_home = Path(
        os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    )
    return config_home / "autostart" / DESKTOP_FILENAME


def is_autostart_enabled(path: Path | None = None) -> bool:
    """Return whether the Sentinelux autostart entry currently exists."""

    return (path or autostart_path()).is_file()


def _resolve_executable() -> Path:
    explicit = os.environ.get("SENTINELUX_AUTOSTART_EXEC")
    candidates = [
        explicit,
        shutil.which("sentinelux"),
        str(Path.home() / ".local" / "bin" / "sentinelux"),
    ]

    for raw_candidate in candidates:
        if not raw_candidate:
            continue
        candidate = Path(raw_candidate).expanduser().resolve()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate

    raise AutostartError(
        "Nessun launcher Sentinelux eseguibile trovato. "
        "Avvia l'app dal repository oppure esegui scripts/install-user.sh."
    )


def _desktop_exec(path: Path) -> str:
    escaped = str(path).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def desktop_entry(executable: Path) -> str:
    """Build the desktop-entry content for the selected launcher."""

    return (
        "[Desktop Entry]\n"
        "Type=Application\n"
        "Name=Sentinelux\n"
        "Comment=Linux hardware monitor with thermal alerts\n"
        f"Exec={_desktop_exec(executable)}\n"
        "Icon=utilities-system-monitor\n"
        "Terminal=false\n"
        "Categories=System;Monitor;\n"
        "StartupNotify=false\n"
        "X-GNOME-Autostart-enabled=true\n"
    )


def set_autostart_enabled(
    enabled: bool,
    *,
    path: Path | None = None,
    executable: Path | None = None,
) -> Path:
    """Enable or disable autostart and return the managed desktop-entry path."""

    target = path or autostart_path()
    if not enabled:
        target.unlink(missing_ok=True)
        return target

    launcher = executable.expanduser().resolve() if executable else _resolve_executable()
    if not launcher.is_file() or not os.access(launcher, os.X_OK):
        raise AutostartError(f"Launcher non eseguibile: {launcher}")

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".desktop.tmp")
    temporary.write_text(desktop_entry(launcher), encoding="utf-8")
    temporary.replace(target)
    return target
