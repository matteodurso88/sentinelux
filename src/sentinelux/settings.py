"""GTK preferences window for Sentinelux."""

from __future__ import annotations

from typing import Any, Callable

from .autostart import (
    AutostartError,
    autostart_path,
    is_autostart_enabled,
    set_autostart_enabled,
)
from .config import AppConfig, save_config


class SettingsWindow:
    """Small preferences page for thermal policy, alerts, and startup."""

    def __init__(
        self,
        Gtk: Any,
        config: AppConfig,
        on_save: Callable[[AppConfig], None],
    ) -> None:
        self.Gtk = Gtk
        self.on_save = on_save

        self.window = Gtk.Window(title="Preferenze Sentinelux")
        self.window.set_default_size(560, 500)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("delete-event", self._hide)

        header = Gtk.HeaderBar()
        header.set_title("Sentinelux")
        header.set_subtitle("Monitoraggio, alert e avvio")
        header.set_show_close_button(True)
        self.window.set_titlebar(header)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_border_width(16)
        self.window.add(root)

        notebook = Gtk.Notebook()
        notebook.set_hexpand(True)
        notebook.set_vexpand(True)
        root.pack_start(notebook, True, True, 0)

        general_page = self._build_general_page()
        alerts_page = self._build_alerts_page()
        startup_page = self._build_startup_page()
        notebook.append_page(general_page, Gtk.Label(label="Monitoraggio"))
        notebook.append_page(alerts_page, Gtk.Label(label="Alert"))
        notebook.append_page(startup_page, Gtk.Label(label="Avvio"))

        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        root.pack_start(separator, False, False, 0)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        root.pack_start(actions, False, False, 0)

        defaults_button = Gtk.Button(label="Ripristina predefiniti")
        defaults_button.connect("clicked", self._restore_defaults)
        actions.pack_start(defaults_button, False, False, 0)

        cancel_button = Gtk.Button(label="Annulla")
        cancel_button.connect("clicked", self._hide)
        actions.pack_end(cancel_button, False, False, 0)

        save_button = Gtk.Button(label="Salva")
        save_button.get_style_context().add_class("suggested-action")
        save_button.connect("clicked", self._save)
        actions.pack_end(save_button, False, False, 0)

        self.load_config(config)
        self.window.show_all()
        self.window.hide()

    def _build_general_page(self) -> Any:
        grid = self.Gtk.Grid(column_spacing=18, row_spacing=14)
        grid.set_border_width(18)

        title = self.Gtk.Label()
        title.set_markup("<b>Monitoraggio del sistema</b>")
        title.set_xalign(0)
        grid.attach(title, 0, 0, 2, 1)

        self.refresh_spin = self._spin(0.5, 60.0, 0.5, 1)
        self._attach_row(grid, 1, "Intervallo aggiornamento", self.refresh_spin, "secondi")

        thermal_title = self.Gtk.Label()
        thermal_title.set_markup("<b>Politica termica</b>")
        thermal_title.set_xalign(0)
        thermal_title.set_margin_top(12)
        grid.attach(thermal_title, 0, 2, 2, 1)

        self.warning_spin = self._spin(30.0, 120.0, 1.0, 0)
        self._attach_row(grid, 3, "Soglia attenzione", self.warning_spin, "°C")

        self.critical_spin = self._spin(40.0, 130.0, 1.0, 0)
        self._attach_row(grid, 4, "Soglia critica", self.critical_spin, "°C")

        self.hysteresis_spin = self._spin(0.0, 20.0, 0.5, 1)
        self._attach_row(grid, 5, "Isteresi recupero", self.hysteresis_spin, "°C")

        self.reminder_spin = self._spin(0.5, 120.0, 0.5, 1)
        self._attach_row(grid, 6, "Promemoria temperatura alta", self.reminder_spin, "minuti")

        note = self.Gtk.Label(
            label=(
                "Sentinelux applica le soglie alla temperatura più alta rilevata "
                "tra package e core della CPU."
            )
        )
        note.set_line_wrap(True)
        note.set_xalign(0)
        note.get_style_context().add_class("dim-label")
        note.set_margin_top(12)
        grid.attach(note, 0, 7, 2, 1)
        return grid

    def _build_alerts_page(self) -> Any:
        box = self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL, spacing=12)
        box.set_border_width(18)

        title = self.Gtk.Label()
        title.set_markup("<b>Notifiche desktop</b>")
        title.set_xalign(0)
        box.pack_start(title, False, False, 0)

        master_row = self.Gtk.Box(orientation=self.Gtk.Orientation.HORIZONTAL, spacing=12)
        master_label = self.Gtk.Label(label="Abilita notifiche")
        master_label.set_xalign(0)
        master_row.pack_start(master_label, True, True, 0)
        self.notifications_switch = self.Gtk.Switch()
        self.notifications_switch.connect("notify::active", self._sync_alert_sensitivity)
        master_row.pack_end(self.notifications_switch, False, False, 0)
        box.pack_start(master_row, False, False, 0)

        separator = self.Gtk.Separator(orientation=self.Gtk.Orientation.HORIZONTAL)
        box.pack_start(separator, False, False, 4)

        self.warning_check = self.Gtk.CheckButton(
            label="Attenzione — quando viene superata la prima soglia"
        )
        self.critical_check = self.Gtk.CheckButton(
            label="Critico — quando viene superata la soglia critica"
        )
        self.reminder_check = self.Gtk.CheckButton(
            label="Promemoria — mentre la temperatura resta elevata"
        )
        self.recovery_check = self.Gtk.CheckButton(
            label="Recupero — quando la temperatura torna nella norma"
        )

        self.alert_checks = (
            self.warning_check,
            self.critical_check,
            self.reminder_check,
            self.recovery_check,
        )
        for check in self.alert_checks:
            box.pack_start(check, False, False, 0)

        note = self.Gtk.Label(
            label=(
                "La pausa dal menu tray è temporanea. Le opzioni salvate qui "
                "restano attive ai successivi avvii."
            )
        )
        note.set_line_wrap(True)
        note.set_xalign(0)
        note.get_style_context().add_class("dim-label")
        note.set_margin_top(12)
        box.pack_start(note, False, False, 0)
        return box

    def _build_startup_page(self) -> Any:
        box = self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL, spacing=14)
        box.set_border_width(18)

        title = self.Gtk.Label()
        title.set_markup("<b>Avvio automatico</b>")
        title.set_xalign(0)
        box.pack_start(title, False, False, 0)

        row = self.Gtk.Box(orientation=self.Gtk.Orientation.HORIZONTAL, spacing=12)
        label = self.Gtk.Label(label="Avvia Sentinelux all'accesso")
        label.set_xalign(0)
        row.pack_start(label, True, True, 0)
        self.autostart_switch = self.Gtk.Switch()
        self.autostart_switch.connect("notify::active", self._sync_autostart_status)
        row.pack_end(self.autostart_switch, False, False, 0)
        box.pack_start(row, False, False, 0)

        self.autostart_status = self.Gtk.Label()
        self.autostart_status.set_xalign(0)
        self.autostart_status.set_line_wrap(True)
        box.pack_start(self.autostart_status, False, False, 0)

        path_label = self.Gtk.Label(
            label=f"File gestito: {autostart_path()}"
        )
        path_label.set_xalign(0)
        path_label.set_line_wrap(True)
        path_label.get_style_context().add_class("dim-label")
        box.pack_start(path_label, False, False, 0)

        note = self.Gtk.Label(
            label=(
                "La modifica viene applicata premendo Salva. In modalità sviluppo "
                "l'avvio automatico punta allo script run-dev.sh del repository; "
                "dopo l'installazione punta al launcher utente."
            )
        )
        note.set_xalign(0)
        note.set_line_wrap(True)
        note.get_style_context().add_class("dim-label")
        box.pack_start(note, False, False, 0)
        return box

    def _spin(
        self,
        minimum: float,
        maximum: float,
        step: float,
        digits: int,
    ) -> Any:
        spin = self.Gtk.SpinButton.new_with_range(minimum, maximum, step)
        spin.set_digits(digits)
        spin.set_numeric(True)
        spin.set_width_chars(7)
        return spin

    def _attach_row(
        self,
        grid: Any,
        row: int,
        label_text: str,
        widget: Any,
        suffix: str,
    ) -> None:
        label = self.Gtk.Label(label=label_text)
        label.set_xalign(0)
        grid.attach(label, 0, row, 1, 1)

        value_box = self.Gtk.Box(orientation=self.Gtk.Orientation.HORIZONTAL, spacing=8)
        value_box.pack_start(widget, False, False, 0)
        suffix_label = self.Gtk.Label(label=suffix)
        suffix_label.set_xalign(0)
        value_box.pack_start(suffix_label, False, False, 0)
        grid.attach(value_box, 1, row, 1, 1)

    def load_config(self, config: AppConfig) -> None:
        self.refresh_spin.set_value(config.refresh_interval_seconds)
        self.warning_spin.set_value(config.warning_temperature_c)
        self.critical_spin.set_value(config.critical_temperature_c)
        self.hysteresis_spin.set_value(config.recovery_hysteresis_c)
        self.reminder_spin.set_value(config.reminder_interval_seconds / 60.0)
        self.notifications_switch.set_active(config.notifications_enabled)
        self.warning_check.set_active(config.alert_warning_enabled)
        self.critical_check.set_active(config.alert_critical_enabled)
        self.reminder_check.set_active(config.alert_reminder_enabled)
        self.recovery_check.set_active(config.alert_recovery_enabled)
        self.autostart_switch.set_active(is_autostart_enabled())
        self._sync_alert_sensitivity()
        self._sync_autostart_status()

    def present(self) -> None:
        self.autostart_switch.set_active(is_autostart_enabled())
        self._sync_autostart_status()
        self.window.show_all()
        self.window.present()

    def _sync_alert_sensitivity(self, *_: Any) -> None:
        enabled = bool(self.notifications_switch.get_active())
        for check in self.alert_checks:
            check.set_sensitive(enabled)

    def _sync_autostart_status(self, *_: Any) -> None:
        if self.autostart_switch.get_active():
            self.autostart_status.set_text(
                "Attivo: Sentinelux verrà avviato automaticamente alla prossima sessione."
            )
        else:
            self.autostart_status.set_text(
                "Disattivo: Sentinelux dovrà essere avviato manualmente."
            )

    def _restore_defaults(self, *_: Any) -> None:
        self.load_config(AppConfig())

    def _save(self, *_: Any) -> None:
        config = AppConfig(
            refresh_interval_seconds=float(self.refresh_spin.get_value()),
            warning_temperature_c=float(self.warning_spin.get_value()),
            critical_temperature_c=float(self.critical_spin.get_value()),
            recovery_hysteresis_c=float(self.hysteresis_spin.get_value()),
            reminder_interval_seconds=float(self.reminder_spin.get_value()) * 60.0,
            notifications_enabled=bool(self.notifications_switch.get_active()),
            alert_warning_enabled=bool(self.warning_check.get_active()),
            alert_critical_enabled=bool(self.critical_check.get_active()),
            alert_reminder_enabled=bool(self.reminder_check.get_active()),
            alert_recovery_enabled=bool(self.recovery_check.get_active()),
        )
        original_autostart = is_autostart_enabled()
        requested_autostart = bool(self.autostart_switch.get_active())
        try:
            config.validate()
            set_autostart_enabled(requested_autostart)
            save_config(config)
            self.on_save(config)
        except (AutostartError, OSError, ValueError) as exc:
            if is_autostart_enabled() != original_autostart:
                try:
                    set_autostart_enabled(original_autostart)
                except (AutostartError, OSError):
                    pass
            dialog = self.Gtk.MessageDialog(
                transient_for=self.window,
                modal=True,
                message_type=self.Gtk.MessageType.ERROR,
                buttons=self.Gtk.ButtonsType.CLOSE,
                text="Impossibile salvare le preferenze",
            )
            dialog.format_secondary_text(str(exc))
            dialog.run()
            dialog.destroy()
            return
        self.window.hide()

    def _hide(self, *_: Any) -> bool:
        self.window.hide()
        return True
