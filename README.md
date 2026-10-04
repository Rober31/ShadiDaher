# Shadi Daher · scroll film website

One page. A film plays frame by frame as the visitor scrolls, seven text sections appear over it,
and six quiet sections with the business details follow under it.

Vite, plain HTML/CSS/JS, GSAP (ScrollTrigger, SplitText) and Lenis. No framework, no WebGL.

## Run and build

```bash
npm install
npm run dev       # http://localhost:5173
npm run build     # production files in dist/
npm run preview   # serve dist/ at http://localhost:4173
```

`dist/` is a static site: upload it to any host (Vercel, Netlify, S3, nginx).

To export the frames again from `design/film.mov` (needs ffmpeg on the PATH, or `FFMPEG=/path/to/ffmpeg`):

```bash
npm run frames
```

### From an AI-enhanced master

The site can serve sharper frame tiers (desktop 2880 and 3840 wide, phone 2560 wide) when there is a
source wider than the original 1920 x 814 film. Make that source with a temporally consistent AI video
upscaler (for example Magnific Precision or Topaz, both limited to 3840 wide), then:

```bash
node scripts/frames.mjs --source path/to/upscaled-3840.mov --master ../shadi-daher-master
```

- `--master` writes the 8K master frames (7680 x 3256, 20 fps, lossless WebP, about 1.1 GB) outside the
  repository. Above 3840 they are an ordinary Lanczos resize of the AI output, not AI detail.
- Every web tier is made straight from `--source`, and `src/frames.json` lists the tiers that exist.
- Tiers wider than the source are never made from the original film: enlarging adds bytes, not detail.

The page picks the smallest tier that covers the widest the film is drawn on that screen (device pixels,
pixel ratio capped at 2). Tiers above 2880 are only used on devices with 8 or more cores, because they decode
too slowly for a fast scroll on fewer. `?frames=d3840` (or any tier folder) forces a tier for testing.

## Before going live

- **WhatsApp number.** “Message Shadi” links to `https://wa.me/WHATSAPP_NUMBER`. Replace
  `WHATSAPP_NUMBER` in `index.html` with the number in digits only, country code first.
- **Logos.** `public/logos/` holds the logos taken from the design sheet. They are about 200 px wide,
  so they are slightly soft on retina screens. Drop sharper files (SVG or 2x PNG) in with the same
  names, or update the `src` and `width`/`height` in `index.html`.

## How it is put together

| Path | What it does |
| --- | --- |
| `index.html` | All copy, as real HTML. One `h1`, the other film headlines are `h2`. |
| `src/main.js` | Lenis wired to ScrollTrigger, `gsap.matchMedia` for desktop / phone / reduced motion, in-page links. |
| `src/film.js` | The frame loader and the canvas stage: framing keyframes, white fades, scrub 1.2. |
| `src/sections.js` | Timed entrances and exits of the seven film sections, and the fade-ups under the film. |
| `src/menu.js` | The full-screen menu: wipe, focus trap, Esc, jump while covered. |
| `src/styles.css` | Layout and type, measured from the designs at 1728 x 1117; phone and still layouts. |
| `public/frames/d`, `public/frames/m` | 359 desktop frames (1920 wide, 20 fps, WebP q95) and 270 phone frames (1440 wide, 15 fps, WebP q92). Wider tiers sit beside them when an enhanced master exists. |
| `src/frames.json` | The frame tiers that exist, written by `scripts/frames.mjs`. |
| `design/` | The film, the build reference, the design sheet, the seven designs rendered to PNG, the font sources. |

**Stage.** The film section is 1100vh tall (900svh on phones) with a 100vh sticky stage inside, so it
stays pinned for 1000vh (800svh). A ScrollTrigger timeline with `scrub: 1.2` plays the film over the
first 900vh at a constant rate and holds the last frame for the final 100vh.

**Frames.** Frame 1 loads first, then every 8th frame, then the rest, nearest to the playhead first.
Encoded frames stay in memory; only a window around the playhead is decoded, sized from a memory budget
(320 MB desktop, 140 MB phone: 10 ahead and 4 behind with the current frames, fewer with wider tiers)
(`createImageBitmap`, off the main thread). A missing frame is replaced by the nearest decoded one, so
the canvas never goes blank.

**Framing.** Each scene's framing (film height, the film x at the viewport centre, top offset, hero top
fade) is a set of CSS custom properties in `styles.css`. The canvas reads them and glides between them
with sine.inOut. The reduced-motion stills use the same values.

**Text.** Each section's window is read from the film time on screen (the smoothed value), never from raw
scroll. Opening plays a timed entrance, closing a timed exit, in both directions.

**Reduced motion.** No pin, no Lenis, no canvas: seven stacked sections, each with its still frame and its
text. The same layout is used if JavaScript does not run.
