"""
main.py – Entry Point für TmYNoobs VoiceMorph & Text2Speech.

Startet die PyQt6-Applikation.
"""

import sys
import os

# Sicherstellen dass src/ im Python-Pfad ist (bei Doppelklick-Start)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt

from ui.styles import STYLESHEET
from ui.main_window import MainWindow


def main():
    # High-DPI Support (besonders wichtig für Windows)
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("TmYNoobs VoiceMorph & Text2Speech")
    app.setOrganizationName("TmYNooB")
    app.setApplicationVersion("1.0.0")
    app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
