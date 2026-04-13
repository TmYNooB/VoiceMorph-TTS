"""
Custom Preset Creator – Guided UI zum Erstellen eigener Stimm-Presets.
"""

import uuid
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSlider, QLineEdit, QGroupBox, QComboBox, QSizePolicy,
    QMessageBox, QScrollArea, QWidget,
)
from PyQt6.QtCore import Qt, pyqtSignal

from presets.builtin import PARAM_DESCRIPTIONS, DEFAULT_PARAMS


ICONS = ["⭐", "🎭", "👾", "🎵", "🔥", "💫", "🎪", "🌊", "⚡", "🎯"]


class PresetEditorDialog(QDialog):
    """
    Dialog zum Erstellen oder Bearbeiten eines Custom Presets.
    Gibt beim Accept das fertige Preset-Dict zurück.
    """

    preset_saved = pyqtSignal(dict)

    def __init__(self, parent=None, existing_preset: dict = None):
        super().__init__(parent)
        self._sliders: dict[str, QSlider] = {}
        self._labels:  dict[str, QLabel]  = {}
        self._existing = existing_preset
        self.setWindowTitle("✨ Eigenes Preset erstellen")
        self.setMinimumWidth(560)
        self.setMinimumHeight(600)
        self._build_ui()
        if existing_preset:
            self._load_preset(existing_preset)

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setSpacing(16)
        outer.setContentsMargins(20, 20, 20, 20)

        # ── Titel ──────────────────────────────────────────────────────────
        title = QLabel("✨  Eigenes Preset erstellen")
        title.setObjectName("label_title")
        outer.addWidget(title)

        hint = QLabel(
            "Stelle die Regler nach Belieben ein. Du kannst jederzeit auf\n"
            "\"Vorschau\" klicken um zu hören wie dein Preset klingt."
        )
        hint.setObjectName("label_subtitle")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        # ── Name & Icon ────────────────────────────────────────────────────
        meta_group = QGroupBox("📛  Preset-Name")
        meta_layout = QHBoxLayout(meta_group)

        self.combo_icon = QComboBox()
        for icon in ICONS:
            self.combo_icon.addItem(icon)
        self.combo_icon.setFixedWidth(60)
        meta_layout.addWidget(self.combo_icon)

        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("z.B. Mein Roboter-Preset")
        meta_layout.addWidget(self.input_name, 1)

        outer.addWidget(meta_group)

        # ── Effekt-Regler (scrollbar) ──────────────────────────────────────
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(scroll_area.Shape.NoFrame)

        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(14)

        effects_group = QGroupBox("🎛️  Effekte einstellen")
        effects_layout = QVBoxLayout(effects_group)
        effects_layout.setSpacing(10)

        for param_key, (display_name, unit, min_val, max_val, default) in PARAM_DESCRIPTIONS.items():
            row_widget = QWidget()
            row = QHBoxLayout(row_widget)
            row.setContentsMargins(0, 0, 0, 0)

            lbl_name = QLabel(display_name)
            lbl_name.setFixedWidth(200)
            row.addWidget(lbl_name)

            slider = QSlider(Qt.Orientation.Horizontal)

            is_int = isinstance(min_val, int) and isinstance(max_val, int)
            if is_int:
                slider.setMinimum(int(min_val))
                slider.setMaximum(int(max_val))
                slider.setValue(int(default))
            else:
                # Float-Slider: multipliziert mit 100
                slider.setMinimum(int(min_val * 100))
                slider.setMaximum(int(max_val * 100))
                slider.setValue(int(float(default) * 100))

            slider.setProperty("param_key", param_key)
            slider.setProperty("is_int", is_int)
            slider.setProperty("unit", unit)
            row.addWidget(slider, 1)

            val_label = QLabel()
            val_label.setFixedWidth(90)
            val_label.setObjectName("label_subtitle")
            row.addWidget(val_label)

            self._sliders[param_key] = slider
            self._labels[param_key] = val_label

            slider.valueChanged.connect(lambda v, k=param_key: self._update_label(k))
            self._update_label(param_key)

            effects_layout.addWidget(row_widget)

        scroll_layout.addWidget(effects_group)

        # Preset-Tipps
        tips_group = QGroupBox("💡  Tipps")
        tips_layout = QVBoxLayout(tips_group)
        tips = QLabel(
            "• Pitch: Negativ = tiefere Stimme, Positiv = höhere Stimme\n"
            "• Hall-Intensität auf 0 = kein Hall, auf 1.0 = maximaler Hall\n"
            "• Verzerrung gibt einen raueren, roboterhaften Sound\n"
            "• Ringmod-Frequenz > 0 = metallischer/futuristischer Klang\n"
            "• Bitcrush 4-8 Bit = Lo-Fi Retro-Effekt, 0 = deaktiviert"
        )
        tips.setObjectName("label_subtitle")
        tips.setWordWrap(True)
        tips_layout.addWidget(tips)
        scroll_layout.addWidget(tips_group)

        scroll_area.setWidget(scroll_widget)
        outer.addWidget(scroll_area, 1)

        # ── Buttons ────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()

        btn_reset = QPushButton("↩  Zurücksetzen")
        btn_reset.setObjectName("btn_secondary")
        btn_reset.clicked.connect(self._reset_all)
        btn_row.addWidget(btn_reset)

        btn_row.addStretch()

        btn_cancel = QPushButton("Abbrechen")
        btn_cancel.setObjectName("btn_secondary")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_cancel)

        btn_save = QPushButton("💾  Preset speichern")
        btn_save.clicked.connect(self._save)
        btn_row.addWidget(btn_save)

        outer.addLayout(btn_row)

    def _update_label(self, key: str):
        slider = self._sliders[key]
        label  = self._labels[key]
        unit   = slider.property("unit") or ""
        is_int = slider.property("is_int")

        if is_int:
            val = slider.value()
            text = f"{val}" + (f" {unit}" if unit else "")
        else:
            val = slider.value() / 100.0
            text = f"{val:.2f}" + (f" {unit}" if unit else "")

        if val == slider.minimum() and not is_int:
            text = "Aus"

        label.setText(text)

    def _reset_all(self):
        for key, (_, unit, min_val, max_val, default) in PARAM_DESCRIPTIONS.items():
            slider = self._sliders[key]
            is_int = slider.property("is_int")
            if is_int:
                slider.setValue(int(default))
            else:
                slider.setValue(int(float(default) * 100))

    def _load_preset(self, preset: dict):
        self.input_name.setText(preset.get("name", ""))
        icon = preset.get("icon", "⭐")
        idx = ICONS.index(icon) if icon in ICONS else 0
        self.combo_icon.setCurrentIndex(idx)

        params = preset.get("params", {})
        for key, slider in self._sliders.items():
            val = params.get(key, DEFAULT_PARAMS.get(key, 0))
            is_int = slider.property("is_int")
            if is_int:
                slider.setValue(int(val))
            else:
                slider.setValue(int(float(val) * 100))

    def _build_preset(self) -> dict:
        params = {}
        for key, slider in self._sliders.items():
            is_int = slider.property("is_int")
            if is_int:
                params[key] = slider.value()
            else:
                params[key] = slider.value() / 100.0

        preset_id = (
            self._existing["id"]
            if self._existing and "id" in self._existing
            else "custom_" + uuid.uuid4().hex[:8]
        )

        return {
            "id":         preset_id,
            "name":       self.input_name.text().strip() or "Mein Preset",
            "description": "Eigenes Preset",
            "icon":       self.combo_icon.currentText(),
            "is_custom":  True,
            "params":     params,
        }

    def _save(self):
        name = self.input_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Name fehlt", "Bitte gib deinem Preset einen Namen!")
            self.input_name.setFocus()
            return

        preset = self._build_preset()
        self.preset_saved.emit(preset)
        self.accept()

    def get_preset(self) -> dict:
        """Gibt das Preset zurück (nach accept())."""
        return self._build_preset()
