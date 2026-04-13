"""
Audio Effects Engine – Alle Stimm-Effekte für TmYNoobs VoiceMorph.

Nutzt pedalboard (Spotify) + scipy/numpy für die Signalverarbeitung.
Alle Funktionen arbeiten auf float32 numpy Arrays.
"""

import numpy as np
from scipy import signal as scipy_signal
from typing import Optional

try:
    from pedalboard import (
        Pedalboard,
        PitchShift,
        Reverb,
        Delay,
        Distortion,
        LowpassFilter,
        HighpassFilter,
        Chorus,
    )
    PEDALBOARD_AVAILABLE = True
except ImportError:
    PEDALBOARD_AVAILABLE = False


def build_pedalboard(params: dict, sample_rate: int) -> Optional[object]:
    """Erstellt ein Pedalboard aus einem Preset-Dict. Gibt None zurück wenn nicht verfügbar."""
    if not PEDALBOARD_AVAILABLE:
        return None

    board = Pedalboard()

    pitch = params.get("pitch_semitones", 0.0)
    if pitch != 0.0:
        board.append(PitchShift(semitones=pitch))

    highpass = params.get("highpass_hz", 20.0)
    if highpass > 20.0:
        board.append(HighpassFilter(cutoff_frequency_hz=float(highpass)))

    lowpass = params.get("lowpass_hz", 20000.0)
    if lowpass < 20000.0:
        board.append(LowpassFilter(cutoff_frequency_hz=float(lowpass)))

    distortion = params.get("distortion_drive", 0.0)
    if distortion > 0.0:
        board.append(Distortion(drive_db=float(distortion)))

    chorus_depth = params.get("chorus_depth", 0.0)
    if chorus_depth > 0.0:
        board.append(Chorus(depth=float(chorus_depth)))

    delay_sec = params.get("delay_seconds", 0.0)
    delay_fb = params.get("delay_feedback", 0.0)
    if delay_sec > 0.0:
        board.append(Delay(delay_seconds=float(delay_sec), feedback=float(delay_fb), mix=0.5))

    reverb_room = params.get("reverb_room_size", 0.0)
    reverb_wet = params.get("reverb_wet_level", 0.0)
    if reverb_wet > 0.0:
        board.append(Reverb(room_size=float(reverb_room), wet_level=float(reverb_wet), dry_level=1.0 - float(reverb_wet) * 0.3))

    return board if len(board) > 0 else None


def apply_ringmod(audio: np.ndarray, sample_rate: int, freq_hz: float) -> np.ndarray:
    """Ringmodulation – multipliziert das Signal mit einem Sinus."""
    if freq_hz <= 0.0:
        return audio
    t = np.arange(len(audio)) / sample_rate
    carrier = np.sin(2.0 * np.pi * freq_hz * t).astype(np.float32)
    if audio.ndim == 2:
        carrier = carrier[:, np.newaxis]
    return (audio * carrier).astype(np.float32)


def apply_tremolo(audio: np.ndarray, sample_rate: int, rate_hz: float, depth: float) -> np.ndarray:
    """Tremolo – amplitudenmodulierte Lautstärkeschwankung."""
    if rate_hz <= 0.0 or depth <= 0.0:
        return audio
    t = np.arange(len(audio)) / sample_rate
    lfo = (1.0 - depth) + depth * 0.5 * (1.0 + np.sin(2.0 * np.pi * rate_hz * t))
    lfo = lfo.astype(np.float32)
    if audio.ndim == 2:
        lfo = lfo[:, np.newaxis]
    return (audio * lfo).astype(np.float32)


def apply_bitcrush(audio: np.ndarray, bits: int) -> np.ndarray:
    """Bitcrush – reduziert die Bit-Tiefe für Lo-Fi-Roboter-Sound."""
    if bits <= 0 or bits >= 24:
        return audio
    steps = float(2 ** bits)
    return (np.round(audio * steps) / steps).astype(np.float32)


def process_audio(audio: np.ndarray, sample_rate: int, params: dict,
                  board=None) -> np.ndarray:
    """
    Wendet alle Effekte eines Presets auf einen Audio-Block an.

    Args:
        audio:       float32 numpy array (samples [, channels])
        sample_rate: z.B. 44100
        params:      Preset-Parameter-Dict
        board:       Vorberechnetes Pedalboard (für Performance in Echtzeit)

    Returns:
        Verarbeitetes float32 numpy array
    """
    if audio is None or len(audio) == 0:
        return audio

    n_in = len(audio)
    out = audio.astype(np.float32)

    if board is not None and PEDALBOARD_AVAILABLE:
        # pedalboard erwartet (channels, samples) – wir haben (samples,) oder (samples, channels)
        if out.ndim == 1:
            pb_input = out[np.newaxis, :]  # mono → (1, samples)
            pb_out = board(pb_input, sample_rate)
            out = pb_out[0]
        else:
            pb_input = out.T  # (samples, ch) → (ch, samples)
            pb_out = board(pb_input, sample_rate)
            out = pb_out.T

        # pedalboard PitchShift kann intern mehr oder weniger Samples ausgeben
        # als reinkamen (Latenz-Puffer). Immer auf Eingabelänge normalisieren.
        n_out = len(out)
        if n_out < n_in:
            # Zu wenig Samples: vorne mit Stille auffüllen (anfängliche Latenz)
            pad = np.zeros(n_in - n_out, dtype=np.float32)
            out = np.concatenate([pad, out])
        elif n_out > n_in:
            # Zu viele Samples: letzten Block abschneiden
            out = out[:n_in]

    # Scipy-basierte Effekte (die pedalboard nicht hat)
    ringmod_hz = params.get("ringmod_hz", 0.0)
    if ringmod_hz > 0.0:
        out = apply_ringmod(out, sample_rate, ringmod_hz)

    tremolo_rate = params.get("tremolo_rate", 0.0)
    tremolo_depth = params.get("tremolo_depth", 0.0)
    if tremolo_rate > 0.0 and tremolo_depth > 0.0:
        out = apply_tremolo(out, sample_rate, tremolo_rate, tremolo_depth)

    bits = params.get("bitcrush_bits", 0)
    if bits and bits > 0:
        out = apply_bitcrush(out, int(bits))

    # Clipping verhindern
    out = np.clip(out, -1.0, 1.0)
    return out


def compute_rms(audio: np.ndarray) -> float:
    """Berechnet den RMS-Pegel eines Audio-Blocks (für VU-Meter, 0.0–1.0)."""
    if audio is None or len(audio) == 0:
        return 0.0
    rms = float(np.sqrt(np.mean(audio.astype(np.float32) ** 2)))
    return min(rms * 4.0, 1.0)  # skaliert für sichtbareres VU-Meter
