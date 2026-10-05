"""Cut the 2:44 score to exactly 50 s, ending on its own final chord.

  ffmpeg -i score.mp3 -ar 48000 -ac 2 -c:a pcm_f32le music48.wav && python3 music_edit.py

Track 0:00–0:41.58 plays untouched, then a 90 ms equal-power crossfade on the beat into
track 2:35.43, so the final C chord (track 2:39.0) lands at 0:45.15 and rings out to 0:50.
The ending section is ~3 dB louder, so it ramps from -3 dB at the splice to 0 dB at the chord.
"""
import numpy as np, soundfile as sf

X, Y, TOTAL = 41.58, 155.43, 50.0          # splice out of / into the track (both on the beat)
x, sr = sf.read('music48.wav')
a0, b0, xf = int(X * sr), int(Y * sr), int(0.090 * sr)
A, B = x[:a0 + xf // 2], x[b0 - xf // 2:]
t = np.linspace(0, np.pi / 2, xf)[:, None]
out = np.concatenate([A[:-xf], A[-xf:] * np.cos(t) + B[:xf] * np.sin(t), B[xf:]])[:int(TOTAL * sr)]

fc = int((159.0 - Y + X) * sr)              # final chord position in the edit
g = np.ones(len(out))
g[a0 - xf // 2:fc] = 10 ** (np.linspace(-3.0, 0.0, fc - a0 + xf // 2) / 20)
out *= g[:, None]
fl = int(0.35 * sr)
out[-fl:] *= np.linspace(1, 0, fl)[:, None] ** 2
sf.write('music_50s.wav', out.astype(np.float32), sr, subtype='FLOAT')
print('final chord at', round(fc / sr, 2), 's; length', len(out) / sr)
