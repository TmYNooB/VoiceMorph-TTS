# 🎤 TmYNoobs VoiceMorph & Text2Speech

Ein kostenloser **Voice Changer** und **Text-to-Speech Player** für Windows, macOS und Linux.  
Verändere deine Stimme in Echtzeit, lass Texte auf Deutsch oder Englisch vorlesen – alles gratis, ohne Anmeldung.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🎤 **Live Voice Changer** | Mikrofon → Effekt → Lautsprecher in Echtzeit |
| 📁 **Dateiverarbeitung** | Audiodatei laden, Effekt anwenden, speichern |
| 🎛️ **10 Stimm-Presets** | Robot, Chipmunk, Deep Voice, Telefon, Echo/Hall, Alien, Helium, Movie Villain, Stadion + Kein Effekt |
| ✨ **Custom Preset Creator** | Eigene Presets mit Schiebereglern erstellen und speichern |
| 💬 **Text-to-Speech (Online)** | Microsoft Edge Read-Aloud – sehr natürliche Stimmen, kein Account nötig |
| 💻 **Text-to-Speech (Offline)** | Funktioniert ohne Internet über OS-eigene Stimmen |
| 🇩🇪🇬🇧 **Deutsch & Englisch** | 5 deutsche + 5 englische TTS-Stimmen |
| 🌑 **Dark Mode UI** | Modern, dunkel, schön |
| 💾 **Audio speichern** | TTS-Output als MP3-Datei speichern |

---

## 🚀 Schnellstart (für Einsteiger – Schritt für Schritt)

### Schritt 1: Python installieren

Python ist eine kostenlose Software die du einmalig installieren musst.

