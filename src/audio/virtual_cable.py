"""
Virtual Audio Cable – Erkennung und Setup-Anleitung.

Unterstützte Lösungen:
  Windows:  VB-Cable (kostenlos, donationware – https://vb-audio.com/Cable/)
  macOS:    BlackHole (kostenlos, GPL – https://github.com/ExistentialAudio/BlackHole)
  Linux:    PulseAudio / PipeWire Null-Sink (eingebaut, gratis)
"""

import sys
from dataclasses import dataclass
from typing import Optional

try:
    import sounddevice as sd
    _SD_AVAILABLE = True
except (ImportError, OSError):
    _SD_AVAILABLE = False


# ── Bekannte Gerätenamen pro Produkt ──────────────────────────────────────────

_KNOWN_INPUT_SUBSTRINGS = [
    # VB-Cable (Windows)
    "cable output",
    "vb-audio",
    "vb audio",
    # BlackHole (macOS)
    "blackhole",
    # Loopback (macOS, kostenpflichtig – trotzdem erkennen)
    "loopback",
    # PulseAudio / PipeWire Null-Sink (Linux)
    "monitor of null",
    "pulse_sink",
    "virtual_mic",
    "null output",
    # Weitere bekannte virtuelle Geräte
    "soundflower",
    "voicemeeter",
    "jack audio",
]

_KNOWN_OUTPUT_SUBSTRINGS = [
    # VB-Cable – Eingang des Kabels (das ist die Ausgabe von unserer App)
    "cable input",
    "vb-audio",
    "vb audio",
    # BlackHole
    "blackhole",
    # Loopback
    "loopback",
    # PulseAudio Null-Sink
    "null sink",
    "pulse_sink",
    "virtual_mic",
    "soundflower",
    "voicemeeter",
    "jack audio",
]


@dataclass
class VirtualDevice:
    index: int
    name: str
    is_input: bool   # True = Eingang (für andere Apps als Mikrofon sichtbar)
    is_output: bool  # True = Ausgang (hierhin schickt unsere App den Sound)
    product: str     # "VB-Cable", "BlackHole", etc.


def detect_virtual_cables() -> list[VirtualDevice]:
    """
    Sucht nach installierten Virtual Audio Cables in der Geräteliste.
    Gibt eine Liste gefundener virtueller Geräte zurück.
    """
    if not _SD_AVAILABLE:
        return []

    found = []
    try:
        devices = sd.query_devices()
    except Exception:
        return []

    for i, dev in enumerate(devices):
        name_lower = dev["name"].lower()
        product = _identify_product(name_lower)
        if not product:
            continue

        is_out = dev["max_output_channels"] > 0
        is_in  = dev["max_input_channels"] > 0

        # Prüfe ob Name zu virtuellem Ausgang ODER Eingang passt
        matches_out = any(s in name_lower for s in _KNOWN_OUTPUT_SUBSTRINGS)
        matches_in  = any(s in name_lower for s in _KNOWN_INPUT_SUBSTRINGS)

        if matches_out and is_out:
            found.append(VirtualDevice(i, dev["name"], False, True, product))
        elif matches_in and is_in:
            found.append(VirtualDevice(i, dev["name"], True, False, product))

    return found


def get_best_output_device() -> Optional[VirtualDevice]:
    """
    Gibt das beste virtuelle Ausgabegerät zurück (wo unsere App hinschicken soll).
    Das ist das Gegenstück zum virtuellen Mikrofon das Teams/Discord sieht.
    """
    cables = detect_virtual_cables()
    outputs = [d for d in cables if d.is_output]
    return outputs[0] if outputs else None


