# ZEIAD WATCHES · 50 s vertical film

A 9:16 Instagram film about new and vintage Rolex Day-Dates, cut to the supplied score.
Every shot is AI-generated in Magnific from the four client references (modern Everose Day-Date 40,
vintage yellow-gold Day-Date 36, box and papers, navy satin mood). The edit, the music cut and the sound
design are built here.

## Story and timing (seconds, locked to the score)

| Time | Section | What happens | Score |
| --- | --- | --- | --- |
| 0.00–4.84 | Hook | Navy satin slides off the lens onto a bezel fragment, then a cyclops macro on "28", then the bracelet | quiet intro |
| 4.84–11.83 | Modern Rolex | Wide orbit, 12 o'clock macro, frontal dial with the second hand running, low-angle hero | bass entry at 4.84, big hit at 9.21 |
| 11.83–17.95 | Time starts to turn | Highlights, hands, satin and bracelet reflections all run backward; the second hand ticks and stops | accent at 14.16, near-silence at 17.3 |
| 17.95–28.18 | Time reversal | Second hand runs backward, the date steps back 28→24 on calendar clicks, the camera accelerates into the cyclops, navy darkness, pull back out: it is now the vintage watch | rise at 18.0, dip at 24.5, accent at 27.6/28.18 |
| 28.18–35.14 | Vintage character | Leather, rack focus to the champagne dial, case and crown, vintage hero | slower |
| 35.14–39.53 | Market insight | 1 s cuts: modern and vintage 12 o'clock match cut, two more angles | 35.14 onset |
| 39.53–45.15 | Where people get it wrong | Held crown macro (pattern break), then an inspection montage: case edge, leather and buckle, crystal, box and papers | splice hidden on the 41.58 cut, hit at 42.75 |
| 45.15–50.00 | Choice | Both watches on one satin ribbon, slow arc and light sweep, settles to a still frame with space for text | final chord at 45.15 |

## Files

| File | Purpose |
| --- | --- |
| `edl.py` | The cut: 30 shots with source, in-point, speed or retime mode, grade; SFX cues; music automation. |
| `render.py` | Renders the EDL with ffmpeg: frame-exact shots, reverse, speed ramps, held stills, the date sequence, grade, grain. |
| `mix.py` | Music automation, SFX placement, loudness to −14 LUFS with a −1 dBFS ceiling. |
| `music_edit.py` | Cuts the 2:44 score to 50 s, ending on its own final chord. |
| `sfx_synth.py` | Synthesises the sound kit: ticks, reverse ticks, calendar steps, satin sweeps, swells, metal resonance. |
| `sources.json` | Magnific creation identifiers of every source used. Download URLs are signed and short-lived, so they are not stored here. |

## Build

```bash
pip install numpy scipy soundfile librosa pyloudnorm
ffmpeg -i score.mp3 -ar 48000 -ac 2 -c:a pcm_f32le music48.wav
python3 music_edit.py && python3 sfx_synth.py && python3 mix.py
# put each source in clips/<identifier>.mp4 or .png (export from Magnific)
python3 render.py --clips clips --out out/zeiad_50s.mp4
```

Output: 1080 x 1920, 24 fps, H.264 High CRF 15, AAC 320k, −14 LUFS.
