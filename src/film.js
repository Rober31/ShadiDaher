import { gsap } from 'gsap'

const ASPECT = 1920 / 814
export const DURATION = 17.98 // seconds of film

// Desktop and phone frame sets, as exported by scripts/frames.mjs.
const SETS = {
  desktop: { dir: 'd', fps: 20, count: 359, screens: 10 },
  phone: { dir: 'm', fps: 15, count: 270, screens: 8 },
}

const AHEAD = 10 // decoded frames kept ahead of the playhead
const BEHIND = 4 // and behind it
const KEEP = AHEAD + 2 // anything further away is released

// Encoded frames stay in memory (about 27 MB desktop, 11 MB phone); only a small window around the playhead is decoded.
function createFrames({ count, src }) {
  const blobs = new Array(count)
  const status = new Uint8Array(count) // 0 waiting, 1 loading, 2 loaded, 3 failed
  const bitmaps = new Map()
  const decoding = new Set()
  const abort = new AbortController()
  let target = 0
  let dir = 1
  let fetching = 0
  let maxFetching = 1 // the first frame loads alone
  let shown = null

  const decode = async (blob) => {
    if (window.createImageBitmap) {
      try { return await createImageBitmap(blob) } catch { /* fall back to an <img> */ }
    }
    const img = new Image()
    img.src = URL.createObjectURL(blob)
    await img.decode()
    URL.revokeObjectURL(img.src)
    return img
  }

  // Frame 1 first, then every 8th, then the rest, nearest to the playhead first.
  const nearestWaiting = (step) => {
    let best = -1
    for (let i = 0; i < count; i += step) {
      if (!status[i] && (best < 0 || Math.abs(i - target) < Math.abs(best - target))) best = i
    }
    return best
  }

  function pumpFetch() {
    while (fetching < maxFetching) {
      let i = nearestWaiting(8)
      if (i < 0) i = nearestWaiting(1)
      if (i < 0) return
      status[i] = 1
      fetching++
      fetch(src(i), { signal: abort.signal })
        .then((res) => (res.ok ? res.blob() : Promise.reject(res.status)))
        .then((blob) => { blobs[i] = blob; status[i] = 2; pumpDecode() })
        .catch(() => { status[i] = 3 })
        .finally(() => {
          fetching--
          maxFetching = 6
          if (!abort.signal.aborted) pumpFetch()
        })
    }
  }

  function pumpDecode() {
    for (let k = 0; k <= AHEAD + BEHIND && decoding.size < 3; k++) {
      const i = k <= AHEAD ? target + k * dir : target - (k - AHEAD) * dir
      if (i < 0 || i >= count || !blobs[i] || bitmaps.has(i) || decoding.has(i)) continue
      decoding.add(i)
      decode(blobs[i])
        .then((bmp) => {
          if (abort.signal.aborted || Math.abs(i - target) > KEEP) bmp.close?.()
          else bitmaps.set(i, bmp)
        })
        .catch(() => {})
        .finally(() => { decoding.delete(i); if (!abort.signal.aborted) pumpDecode() })
    }
  }

  pumpFetch()

  return {
    want(i) {
      if (i === target) return
      dir = i > target ? 1 : -1
      target = i
      for (const [j, bmp] of bitmaps) {
        if (Math.abs(j - i) > KEEP && bmp !== shown) { bmp.close?.(); bitmaps.delete(j) }
      }
      pumpDecode()
    },
    // The frame itself, or the nearest decoded one (behind the direction of travel first).
    nearest(i) {
      if (bitmaps.has(i)) return bitmaps.get(i)
      for (let d = 1; d <= KEEP; d++) {
        const b = bitmaps.get(i - d * dir) || bitmaps.get(i + d * dir)
        if (b) return b
      }
      return shown
    },
    shown(bmp) { shown = bmp },
    destroy() {
      abort.abort()
      bitmaps.forEach((bmp) => bmp.close?.())
      bitmaps.clear()
    },
  }
}

const sineInOut = (p) => -(Math.cos(Math.PI * p) - 1) / 2

// The framing keyframes are CSS custom properties on each scene, shared with the reduced-motion stills.
function readKeys(scenes) {
  return scenes.map((el) => {
    const css = getComputedStyle(el)
    const v = (name) => parseFloat(css.getPropertyValue(name))
    return { at: v('--at'), fh: v('--fh') / 100, cx: v('--cx'), top: v('--top') / 100, ft: v('--ft') }
  })
}

