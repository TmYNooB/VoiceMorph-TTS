@echo off
chcp 65001 >nul
title TmYNoobs VoiceMorph - Start

echo.
echo  ██╗   ██╗ ██████╗ ██╗ ██████╗███████╗███╗   ███╗ ██████╗ ██████╗ ██████╗ ██╗  ██╗
echo  ██║   ██║██╔═══██╗██║██╔════╝██╔════╝████╗ ████║██╔═══██╗██╔══██╗██╔══██╗██║  ██║
echo  ██║   ██║██║   ██║██║██║     █████╗  ██╔████╔██║██║   ██║██████╔╝██████╔╝███████║
echo  ╚██╗ ██╔╝██║   ██║██║██║     ██╔══╝  ██║╚██╔╝██║██║   ██║██╔══██╗██╔═══╝ ██╔══██║
echo   ╚████╔╝ ╚██████╔╝██║╚██████╗███████╗██║ ╚═╝ ██║╚██████╔╝██║  ██║██║     ██║  ██║
echo    ╚═══╝   ╚═════╝ ╚═╝ ╚═════╝╚══════╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝  ╚═╝
echo.
echo  TmYNoobs VoiceMorph ^& Text2Speech - Willkommen!
echo  ════════════════════════════════════════════════
echo.

:: ─── Schritt 1: Python prüfen ───────────────────────────────────────────────
echo  [1/3] Prüfe ob Python installiert ist...

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo  ❌ Python wurde nicht gefunden!
    echo.
    echo  Python ist eine kostenlose Software, die du einmalig installieren musst.
    echo  Das dauert nur ein paar Minuten und ist ganz einfach:
    echo.
    echo  👉 Gehe auf: https://www.python.org/downloads/
    echo  👉 Klicke auf den großen "Download Python" Knopf
    echo  👉 Öffne die heruntergeladene Datei
    echo  👉 WICHTIG: Setze den Haken bei "Add Python to PATH" ganz unten!
    echo  👉 Klicke auf "Install Now"
    echo  👉 Nach der Installation: Starte dieses Skript erneut
    echo.
    echo  Drücke eine beliebige Taste um den Browser zu öffnen...
    pause >nul
    start https://www.python.org/downloads/
    echo.
    echo  Wenn Python installiert ist, starte start.bat einfach nochmal.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo  ✅ Python %PYTHON_VERSION% gefunden!

:: ─── Schritt 2: Dependencies installieren ────────────────────────────────────
echo.
echo  [2/3] Installiere benötigte Pakete (nur beim ersten Start nötig)...
echo  Das kann beim ersten Mal 1-2 Minuten dauern - bitte warten...
echo.

python -m pip install --upgrade pip --quiet
if %errorlevel% neq 0 (
    echo.
    echo  ⚠️  Pip-Update fehlgeschlagen - versuche trotzdem fortzufahren...
)

python -m pip install -r "%~dp0requirements.txt" --quiet
if %errorlevel% neq 0 (
    echo.
    echo  ❌ Bei der Installation ist ein Fehler aufgetreten.
    echo.
    echo  Versuche es mit folgendem Befehl manuell:
    echo  python -m pip install -r requirements.txt
    echo.
    echo  Falls das Problem weiterhin besteht, erstelle ein Issue auf GitHub:
    echo  https://github.com/TmYNooB/VoiceMorph-TTS/issues
    echo.
    pause
    exit /b 1
)

echo  ✅ Alle Pakete installiert!

:: ─── Schritt 3: App starten ──────────────────────────────────────────────────
echo.
echo  [3/3] Starte TmYNoobs VoiceMorph...
echo.

cd /d "%~dp0"
python src\main.py

if %errorlevel% neq 0 (
    echo.
    echo  ❌ Die App konnte nicht gestartet werden.
    echo.
    echo  Bitte erstelle ein Issue auf GitHub mit dem obigen Fehler:
    echo  https://github.com/TmYNooB/VoiceMorph-TTS/issues
    echo.
    pause
)
