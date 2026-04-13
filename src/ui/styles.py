"""Dark Mode QSS Stylesheet für TmYNoobs VoiceMorph & Text2Speech."""

DARK_PALETTE = {
    "bg_primary":    "#1a1a2e",
    "bg_secondary":  "#16213e",
    "bg_card":       "#0f3460",
    "accent":        "#e94560",
    "accent_hover":  "#ff6b6b",
    "accent_dim":    "#c73652",
    "text_primary":  "#eaeaea",
    "text_secondary":"#a0a0b0",
    "text_dim":      "#606080",
    "border":        "#2a2a4a",
    "success":       "#4ade80",
    "warning":       "#fbbf24",
    "error":         "#f87171",
    "slider_groove": "#2a2a4a",
    "slider_handle": "#e94560",
    "tab_active":    "#e94560",
    "tab_inactive":  "#1a1a2e",
}

STYLESHEET = """
/* ═══════════════════════════════════════════════════
   TmYNoobs VoiceMorph – Dark Mode Stylesheet
   ═══════════════════════════════════════════════════ */

QMainWindow, QWidget {
    background-color: #1a1a2e;
    color: #eaeaea;
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

/* ── Tab Widget ─────────────────────────────────── */
QTabWidget::pane {
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    background-color: #16213e;
    margin-top: -1px;
}

QTabBar::tab {
    background-color: #1a1a2e;
    color: #a0a0b0;
    padding: 10px 24px;
    margin-right: 4px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
    font-size: 13px;
    min-width: 140px;
}

QTabBar::tab:selected {
    background-color: #e94560;
    color: #ffffff;
}

QTabBar::tab:hover:!selected {
    background-color: #2a2a4a;
    color: #eaeaea;
}

/* ── Buttons ────────────────────────────────────── */
QPushButton {
    background-color: #e94560;
    color: #ffffff;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
    min-height: 36px;
}

QPushButton:hover {
    background-color: #ff6b6b;
}

QPushButton:pressed {
    background-color: #c73652;
}

QPushButton:disabled {
    background-color: #2a2a4a;
    color: #606080;
}

QPushButton#btn_secondary {
    background-color: #2a2a4a;
    color: #eaeaea;
    border: 1px solid #3a3a5a;
}

QPushButton#btn_secondary:hover {
    background-color: #3a3a5a;
}

QPushButton#btn_start {
    background-color: #4ade80;
    color: #0f1a0f;
    font-size: 15px;
    padding: 14px 32px;
    border-radius: 10px;
    min-height: 48px;
}

QPushButton#btn_start:hover {
    background-color: #6ee7a0;
}

QPushButton#btn_stop {
    background-color: #f87171;
    color: #1a0000;
    font-size: 15px;
    padding: 14px 32px;
    border-radius: 10px;
    min-height: 48px;
}

QPushButton#btn_stop:hover {
    background-color: #fca5a5;
}

/* ── Labels ─────────────────────────────────────── */
QLabel {
    color: #eaeaea;
    background: transparent;
}

QLabel#label_title {
    font-size: 20px;
    font-weight: bold;
    color: #e94560;
}

QLabel#label_subtitle {
    font-size: 12px;
    color: #a0a0b0;
}

QLabel#label_section {
    font-size: 14px;
    font-weight: bold;
    color: #eaeaea;
    padding: 4px 0;
}

QLabel#label_status_active {
    color: #4ade80;
    font-weight: bold;
}

QLabel#label_status_inactive {
    color: #a0a0b0;
}

/* ── Sliders ─────────────────────────────────────── */
QSlider::groove:horizontal {
    height: 6px;
    background-color: #2a2a4a;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background-color: #e94560;
    width: 18px;
    height: 18px;
    margin: -6px 0;
    border-radius: 9px;
}

QSlider::handle:horizontal:hover {
    background-color: #ff6b6b;
}

QSlider::sub-page:horizontal {
    background-color: #e94560;
    border-radius: 3px;
}

/* ── ComboBox (Dropdown) ─────────────────────────── */
QComboBox {
    background-color: #16213e;
    color: #eaeaea;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 8px 12px;
    min-height: 36px;
    font-size: 13px;
}

QComboBox:hover {
    border-color: #e94560;
}

QComboBox::drop-down {
    border: none;
    width: 24px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
}

QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #eaeaea;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    selection-background-color: #e94560;
    selection-color: #ffffff;
    outline: none;
}

/* ── TextEdit / TextArea ─────────────────────────── */
QTextEdit, QPlainTextEdit {
    background-color: #16213e;
    color: #eaeaea;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 10px;
    font-size: 13px;
    line-height: 1.5;
    selection-background-color: #e94560;
}

QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #e94560;
}

/* ── LineEdit (Einzeilig) ────────────────────────── */
QLineEdit {
    background-color: #16213e;
    color: #eaeaea;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 8px 12px;
    min-height: 36px;
    font-size: 13px;
    selection-background-color: #e94560;
}

QLineEdit:focus {
    border-color: #e94560;
}

/* ── GroupBox ────────────────────────────────────── */
QGroupBox {
    border: 1px solid #2a2a4a;
    border-radius: 10px;
    margin-top: 16px;
    padding: 12px;
    color: #eaeaea;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #e94560;
    font-size: 13px;
}

/* ── Checkboxes ───────────────────────────────────── */
QCheckBox {
    color: #eaeaea;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid #2a2a4a;
    background-color: #16213e;
}

QCheckBox::indicator:checked {
    background-color: #e94560;
    border-color: #e94560;
}

/* ── Scrollbar ───────────────────────────────────── */
QScrollBar:vertical {
    background-color: #16213e;
    width: 10px;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #2a2a4a;
    border-radius: 5px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #e94560;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* ── Progress Bar ────────────────────────────────── */
QProgressBar {
    background-color: #2a2a4a;
    border-radius: 4px;
    text-align: center;
    color: #eaeaea;
    height: 8px;
}

QProgressBar::chunk {
    background-color: #e94560;
    border-radius: 4px;
}

/* ── Spinner / SpinBox ───────────────────────────── */
QSpinBox, QDoubleSpinBox {
    background-color: #16213e;
    color: #eaeaea;
    border: 1px solid #2a2a4a;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 36px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #e94560;
}

/* ── ToolTips ────────────────────────────────────── */
QToolTip {
    background-color: #0f3460;
    color: #eaeaea;
    border: 1px solid #e94560;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}

/* ── Statusbar ───────────────────────────────────── */
QStatusBar {
    background-color: #0f1020;
    color: #a0a0b0;
    font-size: 12px;
    border-top: 1px solid #2a2a4a;
}

/* ── Karten-Widget ───────────────────────────────── */
QFrame#card {
    background-color: #16213e;
    border: 1px solid #2a2a4a;
    border-radius: 12px;
}

/* ── VU-Meter Label ──────────────────────────────── */
QLabel#vu_meter {
    background-color: #0a0a1a;
    border: 1px solid #2a2a4a;
    border-radius: 6px;
    padding: 4px;
}
"""
