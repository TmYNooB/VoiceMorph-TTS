"""
Live Audio Engine – Echtzeit-Mikrofon-zu-Ausgabe Pipeline.

Direkter Callback-Ansatz (kein Worker-Thread, keine Queues):
  Mic → _callback → process_audio (pedalboard) → Lautsprecher

Warum direkt besser als Queue+Worker:
  ✓ Kein OS-Scheduling-Jitter: Queue-Worker kann für >40ms eingefroren werden
    → out_queue leer → Dropout. Direkter Callback hat dieses Problem nicht.
  ✓ Pedalboard gibt GIL frei während C++-Verarbeitung (~11ms)
    → Qt-Hauptthread kann in dieser Zeit Events verarbeiten (31ms Spielraum).
  ✓ RMS wird direkt in current_rms geschrieben (float), kein emit()
    → kein GIL-Blocking durch Qt-Synchronisation.
  ✓ Keine Pipeline-Latenz, kein Drain-on-Stop nötig.
  ✓ 50ms Hardware-Puffer (latency=0.05) als Sicherheitsnetz.
"""

import math
import threading
import numpy as np
from typing import Optional, Callable, List, Tuple

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except (ImportError, OSError):
    SOUNDDEVICE_AVAILABLE = False

from audio.effects import build_pedalboard, process_audio, compute_rms


SAMPLE_RATE = 48000   # Fallback; wird bei Start auf native Geräte-SR gesetzt
CHANNELS    = 1       # Mono
DTYPE       = np.float32


