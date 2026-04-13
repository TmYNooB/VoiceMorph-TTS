"""
Online TTS via edge-tts (Microsoft Edge Read-Aloud Endpoint).

Komplett kostenlos, kein API-Key, kein Account nötig.
Nutzt den gleichen Endpoint wie der Microsoft Edge Browser.
Sehr hohe Stimmqualität (neural voices).
"""

import asyncio
import tempfile
import os
from typing import Optional, Callable

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import soundfile as sf
    import sounddevice as sd
    import numpy as np
    PLAYBACK_AVAILABLE = True
except ImportError:
    PLAYBACK_AVAILABLE = False


# Empfohlene deutsche und englische Stimmen (neural, sehr natürlich)
VOICES = {
    "de": [
        {"id": "de-DE-KatjaNeural",    "name": "Katja (Deutsch, weiblich)",    "lang": "de"},
        {"id": "de-DE-ConradNeural",   "name": "Conrad (Deutsch, männlich)",   "lang": "de"},
        {"id": "de-DE-AmalaNeural",    "name": "Amala (Deutsch, weiblich)",    "lang": "de"},
        {"id": "de-AT-IngridNeural",   "name": "Ingrid (Österreich, weiblich)","lang": "de"},
        {"id": "de-CH-LeniNeural",     "name": "Leni (Schweiz, weiblich)",     "lang": "de"},
    ],
    "en": [
        {"id": "en-US-JennyNeural",    "name": "Jenny (US English, female)",   "lang": "en"},
        {"id": "en-US-GuyNeural",      "name": "Guy (US English, male)",       "lang": "en"},
        {"id": "en-GB-SoniaNeural",    "name": "Sonia (British English, female)", "lang": "en"},
        {"id": "en-GB-RyanNeural",     "name": "Ryan (British English, male)", "lang": "en"},
        {"id": "en-AU-NatashaNeural",  "name": "Natasha (Australian, female)", "lang": "en"},
    ],
}

ALL_VOICES = VOICES["de"] + VOICES["en"]


async def _synthesize_to_file(text: str, voice_id: str, output_path: str,
                               rate: str = "+0%", volume: str = "+0%") -> None:
    """Synthetisiert Text nach Datei via edge-tts."""
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, volume=volume)
    await communicate.save(output_path)


async def _synthesize_to_bytes(text: str, voice_id: str,
                                rate: str = "+0%", volume: str = "+0%") -> bytes:
    """Synthetisiert Text und gibt die Audio-Bytes zurück (MP3)."""
    communicate = edge_tts.Communicate(text, voice_id, rate=rate, volume=volume)
    audio_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            audio_bytes += chunk["data"]
    return audio_bytes


def synthesize_to_file(
    text: str,
    voice_id: str,
    output_path: str,
    rate: int = 0,
    volume: int = 0,
) -> bool:
    """
    Synchroner Wrapper: Synthetisiert Text und speichert als MP3-Datei.

    Args:
        text:        Text der vorgelesen werden soll
        voice_id:    z.B. "de-DE-KatjaNeural"
        output_path: Ausgabepfad (.mp3)
        rate:        Sprechgeschwindigkeit in Prozent (-50 bis +50)
        volume:      Lautstärke in Prozent (-50 bis +50)

    Returns:
        True bei Erfolg, False bei Fehler.
    """
    if not EDGE_TTS_AVAILABLE:
        return False
    try:
        rate_str = f"+{rate}%" if rate >= 0 else f"{rate}%"
        vol_str  = f"+{volume}%" if volume >= 0 else f"{volume}%"
        asyncio.run(_synthesize_to_file(text, voice_id, output_path, rate_str, vol_str))
        return True
    except Exception:
        return False


def speak_text(
    text: str,
    voice_id: str,
    rate: int = 0,
    volume: int = 0,
    on_done: Optional[Callable] = None,
    on_error: Optional[Callable[[str], None]] = None,
) -> None:
    """
    Spricht Text aus (async, blockiert nicht die UI).
    Wird in einem Thread ausgeführt.
    """
    import threading

    def _worker():
        if not EDGE_TTS_AVAILABLE:
            if on_error:
                on_error("edge-tts ist nicht installiert.")
            return
        try:
            rate_str = f"+{rate}%" if rate >= 0 else f"{rate}%"
            vol_str  = f"+{volume}%" if volume >= 0 else f"{volume}%"

            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                tmp_path = tmp.name

            asyncio.run(_synthesize_to_file(text, voice_id, tmp_path, rate_str, vol_str))

            # Abspielen via sounddevice
            if PLAYBACK_AVAILABLE:
                audio, sr = sf.read(tmp_path, dtype="float32")
                sd.play(audio, sr)
                sd.wait()
            else:
                # Fallback: OS-eigenen Player nutzen
                import subprocess, sys
                if sys.platform == "win32":
                    os.startfile(tmp_path)
                elif sys.platform == "darwin":
                    subprocess.run(["afplay", tmp_path], check=False)
                else:
                    subprocess.run(["aplay", tmp_path], check=False)

        except Exception as exc:
            if on_error:
                on_error(
                    f"Text-to-Speech fehlgeschlagen.\n\n"
                    f"Mögliche Ursache: Kein Internet?\n\n{exc}"
                )
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            if on_done:
                on_done()

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
