import { gsap } from 'gsap'

// Full-screen white panel. It wipes down from the top, traps focus, closes on Esc,
// and jumps to a link's section while it still covers the page.
export function createMenu({ jump, getLenis, reduced }) {
  const burger = document.querySelector('.burger')
  const panel = document.getElementById('menu')
  const close = panel.querySelector('.menu__close')
  const items = panel.querySelectorAll('[data-menu-item]')
  const outside = document.querySelectorAll('.header, main, .footer')
  let open = false
  let tl = null

  const focusables = () => [...panel.querySelectorAll('a, button')]

  function onKey(e) {
    if (e.key === 'Escape') hide()
    if (e.key !== 'Tab') return
    const list = focusables()
    const first = list[0]
    const lastEl = list[list.length - 1]
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); lastEl.focus() }
    else if (!e.shiftKey && document.activeElement === lastEl) { e.preventDefault(); first.focus() }
  }

  function show() {
    if (open) return
    open = true
    panel.hidden = false
    burger.setAttribute('aria-expanded', 'true')
    outside.forEach((el) => { el.inert = true })
    getLenis()?.stop()
    document.addEventListener('keydown', onKey)
    tl?.kill()
    const d = reduced() ? 0 : 1
    tl = gsap.timeline()
      .fromTo(panel, { clipPath: 'inset(0% 0% 100% 0%)' }, { clipPath: 'inset(0% 0% 0% 0%)', duration: 0.7 * d, ease: 'expo.inOut' })
      .fromTo(items, { y: 24, opacity: 0 }, { y: 0, opacity: 1, duration: 0.9 * d, ease: 'power3.out', stagger: 0.07 * d }, 0.35 * d)
    close.focus({ preventScroll: true })
  }

  function hide(target) {
    if (!open) return
    open = false
    burger.setAttribute('aria-expanded', 'false')
    outside.forEach((el) => { el.inert = false })
    document.removeEventListener('keydown', onKey)
    getLenis()?.start()
    if (target) jump(target) // the panel still covers the page, so the jump is never seen
    else burger.focus({ preventScroll: true })
    tl?.kill()
    tl = gsap.to(panel, {
      clipPath: 'inset(0% 0% 100% 0%)',
      duration: reduced() ? 0 : 0.7,
      ease: 'expo.inOut',
      onComplete: () => { panel.hidden = true },
    })
  }

  burger.addEventListener('click', show)
  close.addEventListener('click', () => hide())
  panel.addEventListener('click', (e) => {
    const link = e.target.closest('a[href^="#"]')
    if (!link) return
    e.preventDefault()
    hide(document.getElementById(link.getAttribute('href').slice(1)))
  })
}
