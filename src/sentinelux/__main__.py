"""Sentinelux command-line entry point."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import replace

from . import __version__
from .config import AppConfig, config_path, load_config
from .metrics import collect_metrics


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sentinelux",
        description="Tray-first Linux hardware monitor with thermal alerts",
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument(
        "--once",
        action="store_true",
        help="print one JSON metrics snapshot and exit",
    )
    parser.add_argument("--debug", action="store_true", help="enable debug logs")
    parser.add_argument(
        "--no-notifications",
        action="store_true",
        help="disable desktop notifications for this run",
    )
    parser.add_argument(
        "--warning-temp",
        type=float,
        metavar="CELSIUS",
        help="override the warning threshold",
    )
    parser.add_argument(
        "--critical-temp",
        type=float,
        metavar="CELSIUS",
        help="override the critical threshold",
    )
    parser.add_argument(
        "--interval",
        type=float,
        metavar="SECONDS",
        help="override the refresh interval",
    )
    return parser


def apply_overrides(config: AppConfig, args: argparse.Namespace) -> AppConfig:
    updated = replace(
        config,
        warning_temperature_c=(
            args.warning_temp
            if args.warning_temp is not None
            else config.warning_temperature_c
        ),
        critical_temperature_c=(
            args.critical_temp
            if args.critical_temp is not None
            else config.critical_temperature_c
        ),
        refresh_interval_seconds=(
            args.interval
            if args.interval is not None
            else config.refresh_interval_seconds
        ),
    )
    updated.validate()
    return updated


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    try:
        config = apply_overrides(load_config(), args)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))

    if args.debug:
        logging.getLogger(__name__).debug("configuration path=%s", config_path())

    if args.once:
        try:
            metrics = collect_metrics()
        except RuntimeError as exc:
            print(f"sentinelux: {exc}", file=sys.stderr)
            return 2
        print(json.dumps(metrics.to_dict(), indent=2, sort_keys=True))
        return 0

    try:
        from .app import SentineluxApplication

        application = SentineluxApplication(
            config,
            notifications_enabled=not args.no_notifications,
        )
        return application.run()
    except RuntimeError as exc:
        print(f"sentinelux: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
