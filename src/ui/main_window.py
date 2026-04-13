"""
Hauptfenster – TmYNoobs VoiceMorph & Text2Speech.
"""

from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QStatusBar,
    QSizePolicy, QMenuBar, QMenu, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QFont

from ui.voice_tab import VoiceTab
from ui.tts_tab import TTSTab
from ui.preset_editor import PresetEditorDialog
from presets.manager import save_user_preset, delete_user_preset, is_builtin, load_all_presets

APP_NAME    = "TmYNoobs VoiceMorph & Text2Speech"
APP_VERSION = "1.0.0"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(860, 700)
        self.resize(960, 760)

        self._build_menu()
        self._build_central()
        self._build_statusbar()

        # Status-Nachricht beim Start
        QTimer.singleShot(500, lambda: self.statusbar.showMessage(
            f"✨ Willkommen bei {APP_NAME}!  –  Wähle einen Tab um loszulegen.", 6000
        ))

    # ── Menü ────────────────────────────────────────────────────────────────

    def _build_menu(self):
        menubar = self.menuBar()

        # Presets-Menü
        presets_menu = menubar.addMenu("🎛️  Presets")

        action_new = QAction("✨  Neues Preset erstellen...", self)
        action_new.setShortcut("Ctrl+N")
        action_new.triggered.connect(self._open_preset_creator)
        presets_menu.addAction(action_new)

        presets_menu.addSeparator()

        self.menu_delete_preset = QMenu("🗑  Preset löschen", self)
        presets_menu.addMenu(self.menu_delete_preset)
        self._refresh_delete_menu()

        # Hilfe-Menü
        help_menu = menubar.addMenu("❓  Hilfe")

        action_about = QAction("ℹ️  Über diese App", self)
        action_about.triggered.connect(self._show_about)
        help_menu.addAction(action_about)

        action_github = QAction("🐙  GitHub (Quellcode & Updates)", self)
        action_github.triggered.connect(self._open_github)
        help_menu.addAction(action_github)

    # ── Zentrales Widget ────────────────────────────────────────────────────

    def _build_central(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = QWidget()
        header.setFixedHeight(64)
        header.setStyleSheet("background-color: #0f1020; border-bottom: 2px solid #e94560;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 8, 20, 8)

        title_label = QLabel(f"🎤 {APP_NAME}")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #ffffff;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        version_label = QLabel(f"v{APP_VERSION}")
        version_label.setStyleSheet("color: #606080; font-size: 11px;")
        header_layout.addWidget(version_label)

        main_layout.addWidget(header)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)

        self.voice_tab = VoiceTab()
        self.tts_tab   = TTSTab()

        self.tabs.addTab(self.voice_tab, "🎤  Voice Changer")
        self.tabs.addTab(self.tts_tab,   "💬  Text-to-Speech")

        main_layout.addWidget(self.tabs, 1)

    # ── Statusbar ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Bereit.")

    # ── Preset Creator ───────────────────────────────────────────────────────

    def _open_preset_creator(self, existing: dict = None):
        dialog = PresetEditorDialog(self, existing_preset=existing)
        dialog.preset_saved.connect(self._on_preset_saved)
        dialog.exec()

    def _on_preset_saved(self, preset: dict):
        if save_user_preset(preset):
            self.voice_tab.refresh_presets()
            self._refresh_delete_menu()
            self.statusbar.showMessage(
                f"✅ Preset '{preset['name']}' gespeichert!", 4000
            )
        else:
            QMessageBox.critical(
                self, "Fehler",
                "Das Preset konnte nicht gespeichert werden.\n"
                "Bitte prüfe ob der Ordner 'user_presets/' schreibbar ist."
            )

    def _refresh_delete_menu(self):
        self.menu_delete_preset.clear()
        presets = [p for p in load_all_presets() if not is_builtin(p["id"])]
        if not presets:
            action = QAction("(Keine eigenen Presets)", self)
            action.setEnabled(False)
            self.menu_delete_preset.addAction(action)
        else:
            for preset in presets:
                action = QAction(f"{preset['icon']}  {preset['name']}", self)
                action.triggered.connect(
                    lambda checked, p=preset: self._confirm_delete_preset(p)
                )
                self.menu_delete_preset.addAction(action)

    def _confirm_delete_preset(self, preset: dict):
        reply = QMessageBox.question(
            self,
            "Preset löschen?",
            f"Möchtest du das Preset \"{preset['name']}\" wirklich löschen?\n"
            "Das kann nicht rückgängig gemacht werden.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            delete_user_preset(preset["id"])
            self.voice_tab.refresh_presets()
            self._refresh_delete_menu()
            self.statusbar.showMessage(f"🗑  Preset '{preset['name']}' gelöscht.", 3000)

    # ── Info / GitHub ─────────────────────────────────────────────────────────

    def _show_about(self):
        QMessageBox.about(
            self,
            f"Über {APP_NAME}",
            f"<h2>🎤 {APP_NAME}</h2>"
            f"<p><b>Version:</b> {APP_VERSION}</p>"
            "<p>Ein kostenloser Voice Changer und Text-to-Speech Player.<br>"
            "Funktioniert auf Windows, macOS und Linux.</p>"
            "<p><b>Entwickelt von:</b> TmYNooB</p>"
            "<p><b>Lizenz:</b> GPL v3 – freie und quelloffene Software</p>"
            "<p><a href='https://github.com/TmYNooB/VoiceMorph-TTS'>"
            "github.com/TmYNooB/VoiceMorph-TTS</a></p>"
        )

    def _open_github(self):
        from PyQt6.QtGui import QDesktopServices
        from PyQt6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl("https://github.com/TmYNooB/VoiceMorph-TTS"))

    def closeEvent(self, event):
        self.voice_tab._engine.stop()
        super().closeEvent(event)
