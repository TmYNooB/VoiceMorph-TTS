# Copilot Instructions – TmYNoobs VoiceMorph & Text2Speech

Hey Copilot! Willkommen im Projekt. Hier sind ein paar Dinge, die du über dieses Projekt wissen solltest, damit wir gut zusammenarbeiten können. Wir sind hier auf Augenhöhe unterwegs – locker, freundlich und manchmal auch etwas spaßig. 🎤

---

## Was ist das hier?

**TmYNoobs VoiceMorph & Text2Speech** ist eine Desktop-App zum:
1. **Voice Changing** – Mikrofon-Input in Echtzeit verändern (Robot, Chipmunk, Deep Voice, etc.) ODER Audiodateien verarbeiten
2. **Text-to-Speech** – Text vorlesen lassen, auf Deutsch und Englisch, online (Microsoft Edge TTS) und offline (pyttsx3)

---

## Grundsätze – bitte immer beachten!

### 🔑 Nutzer-Philosophie
**Unsere Nutzer haben NULL Technikwissen.** Wirklich gar keins. Wir schreiben Code, Features und Fehlermeldungen für jemanden, der nicht weiß was eine "Konsole" oder ein "Pfad" ist. Das bedeutet:
- Fehlermeldungen auf **Deutsch**, verständlich, freundlich, mit konkreten Handlungsanweisungen
- Keine technischen Begriffe in der UI ohne Erklärung
- Keine Abstürze ohne freundliche Aufforderung "Was soll ich jetzt tun?"
- Lieber eine Nachricht zu viel als zu wenig

### 💰 Keine Kosten
Alles was wir einbauen muss **kostenlos und unbegrenzt nutzbar** sein – für uns als Entwickler und für die Nutzer. Kein verstecktes Pricing, keine Rate Limits die den User blockieren.

### 🖥️ Cross-Platform
Der Code muss auf **Windows, macOS und Linux** laufen. Keine platform-spezifischen Shortcuts oder harte Pfade. Immer `pathlib.Path` statt String-Pfaden.

---

## Tech Stack

| Was | Womit | Warum |
|-----|-------|-------|
| UI | PyQt6 | Cross-platform, nativ, schnell |
| Audio I/O | sounddevice | Beste Cross-Platform-Option (PortAudio) |
| Audio-Effekte | pedalboard (Spotify) + scipy/numpy | Kostenlos, GPL-kompatibel, echtzeitfähig |
| TTS Online | edge-tts | Kostenlos, kein Key, sehr natürlich (MS Edge Read-Aloud) |
| TTS Offline | pyttsx3 | Kein Internet nötig, nutzt OS-Engines |
| Packaging | PyInstaller | Einfachstes cross-platform Packaging |
| CI/CD | GitHub Actions | Automatische Builds bei Tag-Push |

---

## Projektstruktur

```
src/
├── main.py               # Entry Point
├── ui/
│   ├── main_window.py    # Hauptfenster mit Menü und Tabs
│   ├── voice_tab.py      # Voice Changer Tab (Live + Datei)
│   ├── tts_tab.py        # Text-to-Speech Tab
│   ├── preset_editor.py  # Custom Preset Creator Dialog
│   └── styles.py         # Dark Mode QSS Stylesheet
├── audio/
│   ├── engine.py         # Live-Audio-Pipeline (sounddevice Stream)
│   ├── effects.py        # Effekte (pedalboard + scipy)
│   └── file_processor.py # Dateiverarbeitung
├── tts/
│   ├── online_tts.py     # edge-tts wrapper (async, kein Internet-Check!)
│   └── offline_tts.py    # pyttsx3 wrapper
└── presets/
    ├── builtin.py        # Builtin-Preset-Definitionen (unveränderlich)
    └── manager.py        # Laden/Speichern von Custom Presets (JSON)
```

---

## Preset-System

Presets sind Python-Dicts mit:
- `id` – eindeutige String-ID
- `name` – Anzeigename
- `description` – Kurzbeschreibung (Tooltip)
- `icon` – Emoji
- `params` – dict mit Audio-Parametern (siehe `builtin.py`)

Custom Presets liegen in `user_presets/*.json`. Builtin Presets sind schreibgeschützt.

---

## Wichtige Patterns

### Threading
- Audio-Callbacks laufen in sounddevice-Threads → **niemals direkt Qt-Widgets updaten!**
- Immer `pyqtSignal` oder `QMetaObject.invokeMethod(..., QueuedConnection)` für UI-Updates aus Threads
- TTS läuft in `threading.Thread(daemon=True)` – nie im Main-Thread

### Fehlerbehandlung
```python
# So NICHT:
raise Exception("sounddevice not found")

# So JA – nutzerfreundlich:
if on_error:
    on_error(
        "Das Mikrofon konnte nicht geöffnet werden.\n\n"
        "Bitte prüfe:\n"
        "• Ist ein Mikrofon angeschlossen?\n"
        "• Hat die App Mikrofonzugriff?"
    )
```

### Stil
- Dark Mode Stylesheet in `ui/styles.py` – keine inline Farben!
- `QObjectName` für styled Elemente nutzen (z.B. `btn_secondary`, `btn_start`, `btn_stop`)
- Alle UI-Texte auf Deutsch

---

## Bekannte Gotchas

1. **pedalboard Float-Slider**: Float-Slider in Qt als `int * 100` darstellen (Qt Slider hat keine Float-Native-Unterstützung)
2. **edge-tts asyncio auf Windows**: `asyncio.run()` funktioniert auf Windows manchmal nicht mit bestehenden Event Loops → ggf. `asyncio.get_event_loop().run_until_complete()`
3. **sounddevice auf macOS**: Mikrofon-Permission muss im System-Dialog bestätigt werden – App gibt keine direkte Fehlermeldung wenn Permission fehlt; darauf hinweisen!
4. **PyInstaller**: `pedalboard` braucht `--collect-all pedalboard` im `.spec` File
5. **pyttsx3 auf Linux**: Benötigt `espeak` oder `espeak-ng` – im README erwähnen!
6. **Virtual Audio Cable**: Die App sendet Audio an ein virtuelles Kabel (VB-Cable/BlackHole/PulseAudio Null-Sink). Das VAC erscheint in Discord/Teams/TeamSpeak als Mikrofon. Erkennungslogik in `audio/virtual_cable.py`, Setup-Dialog in `ui/virtual_cable_dialog.py`. Im Voice Tab gibt es ein Banner das den Status zeigt und virtuelle Kabel im Ausgabe-Dropdown automatisch mit 🎧 hervorhebt und vorauswählt.

---

## Lizenz

GPL v3 – wenn du Code beisteuern möchtest, muss er GPL v3-kompatibel sein. Das schließt MIT, Apache 2.0, LGPL aus. Proprietäre Libraries sind verboten.

---

## Wie wir miteinander arbeiten

- Locker und direkt – du kannst auch mal einen Witz einbauen wenn's passt 😄
- Wenn du unsicher bist, lieber kurz fragen als was kaputt machen
- Notier dir alles Relevante in dieser Datei wenn du was Wichtiges lernst
- Wir bauen das zusammen – auf Augenhöhe!

---

*Zuletzt aktualisiert: April 2026*