function framingAt(keys, t) {
  const next = keys.findIndex((k) => k.at > t)
  if (next === 0) return keys[0]
  if (next < 0) return keys[keys.length - 1]
  const a = keys[next - 1]
  const b = keys[next]
  const e = sineInOut((t - a.at) / (b.at - a.at))
  const mix = (key) => a[key] + (b[key] - a[key]) * e
  return { fh: mix('fh'), cx: mix('cx'), top: mix('top'), ft: mix('ft') }
}

export function createFilm({ track, stage, canvas, scenes, kind }) {
  const set = SETS[kind]
  const keys = readKeys(scenes)
  const state = { t: 0 }
  const ctx = canvas.getContext('2d', { alpha: false })
  const frames = createFrames({
    count: set.count,
    src: (i) => `${import.meta.env.BASE_URL}frames/${set.dir}/f_${String(i + 1).padStart(4, '0')}.webp`,
  })
  let width = 0
  let height = 0
  let dpr = 1
  let drawn = null
  let last = ''
  let resolveReady
  const ready = new Promise((resolve) => { resolveReady = resolve })

  function draw(img, k) {
    let fh = k.fh * height
    let fw = fh * ASPECT
    if (fw < width) { fw = width; fh = fw / ASPECT } // never narrower than the viewport
    const x = Math.min(0, Math.max(width - fw, width / 2 - k.cx * fw))
    const y = k.top * height

    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.fillStyle = '#fff'
    ctx.fillRect(0, 0, width, height)
    ctx.drawImage(img, x, y, fw, fh)

    // The film fades into white from 55% of its height to its bottom edge.
    const fade = ctx.createLinearGradient(0, y + fh * 0.55, 0, y + fh)
    fade.addColorStop(0, 'rgba(255,255,255,0)')
    fade.addColorStop(1, '#fff')
    ctx.fillStyle = fade
    ctx.fillRect(0, y + fh * 0.55, width, fh * 0.45 + 1)

    // Hero only: white at the film's top edge, gone 8vh lower.
    if (k.ft > 0.001) {
      const top = ctx.createLinearGradient(0, y, 0, y + height * 0.08)
      top.addColorStop(0, '#fff')
      top.addColorStop(1, 'rgba(255,255,255,0)')
      ctx.globalAlpha = k.ft
      ctx.fillStyle = top
      ctx.fillRect(0, y, width, height * 0.08)
      ctx.globalAlpha = 1
    }
  }

  // Redraw only when the frame or the framing changes.
  function render(force) {
    const t = state.t
    const i = Math.min(set.count - 1, Math.round(t * set.fps))
    frames.want(i)
    const img = frames.nearest(i)
    if (!img) return
    const k = framingAt(keys, t)
    const sig = `${k.fh.toFixed(5)}|${k.cx.toFixed(5)}|${k.top.toFixed(5)}|${k.ft.toFixed(3)}`
    if (force !== true && img === drawn && sig === last) return
    draw(img, k)
    drawn = img
    last = sig
    frames.shown(img)
    if (resolveReady) { resolveReady(); resolveReady = null; stage.classList.add('is-ready') }
  }

  // Backing store = CSS size x devicePixelRatio (capped at 2). Resizing resets the context,
  // so smoothing is set again every time.
  let dprQuery = null
  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2)
    width = stage.clientWidth
    height = stage.clientHeight
    canvas.width = Math.round(width * dpr)
    canvas.height = Math.round(height * dpr)
    ctx.imageSmoothingEnabled = true
    if ('imageSmoothingQuality' in ctx) ctx.imageSmoothingQuality = 'high'
    // A move to a screen with another pixel ratio does not change the CSS size, so watch it too.
    dprQuery?.removeEventListener('change', resize)
    dprQuery = matchMedia(`(resolution: ${window.devicePixelRatio || 1}dppx)`)
    dprQuery.addEventListener('change', resize)
    render(true)
  }
  const observer = new ResizeObserver(() => resize())
  observer.observe(stage)
  resize()

  // The first 900vh (desktop) play the film at a constant rate; the last screen holds the final frame.
  const hold = 1 / set.screens
  const timeline = gsap.timeline({
    scrollTrigger: { trigger: track, start: 'top top', end: 'bottom bottom', scrub: 1.2 },
  })
  timeline.to(state, { t: DURATION, duration: 1 - hold, ease: 'none' }).to({}, { duration: hold })

  gsap.ticker.add(render)

  return {
    state,
    ready,
    // Skip the scrub delay, after an instant jump.
    settle() {
      timeline.scrollTrigger.getTween()?.progress(1)
      render(true)
    },
    destroy() {
      gsap.ticker.remove(render)
      observer.disconnect()
      dprQuery?.removeEventListener('change', resize)
      frames.destroy()
      stage.classList.remove('is-ready')
    },
  }
}
