"""GTK tray application for Sentinelux."""

from __future__ import annotations

import logging
import time
from typing import Any

from . import __version__
from .alerts import AlertEvent, AlertKind, ThermalAlertController, ThermalState
from .config import AppConfig
from .fans import FanControlError, FanManager, format_fan_channel
from .metrics import (
    SystemMetrics,
    TemperatureReading,
    collect_metrics,
    human_bytes,
)
from .presentation import (
    format_memory_summary,
    format_percentage,
    format_temperature,
    sensor_display_name,
    thermal_state_presentation,
)
from .protection import (
    ProtectionEvent,
    ProtectionEventKind,
    ThermalProtectionController,
    request_sleep_action,
)
from .settings import SettingsWindow

LOGGER = logging.getLogger(__name__)


def _load_gi() -> tuple[Any, Any, Any, Any]:
    try:
        import gi
    except ImportError as exc:
        raise RuntimeError(
            "PyGObject is required; run scripts/install-deps-debian.sh"
        ) from exc

    gi.require_version("Gtk", "3.0")
    gi.require_version("Notify", "0.7")

    indicator_module: Any
    try:
        gi.require_version("AyatanaAppIndicator3", "0.1")
        from gi.repository import AyatanaAppIndicator3 as indicator_module
    except (ValueError, ImportError):
        try:
            gi.require_version("AppIndicator3", "0.1")
            from gi.repository import AppIndicator3 as indicator_module
        except (ValueError, ImportError) as exc:
            raise RuntimeError(
                "Ayatana AppIndicator is required; run "
                "scripts/install-deps-debian.sh"
            ) from exc

    from gi.repository import GLib, Gtk, Notify

    return Gtk, GLib, Notify, indicator_module


