#!/bin/bash

# ──────────────────────────────────────────────────────────────────────────────
# TmYNoobs VoiceMorph & Text2Speech – Starter (macOS)
# Doppelklick auf diese Datei startet die App automatisch im Terminal!
# Das Terminalfenster schließt sich automatisch wenn die App beendet wird.
# ──────────────────────────────────────────────────────────────────────────────

# Arbeitsverzeichnis = Ordner dieser Datei (wichtig bei .command!)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Terminal-Fenster-ID jetzt merken (bevor weitere Fenster aufgehen könnten)
TERM_WIN_ID=$(osascript -e 'tell application "Terminal" to id of front window' 2>/dev/null)

# Hilfsfunktion: Terminal-Fenster sauber schließen.
# Der Close-Befehl läuft im Hintergrund NACHDEM die Shell beendet ist,
# damit macOS Terminal nicht mehr fragt "Möchtest du wirklich schließen?".
_close_terminal() {
    if [ -n "$TERM_WIN_ID" ]; then
        ( sleep 0.4 && osascript -e "tell application \"Terminal\" to close (every window whose id is $TERM_WIN_ID)" 2>/dev/null ) &
    fi
}

echo ""
echo "  ╔══════════════════════════════════════════════════╗"
echo "  ║    TmYNoobs VoiceMorph & Text2Speech             ║"
echo "  ║    Willkommen! Das Programm wird gestartet...    ║"
echo "  ╚══════════════════════════════════════════════════╝"
echo ""

# ─── Schritt 1: Python prüfen ─────────────────────────────────────────────────
echo "  [1/3] Prüfe ob Python installiert ist..."

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
    echo "  👉 Option 1 (empfohlen): https://www.python.org/downloads/"
    echo "     Lade Python 3 herunter und installiere es."
    echo ""
    echo "  Nach der Installation: Doppelklicke start.command erneut."
    echo ""
    open "https://www.python.org/downloads/" 2>/dev/null || true
    read -p "  Drücke ENTER zum Beenden..." dummy
    _close_terminal
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
echo "  ✅ $PYTHON_VERSION gefunden!"

# ─── Schritt 2: Dependencies installieren ─────────────────────────────────────
echo ""
echo "  [2/3] Installiere benötigte Pakete (nur beim ersten Start nötig)..."
echo "  Das kann beim ersten Mal 1-2 Minuten dauern - bitte warten..."
echo ""

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
    echo "  Hilfe: https://github.com/TmYNooB/VoiceMorph-TTS/issues"
    echo ""
    read -p "  Drücke ENTER zum Beenden..." dummy
    _close_terminal
    exit 1
fi

echo "  ✅ Alle Pakete installiert!"

# ─── Schritt 3: Mikrofon-Berechtigung hinweisen (macOS-spezifisch) ─────────────
echo ""
echo "  ℹ️  macOS-Hinweis: Falls ein Dialog 'Möchtest du dem Programm Zugriff"
echo "     auf das Mikrofon erlauben?' erscheint – bitte auf OK klicken!"
echo ""

# ─── Schritt 4: App starten ───────────────────────────────────────────────────
echo "  [3/3] Starte TmYNoobs VoiceMorph..."
echo "  (Dieses Fenster schliet sich automatisch wenn du die App beendest.)"
echo ""

$PYTHON_CMD src/main.py
APP_EXIT=$?

if [ $APP_EXIT -eq 0 ]; then
    # Sauberes Beenden → Terminal sofort schließen
    _close_terminal
else
    echo ""
    echo "  ❌ Die App wurde unerwartet beendet (Fehlercode: $APP_EXIT)."
    echo ""
    echo "  Bitte erstelle ein Issue auf GitHub mit dem obigen Fehler:"
    echo "  https://github.com/TmYNooB/VoiceMorph-TTS/issues"
    echo ""
    read -p "  Drücke ENTER zum Beenden..." dummy
    _close_terminal
fi
