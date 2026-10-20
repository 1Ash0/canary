// Site motion helpers (SITE_RULES §4). Every setup goes through gsap.matchMedia with a reduced-motion
// branch that shows the final state; arrivals use the closed-form springs from the tokens, so the
// site moves with the same weight as the strata scene and the video.
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { SplitText } from 'gsap/SplitText';
import { spring } from '../../design/scene/motion.js';
import { motion } from './data.js';

gsap.registerPlugin(ScrollTrigger, SplitText);
export { gsap, ScrollTrigger };

export const MOTION = '(prefers-reduced-motion: no-preference)';
export const REDUCE = '(prefers-reduced-motion: reduce)';
const ms = (key) => motion.duration[key] / 1000;

// A spring as a GSAP ease: progress p of a tween lasting `seconds` maps to the spring's position.
export function springEase(name, seconds) {
  const { k, d } = motion.spring[name];
  return (p) => (p >= 1 ? 1 : spring(p * seconds, k, d));
}

// The one heading per page that gets a line-level reveal (D1): each line rises out of a clip mask.
export function splitHeading(el, { delay = 0.1, onFirstLine } = {}) {
  const mm = gsap.matchMedia();
  mm.add({ motion: MOTION, reduce: REDUCE }, (ctx) => {
    if (ctx.conditions.reduce) { onFirstLine?.(); return; }
    const split = SplitText.create(el, { type: 'lines', mask: 'lines', linesClass: 'split-line' });
    const tl = gsap.timeline({ delay });
    tl.from(split.lines, {
      yPercent: 110, duration: ms('reveal'), ease: springEase('step', ms('reveal')),
      stagger: motion.stagger.lines / 1000,
    });
    if (onFirstLine) tl.call(onFirstLine, [], ms('reveal') * 0.45);
    return () => split.revert();
  });
}

// A single 12 px rise and fade per block as it enters the viewport (the only prose motion).
export function riseOnEnter(elements, { stagger = 0 } = {}) {
  const els = [...elements];
  if (!els.length) return;
  const mm = gsap.matchMedia();
  mm.add({ motion: MOTION, reduce: REDUCE }, (ctx) => {
    if (ctx.conditions.reduce) return;
    gsap.set(els, { y: 12, autoAlpha: 0 });
    ScrollTrigger.batch(els, {
      start: 'top 88%', once: true,
      onEnter: (batch) => gsap.to(batch, {
        y: 0, autoAlpha: 1, duration: ms('base'), ease: 'power2.out', stagger: stagger || 0.06,
      }),
    });
  });
}

// Run `build(tl)` once when `trigger` enters; reduced motion jumps straight to the end state.
export function onEnterOnce(trigger, build, { start = 'top 75%' } = {}) {
  const mm = gsap.matchMedia();
  mm.add({ motion: MOTION, reduce: REDUCE }, (ctx) => {
    const tl = gsap.timeline({ paused: true });
    build(tl);
    if (ctx.conditions.reduce) { tl.progress(1); return; }
    ScrollTrigger.create({ trigger, start, once: true, onEnter: () => tl.play() });
    return () => tl.kill();
  });
}

export { ms };
