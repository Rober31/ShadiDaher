// Export the film frames for the web, and optionally the 8K master frames.
//
//   node scripts/frames.mjs                                 # from design/film.mov (the original)
//   node scripts/frames.mjs --source upscaled.mov --master ../shadi-daher-master
//
// --source  The video to export from. The original MOV, or an AI-enhanced master of it.
// --master  Also write 8K master frames (7680 wide, 20 fps, lossless WebP) to this folder.
//           Keep it outside the repository; it is about a gigabyte or more.
// --out, --manifest  Where the web frames and their list go (default public/frames, src/frames.json).
// --allow-upscale    Also write tiers wider than the source by ordinary resizing. For testing only:
//                    enlarging adds bytes, not detail, so it is never used for the real site.
//
// Every web tier is made straight from --source (never from the 8K frames), so no frame is resized
// twice. Needs ffmpeg on the PATH (or FFMPEG=/path/to/ffmpeg).
import { spawnSync } from 'node:child_process'
import { mkdirSync, rmSync, readdirSync, writeFileSync } from 'node:fs'
import { parseArgs } from 'node:util'

const { values: opt } = parseArgs({
  options: {
    source: { type: 'string', default: 'design/film.mov' },
    master: { type: 'string' },
    out: { type: 'string', default: 'public/frames' },
    manifest: { type: 'string', default: 'src/frames.json' },
    'allow-upscale': { type: 'boolean', default: false },
  },
})
const ffmpeg = process.env.FFMPEG || 'ffmpeg'

// Base tiers ('d', 'm') always exist; the reduced-motion stills and the first-frame preload use them.
const SETS = {
  desktop: { fps: 20, tiers: [
    { dir: 'd', width: 1920, quality: 95, base: true },
    { dir: 'd2880', width: 2880, quality: 92 },
    { dir: 'd3840', width: 3840, quality: 90 },
  ] },
  phone: { fps: 15, tiers: [
    { dir: 'm', width: 1440, quality: 92, base: true },
    { dir: 'm2560', width: 2560, quality: 90 },
  ] },
}

function run(args) {
  const r = spawnSync(ffmpeg, ['-v', 'error', '-y', ...args], { stdio: 'inherit' })
  if (r.status !== 0) process.exit(r.status ?? 1)
}

const probe = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', opt.source], { encoding: 'utf8' })
const [srcW, srcH] = probe.stdout.trim().split(',').map(Number)
if (!srcW) { console.error(`Cannot read ${opt.source}`); process.exit(1) }
console.log(`source ${opt.source}: ${srcW} x ${srcH}`)

if (opt.master) {
  rmSync(opt.master, { recursive: true, force: true })
  mkdirSync(opt.master, { recursive: true })
  run(['-i', opt.source, '-an', '-vf', 'fps=20,scale=7680:-2:flags=lanczos', '-c:v', 'libwebp', '-lossless', '1', '-compression_level', '1', `${opt.master}/f_%04d.webp`])
  console.log(`${opt.master}: ${readdirSync(opt.master).length} master frames, 7680 wide`)
}

const manifest = {}
for (const [kind, { fps, tiers }] of Object.entries(SETS)) {
  manifest[kind] = { fps, count: 0, tiers: [] }
  for (const { dir, width, quality, base } of tiers) {
    const path = `${opt.out}/${dir}`
    if (width > srcW && !base && !opt['allow-upscale']) { rmSync(path, { recursive: true, force: true }); continue }
    rmSync(path, { recursive: true, force: true })
    mkdirSync(path, { recursive: true })
    run(['-i', opt.source, '-an', '-vf', `fps=${fps},scale=${width}:-2:flags=lanczos`, '-c:v', 'libwebp', '-quality', String(quality), '-compression_level', '6', `${path}/f_%04d.webp`])
    const count = readdirSync(path).length
    if (manifest[kind].count && count !== manifest[kind].count) { console.error(`${path}: ${count} frames, expected ${manifest[kind].count}`); process.exit(1) }
    manifest[kind].count = count
    const size = spawnSync('ffprobe', ['-v', 'error', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', `${path}/f_0001.webp`], { encoding: 'utf8' })
    const [w, h] = size.stdout.trim().split(',').map(Number)
    manifest[kind].tiers.push({ dir, width: w, height: h })
    console.log(`${path}: ${count} frames, ${width} wide`)
  }
}
writeFileSync(opt.manifest, JSON.stringify(manifest, null, 2) + '\n')
console.log(`wrote ${opt.manifest}`)
