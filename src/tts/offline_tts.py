"""
Offline TTS.

Plattform-Strategie:
  macOS  -> subprocess 'say -o file.aiff' + sounddevice playback
            Grund: pyttsx3 save_to_file() aus Background-Thread schreibt auf macOS
            nur einen leeren AIFF-Header (NSSpeechSynthesizer benoetigt NSRunLoop
            des Main-Threads). 'say' ist ein eigener Prozess -> kein Problem.
  Andere -> pyttsx3 save_to_file() + sounddevice playback (Windows/Linux OK)
"""

import re
import sys
import subprocess
import threading
import tempfile
import os
from typing import Optional, Callable, List

_LOCALE_RE = re.compile(r'\b([a-z]{2}_[A-Z]{2})\b')

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False

try:
    import soundfile as sf
    import sounddevice as sd
    import numpy as np
    PLAYBACK_AVAILABLE = True
except ImportError:
    PLAYBACK_AVAILABLE = False

_IS_MACOS = sys.platform == "darwin"


def list_voices() -> List[dict]:
    """Gibt alle verfuegbaren Offline-Stimmen zurueck."""
    if _IS_MACOS:
        return _list_voices_macos()
    if not PYTTSX3_AVAILABLE:
        return []
    return _list_voices_pyttsx3()


def _list_voices_macos() -> List[dict]:
    """Liest Stimmen über 'say -v ?' aus (macOS). ID = exakter Name für 'say -v'."""
    try:
        result = subprocess.run(
            ["say", "-v", "?"],
            capture_output=True, text=True, timeout=5
        )
        voices = []
        for line in result.stdout.splitlines():
            # Locale-Code (z.B. "de_DE", "en_US") via Regex finden.
            # Alles davor ist der Stimm-Name (auch mehrteilig wie "Bad News"
            # oder "Eddy (Deutsch (Deutschland))").
            m = _LOCALE_RE.search(line)
            if not m:
                continue
            locale = m.group(1).lower()
            lang   = locale[:2]
            name   = line[:m.start()].strip()
            if not name:
                continue
            voices.append({"id": name, "name": name, "lang": lang})
        return voices
    except Exception:
        return []


def _list_voices_pyttsx3() -> List[dict]:
    """Stimmen via pyttsx3 (Windows/Linux)."""
    try:
        engine = pyttsx3.init()
        raw_voices = engine.getProperty("voices")
        result = []
        for v in raw_voices:
            lang = ""
            if v.languages:
                raw_lang = v.languages[0]
                if isinstance(raw_lang, bytes):
                    raw_lang = raw_lang.decode("utf-8", errors="ignore")
                lang = str(raw_lang)[:5].lower()
            result.append({"id": v.id, "name": v.name, "lang": lang})
        engine.stop()
        return result
    except Exception:
        return []


def speak_text(
    text: str,
    voice_id: Optional[str] = None,
    rate: int = 0,
    volume: int = 0,
    on_done: Optional[Callable] = None,
    on_error: Optional[Callable[[str], None]] = None,
) -> None:
    """Spricht Text offline aus (nicht-blockierend)."""
    target = _speak_macos if _IS_MACOS else _speak_pyttsx3
    threading.Thread(
        target=target,
        args=(text, voice_id, rate, volume, on_done, on_error),
        daemon=True,
    ).start()


def _speak_macos(text, voice_id, rate, volume, on_done, on_error):
    """macOS: say -> AIFF -> sounddevice."""
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
            tmp_path = tmp.name

        wpm = max(50, 200 + rate * 2)
        cmd = ["say", "-r", str(wpm), "-o", tmp_path]
        if voice_id:
            cmd += ["-v", voice_id]
        cmd.append(text)

        ret = subprocess.run(cmd, timeout=120, capture_output=True)
        if ret.returncode != 0:
            raise RuntimeError(
                "'say' fehlgeschlagen: "
                + ret.stderr.decode("utf-8", errors="ignore").strip()
            )

        size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
        if size < 100:
            raise RuntimeError("'say' erzeugte keine Audiodaten.")

        if PLAYBACK_AVAILABLE:
            audio, sr = sf.read(tmp_path, dtype="float32")
            sd.play(audio, sr)
            sd.wait()
        else:
            subprocess.run(["afplay", tmp_path], check=False, timeout=300)

    except Exception as exc:
        if on_error:
            on_error(
                f"Offline-TTS fehlgeschlagen:\n{exc}\n\n"
                "macOS: Systemstimmen unter Einstellungen -> "
                "Eingabehilfen -> Gesprochene Inhalte aktivieren."
            )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        if on_done:
            on_done()


def _speak_pyttsx3(text, voice_id, rate, volume, on_done, on_error):
    """Windows/Linux: pyttsx3 -> WAV -> sounddevice."""
    tmp_path = None
    try:
        if not PYTTSX3_AVAILABLE:
            raise RuntimeError("pyttsx3 ist nicht installiert.")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        engine = pyttsx3.init()
        if voice_id:
            engine.setProperty("voice", voice_id)
        engine.setProperty("rate", max(50, 175 + rate * 2))
        engine.setProperty("volume", max(0.1, min(1.0, 1.0 + volume * 0.01)))
        engine.save_to_file(text, tmp_path)
        engine.runAndWait()
        engine.stop()

        size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
        if size < 100:
            raise RuntimeError("pyttsx3 erzeugte keine Audiodaten.")

        if PLAYBACK_AVAILABLE:
            audio, sr = sf.read(tmp_path, dtype="float32")
            sd.play(audio, sr)
            sd.wait()

    except Exception as exc:
        if on_error:
            on_error(
                f"Offline-TTS fehlgeschlagen:\n{exc}\n\n"
                "Stelle sicher, dass Systemstimmen installiert sind."
            )
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
        if on_done:
            on_done()


def is_available() -> bool:
    if _IS_MACOS:
        return True
    return PYTTSX3_AVAILABLE
