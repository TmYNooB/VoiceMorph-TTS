"""
setup_check.py – Abhängigkeits-Checker für TmYNoobs VoiceMorph & Text2Speech

Dieses Skript prüft, ob alle notwendigen Pakete korrekt installiert sind.
Bei Problemen werden verständliche Fehlermeldungen ausgegeben.
"""

import sys
import subprocess

REQUIRED = [
    ("PyQt6",       "PyQt6",       "Benutzeroberfläche"),
    ("sounddevice", "sounddevice", "Audio-Aufnahme und -Wiedergabe"),
    ("numpy",       "numpy",       "Audio-Verarbeitung"),
    ("scipy",       "scipy",       "Audio-Effekte"),
    ("pedalboard",  "pedalboard",  "Stimm-Effekte"),
    ("edge_tts",    "edge-tts",    "Online Text-To-Speech"),
    ("pyttsx3",     "pyttsx3",     "Offline Text-To-Speech"),
    ("soundfile",   "soundfile",   "Audio-Dateiverarbeitung"),
]


def main():
    print()
    print("  TmYNoobs VoiceMorph – Abhängigkeits-Check")
    print("  " + "═" * 48)
    print()

    python_version = sys.version_info
    print(f"  Python-Version: {python_version.major}.{python_version.minor}.{python_version.micro}")

    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print()
        print("  ❌ Python 3.9 oder neuer wird benötigt!")
        print("  👉 Bitte lade die neueste Version herunter: https://www.python.org/downloads/")
        return False

    print("  ✅ Python-Version ist kompatibel")
    print()
    print("  Prüfe installierte Pakete...")
    print()

    all_ok = True
    missing = []

    for import_name, pip_name, description in REQUIRED:
        try:
            __import__(import_name)
            print(f"  ✅ {pip_name:<15} – {description}")
        except ImportError:
            print(f"  ❌ {pip_name:<15} – {description} (FEHLT!)")
            missing.append(pip_name)
            all_ok = False

    print()

    if all_ok:
        print("  ✅ Alles ist bereit! Du kannst die App starten.")
        print()
        print("  Starte mit:  python src/main.py")
        print("  Oder einfach start.bat (Windows) oder start.sh (Mac/Linux) doppelklicken!")
    else:
        print(f"  ❌ {len(missing)} Paket(e) fehlen: {', '.join(missing)}")
        print()
        print("  Installiere alle fehlenden Pakete mit:")
        print()
        print("    python -m pip install -r requirements.txt")
        print()
        user_input = input("  Soll ich das jetzt automatisch tun? (j/n): ").strip().lower()
        if user_input in ("j", "ja", "y", "yes"):
            print()
            print("  Installiere Pakete...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                capture_output=False
            )
            if result.returncode == 0:
                print()
                print("  ✅ Alle Pakete wurden erfolgreich installiert!")
                print("  Du kannst die App jetzt starten.")
            else:
                print()
                print("  ❌ Installation fehlgeschlagen.")
                print("  Bitte erstelle ein Issue: https://github.com/TmYNooB/VoiceMorph-TTS/issues")

    print()
    return all_ok


if __name__ == "__main__":
    success = main()
    if not success:
        input("  Drücke ENTER zum Beenden...")
        sys.exit(1)
