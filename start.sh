#!/bin/bash

# ──────────────────────────────────────────────────────────────────────────────
# TmYNoobs VoiceMorph & Text2Speech – Starter Script (Linux)
# macOS-Nutzer: Bitte start.command per Doppelklick starten!
# ──────────────────────────────────────────────────────────────────────────────

# Arbeitsverzeichnis = Ordner dieses Skripts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║    TmYNoobs VoiceMorph & Text2Speech             ║"
echo "  ║    Willkommen! Das Programm wird gestartet...    ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""

# ─── Schritt 1: Python prüfen ─────────────────────────────────────────────────
echo "  [1/3] Prüfe ob Python installiert ist..."

# Versuche python3, dann python
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
fi

if [ -z "$PYTHON_CMD" ]; then
    echo ""
    echo "  ❌ Python wurde nicht gefunden!"
    echo ""
    echo "  Python ist kostenlos und muss einmalig installiert werden."
    echo ""

    # macOS-spezifische Anleitung
    echo "  👉 Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  👉 Fedora:        sudo dnf install python3 python3-pip"
    echo "  👉 Arch Linux:    sudo pacman -S python python-pip"

    echo ""
    echo "  Nach der Installation: Starte start.sh erneut."
    echo ""
    read -p "  Drücke ENTER zum Beenden..." dummy
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "  ✅ $PYTHON_VERSION gefunden!"

# ─── Schritt 2: Dependencies installieren ─────────────────────────────────────
echo ""
echo "  [2/3] Installiere benötigte Pakete (nur beim ersten Start nötig)..."
echo "  Das kann beim ersten Mal 1-2 Minuten dauern - bitte warten..."
echo ""

# Sicherstellen dass pip verfügbar ist
$PYTHON_CMD -m ensurepip --upgrade --quiet 2>/dev/null || true
$PYTHON_CMD -m pip install --upgrade pip --quiet 2>/dev/null || true

$PYTHON_CMD -m pip install -r "$SCRIPT_DIR/requirements.txt" --quiet
if [ $? -ne 0 ]; then
    echo ""
    echo "  ❌ Bei der Installation ist ein Fehler aufgetreten."
    echo ""
    echo "  Versuche es manuell mit:"
    echo "  $PYTHON_CMD -m pip install -r requirements.txt"
    echo ""
    echo "  Falls das Problem weiterhin besteht:"
    echo "  https://github.com/TmYNooB/VoiceMorph-TTS/issues"
    echo ""
    read -p "  Drücke ENTER zum Beenden..." dummy
    exit 1
fi

echo "  ✅ Alle Pakete installiert!"

# ─── Schritt 3: App starten ───────────────────────────────────────────────────
echo ""
echo "  [3/3] Starte TmYNoobs VoiceMorph..."
echo ""

$PYTHON_CMD src/main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "  ❌ Die App wurde unerwartet beendet."
    echo ""
    echo "  Bitte erstelle ein Issue auf GitHub mit dem obigen Fehler:"
    echo "  https://github.com/TmYNooB/VoiceMorph-TTS/issues"
    echo ""
    read -p "  Drücke ENTER zum Beenden..." dummy
fi