**Windows:**
1. Gehe auf [python.org/downloads](https://www.python.org/downloads/)
2. Klicke auf den großen **"Download Python 3.x.x"** Knopf
3. Öffne die heruntergeladene `.exe` Datei
4. ⚠️ **WICHTIG:** Setze den Haken bei **"Add Python to PATH"** ganz unten!
5. Klicke auf **"Install Now"**
6. Fertig! ✅

**macOS:**
1. Gehe auf [python.org/downloads](https://www.python.org/downloads/)
2. Lade das macOS-Paket herunter und installiere es
3. Folge dem Installer-Assistenten
4. Fertig! ✅

**Linux:**
```bash
# Ubuntu / Debian:
sudo apt-get install python3 python3-pip

# Fedora:
sudo dnf install python3 python3-pip

# Arch Linux:
sudo pacman -S python python-pip
```

> **Hinweis für Linux-Nutzer:** Für die Offline-TTS-Funktion wird zusätzlich `espeak-ng` benötigt:  
> `sudo apt-get install espeak-ng` (Ubuntu/Debian)

---

### Schritt 2: App herunterladen

1. Gehe auf die [GitHub Releases Seite](https://github.com/TmYNooB/VoiceMorph-TTS/releases)
2. Lade die neuste Version herunter:
   - **Windows:** `VoiceMorph-Windows.zip`
   - **macOS:** `VoiceMorph-macOS.zip`
   - **Linux:** Quellcode als ZIP
3. Entpacke die ZIP-Datei in einen Ordner deiner Wahl

---

### Schritt 3: App starten

**Windows:**
- Doppelklicke auf **`start.bat`**  
  → Das Skript installiert automatisch alles was fehlt und startet die App!

**macOS:**
- Doppelklicke auf **`start.command`**  
  → Terminal öffnet sich automatisch und startet die App!  
  *(Falls macOS fragt ob du die Datei öffnen möchtest: „Öffnen" klicken)*

**Linux:**
- Rechtsklick auf **`start.sh`** → „Als Programm ausführen"  
  *(Falls das nicht klappt: Terminal öffnen → `bash start.sh` eingeben)*

**Das war's!** 🎉 Die App startet automatisch.

> 💡 **Beim ersten Start dauert es etwas länger** – die App installiert einige Pakete automatisch.  
> Das passiert nur einmal. Ab dem zweiten Start geht es sofort los.

---

## 🖥️ Vorgefertigte Binaries (kein Python nötig)

Wenn du keine Lust auf Python-Installation hast, findest du auf der [Releases Seite](https://github.com/TmYNooB/VoiceMorph-TTS/releases) auch fertige ausführbare Dateien:

| Plattform | Download | Hinweis |
|---|---|---|
| Windows | `VoiceMorph-v1.0.0-Windows.exe` | Direkt doppelklicken |
| macOS | `VoiceMorph-v1.0.0-macOS.dmg` | Öffnen → in Applications ziehen |
| Linux | `VoiceMorph-v1.0.0-Linux` | `chmod +x` dann ausführen |

> **Windows Sicherheitswarnung:** Windows Defender zeigt manchmal eine Warnung bei unbekannten Apps.  
> Klicke auf **"Weitere Informationen"** → **"Trotzdem ausführen"**. Die App ist sicher (Quellcode ist öffentlich auf GitHub).

---

## 🎛️ Bedienung

### Voice Changer Tab

1. **Mikrofon auswählen** – Wähle das gewünschte Mikrofon aus der Dropdown-Liste
2. **Ausgabe auswählen** – Wähle Lautsprecher oder Kopfhörer
3. **Preset wählen** – Klicke auf eines der vorgefertigten Presets (Robot, Chipmunk, ...)
4. **"Live starten"** klicken → deine Stimme wird live verändert ausgegeben
5. **"Stop"** zum Beenden

Für **Dateiverarbeitung:**
1. Auf **"Datei öffnen"** klicken und eine WAV/FLAC-Datei auswählen
2. Preset wählen
3. **"Effekt anwenden & speichern"** klicken

### Text-to-Speech Tab

1. Text ins Textfeld eingeben (beliebig lang!)
2. **Modus** wählen: Online (empfohlen) oder Offline (kein Internet nötig)
3. **Stimme** auswählen (Deutsch oder Englisch)
4. Geschwindigkeit und Lautstärke nach Wunsch anpassen
5. **"Vorlesen"** klicken

Optional: **"Als Datei speichern"** speichert den Text als MP3-Datei.

### Eigene Presets erstellen

1. Menü → **"Presets"** → **"Neues Preset erstellen"**
2. Schieberegler einstellen (Pitch, Hall, Verzerrung, etc.)
3. Namen und Icon vergeben
4. **"Preset speichern"** → das Preset erscheint in der Liste

---

## 🔧 Manuelle Installation (für Fortgeschrittene)

```bash
# Repository klonen
git clone https://github.com/TmYNooB/VoiceMorph-TTS.git
cd VoiceMorph-TTS

# Abhängigkeiten installieren
pip install -r requirements.txt

# App starten
python src/main.py
```

**Abhängigkeits-Check:**
```bash
python setup_check.py
```

---

## ❓ Häufige Probleme

**"Mikrofon nicht gefunden"**
- Prüfe ob das Mikrofon angeschlossen und eingeschaltet ist
- Windows: Systemeinstellungen → Datenschutz → Mikrofon → App-Zugriff erlauben
- macOS: Systemeinstellungen → Datenschutz & Sicherheit → Mikrofon → erlauben

**"TTS funktioniert nicht" (Online)**
- Prüfe deine Internetverbindung
- Versuche den Offline-Modus als Alternative

**"pedalboard Installation schlägt fehl"**
- Stelle sicher dass Visual C++ Redistributable installiert ist (Windows)
- Linux: `sudo apt-get install portaudio19-dev python3-dev`

**Weitere Hilfe:** [GitHub Issues](https://github.com/TmYNooB/VoiceMorph-TTS/issues)

---

## 🛠️ Für Entwickler

### Projektstruktur

```
src/
├── main.py                 # Entry Point
├── ui/
│   ├── main_window.py      # Hauptfenster
│   ├── voice_tab.py        # Voice Changer Tab
│   ├── tts_tab.py          # TTS Tab
│   ├── preset_editor.py    # Custom Preset Creator
│   └── styles.py           # Dark Mode Stylesheet
├── audio/
│   ├── engine.py           # Live Audio Pipeline
│   ├── effects.py          # Effekte (pedalboard + scipy)
│   └── file_processor.py   # Dateiverarbeitung
├── tts/
│   ├── online_tts.py       # edge-tts wrapper
│   └── offline_tts.py      # pyttsx3 wrapper
└── presets/
    ├── builtin.py          # Builtin Preset-Definitionen
    └── manager.py          # Preset laden/speichern
```

### Build (lokal)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name VoiceMorph src/main.py
```

---

## 📜 Lizenz

**GPL v3** – freie und quelloffene Software.  
Du darfst den Code verwenden, verändern und weitergeben – aber Ableitungen müssen ebenfalls unter GPL v3 veröffentlicht werden.

Vollständiger Lizenztext: [LICENSE](LICENSE)

---

## 🙏 Danksagungen

- [edge-tts](https://github.com/rany2/edge-tts) – Kostenloser MS Edge TTS Wrapper
- [pedalboard](https://github.com/spotify/pedalboard) – Audio-Effekte von Spotify
- [sounddevice](https://python-sounddevice.readthedocs.io/) – Cross-Platform Audio I/O
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) – UI Framework

---

<div align="center">

Entwickelt mit ❤️ von **TmYNooB**

[GitHub](https://github.com/TmYNooB/VoiceMorph-TTS) · [Issues & Feedback](https://github.com/TmYNooB/VoiceMorph-TTS/issues)

</div>