def _identify_product(name_lower: str) -> Optional[str]:
    if "cable" in name_lower and ("vb" in name_lower or "input" in name_lower or "output" in name_lower):
        return "VB-Cable"
    if "blackhole" in name_lower:
        return "BlackHole"
    if "loopback" in name_lower:
        return "Loopback"
    if "soundflower" in name_lower:
        return "Soundflower"
    if "voicemeeter" in name_lower:
        return "VoiceMeeter"
    if "null" in name_lower and ("sink" in name_lower or "output" in name_lower or "monitor" in name_lower):
        return "PulseAudio/PipeWire Null-Sink"
    if "jack" in name_lower:
        return "JACK Audio"
    if "virtual_mic" in name_lower or "pulse_sink" in name_lower:
        return "Virtuelles Mikrofon"
    return None


# ── Setup-Anleitungen ─────────────────────────────────────────────────────────

def get_setup_instructions() -> dict:
    """
    Gibt plattformspezifische Installations-Anleitung zurück.
    """
    platform = sys.platform

    if platform == "win32":
        return {
            "platform": "Windows",
            "product": "VB-Cable",
            "download_url": "https://vb-audio.com/Cable/",
            "is_free": True,
            "steps": [
                "Gehe auf https://vb-audio.com/Cable/",
                "Lade 'VB-CABLE Driver Pack' herunter",
                "Entpacke die ZIP-Datei",
                "Klicke mit rechts auf VBCABLE_Setup_x64.exe → 'Als Administrator ausführen'",
                "Klicke auf 'Install Driver' und bestätige",
                "Starte deinen PC neu",
                "Öffne die App wieder und wähle 'CABLE Input' als Ausgabe",
                "In Discord/Teams/TeamSpeak: Mikrofon auf 'CABLE Output' setzen",
            ],
            "discord_setting": "Einstellungen → Sprache & Video → Eingabegerät → 'CABLE Output (VB-Audio Virtual Cable)'",
            "teams_setting": "Einstellungen → Geräte → Mikrofon → 'CABLE Output (VB-Audio Virtual Cable)'",
            "teamspeak_setting": "Einstellungen → Aufnahme → 'CABLE Output (VB-Audio Virtual Cable)'",
        }
    elif platform == "darwin":
        return {
            "platform": "macOS",
            "product": "BlackHole",
            "download_url": "https://github.com/ExistentialAudio/BlackHole",
            "is_free": True,
            "steps": [
                "Gehe auf https://existential.audio/blackhole/",
                "Klicke auf 'Download BlackHole 2ch' (kostenlos, kein Account nötig)",
                "Starte die heruntergeladene .pkg Datei",
                "Folge dem Installer",
                "Starte die App neu",
                "Wähle 'BlackHole 2ch' als Ausgabe in dieser App",
                "In Discord/Teams/TeamSpeak: Mikrofon auf 'BlackHole 2ch' setzen",
            ],
            "discord_setting": "Einstellungen → Sprache & Video → Eingabegerät → 'BlackHole 2ch'",
            "teams_setting": "Einstellungen → Geräte → Mikrofon → 'BlackHole 2ch'",
            "teamspeak_setting": "Einstellungen → Aufnahme → 'BlackHole 2ch'",
        }
    else:
        return {
            "platform": "Linux",
            "product": "PulseAudio/PipeWire Null-Sink",
            "download_url": None,
            "is_free": True,
            "steps": [
                "Öffne ein Terminal (z.B. Strg+Alt+T)",
                "Führe diesen Befehl aus:",
                "  pactl load-module module-null-sink sink_name=VirtualMic sink_properties=device.description=VirtualMic",
                "Dann:",
                "  pactl load-module module-virtual-source source_name=VirtualMicSource master=VirtualMic.monitor",
                "In dieser App: 'VirtualMic' als Ausgabe wählen",
                "In Discord/Teams: Mikrofon auf 'VirtualMicSource' setzen",
                "Hinweis: Nach Neustart musst du die Befehle erneut ausführen (oder in /etc/pulse/default.pa eintragen)",
            ],
            "discord_setting": "Einstellungen → Sprache & Video → Eingabegerät → 'VirtualMicSource'",
            "teams_setting": "Einstellungen → Geräte → Mikrofon → 'VirtualMicSource'",
            "teamspeak_setting": "Einstellungen → Aufnahme → 'VirtualMicSource'",
        }
