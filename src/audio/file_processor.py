"""
Dateiverarbeitung – Audio-Dateien laden, Effekte anwenden, speichern.

Unterstützt: WAV, MP3, FLAC, OGG (via soundfile/scipy)
"""

import numpy as np
import tempfile
import os
from pathlib import Path
from typing import Optional, Callable

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

try:
    from scipy.io import wavfile
    SCIPY_WAV_AVAILABLE = True
except ImportError:
    SCIPY_WAV_AVAILABLE = False

from audio.effects import build_pedalboard, process_audio


SUPPORTED_READ_FORMATS  = [".wav", ".flac", ".ogg"]
SUPPORTED_WRITE_FORMATS = [".wav", ".flac", ".ogg"]


def load_audio(path: str) -> tuple[np.ndarray, int]:
    """
    Lädt eine Audiodatei.

    Returns:
        (audio_float32, sample_rate)
    Raises:
        RuntimeError wenn die Datei nicht geladen werden kann.
    """
    if not SOUNDFILE_AVAILABLE:
        raise RuntimeError(
            "soundfile ist nicht installiert.\n"
            "Bitte führe setup_check.py aus."
        )
    try:
        audio, sample_rate = sf.read(path, dtype="float32", always_2d=False)
        return audio, sample_rate
    except Exception as exc:
        raise RuntimeError(f"Datei konnte nicht gelesen werden:\n{path}\n\n{exc}") from exc


def save_audio(path: str, audio: np.ndarray, sample_rate: int) -> None:
    """
    Speichert Audio als Datei.

    Raises:
        RuntimeError bei Fehler.
    """
    if not SOUNDFILE_AVAILABLE:
        raise RuntimeError("soundfile ist nicht installiert.")
    try:
        sf.write(path, audio.astype(np.float32), sample_rate)
    except Exception as exc:
        raise RuntimeError(f"Datei konnte nicht gespeichert werden:\n{path}\n\n{exc}") from exc


def process_file(
    input_path: str,
    output_path: str,
    params: dict,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> None:
    """
    Lädt eine Audiodatei, wendet Effekte an, speichert das Ergebnis.

    Args:
        input_path:        Eingabedatei (z.B. WAV)
        output_path:       Ausgabedatei
        params:            Preset-Parameter-Dict
        progress_callback: Optionale Funktion(prozent: int) für Fortschrittsanzeige
    Raises:
        RuntimeError bei Fehler.
    """
    audio, sample_rate = load_audio(input_path)

    if progress_callback:
        progress_callback(20)

    board = build_pedalboard(params, sample_rate)

    # Bei langen Dateien blockweise verarbeiten (verhindert Speicherprobleme)
    BLOCK_SIZE = sample_rate * 10  # 10 Sekunden pro Block

    if len(audio) <= BLOCK_SIZE:
        processed = process_audio(audio, sample_rate, params, board)
        if progress_callback:
            progress_callback(80)
    else:
        blocks = []
        total = len(audio)
        for i in range(0, total, BLOCK_SIZE):
            block = audio[i:i + BLOCK_SIZE]
            processed_block = process_audio(block, sample_rate, params, board)
            blocks.append(processed_block)
            if progress_callback:
                pct = 20 + int((i / total) * 60)
                progress_callback(pct)
        processed = np.concatenate(blocks)

    save_audio(output_path, processed, sample_rate)

    if progress_callback:
        progress_callback(100)