class AudioEngine:
    """
    Verwaltet den Live-Audio-Stream (Mikrofon → Verarbeitung → Lautsprecher).

    Callbacks:
        on_error(str) – bei Fehler beim Stream-Start
    """

    def __init__(
        self,
        on_rms_update: Optional[Callable[[float], None]] = None,  # Legacy, ungenutzt
        on_error:      Optional[Callable[[str], None]] = None,
    ):
        self._on_error   = on_error

        self._stream:    Optional[object] = None
        self._running:   bool             = False
        self._lock:      threading.Lock   = threading.Lock()

        self._params:    dict             = {}
        self._board                       = None
        self._active_sr: int              = SAMPLE_RATE

        self.input_device:  Optional[int] = None
        self.output_device: Optional[int] = None

        self._chunk_size: int = AudioEngine._calc_chunk(SAMPLE_RATE)

        # RMS-Wert: vom RT-Callback geschrieben (nur float-Assign, GIL-safe).
        # UI liest per QTimer (polling) – kein emit(), kein Qt-Kontakt im RT-Thread.
        self.current_rms: float = 0.0

    # ── Public API ───────────────────────────────────────────────────────────

    def set_preset(self, params: dict) -> None:
        """Wechselt das Effekt-Preset (thread-safe, wirkt beim nächsten Block)."""
        board = build_pedalboard(params, self._active_sr)
        with self._lock:
            self._params = dict(params)
            self._board  = board

    def start(self) -> bool:
        """Startet den Live-Stream. Gibt True bei Erfolg zurück."""
        if not SOUNDDEVICE_AVAILABLE:
            if self._on_error:
                self._on_error(
                    "sounddevice ist nicht installiert.\n"
                    "Bitte führe setup_check.py aus."
                )
            return False

        if self._running:
            return True

        sr = self._detect_sr(self.input_device, self.output_device)
        self._active_sr  = sr
        self._chunk_size = self._calc_chunk(sr)

        with self._lock:
            if self._params:
                self._board = build_pedalboard(self._params, sr)

        try:
            self._stream = sd.Stream(
                samplerate = sr,
                blocksize  = self._chunk_size,
                channels   = CHANNELS,
                dtype      = DTYPE,
                device     = (self.input_device, self.output_device),
                callback   = self._callback,
                # 50ms Hardware-Puffer reicht aus:
                # Callback hält GIL nur für ~11ms (pedalboard C++ gibt ihn frei).
                # Qt hat ~30ms pro Block-Intervall zum Event-Processing.
                latency    = 0.05,
            )
            self._stream.start()
            self._running = True
            return True
        except Exception as exc:
            if self._on_error:
                self._on_error(
                    f"Mikrofon konnte nicht geöffnet werden:\n{exc}\n\n"
                    "Bitte prüfe ob ein Mikrofon angeschlossen ist und "
                    "die App Mikrofonzugriff hat."
                )
            return False

    def stop(self) -> None:
        """Stoppt den Live-Stream."""
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        self.current_rms = 0.0

    @property
    def is_running(self) -> bool:
        return self._running

    # ── Geräteverwaltung ─────────────────────────────────────────────────────

    @staticmethod
    def list_input_devices() -> List[Tuple[int, str]]:
        if not SOUNDDEVICE_AVAILABLE:
            return []
        devices = []
        try:
            for i, dev in enumerate(sd.query_devices()):
                if dev["max_input_channels"] > 0:
                    devices.append((i, dev["name"]))
        except Exception:
            pass
        return devices

    @staticmethod
    def list_output_devices() -> List[Tuple[int, str]]:
        if not SOUNDDEVICE_AVAILABLE:
            return []
        devices = []
        try:
            for i, dev in enumerate(sd.query_devices()):
                if dev["max_output_channels"] > 0:
                    devices.append((i, dev["name"]))
        except Exception:
            pass
        return devices

    # ── Interne Hilfsmethoden ─────────────────────────────────────────────────

    @staticmethod
    def _calc_chunk(sr: int) -> int:
        """~40ms Blockgröße, auf Zweierpotenz gerundet."""
        raw = sr * 0.04
        return max(512, 2 ** math.ceil(math.log2(max(raw, 512))))

    @staticmethod
    def _detect_sr(input_dev, output_dev) -> int:
        """Wählt die höchste von beiden Geräten gemeinsam unterstützte SR."""
        if not SOUNDDEVICE_AVAILABLE:
            return SAMPLE_RATE
        for sr in (96000, 88200, 48000, 44100, 32000, 22050, 16000):
            try:
                sd.check_input_settings(device=input_dev,  samplerate=sr, channels=CHANNELS)
                sd.check_output_settings(device=output_dev, samplerate=sr, channels=CHANNELS)
                return sr
            except Exception:
                continue
        return SAMPLE_RATE

    # ── RT-Callback ──────────────────────────────────────────────────────────
    #
    # Läuft im PortAudio-RT-Thread.
    #
    # Bypass (kein Preset): indata → outdata direkt. Kein Python-Overhead.
    # Effekt-Modus: process_audio() → pedalboard gibt GIL für ~11ms frei
    #   → Qt-Thread kann Events in dieser Zeit verarbeiten.
    #   Kein OS-Scheduling-Jitter (kein Worker-Thread mehr).

    def _callback(
        self,
        indata:    np.ndarray,
        outdata:   np.ndarray,
        frames:    int,
        time_info,
        status,
    ) -> None:
        raw = indata[:frames, 0] if indata.ndim > 1 else indata[:frames]

        # Preset-Status thread-safe lesen
        with self._lock:
            params = dict(self._params)
            board  = self._board

        if params and board is not None:
            try:
                processed = process_audio(raw, self._active_sr, params, board)
            except Exception:
                processed = raw
        else:
            processed = raw  # Bypass: kein Preset → direkte Kopie

        n = min(len(processed), frames)
        if outdata.ndim > 1:
            for ch in range(outdata.shape[1]):
                outdata[:n, ch] = processed[:n]
                if n < frames:
                    outdata[n:, ch] = 0.0
        else:
            outdata[:n] = processed[:n]
            if n < frames:
                outdata[n:] = 0.0

        # RMS-Update: float-Assign ist GIL-sicher, kein emit() nötig.
        self.current_rms = float(compute_rms(processed))


import math
import threading
import queue
import numpy as np
from typing import Optional, Callable, List, Tuple

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except (ImportError, OSError):
    SOUNDDEVICE_AVAILABLE = False

from audio.effects import build_pedalboard, process_audio, compute_rms


# Kein fester CHUNK_SIZE mehr – wird zur Laufzeit aus der SR berechnet (_calc_chunk)
SAMPLE_RATE = 48000   # Fallback; wird bei Start auf native Geräte-SR gesetzt
CHANNELS    = 1       # Mono
DTYPE       = np.float32
QUEUE_SIZE  = 3       # ~255 ms Puffer (3 × 85 ms Blöcke) – genug für Worker-Spikes

# Eigener Sentinel-Typ – von None unterscheidbar (wichtig für Drain-Logik)
_SENTINEL = object()


