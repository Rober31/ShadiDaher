"""Synthesise subtle luxury SFX at 48 kHz stereo (float32 WAV)."""
import numpy as np, soundfile as sf
from scipy.signal import butter, sosfilt, fftconvolve
SR = 48000
rng = np.random.default_rng(7)

def bp(x, lo, hi, order=4):
    return sosfilt(butter(order, [lo, hi], btype='band', fs=SR, output='sos'), x)
def lp(x, f, order=4):
    return sosfilt(butter(order, f, btype='low', fs=SR, output='sos'), x)
def hp(x, f, order=4):
    return sosfilt(butter(order, f, btype='high', fs=SR, output='sos'), x)
def pink(n):
    w = rng.standard_normal(n); f = np.fft.rfft(w); k = np.arange(len(f)); k[0] = 1
    return np.fft.irfft(f / np.sqrt(k), n)
def norm(x, peak_db):
    return x / (np.abs(x).max() + 1e-12) * 10**(peak_db/20)
def stereo(m, pan_from=0.0, pan_to=0.0, width=0.0):
    n = len(m); p = np.linspace(pan_from, pan_to, n)
    l = m*np.cos((p+1)*np.pi/4); r = m*np.sin((p+1)*np.pi/4)
    if width:
        d = int(width*SR/1000); r = np.concatenate([np.zeros(d), r[:-d]]) if d else r
    return np.stack([l, r], 1)
def reverb(x, secs=1.6, damp=4000):
    n = int(secs*SR); t = np.arange(n)/SR
    ir = rng.standard_normal(n) * np.exp(-t*6.0/secs)
    ir = lp(ir, damp); ir[0] = 1.0
    return fftconvolve(x, ir)[:len(x)+n]
def save(name, m):
    sf.write(f'sfx/{name}.wav', m.astype(np.float32), SR, subtype='FLOAT')

def tick(level=-18, bright=1.0):
    n = int(0.05*SR); t = np.arange(n)/SR
    click = np.zeros(n); click[:40] = rng.standard_normal(40)*np.hanning(40)
    modes = sum(a*np.sin(2*np.pi*f*bright*t)*np.exp(-t/d) for f,a,d in
                [(3150,1.0,0.006),(5420,0.6,0.004),(8100,0.35,0.003),(1250,0.25,0.008)])
    return norm(hp(click*0.8 + modes, 600), level)

# 1 mechanical tick + reverse tick
tk = tick(); save('tick', stereo(tk, 0.05, 0.05, 0.3))
save('tick_reverse', stereo(tk[::-1], -0.05, -0.05, 0.3))
# 2 tick that stops (4 ticks at 1/8 s escapement rhythm, last one damped) — used before reversal
seq = np.zeros(int(0.9*SR))
for i, lv in enumerate([-21, -20, -19, -17]):
    s = int(i*0.125*SR); t_ = tick(lv); seq[s:s+len(t_)] += t_
save('tick_stop', stereo(seq, 0, 0, 0.3))
# 3 reversed tick train (time running backward), accelerating
n = int(2.6*SR); train = np.zeros(n); pos = 0.0; gap = 0.30
while pos < 2.5:
    s = int(pos*SR); t_ = tick(-22 + 4*pos/2.5, 0.95)[::-1]; train[s:s+len(t_)] += t_[:n-s]
    pos += gap; gap = max(0.07, gap*0.86)
save('tick_reverse_train', stereo(train, 0.1, -0.1, 0.3))

# 4 calendar clicks (date wheel stepping), accelerating series of 6
def cal_click(level):
    n = int(0.09*SR); t = np.arange(n)/SR
    body = sum(a*np.sin(2*np.pi*f*t)*np.exp(-t/d) for f,a,d in [(1850,1,0.012),(4100,0.5,0.008),(620,0.35,0.02)])
    snap = np.zeros(n); snap[:90] = rng.standard_normal(90)*np.hanning(90)
    return norm(hp(body + 1.2*snap, 300), level)
n = int(1.6*SR); cal = np.zeros(n); pos = 0.0; gap = 0.26
for i in range(7):
    s = int(pos*SR); c = cal_click(-16 - i*0.6); cal[s:s+len(c)] += c[:n-s]
    pos += gap; gap *= 0.78
save('calendar_clicks', stereo(cal, -0.15, 0.15, 0.2))

