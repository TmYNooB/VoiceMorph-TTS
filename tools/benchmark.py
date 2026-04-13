import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import numpy as np, time
from audio.engine import AudioEngine, QUEUE_SIZE, SAMPLE_RATE
from audio.effects import build_pedalboard, process_audio

sr    = 96000
chunk = AudioEngine._calc_chunk(sr)
print(f"SR:            {sr} Hz")
print(f"CHUNK_SIZE:    {chunk} samples  ({chunk/sr*1000:.1f} ms pro Block)")
print(f"QUEUE_SIZE:    {QUEUE_SIZE} Bloecke  ({QUEUE_SIZE*chunk/sr*1000:.0f} ms Puffer)")
print()

params = {'pitch_semitones':4.0,'reverb_room_size':0.0,'reverb_wet_level':0.0,
          'delay_seconds':0.0,'delay_feedback':0.0,'distortion_drive':0.0,
          'lowpass_hz':20000.0,'highpass_hz':20.0,'ringmod_hz':0.0,
          'chorus_depth':0.0,'tremolo_rate':0.0,'tremolo_depth':0.0,'bitcrush_bits':0}
board  = build_pedalboard(params, sr)
audio  = (np.random.randn(chunk) * 0.1).astype('float32')

times = []
for _ in range(30):
    t0 = time.perf_counter()
    process_audio(audio, sr, params, board)
    times.append((time.perf_counter()-t0)*1000)

budget = chunk/sr*1000
print(f"PitchShift benchmark (30 Runs, chunk={chunk}):")
print(f"  min={min(times):.1f}ms  avg={sum(times)/len(times):.1f}ms  max={max(times):.1f}ms")
print(f"  Budget: {budget:.1f}ms")
margin = budget - max(times)
print(f"  Margin: {margin:.1f}ms  => {'OK' if margin > 5 else 'KNAPP oder PROBLEM'}")
