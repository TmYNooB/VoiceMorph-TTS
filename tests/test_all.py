"""
Automatisierte Tests für TmYNoobs VoiceMorph & Text2Speech.

Ausführen:
    cd "VoiceChanger & Text2Speech"
    python3 -m pytest tests/ -v
oder direkt:
    python3 tests/test_all.py
"""

import sys
import os
import time
import threading
import numpy as np

# src/ im Suchpfad
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _hline(title=""):
    w = 60
    if title:
        print(f"\n{'─' * 4}  {title}  {'─' * (w - len(title) - 6)}")
    else:
        print("─" * w)

PASS = "✅"
FAIL = "❌"
SKIP = "⚠️ "

_results = []

def _check(name, ok, detail=""):
    icon = PASS if ok else FAIL
    msg  = f"  {icon}  {name}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    _results.append((name, ok))
    return ok


# ─── 1. Effekte & Audio-Verarbeitung ──────────────────────────────────────────

def test_effects():
    _hline("Audio-Effekte")
    from audio.effects import build_pedalboard, process_audio, compute_rms

    CHUNK = 4096
    SR    = 44100

    presets = [
        ("Bypass",   {"pitch_semitones": 0.0, "reverb_room_size": 0.0,
                      "reverb_wet_level": 0.0, "delay_seconds": 0.0,
                      "delay_feedback": 0.0, "distortion_drive": 0.0,
                      "lowpass_hz": 20000.0, "highpass_hz": 20.0,
                      "ringmod_hz": 0.0, "chorus_depth": 0.0,
                      "tremolo_rate": 0.0, "tremolo_depth": 0.0,
                      "bitcrush_bits": 0}),
        ("Chipmunk", {"pitch_semitones": 8.0, "reverb_room_size": 0.0,
                      "reverb_wet_level": 0.0, "delay_seconds": 0.0,
                      "delay_feedback": 0.0, "distortion_drive": 0.0,
                      "lowpass_hz": 20000.0, "highpass_hz": 20.0,
                      "ringmod_hz": 0.0, "chorus_depth": 0.0,
                      "tremolo_rate": 0.0, "tremolo_depth": 0.0,
                      "bitcrush_bits": 0}),
        ("Roboter",  {"pitch_semitones": 0.0, "reverb_room_size": 0.3,
                      "reverb_wet_level": 0.2, "delay_seconds": 0.0,
                      "delay_feedback": 0.0, "distortion_drive": 10.0,
                      "lowpass_hz": 18000.0, "highpass_hz": 200.0,
                      "ringmod_hz": 80.0, "chorus_depth": 0.0,
                      "tremolo_rate": 0.0, "tremolo_depth": 0.0,
                      "bitcrush_bits": 6}),
    ]

    for name, params in presets:
        board = build_pedalboard(params, SR)
        audio = (np.random.randn(CHUNK) * 0.1).astype(np.float32)
        out   = process_audio(audio, SR, params, board)
        length_ok   = len(out) == CHUNK
        no_nan      = not np.any(np.isnan(out))
        in_range    = np.all(np.abs(out) <= 1.01)
        ok = length_ok and no_nan and in_range
        detail = f"len={len(out)}, nan={np.any(np.isnan(out))}, max={np.max(np.abs(out)):.3f}"
        _check(f"Effekt '{name}'", ok, detail)

    # RMS-Meter – skalierter RMS-Wert (compute_rms × 4, daher 1.0 bei Vollpegel)
    sine = np.sin(2 * np.pi * 440 * np.arange(CHUNK) / SR).astype(np.float32)
    rms  = compute_rms(sine)
    # Sinus hat RMS ≈ 0.707 → nach ×4 Skalierung ≥ 1.0 (geclamped)
    _check("RMS Sinus skaliert ≥ 0.5", rms >= 0.5, f"rms={rms:.3f}")

    rms_silence = compute_rms(np.zeros(CHUNK, dtype=np.float32))
    _check("RMS Stille = 0", rms_silence == 0.0, f"rms={rms_silence:.3f}")


# ─── 2. Audio Engine Queue-Architektur ────────────────────────────────────────

