import { gsap } from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'
import { SplitText } from 'gsap/SplitText'

// The seven blocks over the film. Each plays a timed entrance when its window opens and a timed
// exit when it closes. Windows are read from the film time on screen, never from raw scroll.
export function createScenes(scenes) {
  const items = scenes.map((el) => ({
    el,
    from: parseFloat(el.dataset.in),
    to: el.dataset.out ? parseFloat(el.dataset.out) : Infinity,
    splits: [...el.querySelectorAll('[data-split]')].map((node) =>
      SplitText.create(node, { type: 'lines', mask: 'lines', linesClass: 'ln', tag: 'span', aria: 'none', autoSplit: true }),
    ),
    rise: el.querySelectorAll('[data-rise]'),
    cards: el.querySelectorAll('[data-card]'),
    halo: el.querySelector('.halo'),
    on: false,
    tl: null,
  }))
  let live = false
  gsap.set(scenes, { autoAlpha: 0 })

  function enter(s) {
    s.tl?.kill()
    const lines = s.splits.flatMap((split) => split.lines)
    const tl = (s.tl = gsap.timeline())
    tl.set(s.el, { autoAlpha: 1, y: 0 })
    if (s.halo) tl.fromTo(s.halo, { opacity: 0 }, { opacity: 1, duration: 1.2, ease: 'power2.out' }, 0)
    if (lines.length) {
      tl.fromTo(lines,
        { y: 24, rotationX: 35, opacity: 0 },
        { y: 0, rotationX: 0, opacity: 1, duration: 0.9, ease: 'power3.out', stagger: 0.09 }, 0)
    }
    const body = lines.length ? (lines.length - 1) * 0.09 + 0.15 : 0
    if (s.rise.length) {
      tl.fromTo(s.rise,
        { y: 12, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.9, ease: 'power3.out', stagger: 0.09 }, body)
    }
    s.cards.forEach((card, i) => {
      const at = body + 0.1 + i * 0.08
      tl.fromTo(card, { y: 24, opacity: 0 }, { y: 0, opacity: 1, duration: 0.9, ease: 'power3.out' }, at)
      const rule = card.querySelector('[data-rule]')
      const cap = card.querySelector('[data-cap]')
      const num = card.querySelector('[data-count]')
      if (rule) tl.fromTo(rule, { scaleX: 0 }, { scaleX: 1, duration: 0.8, ease: 'power2.inOut' }, at + 0.45)
      if (cap) tl.fromTo(cap, { opacity: 0 }, { opacity: 1, duration: 0.6, ease: 'power2.out' }, at + 0.85)
      if (num) {
        const end = parseFloat(num.dataset.count)
        const n = { v: 0 }
        num.textContent = '0'
        tl.to(n, { v: end, duration: 1.4, ease: 'power2.out', onUpdate: () => { num.textContent = Math.round(n.v) } }, at)
      }
    })
  }

  function leave(s) {
    s.tl?.kill()
    s.tl = gsap.to(s.el, { autoAlpha: 0, y: -12, duration: 0.5, ease: 'power2.in' })
  }

  return {
    update(t) {
      if (!live) return
      for (const s of items) {
        const on = t >= s.from && t < s.to
        if (on !== s.on) {
          s.on = on
          if (on) enter(s)
          else leave(s)
        }
      }
    },
    start() { live = true },
    // Under the veil of a long jump: clear the stage now, let the right block enter after.
    hideAll() {
      live = false
      for (const s of items) {
        s.tl?.kill()
        s.on = false
        gsap.set(s.el, { autoAlpha: 0 })
      }
    },
  }
}

// The page under the film: each element fades up 24px as it enters, once. Rules draw from the left.
export function createReveals() {
  const els = gsap.utils.toArray('[data-reveal]')
  const rules = gsap.utils.toArray('[data-draw]')
  gsap.set(els, { y: 24, autoAlpha: 0 })
  gsap.set(rules, { scaleX: 0 })
  ScrollTrigger.batch(els, {
    start: 'top 90%',
    once: true,
    onEnter: (batch) => gsap.to(batch, { y: 0, autoAlpha: 1, duration: 1.1, ease: 'power3.out', stagger: 0.09 }),
  })
  ScrollTrigger.batch(rules, {
    start: 'top 92%',
    once: true,
    onEnter: (batch) => gsap.to(batch, { scaleX: 1, duration: 1.4, ease: 'power3.inOut', stagger: 0.09 }),
  })
}
