"""
Live Audio Engine – Echtzeit-Mikrofon-zu-Ausgabe Pipeline.

Queue-Architektur mit drainiertem Stop:
  Mic → RT-Callback (raw_queue.put) → Worker-Thread (process_audio)
      → out_queue.put → RT-Callback (out_queue.get) → Lautsprecher

Warum Queue besser als direkter Callback:
  ✓ RT-Callback macht nur Queue-Ops (<0.1 ms) – kein GIL-bedingtes Stottern
  ✓ PyQt-Ereignisse können den GIL beliebig lang halten; betrifft RT-Thread nicht
  ✓ Drain-on-Stop: Worker verarbeitet alle verbliebenen Blöcke → kein Satzende-Cutoff
  ✓ Eigener _SENTINEL statt None → kein vorzeitiger Stop bei kurz leerer Queue
  ✓ stop() → _running=False sofort (UI reagiert) – Drain läuft still im Hintergrund
  ✓ SR-Erkennung ab 96kHz abwärts → beste verfügbare Qualität
  ✓ Dynamische CHUNK_SIZE (~85ms) passt sich an jede SR an
"""

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


class AudioEngine:
    """
    Verwaltet den Live-Audio-Stream (Mikrofon → Verarbeitung → Lautsprecher).

    Callbacks:
        on_rms_update(float)  – wird pro Block aufgerufen mit RMS-Wert (0–1)
        on_error(str)         – bei Fehler im Stream
    """

    def __init__(
        self,
        on_rms_update: Optional[Callable[[float], None]] = None,
        on_error:      Optional[Callable[[str], None]] = None,
    ):
        self._on_rms_update = on_rms_update   # Legacy – wird nicht mehr vom RT-Thread gerufen!
        self._on_error      = on_error

        self._stream:   Optional[object] = None
        self._running:  bool             = False
        self._stopping: bool             = False
        self._lock:     threading.Lock   = threading.Lock()

        self._params:    dict             = {}
        self._board                       = None
        self._active_sr: int              = SAMPLE_RATE

        self.input_device:  Optional[int] = None
        self.output_device: Optional[int] = None

        self._raw_queue: queue.Queue = queue.Queue(maxsize=QUEUE_SIZE)
        self._out_queue: queue.Queue = queue.Queue(maxsize=QUEUE_SIZE)
        self._worker_thread: Optional[threading.Thread] = None
        self._chunk_size: int = AudioEngine._calc_chunk(SAMPLE_RATE)

        # RT-sicherer RMS-Wert: vom Callback geschrieben, per QTimer gelesen.
        # Kein emit() aus dem RT-Thread → kein GIL-Blocking.
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

        # Laufenden/drainierenden Stream sauber abbrechen
        self._abort_stream()

        sr = self._detect_sr(self.input_device, self.output_device)
        self._active_sr  = sr
        self._chunk_size = self._calc_chunk(sr)

        with self._lock:
            if self._params:
                self._board = build_pedalboard(self._params, sr)

        # Zustand zurücksetzen
        self._stopping = False
        self._running  = False

        # Queues leeren
        for q in (self._raw_queue, self._out_queue):
            while True:
                try:
                    q.get_nowait()
                except queue.Empty:
                    break

        # Worker-Thread starten
        self._worker_thread = threading.Thread(
            target=self._worker_loop,
            daemon=True,
            name="AudioWorker",
        )
        self._worker_thread.start()

        try:
            self._stream = sd.Stream(
                samplerate        = sr,
                blocksize         = self._chunk_size,
                channels          = CHANNELS,
                dtype             = DTYPE,
                device            = (self.input_device, self.output_device),
                callback          = self._callback,
                finished_callback = self._on_stream_finished,
                # 50 ms reichen jetzt aus: RT-Callback macht nur Queue-Ops (<0.1 ms)
                # → kein GIL-Blocking möglich. GIL-Holdup kommt nur noch aus dem
                # Worker-Thread (pedalboard), der NICHT im RT-Thread läuft.
                latency           = 0.05,
            )
            self._stream.start()
            self._running = True
            return True
        except Exception as exc:
            self._stopping = False
            if self._on_error:
                self._on_error(
                    f"Mikrofon konnte nicht geöffnet werden:\n{exc}\n\n"
                    "Bitte prüfe ob ein Mikrofon angeschlossen ist und "
                    "die App Mikrofonzugriff hat."
                )
            return False

    def stop(self) -> None:
        """
        Stoppt den Live-Stream mit sauberem Drain.

        _running = False sofort (UI kann sofort reagieren).
        Stream drainiert im Hintergrund und stoppt via sd.CallbackStop
        nachdem der letzte echte Audio-Block gespielt wurde.
        """
        if not self._running:
            return
        self._running  = False
        self._stopping = True
        # Worker erkennt _stopping per 50ms-Timeout → sendet None-Sentinel
        # → Callback hebt sd.CallbackStop → _on_stream_finished bereinigt

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

    # ── Interne Methoden ─────────────────────────────────────────────────────

    def _abort_stream(self) -> None:
        """Bricht laufenden/drainierenden Stream sofort ab (kein Drain)."""
        old_stream = self._stream
        self._stream = None  # Verhindert Doppelbereinigung in _on_stream_finished
        if old_stream is not None:
            try:
                old_stream.abort()
                old_stream.close()
            except Exception:
                pass
        # Worker stoppen falls noch aktiv
        if self._worker_thread and self._worker_thread.is_alive():
            self._stopping = True
            try:
                self._raw_queue.put_nowait(None)  # Explicit sentinel
            except queue.Full:
                pass
            self._worker_thread.join(timeout=0.3)
        self._stopping = False

    @staticmethod
    def _calc_chunk(sr: int) -> int:
        """Berechnet CHUNK_SIZE für ~40 ms Blockgröße, auf Zweierpotenz gerundet."""
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

    def _worker_loop(self) -> None:
        """
        Verarbeitungs-Thread: raw_queue → process_audio → out_queue.

        Stoppt sauber wenn _stopping=True und raw_queue leer ist:
        Schreibt None-Sentinel in out_queue → Callback hebt sd.CallbackStop →
        PortAudio spielt verbleibende Hardware-Buffer aus → sauberes Ende.
        """
        while True:
            try:
                raw = self._raw_queue.get(timeout=0.03)  # 30 ms – schnelles Drain-Fenster
            except queue.Empty:
                if self._stopping:
                    # Kein Input mehr → Sentinel senden → Stream stoppt sauber
                    try:
                        self._out_queue.put(_SENTINEL, timeout=1.0)
                    except queue.Full:
                        pass
                    break
                continue

            if raw is None:  # Expliziter Sentinel (aus _abort_stream)
                try:
                    self._out_queue.put(_SENTINEL, timeout=1.0)
                except queue.Full:
                    pass
                break

            # Preset-Parameter thread-safe lesen
            with self._lock:
                params = dict(self._params)
                board  = self._board

            try:
                processed = (
                    process_audio(raw, self._active_sr, params, board)
                    if params else raw.copy()
                )
            except Exception:
                processed = raw.copy()

            try:
                self._out_queue.put(processed, timeout=0.2)
            except queue.Full:
                pass  # Block verwerfen wenn Ausgabe-Queue voll

    def _callback(
        self,
        indata:    np.ndarray,
        outdata:   np.ndarray,
        frames:    int,
        time_info,
        status,
    ) -> None:
        """
        RT-Callback: so wenig Python wie möglich.

        Bypass-Modus (kein Preset): indata direkt nach outdata – keine Queue,
        keine Latenz, kein Dropout-Risiko.
        Effekt-Modus: Queue-Operationen (put_nowait / get_nowait = C-Calls).
        """
        # Preset-Status thread-safe lesen (minimaler Lock)
        with self._lock:
            has_effects = bool(self._params) and self._board is not None

        # ── BYPASS: direktes Passthrough – null Latenz, null Dropout ─────────
        if not has_effects:
            raw = indata[:frames, 0] if indata.ndim > 1 else indata[:frames]
            n = min(len(raw), frames)
            if outdata.ndim > 1:
                for ch in range(outdata.shape[1]):
                    outdata[:n, ch] = raw[:n]
                    if n < frames:
                        outdata[n:, ch] = 0.0
            else:
                outdata[:n] = raw[:n]
                if n < frames:
                    outdata[n:] = 0.0
            self.current_rms = float(compute_rms(raw))
            return

        # ── EFFEKT-MODUS: Queue-Operationen ──────────────────────────────────
        # Mikrofon → raw_queue
        if not self._stopping:
            raw = indata[:frames, 0].copy() if indata.ndim > 1 else indata[:frames].copy()
            try:
                self._raw_queue.put_nowait(raw)
            except queue.Full:
                pass  # Verwerfen wenn Worker nicht mitkommt

        # out_queue → Lautsprecher
        try:
            block = self._out_queue.get_nowait()
        except queue.Empty:
            block = None

        # _SENTINEL → Worker fertig, Drain abgeschlossen → stoppen.
        # None → Queue kurz leer (Startup/Spike) → Stille, NICHT stoppen.
        if block is _SENTINEL:
            outdata.fill(0)
            raise sd.CallbackStop

        if block is None:
            outdata.fill(0)
            return

        # Audio schreiben
        n = min(len(block), frames)
        if outdata.ndim > 1:
            for ch in range(outdata.shape[1]):
                outdata[:n, ch] = block[:n]
                if n < frames:
                    outdata[n:, ch] = 0.0
        else:
            outdata[:n] = block[:n]
            if n < frames:
                outdata[n:] = 0.0

        self.current_rms = float(compute_rms(block))

    def _on_stream_finished(self) -> None:
        """
        Wird von PortAudio aufgerufen nachdem Stream vollständig gestoppt hat.
        Bereinigt Stream-Objekt in einem separaten Thread (sicher vor PortAudio re-entrancy).
        """
        self._stopping = False
        stream = self._stream
        self._stream = None
        if stream is not None:
            def _close():
                try:
                    stream.close()
                except Exception:
                    pass
            threading.Thread(target=_close, daemon=True).start()

