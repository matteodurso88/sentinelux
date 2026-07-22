"""GTK tray application for Sentinelux."""

from __future__ import annotations

import logging
import time
from typing import Any

from . import __version__
from .alerts import AlertEvent, AlertKind, ThermalAlertController, ThermalState
from .config import AppConfig
from .metrics import SystemMetrics, collect_metrics, human_bytes
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

    def _build_menu(self) -> None:
        self.header_item, self.header_label = self._markup_item(
            f"<b>Sentinelux</b>  <span size='small'>v{__version__}</span>\n"
            "<span size='small'>Monitoraggio locale del sistema</span>"
        )
        self.menu.append(self.header_item)
        self.menu.append(self.Gtk.SeparatorMenuItem())

        self.menu.append(self._section_item("RISORSE"))
        self.cpu_item, self.cpu_value = self._value_item("Carico CPU")
        self.memory_item, self.memory_value = self._value_item("Memoria RAM")
        self.swap_item, self.swap_value = self._value_item("Swap")
        for item in (self.cpu_item, self.memory_item, self.swap_item):
            self.menu.append(item)

        self.menu.append(self.Gtk.SeparatorMenuItem())
        self.menu.append(self._section_item("TEMPERATURE CPU"))
        self.temperature_item, self.temperature_value = self._value_item("Massima / media")
        self.state_item, self.state_label = self._markup_item("<b>Stato:</b> —")
        self.sensor_detail_item = self.Gtk.MenuItem(label="Dettaglio package e core")
        self.sensor_submenu = self.Gtk.Menu()
        self.sensor_detail_item.set_submenu(self.sensor_submenu)
        self.menu.append(self.temperature_item)
        self.menu.append(self.state_item)
        self.menu.append(self.sensor_detail_item)

        self.menu.append(self.Gtk.SeparatorMenuItem())

        self.pause_item = self.Gtk.CheckMenuItem(label="Pausa notifiche")
        self.pause_item.connect("toggled", self._on_pause_toggled)
        self.menu.append(self.pause_item)

        preferences_item = self.Gtk.MenuItem(label="Preferenze…")
        preferences_item.connect("activate", self._open_settings)
        self.menu.append(preferences_item)

        refresh_item = self.Gtk.MenuItem(label="Aggiorna ora")
        refresh_item.connect("activate", lambda *_: self._refresh())
        self.menu.append(refresh_item)

        self.menu.append(self.Gtk.SeparatorMenuItem())

        quit_item = self.Gtk.MenuItem(label="Esci")
        quit_item.connect("activate", lambda *_: self.Gtk.main_quit())
        self.menu.append(quit_item)

        self._sync_notification_controls()

    def _section_item(self, text: str) -> Any:
        item, _label = self._markup_item(
            f"<span size='small' weight='bold'>{text}</span>"
        )
        item.set_sensitive(False)
        return item

    def _markup_item(self, markup: str) -> tuple[Any, Any]:
        item = self.Gtk.MenuItem()
        label = self.Gtk.Label()
        label.set_markup(markup)
        label.set_xalign(0)
        label.set_margin_start(6)
        label.set_margin_end(6)
        label.set_margin_top(3)
        label.set_margin_bottom(3)
        item.add(label)
        return item, label

    def _value_item(self, title: str) -> tuple[Any, Any]:
        item = self.Gtk.MenuItem()
        box = self.Gtk.Box(orientation=self.Gtk.Orientation.HORIZONTAL, spacing=18)
        box.set_margin_start(6)
        box.set_margin_end(6)
        box.set_margin_top(3)
        box.set_margin_bottom(3)

        title_label = self.Gtk.Label(label=title)
        title_label.set_xalign(0)
        box.pack_start(title_label, True, True, 0)

        value_label = self.Gtk.Label(label="—")
        value_label.set_xalign(1)
        value_label.set_selectable(False)
        box.pack_end(value_label, False, False, 0)

        item.add(box)
        return item, value_label

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

    def _state_markup(self) -> str:
        mapping = {
            ThermalState.NORMAL: ("#2e7d32", "Normale"),
            ThermalState.WARNING: ("#f9a825", "Attenzione"),
            ThermalState.CRITICAL: ("#c62828", "Critico"),
        }
        colour, label = mapping[self.alerts.state]
        return f"<b>Stato:</b> <span foreground='{colour}'>● {label}</span>"

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
        except Exception as exc:
            LOGGER.exception("metrics refresh failed")
            self.header_label.set_markup(
                "<b>Sentinelux</b>\n<span foreground='#c62828'>Errore lettura metriche</span>"
            )
            self.state_label.set_markup(f"<b>Errore:</b> {exc}")
            return True

        event = self.alerts.evaluate(
            metrics.cpu_temperature_c,
            time.monotonic(),
        )
        if event is not None:
            self._notify(event, metrics)

        self.header_label.set_markup(
            f"<b>Sentinelux</b>  <span size='small'>v{__version__}</span>\n"
            "<span size='small'>Monitoraggio attivo</span>"
        )
        self.cpu_value.set_text(f"{metrics.cpu_percent:.1f}%")
        self.memory_value.set_text(
            f"{metrics.memory_percent:.1f}%  ·  "
            f"{human_bytes(metrics.memory_used_bytes)} / "
            f"{human_bytes(metrics.memory_total_bytes)}"
        )
        self.swap_value.set_text(
            f"{metrics.swap_percent:.1f}%  ·  "
            f"{human_bytes(metrics.swap_used_bytes)} / "
            f"{human_bytes(metrics.swap_total_bytes)}"
        )

        if metrics.cpu_temperature_c is None:
            self.temperature_value.set_text("non disponibile")
        else:
            average = metrics.cpu_temperature_average_c
            average_text = f"{average:.1f}°C" if average is not None else "—"
            self.temperature_value.set_text(
                f"{metrics.cpu_temperature_c:.1f}°C / {average_text}"
            )

        self.state_label.set_markup(self._state_markup())
        self._update_sensor_submenu(metrics)
        self._set_indicator_label(metrics)
        self._set_indicator_icon()

        LOGGER.debug("metrics=%s", metrics.to_dict())
        return True

    def _update_sensor_submenu(self, metrics: SystemMetrics) -> None:
        for child in self.sensor_submenu.get_children():
            self.sensor_submenu.remove(child)

        if not metrics.temperature_readings:
            item = self.Gtk.MenuItem(label="Nessun sensore CPU disponibile")
            item.set_sensitive(False)
            self.sensor_submenu.append(item)
        else:
            for reading in metrics.temperature_readings:
                label = f"{reading.label}: {reading.value_c:.1f} °C"
                item = self.Gtk.MenuItem(label=label)
                item.set_sensitive(False)
                item.set_tooltip_text(f"Sorgente: {reading.source}")
                self.sensor_submenu.append(item)

        self.sensor_submenu.show_all()

    def _on_pause_toggled(self, item: Any) -> None:
        self.notifications_paused = bool(item.get_active())
        LOGGER.info("notifications paused=%s", self.notifications_paused)

    def _open_settings(self, *_: Any) -> None:
        if self.settings_window is None:
            self.settings_window = SettingsWindow(
                self.Gtk,
                self.config,
                self._apply_config,
            )
        else:
            self.settings_window.load_config(self.config)
        self.settings_window.present()

    def _apply_config(self, config: AppConfig) -> None:
        self.config = config
        self.alerts = self._new_alert_controller(config)
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

    def _schedule_refresh(self) -> None:
        if self.timeout_source_id is not None:
            self.GLib.source_remove(self.timeout_source_id)
        interval_ms = max(500, int(self.config.refresh_interval_seconds * 1000))
        self.timeout_source_id = self.GLib.timeout_add(interval_ms, self._refresh)

    def run(self) -> int:
        self.running = True
        self._refresh()
        self._schedule_refresh()
        self.Gtk.main()
        self.running = False
        if self.runtime_notifications_allowed:
            self.Notify.uninit()
        return 0
