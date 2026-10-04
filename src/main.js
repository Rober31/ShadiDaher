import 'lenis/dist/lenis.css'
import './styles.css'
import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { SplitText } from 'gsap/SplitText'
import Lenis from 'lenis'
import { createFilm } from './film.js'
import { createScenes, createReveals } from './sections.js'
import { createMenu } from './menu.js'

gsap.registerPlugin(ScrollTrigger, SplitText)
if ('scrollRestoration' in history) history.scrollRestoration = 'manual'

const root = document.documentElement
const track = document.querySelector('.film')
const stage = document.querySelector('.stage')
const canvas = document.querySelector('.stage__canvas')
const veil = document.querySelector('.veil')
const scenes = gsap.utils.toArray('.scene')

let lenis = null
let film = null
let story = null

// Desktop and phone each get their own frame set, framing and pin length.
// Reduced motion gets neither: the CSS shows seven still sections, with no pin, Lenis or canvas.
function setupMotion(kind) {
  root.classList.add('motion')
  lenis = new Lenis({ lerp: 0.09, syncTouch: false }) // touch scrolling stays native
  lenis.on('scroll', ScrollTrigger.update)
  const raf = (time) => lenis.raf(time * 1000)
  gsap.ticker.add(raf)
  gsap.ticker.lagSmoothing(0)

  const scenesNow = (story = createScenes(scenes))
  film = createFilm({ track, stage, canvas, scenes, kind })
  const tick = () => scenesNow.update(film.state.t)
  gsap.ticker.add(tick)
  createReveals()

  // The hero enters with its first frame and the font, or after 2.5 s at the latest.
  const late = new Promise((resolve) => setTimeout(resolve, 2500))
  Promise.race([Promise.all([film.ready, document.fonts.ready]), late]).then(() => scenesNow.start())

  return () => {
    gsap.ticker.remove(raf)
    gsap.ticker.remove(tick)
    film.destroy()
    lenis.destroy()
    film = story = lenis = null
    root.classList.remove('motion')
  }
}

const mm = gsap.matchMedia()
mm.add('(min-width: 768px) and (prefers-reduced-motion: no-preference)', () => setupMotion('desktop'))
mm.add('(max-width: 767.98px) and (prefers-reduced-motion: no-preference)', () => setupMotion('phone'))

// ---------- in-page links ----------
const yOf = (el) => (el === track ? 0 : el.getBoundingClientRect().top + window.scrollY)

function focusTarget(el) {
  if (!el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1')
  el.focus({ preventScroll: true })
}

// Instant jump. The film settles on its frame straight away and the right block enters after.
function jump(el) {
  if (!lenis) {
    window.scrollTo(0, yOf(el))
  } else {
    story.hideAll()
    lenis.scrollTo(yOf(el), { immediate: true, force: true })
    ScrollTrigger.update()
    film.settle()
    const scenesNow = story
    gsap.delayedCall(0.35, () => scenesNow.start())
  }
  focusTarget(el)
}

// Short distances scroll smoothly. Long ones cut through white instead of racing through the film.
function goTo(el, { covered = false } = {}) {
  if (!lenis) return jump(el)
  if (Math.abs(yOf(el) - window.scrollY) < window.innerHeight * 1.5) {
    lenis.scrollTo(yOf(el), { duration: 1.2 })
    return focusTarget(el)
  }
  if (covered) return jump(el)
  gsap.to(veil, {
    autoAlpha: 1,
    duration: 0.45,
    ease: 'power2.inOut',
    onComplete: () => {
      jump(el)
      gsap.to(veil, { autoAlpha: 0, duration: 0.8, delay: 0.15, ease: 'power2.out' })
    },
  })
}

document.addEventListener('click', (e) => {
  const link = e.target.closest('a[href^="#"]')
  if (!link || link.closest('.menu')) return
  const el = document.getElementById(link.getAttribute('href').slice(1))
  if (!el) return
  e.preventDefault()
  goTo(el)
})

createMenu({
  jump: (el) => goTo(el, { covered: true }),
  getLenis: () => lenis,
  reduced: () => !root.classList.contains('motion'),
})

// Below the film the header gets a soft white backing.
ScrollTrigger.create({
  trigger: '.page',
  start: 'top 12%',
  end: 'max',
  toggleClass: { targets: '.header', className: 'is-solid' },
})

const start = location.hash && document.getElementById(location.hash.slice(1))
if (start) requestAnimationFrame(() => jump(start))
else window.scrollTo(0, 0)