class SentineluxApplication:
    def __init__(self, config: AppConfig, notifications_enabled: bool = True) -> None:
        self.Gtk, self.GLib, self.Notify, self.AppIndicator = _load_gi()
        self.config = config
        self.runtime_notifications_allowed = notifications_enabled
        self.notifications_paused = False
        self.settings_window: SettingsWindow | None = None
        self.timeout_source_id: int | None = None
        self.running = False

        self.alerts = self._new_alert_controller(config)
        self.protection = self._new_protection_controller(config)
        self.fans = FanManager()

        self.indicator = self.AppIndicator.Indicator.new(
            "sentinelux",
            "utilities-system-monitor",
            self.AppIndicator.IndicatorCategory.SYSTEM_SERVICES,
        )
        self.indicator.set_status(self.AppIndicator.IndicatorStatus.ACTIVE)
        try:
            self.indicator.set_title("Sentinelux")
        except AttributeError:
            pass

        self.menu = self.Gtk.Menu()
        self._build_menu()
        self.menu.show_all()
        self.indicator.set_menu(self.menu)

        if self.runtime_notifications_allowed:
            self.Notify.init("Sentinelux")

    def _new_alert_controller(self, config: AppConfig) -> ThermalAlertController:
        return ThermalAlertController(
            warning_c=config.warning_temperature_c,
            critical_c=config.critical_temperature_c,
            hysteresis_c=config.recovery_hysteresis_c,
            reminder_seconds=config.reminder_interval_seconds,
        )

    def _new_protection_controller(
        self,
        config: AppConfig,
    ) -> ThermalProtectionController:
        return ThermalProtectionController(
            enabled=config.thermal_protection_enabled,
            threshold_c=config.thermal_protection_temperature_c,
            persistence_seconds=config.thermal_protection_persistence_seconds,
            recovery_hysteresis_c=(
                config.thermal_protection_recovery_hysteresis_c
            ),
            action=config.thermal_protection_action,
        )

    def _build_menu(self) -> None:
        self.sensor_signature: tuple[tuple[str, str], ...] | None = None
        self.sensor_rows: list[Any] = []
        self.fan_signature: tuple[str, ...] | None = None
        self.fan_rows: list[Any] = []

        self.header_item = self._info_item(
            f"🛡 Sentinelux v{__version__} · inizializzazione"
        )
        self.menu.append(self.header_item)
        self.menu.append(self.Gtk.SeparatorMenuItem())

        self.cpu_item = self._info_item("⚙ CPU · —")
        self.memory_item = self._info_item("▣ RAM · —")
        self.swap_item = self._info_item("▤ Swap · —")
        for item in (self.cpu_item, self.memory_item, self.swap_item):
            self.menu.append(item)

        self.menu.append(self.Gtk.SeparatorMenuItem())
        self.sensor_anchor = self.Gtk.SeparatorMenuItem()
        self.menu.append(self.sensor_anchor)
        self.fan_anchor = self.Gtk.SeparatorMenuItem()
        self.menu.append(self.fan_anchor)

        self.pause_item = self.Gtk.CheckMenuItem(label="🔔 Sospendi avvisi")
        self.pause_item.connect("toggled", self._on_pause_toggled)
        self.menu.append(self.pause_item)

        preferences_item = self.Gtk.MenuItem(label="⚙ Preferenze…")
        preferences_item.connect("activate", self._open_settings)
        self.menu.append(preferences_item)

        refresh_item = self.Gtk.MenuItem(label="↻ Aggiorna ora")
        refresh_item.connect("activate", lambda *_: self._refresh())
        self.menu.append(refresh_item)

        self.menu.append(self.Gtk.SeparatorMenuItem())

        quit_item = self.Gtk.MenuItem(label="⏻ Esci")
        quit_item.connect("activate", self._quit)
        self.menu.append(quit_item)

        self._update_sensor_rows(())
        self._update_fan_rows(())
        self._sync_notification_controls()

    def _info_item(self, label: str) -> Any:
        item = self.Gtk.MenuItem(label=label)
        item.set_sensitive(False)
        return item

    def _set_indicator_label(self, metrics: SystemMetrics) -> None:
        if metrics.cpu_temperature_c is not None:
            text = f"{metrics.cpu_temperature_c:.0f}°C"
            guide = "100°C"
        else:
            text = f"CPU {metrics.cpu_percent:.0f}%"
            guide = "CPU 100%"
        try:
            self.indicator.set_label(text, guide)
        except (AttributeError, TypeError):
            LOGGER.debug("indicator implementation does not support labels")

    def _set_indicator_icon(self) -> None:
        icons = {
            ThermalState.NORMAL: "utilities-system-monitor",
            ThermalState.WARNING: "dialog-warning",
            ThermalState.CRITICAL: "dialog-error",
        }
        icon = icons[self.alerts.state]
        try:
            self.indicator.set_icon_full(icon, "Sentinelux")
        except AttributeError:
            try:
                self.indicator.set_icon(icon)
            except AttributeError:
                LOGGER.debug("indicator implementation does not support icon updates")

    def _notify(self, event: AlertEvent, metrics: SystemMetrics) -> None:
        if not self.runtime_notifications_allowed or self.notifications_paused:
            return
        if not self.config.alert_enabled(event.kind.value):
            return

        temperature = f"{event.temperature_c:.1f} °C"
        sensor = metrics.temperature_label or "sensore CPU"
        if event.kind is AlertKind.CRITICAL:
            title = "Sentinelux: temperatura CPU critica"
            body = (
                f"{sensor} ha raggiunto {temperature}. "
                "Riduci subito il carico e controlla la ventilazione."
            )
            urgency = self.Notify.Urgency.CRITICAL
        elif event.kind is AlertKind.WARNING:
            title = "Sentinelux: temperatura CPU elevata"
            body = f"{sensor} ha raggiunto {temperature}. Controlla carico e ventilazione."
            urgency = self.Notify.Urgency.NORMAL
        elif event.kind is AlertKind.REMINDER:
            title = "Sentinelux: temperatura ancora elevata"
            body = f"Il sensore più caldo ({sensor}) è ancora a {temperature}."
            urgency = (
                self.Notify.Urgency.CRITICAL
                if event.current_state is ThermalState.CRITICAL
                else self.Notify.Urgency.NORMAL
            )
        else:
            title = "Sentinelux: temperatura rientrata"
            body = f"Il sensore più caldo è sceso a {temperature}."
            urgency = self.Notify.Urgency.LOW

        notification = self.Notify.Notification.new(
            title,
            body,
            "utilities-system-monitor",
        )
        notification.set_urgency(urgency)
        try:
            notification.show()
        except Exception:
            LOGGER.exception("desktop notification failed")

    def _refresh(self) -> bool:
        try:
            metrics = collect_metrics()
        except Exception:
            LOGGER.exception("metrics refresh failed")
            self.header_item.set_label(f"🛡 Sentinelux v{__version__} · ❌ errore metriche")
            return True

        event = self.alerts.evaluate(
            metrics.cpu_temperature_c,
            time.monotonic(),
        )
        if event is not None:
            self._notify(event, metrics)

        protection_event = self.protection.evaluate(
            metrics.cpu_temperature_c,
            time.monotonic(),
        )
        if protection_event is not None:
            self._handle_protection_event(protection_event, metrics)

        state_label, _state_colour = thermal_state_presentation(self.alerts.state)
        state_icon = {
            ThermalState.NORMAL: "🟢",
            ThermalState.WARNING: "🟠",
            ThermalState.CRITICAL: "🔴",
        }[self.alerts.state]
        hottest = format_temperature(metrics.cpu_temperature_c)
        self.header_item.set_label(
            f"🛡 Sentinelux v{__version__} · {state_icon} {state_label} · {hottest}"
        )
        self.cpu_item.set_label(
            f"⚙ CPU · {format_percentage(metrics.cpu_percent)}"
        )
        self.memory_item.set_label(
            "▣ RAM · "
            + format_memory_summary(
                metrics.memory_percent,
                metrics.memory_unavailable_bytes,
                metrics.memory_total_bytes,
                metrics.memory_available_bytes,
            )
        )
        self.swap_item.set_label(
            f"▤ Swap · {format_percentage(metrics.swap_percent)} · "
            f"{human_bytes(metrics.swap_used_bytes)} / "
            f"{human_bytes(metrics.swap_total_bytes)}"
        )

        self._update_sensor_rows(metrics.temperature_readings)
        self._update_fan_rows(self.fans.refresh())
        self._set_indicator_label(metrics)
        self._set_indicator_icon()

        LOGGER.debug("metrics=%s", metrics.to_dict())
        return True


    def _handle_protection_event(
        self,
        event: ProtectionEvent,
        metrics: SystemMetrics,
    ) -> None:
        action_name = (
            "ibernazione" if event.action == "hibernate" else "sospensione"
        )
        temperature = f"{event.temperature_c:.1f} °C"
        sensor = metrics.temperature_label or "sensore CPU"

        if event.kind is ProtectionEventKind.ARMED:
            self._show_protection_notification(
                "Sentinelux: protezione termica armata",
                (
                    f"{sensor} è a {temperature}. {action_name.capitalize()} tra "
                    f"{event.persistence_seconds:.0f} secondi se la temperatura "
                    "resta oltre soglia."
                ),
                critical=True,
            )
            return

        if event.kind is ProtectionEventKind.CANCELLED:
            self._show_protection_notification(
                "Sentinelux: azione termica annullata",
                f"La temperatura è rientrata a {temperature}.",
                critical=False,
            )
            return

        self._show_protection_notification(
            f"Sentinelux: avvio {action_name}",
            (
                f"Temperatura persistente a {temperature}. "
                "Richiesta di protezione inviata a systemd-logind."
            ),
            critical=True,
        )
        try:
            request_sleep_action(event.action)
        except (RuntimeError, ValueError) as exc:
            LOGGER.exception("thermal protection action failed")
            self._show_protection_notification(
                "Sentinelux: protezione termica non eseguita",
                str(exc),
                critical=True,
            )

    def _show_protection_notification(
        self,
        title: str,
        body: str,
        *,
        critical: bool,
    ) -> None:
        if not self.runtime_notifications_allowed:
            return
        notification = self.Notify.Notification.new(
            title,
            body,
            "dialog-warning" if critical else "utilities-system-monitor",
        )
        notification.set_urgency(
            self.Notify.Urgency.CRITICAL
            if critical
            else self.Notify.Urgency.LOW
        )
        try:
            notification.show()
        except Exception:
            LOGGER.exception("thermal protection notification failed")

    def _update_sensor_rows(
        self,
        readings: tuple[TemperatureReading, ...],
    ) -> None:
        signature = tuple((reading.source, reading.label) for reading in readings)
        if signature != self.sensor_signature:
            for item in self.sensor_rows:
                self.menu.remove(item)
            self.sensor_rows.clear()

            anchor_index = self.menu.get_children().index(self.sensor_anchor)
            row_count = len(readings) if readings else 1
            for offset in range(row_count):
                item = self._info_item("🌡 Temperatura CPU · non disponibile")
                self.menu.insert(item, anchor_index + offset)
                self.sensor_rows.append(item)

            self.sensor_signature = signature
            self.menu.show_all()

        if readings:
            for item, reading in zip(self.sensor_rows, readings):
                item.set_label(
                    f"🌡 {sensor_display_name(reading.label)} · "
                    f"{format_temperature(reading.value_c)}"
                )
                item.set_tooltip_text(f"Sorgente: {reading.source}")
        else:
            self.sensor_rows[0].set_label("🌡 Temperatura CPU · non disponibile")
            self.sensor_rows[0].set_tooltip_text(None)

    def _update_fan_rows(self, channels: tuple[Any, ...]) -> None:
        signature = tuple(channel.identifier for channel in channels)
        if signature != self.fan_signature:
            for item in self.fan_rows:
                self.menu.remove(item)
            self.fan_rows.clear()

            anchor_index = self.menu.get_children().index(self.fan_anchor)
            row_count = len(channels) if channels else 1
            for offset in range(row_count):
                item = self._info_item("🌀 Ventole · non esposte")
                self.menu.insert(item, anchor_index + offset)
                self.fan_rows.append(item)

            self.fan_signature = signature
            self.menu.show_all()

        if channels:
            for item, channel in zip(self.fan_rows, channels):
                item.set_label(f"🌀 {format_fan_channel(channel)}")
                item.set_tooltip_text(f"Controller: {channel.chip}")
        else:
            self.fan_rows[0].set_label("🌀 Ventole · non esposte")
            self.fan_rows[0].set_tooltip_text(None)

    def _on_pause_toggled(self, item: Any) -> None:
        self.notifications_paused = bool(item.get_active())
        item.set_label(
            "🔕 Avvisi sospesi"
            if self.notifications_paused
            else "🔔 Sospendi avvisi"
        )
        LOGGER.info("notifications paused=%s", self.notifications_paused)

    def _open_settings(self, *_: Any) -> None:
        if self.settings_window is None:
            self.settings_window = SettingsWindow(
                self.Gtk,
                self.config,
                self._apply_config,
                self.fans,
            )
        else:
            self.settings_window.load_config(self.config)
        self.settings_window.present()

    def _apply_config(self, config: AppConfig) -> None:
        self.config = config
        self.alerts = self._new_alert_controller(config)
        self.protection = self._new_protection_controller(config)
        self.fans = FanManager()
        self._sync_notification_controls()
        if self.running:
            self._schedule_refresh()
        self._refresh()
        LOGGER.info("configuration updated")

    def _sync_notification_controls(self) -> None:
        enabled = self.runtime_notifications_allowed and self.config.notifications_enabled
        self.pause_item.set_sensitive(enabled)
        if not enabled and self.pause_item.get_active():
            self.pause_item.set_active(False)

    def _quit(self, *_: Any) -> None:
        try:
            self.fans.restore_original()
        except FanControlError:
            LOGGER.exception("cannot restore original fan state during exit")
        self.Gtk.main_quit()

    def _schedule_refresh(self) -> None:
        if self.timeout_source_id is not None:
            self.GLib.source_remove(self.timeout_source_id)
        interval_ms = max(500, int(self.config.refresh_interval_seconds * 1000))
        self.timeout_source_id = self.GLib.timeout_add(interval_ms, self._refresh)

    def run(self) -> int:
        self.running = True
        try:
            self._refresh()
            self._schedule_refresh()
            self.Gtk.main()
        finally:
            self.running = False
            try:
                self.fans.restore_original()
            except FanControlError:
                LOGGER.exception("cannot restore original fan state")
            if self.runtime_notifications_allowed:
                self.Notify.uninit()
        return 0