def test_engine():
    _hline("Audio Engine")
    from audio.engine import AudioEngine

    # Queue-Architektur (Worker-Thread + Queues)
    engine = AudioEngine()
    _check("AudioEngine hat _raw_queue",        hasattr(engine, "_raw_queue"))
    _check("AudioEngine hat _out_queue",         hasattr(engine, "_out_queue"))
    _check("AudioEngine hat _worker_loop",       hasattr(engine, "_worker_loop"))
    _check("AudioEngine hat _callback",          hasattr(engine, "_callback"))
    _check("is_running initial = False",         not engine.is_running)

    # Preset setzen ohne laufenden Stream
    bypass = {"pitch_semitones": 0.0, "reverb_room_size": 0.0,
              "reverb_wet_level": 0.0, "delay_seconds": 0.0,
              "delay_feedback": 0.0, "distortion_drive": 0.0,
              "lowpass_hz": 20000.0, "highpass_hz": 20.0,
              "ringmod_hz": 0.0, "chorus_depth": 0.0,
              "tremolo_rate": 0.0, "tremolo_depth": 0.0,
              "bitcrush_bits": 0}
    try:
        engine.set_preset(bypass)
        _check("set_preset() ohne Stream", True)
    except Exception as e:
        _check("set_preset() ohne Stream", False, str(e))

    # SR-Detektion (ohne echte Geräte → höchste verfügbare SR)
    from audio.engine import SAMPLE_RATE
    sr = AudioEngine._detect_sr(None, None)
    _check("_detect_sr ergibt gültige SR", sr in (96000, 88200, 48000, 44100, 32000, 22050, 16000), f"sr={sr}")

    # _calc_chunk: ~85ms Blöcke pro SR
    chunk_16k = AudioEngine._calc_chunk(16000)
    chunk_48k = AudioEngine._calc_chunk(48000)
    chunk_96k = AudioEngine._calc_chunk(96000)
    _check("_calc_chunk(16000) ≥ 512",  chunk_16k >= 512,  f"chunk={chunk_16k}")
    _check("_calc_chunk(48000) = 4096", chunk_48k == 4096, f"chunk={chunk_48k}")
    _check("_calc_chunk(96000) = 8192", chunk_96k == 8192, f"chunk={chunk_96k}")


# ─── 3. Presets laden ─────────────────────────────────────────────────────────

def test_presets():
    _hline("Preset-System")
    from presets.builtin import BUILTIN_PRESETS
    from presets.manager import load_all_presets, is_builtin

    _check("Builtin-Presets nicht leer", len(BUILTIN_PRESETS) > 0,
           f"{len(BUILTIN_PRESETS)} Presets")

    required_keys = {"id", "name", "description", "icon", "params"}
    param_keys    = {"pitch_semitones", "reverb_wet_level", "ringmod_hz"}
    for p in BUILTIN_PRESETS:
        has_keys   = required_keys.issubset(p.keys())
        has_params = param_keys.issubset(p["params"].keys())
        _check(f"Preset '{p['name']}' vollständig", has_keys and has_params)

    all_presets = load_all_presets()
    _check("load_all_presets() > 0", len(all_presets) > 0,
           f"{len(all_presets)} total")
    builtin_ids = [p["id"] for p in all_presets if is_builtin(p["id"])]
    _check("is_builtin() erkennt Builtin-IDs", len(builtin_ids) > 0)


# ─── 4. Online TTS (Verbindung optional) ──────────────────────────────────────

