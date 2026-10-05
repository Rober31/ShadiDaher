"""ZEIAD WATCHES — 50 s 9:16 film. Edit decision list, timed to music_50s.wav.

Music landmarks (output seconds):
  0.16 first onset · 4.84 bass entry · 9.21/9.51 big hit · 11.83 · 14.16 accent
  17.1–17.95 quiet before the rise · 18.0 rise (time reversal) · 24.5–26.6 dip
  27.6–28.18 accent (vintage reveal) · 30.5 · 32.82 · 35.14 · 37.5 · 39.53
  41.58 music splice (hidden under a cut) · 42.75 hit · 45.15 final chord · 50.0 end

Each shot: (start, end, src, mode, params). Source times are in seconds of the clip.
modes:
  play      — src_in, speed (1.0 default)
  reverse   — src_in, src_out: played backward to fill the slot
  ramp_in   — src_in, src_out: accelerating time remap (ease-in), for the push into the cyclops
  ramp_out  — src_in, src_out: decelerating time remap (ease-out), for the pull-back reveal
  freeze_tail — src_in: plays, then holds its last frame for `hold` seconds
  still     — image: very slow digital push (z0 -> z1)
Common options: zoom (static punch-in), grade ('modern' | 'vintage' | 'neutral'),
  fade_out_to_navy (s), fade_in_from_navy (s).
"""

SHOTS = [
    # ---------- 0–4.84  HOOK: fragments, satin passes the lens -----------------------------
    dict(t0=0.00, t1=1.75, src='79MGxVDJAL', mode='play', src_in=0.40, speed=2.0, grade='modern'),    # satin slides off the lens -> bezel fragment
    dict(t0=1.75, t1=3.30, src='gOcRKTQSXO', mode='play', src_in=0.30, grade='modern'),                # extreme macro: date 28 under the cyclops (callback at 20.6)
    dict(t0=3.30, t1=4.84, src='p8kESrWehw', mode='play', src_in=0.30, grade='modern'),                # bracelet reflection
    # ---------- 4.84–11.83  ESTABLISH THE MODERN ROLEX ------------------------------------
    dict(t0=4.84, t1=6.59, src='fHJjJ2NCDY', mode='play', src_in=0.00, grade='modern'),                # K1b WIDE hero orbit (bass entry)
    dict(t0=6.59, t1=7.76, src='ksZyTJR16B', mode='play', src_in=0.40, grade='modern'),                # MD 12 o'clock MONDAY macro
    dict(t0=7.76, t1=9.21, src='vQwrw9Qa47', mode='play', src_in=0.30, grade='modern'),                # K2a frontal, second hand running forward
    dict(t0=9.21, t1=11.83, src='s7Yid4Bl8e', mode='play', src_in=0.00, grade='modern'),               # K7 low-angle hero on the big hit
    # ---------- 11.83–17.95  EXPAND: time starts to run backward --------------------------
    dict(t0=11.83, t1=13.00, src='8asbylYIrU', mode='reverse', src_in=2.2, src_out=4.6, grade='modern'),  # bezel ridges, highlight travels back
    dict(t0=13.00, t1=14.16, src='vQwrw9Qa47', mode='reverse', src_in=1.8, src_out=3.0, grade='modern', zoom=1.3),  # hands, tighter: second hand's first backward hint
    dict(t0=14.16, t1=15.90, src='fHJjJ2NCDY', mode='reverse', src_in=1.7, src_out=3.6, grade='modern'),  # orbit + satin flow reversed
    dict(t0=15.90, t1=17.10, src='p8kESrWehw', mode='reverse', src_in=2.6, src_out=4.4, grade='modern'),  # bracelet reflection runs back
    dict(t0=17.10, t1=17.95, src='vQwrw9Qa47', mode='freeze_tail', src_in=3.15, hold=0.50, grade='modern'),  # the second hand ticks… and stops
    # ---------- 17.95–28.18  THE TIME REVERSAL -------------------------------------------
    dict(t0=17.95, t1=20.60, src='vQwrw9Qa47', mode='reverse', src_in=0.0, src_out=3.6, grade='modern', push=(1.0, 1.10)),  # second hand runs backward
    dict(t0=20.60, t1=22.40, src=None, mode='stills_seq', grade='modern', z0=1.0, z1=1.12,
         seq=[('KLROfAAkqp', 0.30), ('eI1uYy1dqL', 0.32), ('3ztDJkOREY', 0.26), ('4RXcg5w9Aa', 0.22), ('aF7xXTIfSh', 0.70)]),  # date wheel steps back 28->24
    dict(t0=22.40, t1=24.75, src='DoKCgsLpcl', mode='ramp_in', src_in=0.0, src_out=5.0, grade='modern', fade_out_to_navy=0.35),  # accelerate into the cyclops
    dict(t0=24.75, t1=25.35, src=None, mode='navy'),                                                    # navy darkness at maximum macro
    dict(t0=25.35, t1=28.18, src='lJW3oXVgv9', mode='segments', grade='vintage', fade_in_from_navy=0.25,
         segs=[(5.0, 3.3, 1.00, 'linear', 2), (3.3, 1.5, 0.30, 'linear', 7), (1.5, 0.0, 1.53, 'out', 2)]),  # pull back out of the cyclops: it is now the vintage watch
    # ---------- 28.18–35.14  VINTAGE CHARACTER (slower) ------------------------------------
    dict(t0=28.18, t1=30.50, src='bxi7YW25Y2', mode='play', src_in=0.6, grade='vintage'),              # leather -> rack focus to champagne dial
    dict(t0=30.50, t1=32.82, src='79MGImlJAL', mode='play', src_in=0.2, grade='vintage'),              # case profile, crown
    dict(t0=32.82, t1=35.14, src='79MGMCiJAL', mode='play', src_in=0.3, grade='vintage'),              # K4b vintage hero, dial details
    # ---------- 35.14–39.53  MARKET INSIGHT (faster, 0.8–1.5 s) ----------------------------
    dict(t0=35.14, t1=36.30, src='ksZyTJR16B', mode='play', src_in=1.8, grade='modern'),               # modern 12 o'clock
    dict(t0=36.30, t1=37.50, src='fHJj3AwCDY', mode='play', src_in=1.6, grade='vintage'),              # vintage 12 o'clock — same geometry, other era
    dict(t0=37.50, t1=38.55, src='iGIMIFz3uK', mode='play', src_in=0.4, grade='modern'),               # K1a modern, other angle (before cuff at 3.2 s)
    dict(t0=38.55, t1=39.53, src='WDQtQlbcXe', mode='play', src_in=0.2, grade='vintage'),              # K4a vintage, other angle (before 2.0 s warp)
    # ---------- 39.53–45.15  WHERE PEOPLE GET IT WRONG -----------------------------------
    dict(t0=39.53, t1=40.85, src='79MGImlJAL', mode='still', z0=1.00, z1=1.025, grade='vintage'),     # pattern interrupt: held macro, crown
    dict(t0=40.85, t1=41.58, src='vQwrirna47', mode='play', src_in=0.8, grade='modern'),               # inspection: case edge + crown
    dict(t0=41.58, t1=42.75, src='ovLqy5O829', mode='play', src_in=0.6, grade='vintage'),              # leather stitching + buckle — cut hides the music splice
    dict(t0=42.75, t1=43.60, src='mESkD6zhJQ', mode='play', src_in=1.0, grade='vintage'),              # crystal / dial inspection on the 42.75 hit (vintage push, clean before 2.5 s)
    dict(t0=43.60, t1=45.15, src='jUzNzv7LD0', mode='play', src_in=0.6, grade='vintage'),              # box, papers, seal — shallow focus
    # ---------- 45.15–50.00  FINAL QUESTION ----------------------------------------------
    dict(t0=45.15, t1=50.00, src='0eHhLBzTfW', mode='freeze_tail', src_in=0.0, hold=0.0, grade='neutral', settle=True),  # both eras, arc settles to stillness
]


