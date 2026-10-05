"""Final audio: music_50s.wav + automation + SFX from edl.py -> mix_final.wav (-14 LUFS, -1 dBTP)."""
import importlib.util, numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import butter, sosfilt

spec = importlib.util.spec_from_file_location('edl', 'edl.py')
edl = importlib.util.module_from_spec(spec); spec.loader.exec_module(edl)

music, sr = sf.read('music_50s.wav')
n = len(music)
t = np.arange(n) / sr

# ---- music automation: gain dips with a low-pass blend, 60 ms ramps -------------------------
out = music.copy()
for a, b, gdb, lpf in edl.MUSIC_AUTOMATION:
    r = 0.06
    env = np.clip(np.minimum((t - a) / r, (b - t) / r), 0, 1)     # 0 outside, 1 inside
    env = 0.5 - 0.5 * np.cos(np.pi * env)                          # smooth ramps
    g = 10 ** (gdb * env / 20)
    if lpf:
        sos = butter(2, lpf, btype='low', fs=sr, output='sos')
        wet = sosfilt(sos, out, axis=0)
        out = out * (1 - env[:, None]) + wet * env[:, None]
    out = out * g[:, None]

# ---- SFX ------------------------------------------------------------------------------------
fx = np.zeros_like(out)
for when, name, gdb in edl.SFX:
    x, xsr = sf.read(f'sfx/{name}.wav')
    assert xsr == sr
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    s = int(when * sr); e = min(n, s + len(x))
    fx[s:e] += x[:e - s] * 10 ** (gdb / 20)

mix = out + fx

# ---- loudness: -14 LUFS integrated, true-peak-ish ceiling at -1 dBFS (4x oversampled check) ---
meter = pyln.Meter(sr)
mix = pyln.normalize.loudness(mix, meter.integrated_loudness(mix), -14.0)
from scipy.signal import resample_poly
peak = np.abs(resample_poly(mix, 4, 1, axis=0)).max()
ceil = 10 ** (-1.0 / 20)
if peak > ceil:   # gentle soft-knee limiter on the few overs instead of turning the whole mix down
    over = np.abs(mix) > ceil * 0.8
    k = ceil * 0.8
    mix = np.where(over, np.sign(mix) * (k + (ceil - k) * np.tanh((np.abs(mix) - k) / (ceil - k))), mix)
print('LUFS', round(meter.integrated_loudness(mix), 2),
      'peak dBFS', round(20 * np.log10(np.abs(resample_poly(mix, 4, 1, axis=0)).max()), 2))
sf.write('mix_final.wav', mix.astype(np.float32), sr, subtype='FLOAT')
