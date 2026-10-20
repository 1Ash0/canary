// Minimal stand-in for the site's planned GSAP use: one heading reveal and one pinned, scrubbed section.
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';

gsap.registerPlugin(ScrollTrigger);
const mm = gsap.matchMedia();

mm.add({ motion: '(prefers-reduced-motion: no-preference)', reduce: '(prefers-reduced-motion: reduce)' }, (ctx) => {
  if (ctx.conditions.reduce) {
    // Reduced motion: final state, no scroll choreography.
    gsap.set(['#title', '#bar'], { clearProps: 'all' });
    window.__trial = { mode: 'reduce', triggers: ScrollTrigger.getAll().length };
    return;
  }
  gsap.from('#title', { yPercent: 40, opacity: 0, duration: 0.9, ease: 'power3.out' });
  gsap.fromTo('#bar', { scaleX: 0 }, {
    scaleX: 1, ease: 'none',
    scrollTrigger: { trigger: '#pin', start: 'top top', end: '+=800', pin: true, scrub: 0.5 },
  });
  window.__trial = { mode: 'motion', triggers: ScrollTrigger.getAll().length };
});
