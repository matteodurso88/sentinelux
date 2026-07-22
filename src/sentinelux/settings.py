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
from .fans import (
    PRESET_LABELS,
    FanControlError,
    FanManager,
    format_fan_channel,
)
from .protection import (
    format_kernel_trip_summary,
    read_kernel_critical_trips,
    sleep_action_capability,
)


class SettingsWindow:
    """Small preferences page for thermal policy, alerts, and startup."""

    def __init__(
        self,
        Gtk: Any,
        config: AppConfig,
        on_save: Callable[[AppConfig], None],
        fan_manager: FanManager,
    ) -> None:
        self.Gtk = Gtk
        self.on_save = on_save
        self.fan_manager = fan_manager

        self.window = Gtk.Window(title="Preferenze Sentinelux")
        self.window.set_default_size(640, 560)
        self.window.set_position(Gtk.WindowPosition.CENTER)
        self.window.connect("delete-event", self._hide)

        header = Gtk.HeaderBar()
        header.set_title("Sentinelux")
        header.set_subtitle("Monitoraggio, protezione, alert e avvio")
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
        protection_page = self._build_protection_page()
        fans_page = self._build_fans_page()
        startup_page = self._build_startup_page()
        notebook.append_page(general_page, Gtk.Label(label="Monitoraggio"))
        notebook.append_page(alerts_page, Gtk.Label(label="Alert"))
        notebook.append_page(protection_page, Gtk.Label(label="Protezione"))
        notebook.append_page(fans_page, Gtk.Label(label="Ventole"))
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


    def _build_protection_page(self) -> Any:
        box = self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL, spacing=12)
        box.set_border_width(18)

        title = self.Gtk.Label()
        title.set_markup("<b>Protezione termica preventiva</b>")
        title.set_xalign(0)
        box.pack_start(title, False, False, 0)

        enable_row = self.Gtk.Box(
            orientation=self.Gtk.Orientation.HORIZONTAL,
            spacing=12,
        )
        enable_label = self.Gtk.Label(
            label="Attiva azione automatica per sovratemperatura"
        )
        enable_label.set_xalign(0)
        enable_row.pack_start(enable_label, True, True, 0)
        self.protection_switch = self.Gtk.Switch()
        self.protection_switch.connect(
            "notify::active",
            self._sync_protection_sensitivity,
        )
        enable_row.pack_end(self.protection_switch, False, False, 0)
        box.pack_start(enable_row, False, False, 0)

        grid = self.Gtk.Grid(column_spacing=18, row_spacing=12)
        box.pack_start(grid, False, False, 0)

        action_label = self.Gtk.Label(label="Azione")
        action_label.set_xalign(0)
        grid.attach(action_label, 0, 0, 1, 1)
        self.protection_action_combo = self.Gtk.ComboBoxText()
        self.protection_action_combo.append("hibernate", "Ibernazione")
        self.protection_action_combo.append("suspend", "Sospensione")
        self.protection_action_combo.connect(
            "changed",
            self._refresh_protection_capability,
        )
        grid.attach(self.protection_action_combo, 1, 0, 1, 1)

        self.protection_temperature_spin = self._spin(40.0, 130.0, 1.0, 0)
        self._attach_row(
            grid,
            1,
            "Soglia azione preventiva",
            self.protection_temperature_spin,
            "°C",
        )

        self.protection_persistence_spin = self._spin(5.0, 300.0, 5.0, 0)
        self._attach_row(
            grid,
            2,
            "Temperatura persistente per",
            self.protection_persistence_spin,
            "secondi",
        )

        self.protection_hysteresis_spin = self._spin(0.0, 20.0, 0.5, 1)
        self._attach_row(
            grid,
            3,
            "Isteresi annullamento",
            self.protection_hysteresis_spin,
            "°C",
        )

        kernel_title = self.Gtk.Label()
        kernel_title.set_markup(
            "<b>Arresto termico kernel · soglia più bassa (sola lettura)</b>"
        )
        kernel_title.set_xalign(0)
        kernel_title.set_margin_top(8)
        box.pack_start(kernel_title, False, False, 0)

        self.kernel_trip_label = self.Gtk.Label()
        self.kernel_trip_label.set_xalign(0)
        self.kernel_trip_label.set_line_wrap(True)
        self.kernel_trip_label.set_selectable(True)
        box.pack_start(self.kernel_trip_label, False, False, 0)

        self.protection_capability_label = self.Gtk.Label()
        self.protection_capability_label.set_xalign(0)
        self.protection_capability_label.set_line_wrap(True)
        box.pack_start(self.protection_capability_label, False, False, 0)

        note = self.Gtk.Label(
            label=(
                "Sentinelux non modifica le soglie del kernel, del BIOS o del firmware. "
                "L'azione preventiva viene richiesta prima della soglia critica più "
                "bassa esposta; "
                "le protezioni hardware restano sempre attive. La sospensione può non "
                "raffreddare completamente il computer: per la tutela dei lavori aperti "
                "è preferibile l'ibernazione quando supportata."
            )
        )
        note.set_xalign(0)
        note.set_line_wrap(True)
        note.get_style_context().add_class("dim-label")
        box.pack_start(note, False, False, 0)

        self.protection_controls = (
            self.protection_action_combo,
            self.protection_temperature_spin,
            self.protection_persistence_spin,
            self.protection_hysteresis_spin,
        )
        return box

    def _build_fans_page(self) -> Any:
        root = self.Gtk.Box(orientation=self.Gtk.Orientation.VERTICAL, spacing=12)
        root.set_border_width(18)

        title = self.Gtk.Label()
        title.set_markup("<b>Ventole e controllo PWM</b>")
        title.set_xalign(0)
        root.pack_start(title, False, False, 0)

        self.fan_status_label = self.Gtk.Label()
        self.fan_status_label.set_xalign(0)
        self.fan_status_label.set_line_wrap(True)
        root.pack_start(self.fan_status_label, False, False, 0)

        scroller = self.Gtk.ScrolledWindow()
        scroller.set_policy(
            self.Gtk.PolicyType.NEVER,
            self.Gtk.PolicyType.AUTOMATIC,
        )
        scroller.set_min_content_height(150)
        self.fan_channels_box = self.Gtk.Box(
            orientation=self.Gtk.Orientation.VERTICAL,
            spacing=8,
        )
        scroller.add(self.fan_channels_box)
        root.pack_start(scroller, True, True, 0)

        preset_row = self.Gtk.Box(
            orientation=self.Gtk.Orientation.HORIZONTAL,
            spacing=10,
        )
        preset_label = self.Gtk.Label(label="Preset per questa sessione")
        preset_label.set_xalign(0)
        preset_row.pack_start(preset_label, True, True, 0)
        self.fan_preset_combo = self.Gtk.ComboBoxText()
        for preset, label in PRESET_LABELS.items():
            self.fan_preset_combo.append(preset, label)
        self.fan_preset_combo.set_active_id("automatic")
        preset_row.pack_end(self.fan_preset_combo, False, False, 0)
        root.pack_start(preset_row, False, False, 0)

        buttons = self.Gtk.Box(
            orientation=self.Gtk.Orientation.HORIZONTAL,
            spacing=8,
        )
        refresh_button = self.Gtk.Button(label="Rileva di nuovo")
        refresh_button.connect("clicked", self._refresh_fan_display)
        buttons.pack_start(refresh_button, False, False, 0)
        self.fan_apply_button = self.Gtk.Button(label="Applica preset")
        self.fan_apply_button.connect("clicked", self._apply_fan_preset)
        self.fan_apply_button.get_style_context().add_class("suggested-action")
        buttons.pack_end(self.fan_apply_button, False, False, 0)
        root.pack_start(buttons, False, False, 0)

        note = self.Gtk.Label(
            label=(
                "Il controllo è temporaneo e richiede autorizzazione amministrativa "
                "tramite Polkit. Sentinelux usa solo canali hwmon con tachimetro RPM, "
                "PWM e modalità leggibile; non consente lo spegnimento delle ventole. "
                "Alla chiusura ripristina i valori rilevati all'avvio."
            )
        )
        note.set_xalign(0)
        note.set_line_wrap(True)
        note.get_style_context().add_class("dim-label")
        root.pack_start(note, False, False, 0)
        return root

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
        self.protection_switch.set_active(config.thermal_protection_enabled)
        self.protection_action_combo.set_active_id(config.thermal_protection_action)
        self.protection_temperature_spin.set_value(
            config.thermal_protection_temperature_c
        )
        self.protection_persistence_spin.set_value(
            config.thermal_protection_persistence_seconds
        )
        self.protection_hysteresis_spin.set_value(
            config.thermal_protection_recovery_hysteresis_c
        )
        self.autostart_switch.set_active(is_autostart_enabled())
        self._sync_alert_sensitivity()
        self._sync_protection_sensitivity()
        self._refresh_kernel_trip_display()
        self._refresh_protection_capability()
        self._refresh_fan_display()
        self._sync_autostart_status()

    def present(self) -> None:
        self.autostart_switch.set_active(is_autostart_enabled())
        self._sync_autostart_status()
        self._refresh_kernel_trip_display()
        self._refresh_protection_capability()
        self._refresh_fan_display()
        self.window.show_all()
        self.window.present()

    def _sync_alert_sensitivity(self, *_: Any) -> None:
        enabled = bool(self.notifications_switch.get_active())
        for check in self.alert_checks:
            check.set_sensitive(enabled)

    def _sync_protection_sensitivity(self, *_: Any) -> None:
        enabled = bool(self.protection_switch.get_active())
        for control in self.protection_controls:
            control.set_sensitive(enabled)
        self._refresh_protection_capability()

    def _refresh_kernel_trip_display(self) -> None:
        self.kernel_trips = read_kernel_critical_trips()
        self.kernel_trip_label.set_text(
            format_kernel_trip_summary(self.kernel_trips)
        )

    def _refresh_protection_capability(self, *_: Any) -> None:
        action = self.protection_action_combo.get_active_id() or "hibernate"
        capability = sleep_action_capability(action)
        labels = {
            "yes": "Disponibile senza autenticazione aggiuntiva",
            "challenge": "Disponibile: il sistema può richiedere autorizzazione",
            "no": "Disponibile ma non autorizzata per questo utente",
            "na": "Non supportata da hardware, kernel o configurazione",
            "unknown": "Disponibilità non determinabile",
        }
        action_name = "Ibernazione" if action == "hibernate" else "Sospensione"
        self.protection_capability_label.set_text(
            f"{action_name}: {labels[capability]}"
        )

    def _refresh_fan_display(self, *_: Any) -> None:
        channels = self.fan_manager.refresh()
        for child in self.fan_channels_box.get_children():
            self.fan_channels_box.remove(child)

        if not channels:
            label = self.Gtk.Label(
                label="Nessuna ventola esposta dal kernel tramite hwmon."
            )
            label.set_xalign(0)
            self.fan_channels_box.pack_start(label, False, False, 0)
        else:
            for channel in channels:
                row = self.Gtk.Label(label=format_fan_channel(channel))
                row.set_xalign(0)
                row.set_selectable(True)
                self.fan_channels_box.pack_start(row, False, False, 0)

        detected = len(channels)
        controllable = len(self.fan_manager.controllable_channels)
        if controllable and self.fan_manager.helper_ready:
            status = (
                f"Rilevate {detected} ventole; {controllable} controllabili. "
                f"Preset attuale: {PRESET_LABELS[self.fan_manager.current_preset]}."
            )
        elif controllable:
            status = (
                f"Rilevate {detected} ventole e {controllable} canali PWM, ma il "
                "helper privilegiato non è installato. Esegui "
                "scripts/install-fan-helper.sh dal repository."
            )
        elif detected:
            status = (
                f"Rilevate {detected} ventole in sola lettura: il driver non espone "
                "insieme feedback RPM, PWM e modalità di controllo leggibile."
            )
        else:
            status = "Nessun canale ventola disponibile."
        self.fan_status_label.set_text(status)
        self.fan_apply_button.set_sensitive(self.fan_manager.control_available)
        self.fan_channels_box.show_all()

    def _apply_fan_preset(self, *_: Any) -> None:
        preset = self.fan_preset_combo.get_active_id() or "automatic"
        try:
            self.fan_manager.apply_preset(preset)
        except FanControlError as exc:
            self._show_error(
                "Impossibile applicare il preset ventole",
                str(exc),
            )
            self._refresh_fan_display()
            return
        self._refresh_fan_display()

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
            thermal_protection_enabled=bool(self.protection_switch.get_active()),
            thermal_protection_action=(
                self.protection_action_combo.get_active_id() or "hibernate"
            ),
            thermal_protection_temperature_c=float(
                self.protection_temperature_spin.get_value()
            ),
            thermal_protection_persistence_seconds=float(
                self.protection_persistence_spin.get_value()
            ),
            thermal_protection_recovery_hysteresis_c=float(
                self.protection_hysteresis_spin.get_value()
            ),
        )
        original_autostart = is_autostart_enabled()
        requested_autostart = bool(self.autostart_switch.get_active())
        try:
            config.validate()
            capability = sleep_action_capability(config.thermal_protection_action)
            if config.thermal_protection_enabled and capability in {"no", "na"}:
                raise ValueError(
                    "l'azione termica selezionata non è disponibile o autorizzata"
                )
            if config.thermal_protection_enabled and self.kernel_trips:
                kernel_limit = min(
                    trip.temperature_c for trip in self.kernel_trips
                )
                if config.thermal_protection_temperature_c >= kernel_limit:
                    raise ValueError(
                        "la soglia preventiva deve essere inferiore alla soglia "
                        f"critica kernel ({kernel_limit:.1f} °C)"
                    )
            set_autostart_enabled(requested_autostart)
            save_config(config)
            self.on_save(config)
        except (AutostartError, OSError, ValueError) as exc:
            if is_autostart_enabled() != original_autostart:
                try:
                    set_autostart_enabled(original_autostart)
                except (AutostartError, OSError):
                    pass
            self._show_error(
                "Impossibile salvare le preferenze",
                str(exc),
            )
            return
        self.window.hide()

    def _show_error(self, title: str, detail: str) -> None:
        dialog = self.Gtk.MessageDialog(
            transient_for=self.window,
            modal=True,
            message_type=self.Gtk.MessageType.ERROR,
            buttons=self.Gtk.ButtonsType.CLOSE,
            text=title,
        )
        dialog.format_secondary_text(detail)
        dialog.run()
        dialog.destroy()

    def _hide(self, *_: Any) -> bool:
        self.window.hide()
        return True
