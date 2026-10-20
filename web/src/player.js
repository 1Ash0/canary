// The strata player: renders the scene for a run, plays it once (GSAP playhead over the pure
// timeline), and handles pause/replay, scrubbing, keyboard stepping and the ?step= deep link.
// Reduced motion, or a deep link, shows a still state with no autoplay (SITE_RULES §4.5).
import { gsap } from 'gsap';
import { renderStrata, extraBottom, ORDER, LAYER_LABEL, formatTokens } from '../../design/scene/strata.js';
import { buildSchedule, timeForStep, frameAt, bind, apply } from '../../design/scene/timeline.js';
import { motion } from './data.js';

const COMPACT = '(max-width: 767px)'; // = layout.breakpoints.md in base.tokens.json

export function mountPlayer({ root, run, height = { wide: 376, compact: 460 }, autoplayDelay = 0.75, onStep }) {
  const q = (sel) => root.querySelector(sel);
  const N = run.steps.length, AT = run.compaction?.at_step ?? 0;
  const stage = q('[data-stage]');
  const compact = matchMedia(COMPACT).matches;
  const h = compact ? height.compact : height.wide + extraBottom(run);
  stage.innerHTML = renderStrata(run, { width: stage.clientWidth, height: h, compact });
  const refs = bind(stage.querySelector('svg'));
  const schedule = buildSchedule(run, motion, { start: 0.35 });
  const scrub = q('[data-scrub]');
  scrub.max = N;
  q('[data-out="label"]').textContent = run.meta.label;

  const fateItems = [];
  const list = q('[data-fates]');
  if (compact && list) {
    list.innerHTML = run.canaries.map((k) => {
      const detail = k.fate === 'changed' ? `→ ${k.after_text}` : k.fate === 'gone' ? 'absent from the summary' : 'named in the summary';
      return `<li class="fate-${k.fate}" data-fate-item="${k.id}"><span class="cite">${k.id} · ${k.type.replace('_', ' ')}</span> ${k.text} <span data-part="fate"><span class="cite">${k.fate}${k.fate === 'gone' ? ' ↓' : ''}</span> <span class="dim">${detail}</span></span></li>`;
    }).join('');
    for (const li of list.querySelectorAll('[data-fate-item]')) fateItems.push({ id: li.dataset.fateItem, li, fate: li.querySelector('[data-part="fate"]') });
  }

  const table = q('[data-table]');
  if (table) {
    const head = `<tr><th scope="col">step</th>${ORDER.map((l) => `<th scope="col">${LAYER_LABEL[l]}</th>`).join('')}</tr>`;
    table.insertAdjacentHTML('beforeend', head + run.steps.map((s) => `<tr><th scope="row">${s.i}</th>${ORDER.map((l) => `<td>${s.layers[l]}</td>`).join('')}</tr>`).join(''));
  }

  const playhead = { t: schedule.duration };
  let tween = null;
  function show(t) {
    playhead.t = t;
    const f = frameAt(schedule, t);
    apply(refs, f);
    q('[data-out="step"]').textContent = `${f.readout.step} / ${N}`;
    q('[data-out="tokens"]').textContent = `${formatTokens(f.readout.tokens)} / ${formatTokens(run.meta.limit_tokens)}`;
    scrub.value = Math.max(1, f.readout.step);
    for (const item of fateItems) {
      const c = f.canaries.find((x) => x.id === item.id);
      item.li.style.opacity = String(c.plantCallout);
      item.fate.style.opacity = String(c.fateCallout);
    }
    onStep?.(Math.max(1, f.readout.step), f);
  }

  const btn = q('[data-play]');
  function setButton(state) {
    const label = { playing: 'Pause', paused: 'Resume', ended: 'Replay' }[state];
    q('[data-play-label]').textContent = label;
    btn.setAttribute('aria-label', `${label} the sample run`);
    q('[data-icon-pause]').toggleAttribute('hidden', state !== 'playing');
    q('[data-icon-play]').toggleAttribute('hidden', state === 'playing');
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

  function goToStep(i, { writeUrl = true } = {}) {
    const step = Math.min(N, Math.max(1, i));
    tween?.pause();
    if (tween) setButton(tween.progress() === 1 ? 'ended' : 'paused');
    show(timeForStep(schedule, step));
    if (writeUrl) {
      const url = new URL(location.href);
      url.searchParams.set('step', String(step));
      history.replaceState(null, '', url);
    }
    return step;
  }
  scrub.addEventListener('input', () => goToStep(+scrub.value));

  const api = {
    schedule, show, goToStep, N, AT,
    currentStep: () => Math.max(1, frameAt(schedule, playhead.t).readout.step),
    start({ step, autoplay = true } = {}) {
      const mm = gsap.matchMedia();
      // matchMedia runs the callback only if a declared query matches, so declare both
      mm.add({ motion: '(prefers-reduced-motion: no-preference)', reduce: '(prefers-reduced-motion: reduce)' }, (ctx) => {
        const deep = step >= 1 && step <= N;
        if (ctx.conditions.reduce || deep || !autoplay) {
          show(deep ? timeForStep(schedule, step) : schedule.duration);
          setButton('ended');
          return;
        }
        play(0, autoplayDelay);
        return () => tween?.kill();
      });
    },
  };
  // QA hooks, same contract as the video page will use
  window.__duration = schedule.duration;
  window.__schedule = { seam: schedule.seam, fates: schedule.fates, fatesDone: schedule.fatesDone };
  window.__seek = (t) => { tween?.kill(); tween = null; setButton(t >= schedule.duration ? 'ended' : 'paused'); show(t); };
  return api;
}

export const playerMarkup = `
  <dl class="readout" aria-live="off">
    <div><dt>step</dt><dd data-out="step">–</dd></div>
    <div><dt>tokens</dt><dd data-out="tokens">–</dd></div>
    <div><dt>data</dt><dd data-out="label">–</dd></div>
  </dl>
  <div class="stage" data-stage></div>
  <div class="controls">
    <button class="replay" type="button" data-play aria-label="Replay the sample run">
      <svg viewBox="0 0 16 16" aria-hidden="true" data-icon-play><path d="M3 2v12l10-6z"/></svg>
      <svg viewBox="0 0 16 16" aria-hidden="true" data-icon-pause hidden><path d="M3 2h3.5v12H3zM9.5 2H13v12H9.5z"/></svg>
      <span data-play-label>Replay</span>
    </button>
    <label class="scrub"><span class="visually-hidden">Step</span><input type="range" min="1" value="1" data-scrub></label>
    <span class="keys" aria-hidden="true">← →</span>
  </div>
  <ul class="fates" data-fates></ul>
  <div class="visually-hidden"><table data-table><caption>Tokens per layer by step</caption></table></div>`;
