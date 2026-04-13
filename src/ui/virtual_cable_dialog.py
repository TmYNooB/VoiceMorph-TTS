"""
Setup-Dialog für Virtual Audio Cable (VB-Cable / BlackHole / Linux Null-Sink).

Zeigt dem Nutzer:
  - Ob ein virtuelles Kabel erkannt wurde (✅) oder nicht (❌)
  - Schritt-für-Schritt Installationsanleitung für die aktuelle Plattform
  - Download-Button
  - Wie er das virtuelle Mikrofon in Discord / Teams / TeamSpeak einstellt
"""

import sys
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QScrollArea, QWidget, QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDesktopServices, QFont
from PyQt6.QtCore import QUrl

from audio.virtual_cable import detect_virtual_cables, get_setup_instructions


class VirtualCableSetupDialog(QDialog):
    """Dialog der erklärt wie man ein virtuelles Audiokabel einrichtet."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎧 Virtuelle Audiokabel – Setup")
        self.setMinimumWidth(620)
        self.setMinimumHeight(540)
        self._instructions = get_setup_instructions()
        self._cables = detect_virtual_cables()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 20)

        # ── Titel ──────────────────────────────────────────────────────────
        title = QLabel("🎧  Virtuelle Audiokabel – für Discord, Teams & TeamSpeak")
        title.setObjectName("label_title")
        layout.addWidget(title)

        info = QLabel(
            "Um deine veränderte Stimme in Discord, Teams oder TeamSpeak zu nutzen,\n"
            "brauchst du ein <b>virtuelles Audiokabel</b>. Das ist eine kostenlose\n"
            "Software die ein \"unsichtbares Kabel\" zwischen der App und deinem\n"
            "Kommunikationsprogramm herstellt."
        )
        info.setObjectName("label_subtitle")
        info.setWordWrap(True)
        info.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info)

        # ── Status-Box ─────────────────────────────────────────────────────
        status_frame = QFrame()
        status_frame.setObjectName("card")
        status_frame.setStyleSheet(
            "QFrame#card { background-color: #16213e; border: 1px solid #2a2a4a; border-radius: 10px; padding: 8px; }"
        )
        status_layout = QHBoxLayout(status_frame)

        if self._cables:
            names = ", ".join(f"'{c.name}'" for c in self._cables[:3])
            icon_lbl = QLabel("✅")
            icon_lbl.setStyleSheet("font-size: 24px;")
            status_layout.addWidget(icon_lbl)
            status_text = QLabel(
                f"<b>Virtuelles Kabel erkannt!</b><br>"
                f"Gefunden: {names}<br>"
                f"<span style='color:#4ade80;'>Du kannst die App sofort mit Discord/Teams nutzen – "
                f"wähle unten das richtige Gerät aus.</span>"
            )
        else:
            icon_lbl = QLabel("❌")
            icon_lbl.setStyleSheet("font-size: 24px;")
            status_layout.addWidget(icon_lbl)
            product = self._instructions["product"]
            status_text = QLabel(
                f"<b>Kein virtuelles Kabel gefunden.</b><br>"
                f"Für {self._instructions['platform']} empfehlen wir <b>{product}</b> "
                f"(kostenlos).<br>"
                f"Folge der Anleitung unten um es zu installieren."
            )
        status_text.setWordWrap(True)
        status_text.setTextFormat(Qt.TextFormat.RichText)
        status_text.setStyleSheet("color: #eaeaea; font-size: 13px;")
        status_layout.addWidget(status_text, 1)
        layout.addWidget(status_frame)

        # ── Scrollbarer Bereich ────────────────────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(14)

        # Installations-Schritte
        steps_group = QGroupBox(
            f"📋  Installationsanleitung – {self._instructions['product']}"
        )
        steps_layout = QVBoxLayout(steps_group)
        steps_layout.setSpacing(6)

        for i, step in enumerate(self._instructions["steps"], start=1):
            if step.startswith("  "):
                # Code-Block
                code_lbl = QLabel(f"<code>{step.strip()}</code>")
                code_lbl.setStyleSheet(
                    "background-color: #0f1020; color: #4ade80; "
                    "font-family: monospace; padding: 6px 10px; border-radius: 6px;"
                )
                code_lbl.setTextFormat(Qt.TextFormat.RichText)
                steps_layout.addWidget(code_lbl)
            else:
                step_lbl = QLabel(f"  <b>{i}.</b>  {step}")
                step_lbl.setWordWrap(True)
                step_lbl.setTextFormat(Qt.TextFormat.RichText)
                step_lbl.setStyleSheet("color: #eaeaea; padding: 2px 0;")
                steps_layout.addWidget(step_lbl)

        scroll_layout.addWidget(steps_group)

        # Einstellungen in Discord / Teams / TeamSpeak
        apps_group = QGroupBox("⚙️  So richtest du dein Kommunikationsprogramm ein")
        apps_layout = QVBoxLayout(apps_group)
        apps_layout.setSpacing(8)

        app_settings = [
            ("🎮 Discord",    self._instructions["discord_setting"]),
            ("💼 MS Teams",   self._instructions["teams_setting"]),
            ("🎧 TeamSpeak",  self._instructions["teamspeak_setting"]),
        ]

        for app_name, setting in app_settings:
            app_lbl = QLabel(f"<b>{app_name}:</b>")
            app_lbl.setStyleSheet("color: #eaeaea;")
            app_lbl.setTextFormat(Qt.TextFormat.RichText)
            apps_layout.addWidget(app_lbl)

            setting_lbl = QLabel(f"  {setting}")
            setting_lbl.setWordWrap(True)
            setting_lbl.setStyleSheet(
                "color: #a0a0b0; padding: 2px 0 8px 12px;"
            )
            apps_layout.addWidget(setting_lbl)

        scroll_layout.addWidget(apps_group)

        # Erklärbild (Text-basiert)
        how_group = QGroupBox("💡  Wie funktioniert das?")
        how_layout = QVBoxLayout(how_group)
        how_lbl = QLabel(
            "<pre style='font-family: monospace; color: #a0a0b0; font-size: 12px;'>"
            "  Dein Mikrofon\n"
            "       │\n"
            "       ▼\n"
            "  TmYNoobs VoiceMorph\n"
            "  (Effekte anwenden)\n"
            "       │\n"
            "       ▼\n"
            f"  Virtuelle Kabel-Ausgabe  ←── diese App schickt Sound hierhin\n"
            "       │\n"
            "       ▼\n"
            "  Virtuelle Kabel-Eingabe  ←── Discord/Teams/TS hören das als Mikrofon\n"
            "       │\n"
            "       ▼\n"
            "  Deine Gesprächspartner 🎉"
            "</pre>"
        )
        how_lbl.setTextFormat(Qt.TextFormat.RichText)
        how_layout.addWidget(how_lbl)
        scroll_layout.addWidget(how_group)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll, 1)

        # ── Buttons ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()

        if self._instructions.get("download_url"):
            btn_download = QPushButton(
                f"🌐  {self._instructions['product']} herunterladen (kostenlos)"
            )
            btn_download.clicked.connect(
                lambda: QDesktopServices.openUrl(QUrl(self._instructions["download_url"]))
            )
            btn_row.addWidget(btn_download, 2)

        btn_row.addStretch()

        btn_close = QPushButton("Schließen")
        btn_close.setObjectName("btn_secondary")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)
