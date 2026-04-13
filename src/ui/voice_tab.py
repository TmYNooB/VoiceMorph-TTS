"""
Voice Changer Tab – Live-Modus und Dateiverarbeitungs-Modus.
"""

import os
import threading
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton,
    QComboBox, QSlider, QGroupBox, QFileDialog, QProgressBar,
    QSizePolicy, QFrame, QScrollArea, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont

from audio.engine import AudioEngine
from audio.file_processor import process_file
from audio.virtual_cable import detect_virtual_cables, get_best_output_device
from presets.manager import load_all_presets, is_builtin

# Bekannte Substring-Muster für virtuelle Kabel (für Highlighting im Dropdown)
_VAC_SUBSTRINGS = [
    "cable", "blackhole", "loopback", "soundflower",
    "voicemeeter", "null sink", "virtual",
]


class VuMeterWidget(QWidget):
    """Einfaches vertikales VU-Meter als farbige Balken."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._level = 0.0
        self.setFixedWidth(24)
        self.setMinimumHeight(80)

    def set_level(self, value: float):
        self._level = max(0.0, min(1.0, value))
        self.update()

    def paintEvent(self, event):
        from PyQt6.QtGui import QPainter, QColor, QLinearGradient
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Hintergrund
        painter.fillRect(0, 0, w, h, QColor("#0a0a1a"))

        # Pegelbalken
        fill_h = int(h * self._level)
        if fill_h > 0:
            gradient = QLinearGradient(0, h, 0, h - fill_h)
            gradient.setColorAt(0.0, QColor("#4ade80"))
            gradient.setColorAt(0.6, QColor("#fbbf24"))
            gradient.setColorAt(1.0, QColor("#f87171"))
            painter.fillRect(2, h - fill_h, w - 4, fill_h, gradient)

        painter.end()


class VoiceTab(QWidget):
    """Tab für den Voice Changer (Live + Datei)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._presets = []
        self._current_preset = None
        self._vac_devices = []
        self._engine = AudioEngine(
            on_error=self._on_engine_error,
        )
        # VU-Meter: QTimer liest engine.current_rms 20×/s – kein emit() vom RT-Thread!
        self._vu_timer = QTimer(self)
        self._vu_timer.setInterval(50)  # 20 fps
        self._vu_timer.timeout.connect(self._poll_vu)
        self._build_ui()
        self._load_presets()

    # ── UI aufbauen ─────────────────────────────────────────────────────────

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 14, 16, 14)

        # ── Titel (kompakt) ────────────────────────────────────────────────
        title = QLabel("🎤  Voice Changer")
        title.setObjectName("label_title")
        layout.addWidget(title)

        # ── VAC-Banner ─────────────────────────────────────────────────────
        self.vac_banner = QFrame()
        self.vac_banner.setObjectName("card")
        vac_layout = QHBoxLayout(self.vac_banner)
        vac_layout.setContentsMargins(12, 8, 12, 8)
        vac_layout.setSpacing(8)

        self.vac_icon_label = QLabel("❌")
        self.vac_icon_label.setStyleSheet("font-size: 18px;")
        self.vac_icon_label.setFixedWidth(26)
        vac_layout.addWidget(self.vac_icon_label)

        self.vac_text_label = QLabel()
        self.vac_text_label.setWordWrap(True)
        self.vac_text_label.setTextFormat(Qt.TextFormat.RichText)
        self.vac_text_label.setStyleSheet("color: #eaeaea; font-size: 12px;")
        vac_layout.addWidget(self.vac_text_label, 1)

        self.btn_vac_setup = QPushButton("⚙️  Einrichten")
        self.btn_vac_setup.setObjectName("btn_secondary")
        self.btn_vac_setup.setFixedWidth(120)
        self.btn_vac_setup.clicked.connect(self._open_vac_setup)
        vac_layout.addWidget(self.btn_vac_setup)

        layout.addWidget(self.vac_banner)
        self._update_vac_banner()

        # ── Live-Modus ─────────────────────────────────────────────────────
        live_group = QGroupBox("🎙️  Live-Modus")
        live_layout = QVBoxLayout(live_group)
        live_layout.setSpacing(8)
        live_layout.setContentsMargins(12, 16, 12, 12)

        # Mikrofon | Ausgabe nebeneinander
        dev_row = QHBoxLayout()
        dev_row.setSpacing(8)

        dev_row.addWidget(QLabel("Mikrofon:"))
        self.combo_input = QComboBox()
        self.combo_input.setToolTip("Wähle das Mikrofon das du verwenden möchtest")
        dev_row.addWidget(self.combo_input, 2)

        dev_row.addSpacing(4)
        dev_row.addWidget(QLabel("Ausgabe:"))
        self.combo_output = QComboBox()
        self.combo_output.setToolTip("Wähle Lautsprecher oder Kopfhörer")
        dev_row.addWidget(self.combo_output, 2)

        refresh_btn = QPushButton("🔄  Aktualisieren")
        refresh_btn.setObjectName("btn_secondary")
        refresh_btn.setToolTip("Geräteliste neu laden")
        refresh_btn.clicked.connect(self._refresh_devices)
        dev_row.addWidget(refresh_btn)

        live_layout.addLayout(dev_row)

        # Start/Stop + VU-Meter + Status
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(10)

        self.btn_start = QPushButton("▶  Live starten")
        self.btn_start.setObjectName("btn_start")
        self.btn_start.clicked.connect(self._toggle_live)
        ctrl_row.addWidget(self.btn_start, 1)

        self.vu_meter = VuMeterWidget()
        ctrl_row.addWidget(self.vu_meter)

        self.label_status = QLabel("● Gestoppt")
        self.label_status.setObjectName("label_status_inactive")
        self.label_status.setFixedWidth(100)
        ctrl_row.addWidget(self.label_status)

        live_layout.addLayout(ctrl_row)
        layout.addWidget(live_group)

        # ── Preset-Auswahl ─────────────────────────────────────────────────
        preset_group = QGroupBox("🎛️  Stimm-Preset")
        preset_layout = QVBoxLayout(preset_group)
        preset_layout.setSpacing(6)
        preset_layout.setContentsMargins(12, 16, 12, 12)

        self.combo_preset = QComboBox()
        self.combo_preset.setToolTip("Wähle einen Stimm-Effekt")
        self.combo_preset.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self.combo_preset)

        self.label_preset_desc = QLabel("Kein Effekt ausgewählt.")
        self.label_preset_desc.setObjectName("label_subtitle")
        self.label_preset_desc.setWordWrap(True)
        self.label_preset_desc.setMinimumHeight(32)
        preset_layout.addWidget(self.label_preset_desc)

        layout.addWidget(preset_group)

        # ── Dateiverarbeitung ─────────────────────────────────────────────
        file_group = QGroupBox("📁  Datei verarbeiten")
        file_layout = QVBoxLayout(file_group)
        file_layout.setSpacing(8)
        file_layout.setContentsMargins(12, 16, 12, 12)

        file_info = QLabel(
            "Audiodatei (WAV, FLAC, OGG) laden, Effekt anwenden und speichern."
        )
        file_info.setObjectName("label_subtitle")
        file_info.setWordWrap(True)
        file_layout.addWidget(file_info)

        file_row = QHBoxLayout()
        file_row.setSpacing(8)

        self.btn_open_file = QPushButton("📂  Öffnen...")
        self.btn_open_file.setObjectName("btn_secondary")
        self.btn_open_file.setFixedWidth(120)
        self.btn_open_file.clicked.connect(self._open_file)
        file_row.addWidget(self.btn_open_file)

        self.label_input_file = QLabel("Keine Datei ausgewählt")
        self.label_input_file.setObjectName("label_subtitle")
        self.label_input_file.setWordWrap(True)
        file_row.addWidget(self.label_input_file, 1)
        file_layout.addLayout(file_row)

        self.btn_process_file = QPushButton("⚙️  Effekt anwenden & speichern")
        self.btn_process_file.setObjectName("btn_secondary")
        self.btn_process_file.setEnabled(False)
        self.btn_process_file.clicked.connect(self._process_file)
        file_layout.addWidget(self.btn_process_file)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        file_layout.addWidget(self.progress_bar)

        layout.addWidget(file_group)
        layout.addStretch()

        self._refresh_devices()

    # ── Geräte ──────────────────────────────────────────────────────────────

    def _refresh_devices(self):
        self.combo_input.clear()
        self.combo_output.clear()

        inputs  = AudioEngine.list_input_devices()
        outputs = AudioEngine.list_output_devices()
        self._vac_devices = detect_virtual_cables()
        vac_output_names = {
            c.name.lower() for c in self._vac_devices if c.is_output
        }

        if not inputs:
            self.combo_input.addItem("Kein Mikrofon gefunden", None)
        else:
            for idx, name in inputs:
                self.combo_input.addItem(name, idx)

        if not outputs:
            self.combo_output.addItem("Keine Ausgabe gefunden", None)
        else:
            best_vac_idx = None
            for list_pos, (idx, name) in enumerate(outputs):
                is_vac = name.lower() in vac_output_names or any(
                    s in name.lower() for s in _VAC_SUBSTRINGS
                )
                if is_vac:
                    # Virtuelles Kabel mit Hinweis kennzeichnen
                    self.combo_output.addItem(
                        f"🎧 {name}  ← für Discord/Teams!", idx
                    )
                    if best_vac_idx is None:
                        best_vac_idx = list_pos
                else:
                    self.combo_output.addItem(name, idx)

            # Virtuelles Kabel automatisch vorauswählen
            if best_vac_idx is not None:
                self.combo_output.setCurrentIndex(best_vac_idx)

        self._update_vac_banner()

    # ── VAC Banner + Setup ───────────────────────────────────────────────────

    def _update_vac_banner(self):
        """Aktualisiert das Banner je nachdem ob ein VAC erkannt wurde."""
        cables = detect_virtual_cables()
        if cables:
            names = " / ".join(c.name for c in cables[:2])
            self.vac_icon_label.setText("✅")
            self.vac_text_label.setText(
                f"<b>Virtuelles Kabel erkannt:</b> {names}<br>"
                "<span style='color:#4ade80;'>Du kannst deine veränderte Stimme jetzt "
                "in Discord, Teams und TeamSpeak nutzen! "
                "Wähle das 🎧-Gerät als Ausgabe und setze es in Discord/Teams als Mikrofon.</span>"
            )
            self.vac_banner.setStyleSheet(
                "QFrame { background-color: #0d2b1a; border: 1px solid #4ade80; border-radius: 10px; }"
            )
            self.btn_vac_setup.setText("ℹ️  Anleitung")
        else:
            self.vac_icon_label.setText("❌")
            self.vac_text_label.setText(
                "<b>Kein virtuelles Kabel gefunden.</b><br>"
                "Um deine Stimme in <b>Discord, Teams oder TeamSpeak</b> zu nutzen, "
                "installiere ein kostenloses virtuelles Audiokabel. "
                "Klicke auf <b>Einrichten</b> für die Schritt-für-Schritt Anleitung."
            )
            self.vac_banner.setStyleSheet(
                "QFrame { background-color: #2b1a0d; border: 1px solid #f87171; border-radius: 10px; }"
            )
            self.btn_vac_setup.setText("⚙️  Einrichten")

    def _open_vac_setup(self):
        from ui.virtual_cable_dialog import VirtualCableSetupDialog
        dlg = VirtualCableSetupDialog(self)
        dlg.exec()
        # Nach Dialog neu prüfen (User könnte gerade installiert haben)
        self._refresh_devices()

    # ── Presets ─────────────────────────────────────────────────────────────

    def _load_presets(self):
        self._presets = load_all_presets()
        self.combo_preset.clear()
        for p in self._presets:
            self.combo_preset.addItem(f"{p['icon']}  {p['name']}", p["id"])
        if self._presets:
            self.combo_preset.setCurrentIndex(0)

    def refresh_presets(self):
        """Kann von außen aufgerufen werden wenn Custom Presets geändert wurden."""
        self._load_presets()

    def _on_preset_changed(self, index: int):
        if index < 0 or index >= len(self._presets):
            return
        preset = self._presets[index]
        self._current_preset = preset
        self.label_preset_desc.setText(preset.get("description", ""))
        if self._engine.is_running:
            self._engine.set_preset(preset["params"])

    # ── Live-Steuerung ──────────────────────────────────────────────────────

    def _toggle_live(self):
        if self._engine.is_running:
            self._engine.stop()
            self._vu_timer.stop()
            self.btn_start.setText("▶  Live starten")
            self.btn_start.setObjectName("btn_start")
            self.btn_start.style().unpolish(self.btn_start)
            self.btn_start.style().polish(self.btn_start)
            self.label_status.setText("● Gestoppt")
            self.label_status.setObjectName("label_status_inactive")
            self.label_status.style().unpolish(self.label_status)
            self.label_status.style().polish(self.label_status)
            self.vu_meter.set_level(0.0)
        else:
            # Geräte setzen
            in_idx = self.combo_input.currentData()
            out_idx = self.combo_output.currentData()
            self._engine.input_device  = in_idx
            self._engine.output_device = out_idx

            if self._current_preset:
                self._engine.set_preset(self._current_preset["params"])

            if self._engine.start():
                self.btn_start.setText("⏹  Stop")
                self.btn_start.setObjectName("btn_stop")
                self.btn_start.style().unpolish(self.btn_start)
                self.btn_start.style().polish(self.btn_start)
                self.label_status.setText("● Live aktiv")
                self.label_status.setObjectName("label_status_active")
                self.label_status.style().unpolish(self.label_status)
                self.label_status.style().polish(self.label_status)
                self._vu_timer.start()

    def _poll_vu(self):
        """Liest engine.current_rms per QTimer – kein RT-Thread-Kontakt."""
        self.vu_meter.set_level(self._engine.current_rms)

    def _on_engine_error(self, message: str):
        QMessageBox.critical(self, "Audio-Fehler", message)

    # ── Dateiverarbeitung ────────────────────────────────────────────────────

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Audiodatei öffnen",
            str(Path.home()),
            "Audiodateien (*.wav *.flac *.ogg);;Alle Dateien (*)",
        )
        if path:
            self._input_file = path
            self.label_input_file.setText(Path(path).name)
            self.btn_process_file.setEnabled(self._current_preset is not None)

    def _process_file(self):
        if not hasattr(self, "_input_file") or not self._current_preset:
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Speichern als...",
            str(Path.home() / "veränderte_stimme.wav"),
            "WAV-Datei (*.wav);;FLAC-Datei (*.flac)",
        )
        if not save_path:
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.btn_process_file.setEnabled(False)
        self.btn_open_file.setEnabled(False)

        params = self._current_preset["params"]
        input_path = self._input_file

        def _run():
            try:
                process_file(input_path, save_path, params, self._update_progress)
                self._on_file_done(save_path)
            except Exception as exc:
                self._on_file_error(str(exc))

        threading.Thread(target=_run, daemon=True).start()

    def _update_progress(self, pct: int):
        self.progress_bar.setValue(pct)

    def _on_file_done(self, output_path: str):
        from PyQt6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(self, "_file_done_slot", Qt.ConnectionType.QueuedConnection)

    def _on_file_error(self, message: str):
        from PyQt6.QtCore import QMetaObject, Qt
        self._file_error_msg = message
        QMetaObject.invokeMethod(self, "_file_error_slot", Qt.ConnectionType.QueuedConnection)

    @pyqtSlot()
    def _file_done_slot(self):
        self.progress_bar.setValue(100)
        self.btn_process_file.setEnabled(True)
        self.btn_open_file.setEnabled(True)
        QMessageBox.information(self, "Fertig! ✅", "Die Datei wurde erfolgreich verarbeitet und gespeichert.")
        QTimer.singleShot(2000, lambda: self.progress_bar.setVisible(False))

    @pyqtSlot()
    def _file_error_slot(self):
        self.btn_process_file.setEnabled(True)
        self.btn_open_file.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Fehler", getattr(self, "_file_error_msg", "Unbekannter Fehler"))

    def closeEvent(self, event):
        self._engine.stop()
        super().closeEvent(event)