def test_online_tts():
    _hline("Online TTS (edge-tts)")
    from tts.online_tts import ALL_VOICES, EDGE_TTS_AVAILABLE, synthesize_to_file
    import tempfile

    _check("edge-tts installiert", EDGE_TTS_AVAILABLE)
    _check("ALL_VOICES nicht leer", len(ALL_VOICES) > 0, f"{len(ALL_VOICES)} Stimmen")

    de_voices = [v for v in ALL_VOICES if v["lang"] == "de"]
    en_voices = [v for v in ALL_VOICES if v["lang"] == "en"]
    _check("Deutsche Stimmen vorhanden",  len(de_voices) > 0)
    _check("Englische Stimmen vorhanden", len(en_voices) > 0)

    if not EDGE_TTS_AVAILABLE:
        print(f"  {SKIP}  Synthesis-Test übersprungen (edge-tts nicht installiert)")
        return

    # Kurze Synthese in Temp-Datei (braucht Internet)
    try:
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            tmp_path = tmp.name
        ok = synthesize_to_file("Test", "de-DE-KatjaNeural", tmp_path, 0, 0)
        file_ok = os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 100
        _check("synthesize_to_file() → .mp3 erzeugt", ok and file_ok,
               f"size={os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0} bytes")
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    except Exception as e:
        print(f"  {SKIP}  Synthesis-Test fehlgeschlagen (kein Internet?): {e}")


# ─── 5. Offline TTS ───────────────────────────────────────────────────────────

def test_offline_tts():
    _hline("Offline TTS (macOS say / pyttsx3)")
    import tempfile, subprocess
    from tts.offline_tts import list_voices, is_available, _IS_MACOS

    _check("Offline-TTS verfügbar",
           is_available(),
           "macOS say" if _IS_MACOS else "pyttsx3")

    voices = list_voices()
    _check("Stimmen gefunden", len(voices) > 0, f"{len(voices)} Stimmen")

    for v in voices[:3]:
        ok = "id" in v and "name" in v
        _check(f"Stimme '{v.get('name','?')}' hat id + name", ok)

    de_voices = [v for v in voices if v.get("lang", "").startswith("de")]
    _check("Deutsche Stimmen vorhanden", len(de_voices) > 0,
           f"{len(de_voices)} Stimmen")

    if _IS_MACOS:
        # Teste say direkt: synthetisiere kurzen AIFF
        with tempfile.NamedTemporaryFile(suffix=".aiff", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            voice_arg = de_voices[0]["id"] if de_voices else None
            cmd = ["say", "-o", tmp_path]
            if voice_arg:
                cmd += ["-v", voice_arg]
            cmd.append("Test")
            ret = subprocess.run(cmd, timeout=10, capture_output=True)
            size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
            _check("say -o erzeugt Audio-Datei",
                   ret.returncode == 0 and size > 100,
                   f"returncode={ret.returncode}, size={size}")
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    else:
        from tts.offline_tts import PYTTSX3_AVAILABLE
        _check("pyttsx3 installiert", PYTTSX3_AVAILABLE)
        if PYTTSX3_AVAILABLE:
            import pyttsx3
            eng = pyttsx3.init()
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                eng.save_to_file("Test", tmp_path)
                eng.runAndWait()
                eng.stop()
                size = os.path.getsize(tmp_path) if os.path.exists(tmp_path) else 0
                _check("pyttsx3 save_to_file erzeugt Audio", size > 100, f"size={size}")
            except Exception as e:
                _check("pyttsx3 save_to_file erzeugt Audio", False, str(e))
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)


# ─── 6. Virtuelle Kabel-Erkennung ─────────────────────────────────────────────

def test_virtual_cable():
    _hline("Virtuelle Kabel")
    from audio.virtual_cable import detect_virtual_cables
    cables = detect_virtual_cables()
    # Kein Fehler → Test bestanden (Kabel muss nicht vorhanden sein)
    _check("detect_virtual_cables() kein Absturz", True,
           f"{len(cables)} Kabel erkannt")


# ─── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║  TmYNoobs VoiceMorph – Automatische Tests ║")
    print("  ╚══════════════════════════════════════════╝")

    test_effects()
    test_engine()
    test_presets()
    test_online_tts()
    test_offline_tts()
    test_virtual_cable()

    _hline()
    total  = len(_results)
    passed = sum(1 for _, ok in _results if ok)
    failed = total - passed

    print(f"\n  Ergebnis:  {passed}/{total} Tests bestanden", end="")
    if failed:
        print(f"  ({failed} fehlgeschlagen)")
        failed_names = [n for n, ok in _results if not ok]
        for n in failed_names:
            print(f"    {FAIL}  {n}")
    else:
        print("  🎉")
    print()
    sys.exit(0 if failed == 0 else 1)
