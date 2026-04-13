"""
Text-to-Speech Tab – Online (edge-tts) und Offline (pyttsx3) TTS.
"""

import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTextEdit, QSlider, QGroupBox, QFileDialog,
    QSizePolicy, QMessageBox,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot

from tts import online_tts, offline_tts


class TTSTab(QWidget):
    """Tab für Text-to-Speech."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._is_speaking = False
        self._build_ui()
        self._load_voices()

    # ── UI aufbauen ─────────────────────────────────────────────────────────

    def _build_ui(self):
        # Kein ScrollArea – alles passt in den Tab.
        # Layout: Settings (fix) → Text (expandiert) → Buttons (fix unten)
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 14, 16, 14)

        # ── Titel ──────────────────────────────────────────────────────────
        title = QLabel("💬  Text-to-Speech")
        title.setObjectName("label_title")
        layout.addWidget(title)

        # ── Stimm-Einstellungen (kompakt, eine Sektion) ────────────────────
        voice_group = QGroupBox("🗣️  Einstellungen")
        voice_outer = QVBoxLayout(voice_group)
        voice_outer.setContentsMargins(12, 16, 12, 12)
        voice_outer.setSpacing(8)

        # Zeile 1: Modus | Sprache | Stimme – alle in einer Zeile
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        top_row.addWidget(QLabel("Modus:"))
        self.combo_mode = QComboBox()
        self.combo_mode.addItem("🌐  Online", "online")
        self.combo_mode.addItem("💻  Offline", "offline")
        self.combo_mode.setToolTip("Online: sehr natürlich (Internet nötig) · Offline: kein Internet")
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        self.combo_mode.setMinimumWidth(120)
        top_row.addWidget(self.combo_mode)

        top_row.addSpacing(4)
        top_row.addWidget(QLabel("Sprache:"))
        self.combo_lang = QComboBox()
        self.combo_lang.addItem("🇩🇪  Deutsch", "de")
        self.combo_lang.addItem("🇬🇧  Englisch", "en")
        self.combo_lang.addItem("🌍  Alle", "all")
        self.combo_lang.currentIndexChanged.connect(self._filter_voices)
        self.combo_lang.setMinimumWidth(110)
        top_row.addWidget(self.combo_lang)

        top_row.addSpacing(4)
        top_row.addWidget(QLabel("Stimme:"))
        self.combo_voice = QComboBox()
        self.combo_voice.setToolTip("Wähle die Stimme die den Text vorlesen soll")
        top_row.addWidget(self.combo_voice, 1)

        voice_outer.addLayout(top_row)

        # Zeile 2: Geschwindigkeit + Lautstärke nebeneinander
        sliders_row = QHBoxLayout()
        sliders_row.setSpacing(16)

        # Geschwindigkeit
        sliders_row.addWidget(QLabel("Geschw.:"))
        self.slider_speed = QSlider(Qt.Orientation.Horizontal)
        self.slider_speed.setMinimum(-50)
        self.slider_speed.setMaximum(50)
        self.slider_speed.setValue(0)
        self.slider_speed.setToolTip("Sprechgeschwindigkeit (-50 = langsamer, +50 = schneller)")
        sliders_row.addWidget(self.slider_speed, 2)
        self.label_speed = QLabel("Normal")
        self.label_speed.setFixedWidth(100)
        self.label_speed.setObjectName("label_subtitle")
        sliders_row.addWidget(self.label_speed)

        sliders_row.addSpacing(8)

        # Lautstärke
        sliders_row.addWidget(QLabel("Lautstärke:"))
        self.slider_volume = QSlider(Qt.Orientation.Horizontal)
        self.slider_volume.setMinimum(-50)
        self.slider_volume.setMaximum(50)
        self.slider_volume.setValue(0)
        self.slider_volume.setToolTip("Lautstärke des vorgelesenen Texts")
        sliders_row.addWidget(self.slider_volume, 2)
        self.label_volume = QLabel("Normal")
        self.label_volume.setFixedWidth(100)
        self.label_volume.setObjectName("label_subtitle")
        sliders_row.addWidget(self.label_volume)

        voice_outer.addLayout(sliders_row)
        layout.addWidget(voice_group)

        self.slider_speed.valueChanged.connect(self._update_speed_label)
        self.slider_volume.valueChanged.connect(self._update_volume_label)

        # ── Text-Eingabe (expandiert) ──────────────────────────────────────
        text_group = QGroupBox("📝  Text eingeben")
        text_layout = QVBoxLayout(text_group)
        text_layout.setContentsMargins(12, 16, 12, 10)
        text_layout.setSpacing(6)

        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText(
            "Gib hier deinen Text ein...\n\n"
            "Zum Beispiel:\n"
            "Hallo! Ich bin TmYNoobs VoiceMorph. Ich kann jeden Text für dich vorlesen."
        )
        self.text_edit.setMinimumHeight(100)
        # Expandiert vertikal – füllt den gesamten verfügbaren Platz
        self.text_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        text_layout.addWidget(self.text_edit, 1)

        char_row = QHBoxLayout()
        self.label_char_count = QLabel("0 Zeichen")
        self.label_char_count.setObjectName("label_subtitle")
        char_row.addWidget(self.label_char_count)
        char_row.addStretch()
        btn_clear = QPushButton("🗑  Löschen")
        btn_clear.setObjectName("btn_secondary")
        btn_clear.clicked.connect(self.text_edit.clear)
        char_row.addWidget(btn_clear)
        text_layout.addLayout(char_row)

        layout.addWidget(text_group, 1)  # stretch=1 → wächst mit dem Fenster

        self.text_edit.textChanged.connect(self._update_char_count)

        # ── Aktions-Buttons (immer sichtbar, ganz unten) ────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.btn_speak = QPushButton("▶  Vorlesen")
        self.btn_speak.setObjectName("btn_start")
        self.btn_speak.clicked.connect(self._speak)
        btn_row.addWidget(self.btn_speak, 2)

        self.btn_stop_speaking = QPushButton("⏹  Stop")
        self.btn_stop_speaking.setObjectName("btn_stop")
        self.btn_stop_speaking.setEnabled(False)
        self.btn_stop_speaking.clicked.connect(self._stop_speaking)
        btn_row.addWidget(self.btn_stop_speaking, 1)

        self.btn_save_audio = QPushButton("💾  Als Datei speichern")
        self.btn_save_audio.setObjectName("btn_secondary")
        self.btn_save_audio.clicked.connect(self._save_to_file)
        btn_row.addWidget(self.btn_save_audio, 2)

        layout.addLayout(btn_row)

        self.label_tts_status = QLabel("")
        self.label_tts_status.setObjectName("label_subtitle")
        self.label_tts_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label_tts_status)

    # ── Stimmen Laden ────────────────────────────────────────────────────────

    def _load_voices(self):
        self._online_voices = online_tts.ALL_VOICES
        self._offline_voices = offline_tts.list_voices()
        self._filter_voices()

    def _on_mode_changed(self, idx: int):
        self._filter_voices()

    def _filter_voices(self):
        mode = self.combo_mode.currentData()
        lang_filter = self.combo_lang.currentData()
        self.combo_voice.clear()

        if mode == "online":
            voices = [
                v for v in self._online_voices
                if lang_filter == "all" or v["lang"] == lang_filter
            ]
            for v in voices:
                self.combo_voice.addItem(v["name"], v["id"])
        else:
            # Offline – nach Sprache filtern wenn möglich
            all_voices = self._offline_voices
            if lang_filter != "all" and all_voices:
                filtered = [
                    v for v in all_voices
                    if v.get("lang", "").startswith(lang_filter)
                ]
                voices = filtered if filtered else all_voices
            else:
                voices = all_voices

            if not voices:
                self.combo_voice.addItem("Keine Offline-Stimmen gefunden", None)
            else:
                for v in voices:
                    self.combo_voice.addItem(v["name"], v["id"])

    # ── Steuerung ────────────────────────────────────────────────────────────

    def _update_char_count(self):
        count = len(self.text_edit.toPlainText())
        self.label_char_count.setText(f"{count:,} Zeichen".replace(",", "."))

    def _update_speed_label(self, val: int):
        if val == 0:
            self.label_speed.setText("Normal")
        elif val > 0:
            self.label_speed.setText(f"+{val}% schneller")
        else:
            self.label_speed.setText(f"{abs(val)}% langsamer")

    def _update_volume_label(self, val: int):
        if val == 0:
            self.label_volume.setText("Normal")
        elif val > 0:
            self.label_volume.setText(f"+{val}% lauter")
        else:
            self.label_volume.setText(f"{abs(val)}% leiser")

    def _speak(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Kein Text", "Bitte gib erst einen Text ein!")
            return

        mode     = self.combo_mode.currentData()
        voice_id = self.combo_voice.currentData()
        rate     = self.slider_speed.value()
        volume   = self.slider_volume.value()

        self._set_speaking(True)

        if mode == "online":
            online_tts.speak_text(
                text, voice_id, rate, volume,
                on_done=self._on_speak_done,
                on_error=self._on_speak_error,
            )
        else:
            offline_tts.speak_text(
                text, voice_id, rate, volume,
                on_done=self._on_speak_done,
                on_error=self._on_speak_error,
            )

    def _stop_speaking(self):
        import sounddevice as sd
        try:
            sd.stop()
        except Exception:
            pass
        self._set_speaking(False)
        self.label_tts_status.setText("Gestoppt.")

    def _save_to_file(self):
        text = self.text_edit.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Kein Text", "Bitte gib erst einen Text ein!")
            return

        mode     = self.combo_mode.currentData()
        voice_id = self.combo_voice.currentData()

        if mode == "offline":
            QMessageBox.information(
                self, "Offline-Modus",
                "Das Speichern als Datei ist nur im Online-Modus möglich.\n"
                "Bitte wechsle zu 'Online' um die Datei zu speichern."
            )
            return

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Text als Audiodatei speichern",
            str(Path.home() / "vorlesen.mp3"),
            "MP3-Datei (*.mp3)",
        )
        if not save_path:
            return

        rate   = self.slider_speed.value()
        volume = self.slider_volume.value()

        self.label_tts_status.setText("Speichere Datei...")
        self.btn_save_audio.setEnabled(False)

        def _save_worker():
            success = online_tts.synthesize_to_file(text, voice_id, save_path, rate, volume)
            from PyQt6.QtCore import QMetaObject, Qt
            if success:
                self._save_result = ("ok", save_path)
            else:
                self._save_result = ("error", "Datei konnte nicht gespeichert werden.\nIst das Internet aktiv?")
            QMetaObject.invokeMethod(self, "_save_done_slot", Qt.ConnectionType.QueuedConnection)

        import threading
        threading.Thread(target=_save_worker, daemon=True).start()

    @pyqtSlot()
    def _save_done_slot(self):
        self.btn_save_audio.setEnabled(True)
        status, msg = getattr(self, "_save_result", ("error", "Unbekannter Fehler"))
        if status == "ok":
            self.label_tts_status.setText(f"✅ Gespeichert: {Path(msg).name}")
            QMessageBox.information(self, "Gespeichert! ✅", f"Die Audiodatei wurde gespeichert:\n{msg}")
        else:
            self.label_tts_status.setText("❌ Fehler beim Speichern")
            QMessageBox.critical(self, "Fehler", msg)

    def _set_speaking(self, speaking: bool):
        self._is_speaking = speaking
        self.btn_speak.setEnabled(not speaking)
        self.btn_stop_speaking.setEnabled(speaking)
        self.btn_save_audio.setEnabled(not speaking)
        if speaking:
            self.label_tts_status.setText("🔊 Liest vor...")
        else:
            self.label_tts_status.setText("")

    def _on_speak_done(self):
        from PyQt6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(self, "_speak_done_slot", Qt.ConnectionType.QueuedConnection)

    def _on_speak_error(self, message: str):
        self._speak_error_msg = message
        from PyQt6.QtCore import QMetaObject, Qt
        QMetaObject.invokeMethod(self, "_speak_error_slot", Qt.ConnectionType.QueuedConnection)

    @pyqtSlot()
    def _speak_done_slot(self):
        self._set_speaking(False)
        self.label_tts_status.setText("✅ Fertig.")
        QTimer.singleShot(3000, lambda: self.label_tts_status.setText(""))

    @pyqtSlot()
    def _speak_error_slot(self):
        self._set_speaking(False)
        self.label_tts_status.setText("❌ Fehler")
        QMessageBox.critical(self, "TTS-Fehler", getattr(self, "_speak_error_msg", "Unbekannter Fehler"))
