// Export the film as WebP frames, exactly as the build reference says.
// Needs ffmpeg on the PATH (or set FFMPEG=/path/to/ffmpeg).
import { spawnSync } from 'node:child_process'
import { mkdirSync, rmSync, readdirSync } from 'node:fs'

const ffmpeg = process.env.FFMPEG || 'ffmpeg'
const film = process.argv[2] || 'design/film.mov'

const sets = [
  { dir: 'public/frames/d', vf: 'fps=20,scale=1920:-2:flags=lanczos', quality: 80 },
  { dir: 'public/frames/m', vf: 'fps=15,scale=1080:-2:flags=lanczos', quality: 78 },
]

for (const { dir, vf, quality } of sets) {
  rmSync(dir, { recursive: true, force: true })
  mkdirSync(dir, { recursive: true })
  const args = ['-v', 'error', '-i', film, '-an', '-vf', vf, '-c:v', 'libwebp', '-quality', String(quality), `${dir}/f_%04d.webp`]
  const run = spawnSync(ffmpeg, args, { stdio: 'inherit' })
  if (run.status !== 0) process.exit(run.status ?? 1)
  console.log(`${dir}: ${readdirSync(dir).length} frames`)
}