# Sound design cues: (time, file, gain_db, pan_override)
SFX = [
    (0.00, 'fabric_sweep', -4), (0.95, 'metal_resonance', -6),
    (3.15, 'fabric_soft', -6),
    (4.84, 'metal_resonance', -9),
    (7.76, 'tick', -8), (8.26, 'tick', -10),
    (11.83, 'tick_reverse', -6), (13.00, 'tick_reverse', -8),
    (14.05, 'fabric_reverse', -5),
    (17.10, 'tick_stop', -3),
    (17.95, 'tick_reverse_train', -4), (17.95, 'low_reverse_swell', -6),
    (20.60, 'calendar_steps', -3),
    (23.70, 'push_whoosh', -5),
    (25.10, 'reverse_swell', -3),          # swells into the darkness -> reveal (ends ~26.9)
    (27.62, 'metal_resonance', -5),        # soft metallic resonance on the vintage accent
    (30.40, 'fabric_soft', -10),
    (39.53, 'crown_ratchet', -8),
    (41.58, 'clasp', -8),
    (43.55, 'fabric_soft', -9),
    (45.15, 'metal_resonance', -8),
]

# Music automation: (t_start, t_end, gain_db, lowpass_hz or None) with 60 ms ramps
MUSIC_AUTOMATION = [
    (17.30, 17.95, -12.0, 900),     # near-silence: the second hand stops
    (24.55, 26.70, -7.0, 700),      # navy darkness: music recedes, reverse swell carries it
]
