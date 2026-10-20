// D4b hero motion prototype. GSAP owns the claim reveal and the playhead; every frame of the instrument
// comes from the pure timeline (scene/timeline.js), the same function the video renderer will call.
import { gsap } from 'gsap';
import { SplitText } from 'gsap/SplitText';
import { renderStrata, ORDER, LAYER_LABEL, formatTokens } from '../scene/strata.js';
import { buildSchedule, timeForStep, frameAt, bind, apply } from '../scene/timeline.js';

gsap.registerPlugin(SplitText);
const $ = (sel) => document.querySelector(sel);

const [run, tokens] = await Promise.all([
  fetch('../d2/strata_sample.json').then((r) => r.json()),
  fetch('../identity/base.tokens.json').then((r) => r.json()),
]);
const N = run.steps.length, AT = run.compaction.at_step;

// ---- render the final state (complete without JS motion), then bind animatable parts
const stage = $('[data-stage]');
const compact = matchMedia('(max-width: 767px)').matches; // = layout.breakpoints.md
stage.innerHTML = renderStrata(run, { width: stage.clientWidth, height: compact ? 460 : 376, compact });
const refs = bind(stage.querySelector('svg'));
const schedule = buildSchedule(run, tokens.motion, { start: 0.35 }); // a beat of empty instrument at 0 / N

$('[data-out="label"]').textContent = run.meta.label;
const scrub = $('[data-scrub]');
scrub.max = N;

if (compact) {
  $('[data-fates]').innerHTML = run.canaries.map((k) => {
    const detail = k.fate === 'changed' ? `→ ${k.after_text}` : k.fate === 'gone' ? 'absent from the summary' : 'verbatim in summary';
    return `<li class="fate-${k.fate}" data-fate-item="${k.id}"><span data-part="plant"><span class="cite">${k.id} · ${k.type.replace('_', ' ')}</span> ${k.text}</span> <span data-part="fate"><span class="cite">${k.fate}${k.fate === 'gone' ? ' ↓' : ''}</span> <span class="dim">${detail}</span></span></li>`;
  }).join('');
}
// The phone fate list follows the same frame as the figure: facts appear when planted, fates when resolved.
const fateItems = [...document.querySelectorAll('[data-fate-item]')].map((li) => ({
  id: li.dataset.fateItem, fate: li.querySelector('[data-part="fate"]'), li,
}));
const head = `<tr><th scope="col">step</th>${ORDER.map((l) => `<th scope="col">${LAYER_LABEL[l]}</th>`).join('')}</tr>`;
$('[data-table]').insertAdjacentHTML('beforeend', head + run.steps.map((s) => `<tr><th scope="row">${s.i}</th>${ORDER.map((l) => `<td>${s.layers[l]}</td>`).join('')}</tr>`).join(''));

// ---- the one place a frame is shown
const playhead = { t: schedule.duration };
function show(t) {
  playhead.t = t;
  const f = frameAt(schedule, t);
  apply(refs, f);
  $('[data-out="step"]').textContent = `${f.readout.step} / ${N}`;
  $('[data-out="tokens"]').textContent = `${formatTokens(f.readout.tokens)} / ${formatTokens(run.meta.limit_tokens)}`;
  scrub.value = Math.max(1, f.readout.step);
  for (const item of fateItems) {
    const c = f.canaries.find((x) => x.id === item.id);
    item.li.style.opacity = String(c.plantCallout);
    item.fate.style.opacity = String(c.fateCallout);
  }
}

// ---- play / pause / replay
const btn = $('[data-play]');
let tween = null;
function setButton(state) {
  const label = { playing: 'Pause', paused: 'Resume', ended: 'Replay' }[state];
  $('[data-play-label]').textContent = label;
  btn.setAttribute('aria-label', `${label} the sample run`);
  // SVG elements have no .hidden property; set the attribute
  $('[data-icon-pause]').toggleAttribute('hidden', state !== 'playing');
  $('[data-icon-play]').toggleAttribute('hidden', state === 'playing');
}
function play(from = 0, delay = 0) {
  tween?.kill();
  show(from);
  setButton('playing');
  tween = gsap.to(playhead, {
    t: schedule.duration, duration: schedule.duration - from, ease: 'none', delay,
    onUpdate: () => show(playhead.t),
    onComplete: () => setButton('ended'),
  });
}
btn.addEventListener('click', () => {
  if (!tween || tween.progress() === 1) return play(0);
  if (tween.paused()) { tween.resume(); setButton('playing'); } else { tween.pause(); setButton('paused'); }
});

// ---- scrubbing interrupts playback; the step is deep-linked in the URL
function goToStep(i) {
  tween?.pause();
  if (tween) setButton(tween.progress() === 1 ? 'ended' : 'paused');
  show(timeForStep(schedule, i));
  const url = new URL(location.href);
  url.searchParams.set('step', String(i));
  history.replaceState(null, '', url);
}
scrub.addEventListener('input', () => goToStep(+scrub.value));
addEventListener('keydown', (e) => {
  if (e.target instanceof HTMLInputElement || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.key === 'c') goToStep(AT + 1);
});

// ---- motion policy: reduced motion or a deep link shows a still state; otherwise play once
const deep = Number(new URLSearchParams(location.search).get('step'));
const mm = gsap.matchMedia();
mm.add({ motion: '(prefers-reduced-motion: no-preference)', reduce: '(prefers-reduced-motion: reduce)' }, (ctx) => {
  if (ctx.conditions.reduce || (deep >= 1 && deep <= N)) {
    show(deep >= 1 && deep <= N ? timeForStep(schedule, deep) : schedule.duration);
    setButton('ended');
    return;
  }
  const split = SplitText.create('#claim', { type: 'lines', mask: 'lines' });
  gsap.from(split.lines, { yPercent: 100, duration: tokens.motion.duration.reveal / 1000, stagger: tokens.motion.stagger.lines / 1000, ease: 'power3.out' });
  play(0, 0.75); // the instrument starts as the claim settles: one moving picture at a time
  return () => { tween?.kill(); split.revert(); };
});

// QA hooks: deterministic frames for strips and the renderer
window.__duration = schedule.duration;
window.__schedule = { seam: schedule.seam, fates: schedule.fates, fatesDone: schedule.fatesDone };
window.__seek = (t) => { tween?.kill(); tween = null; setButton(t >= schedule.duration ? 'ended' : 'paused'); show(t); };
document.documentElement.dataset.ready = 'true';