# 5 fabric sweep (satin passing close to lens), 1.4 s, panned L->R
def fabric(dur, level, lo=250, hi=5200, pan=(-0.6, 0.6)):
    n = int(dur*SR); t = np.linspace(0, 1, n)
    env = np.sin(np.pi*t)**1.6 * (1 + 0.25*np.sin(2*np.pi*3.1*t*dur))
    x = bp(pink(n), lo, hi, 2) * env
    x += 0.35*bp(rng.standard_normal(n), 2500, 9000, 2) * env**3   # silky top
    return stereo(norm(x, level), *pan, width=0.6)
save('fabric_sweep', fabric(1.4, -17))
save('fabric_soft', fabric(2.2, -22, 200, 3500, (0.4, -0.3)))
fs = fabric(1.6, -19); save('fabric_reverse', fs[::-1].copy())

# 6 low whoosh for camera acceleration (0.9 s, rises then cuts)
n = int(0.9*SR); t = np.linspace(0, 1, n)
w = lp(pink(n), 420, 2) * (t**2.2) * np.minimum(1, (1-t)*25)
save('push_whoosh', stereo(norm(w, -16), -0.1, 0.1, 0.8))

# 7 metal resonance (soft struck gold), 2.2 s
n = int(2.2*SR); t = np.arange(n)/SR
partials = [(1180,1.0,0.9),(2865,0.55,0.6),(4930,0.35,0.4),(7410,0.18,0.25),(612,0.3,1.2)]
mr = sum(a*np.sin(2*np.pi*f*t + rng.uniform(0, 6))*np.exp(-t/d) for f,a,d in partials)
mr *= np.minimum(1, t/0.004)
save('metal_resonance', stereo(norm(mr, -24), 0.1, 0.1, 0.5))

# 8 reverse swell into the vintage reveal: reverbed metal + air, reversed (1.8 s), plus sub swell
src = np.zeros(int(0.3*SR)); src[:len(mr[:int(0.3*SR)])] = mr[:int(0.3*SR)]
src += 0.4*bp(rng.standard_normal(len(src)), 800, 6000)*np.exp(-np.arange(len(src))/SR/0.05)
rv = reverb(src, 1.8)[:int(1.8*SR)][::-1]
n = len(rv); t = np.linspace(0, 1, n)
sub = np.sin(2*np.pi*(38 + 10*t)*np.arange(n)/SR) * t**2.5
sw = norm(rv, -16) + norm(sub, -14)
sw[-int(0.012*SR):] *= np.linspace(1, 0, int(0.012*SR))
save('reverse_swell', stereo(sw, 0.25, -0.05, 0.9))

# 9 low reverse swell under the reversal (3 s), very subtle
n = int(3.0*SR); t = np.linspace(0, 1, n)
lsw = lp(pink(n), 180, 2)*t**2 + 0.6*np.sin(2*np.pi*42*np.arange(n)/SR)*t**3
lsw[-int(0.02*SR):] *= np.linspace(1, 0, int(0.02*SR))
save('low_reverse_swell', stereo(norm(lsw, -15), 0, 0, 1.2))

# 10 crown winding ratchet (0.5 s), and clasp/buckle tick
n = int(0.55*SR); cr = np.zeros(n)
for i in range(14):
    s = max(0, int(i*0.036*SR + rng.uniform(-0.002, 0.002)*SR)); c = tick(-26 + rng.uniform(-2, 2), 1.4)[:int(0.02*SR)]
    m_ = min(len(c), n-s); cr[s:s+m_] += c[:m_]
save('crown_ratchet', stereo(cr, 0.2, 0.2, 0.2))
cl = cal_click(-19); cl2 = np.concatenate([cl, np.zeros(int(0.05*SR))]); cl2[int(0.045*SR):int(0.045*SR)+len(tk)] += norm(tk, -24)
save('clasp', stereo(cl2, -0.1, -0.1, 0.2))
print('ok')

# 11 calendar steps matched to the date-wheel stills: 28 -> 27 -> 26 -> 25 -> 24
steps = [0.30, 0.62, 0.88, 1.10]
n = int(1.8*SR); cs = np.zeros(n)
for i, st in enumerate(steps):
    s = int(st*SR); c = cal_click(-15 - i*0.5); cs[s:s+len(c)] += c[:n-s]
save('calendar_steps', stereo(cs, -0.1, 0.1, 0.2))
print('ok2')
