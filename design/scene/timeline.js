// Hero/video timeline for the strata scene. frameAt(schedule, t) is a pure function of time, so the site
// (GSAP playhead) and the video renderer (seek(t)) produce identical states. Springs come from
// motion.spring in identity/base.tokens.json.
import { spring, ramp, clamp } from './motion.js';
import { totalOf } from './strata.js';

export function buildSchedule(run, motion, { start = 0 } = {}) {
  const N = run.steps.length, AT = run.compaction.at_step;
  const arrive = new Array(N + 1).fill(Infinity);
  // Cadence accelerates as the window fills: tension builds toward the limit.
  let t = start;
  for (let i = 1; i <= AT; i++) {
    arrive[i] = t;
    const p = (i - 1) / Math.max(1, AT - 1);
    t += 0.34 - 0.23 * Math.pow(p, 0.8);
  }
  const seam = arrive[AT] + 0.8;           // hold at the limit, then the seam
  arrive[AT + 1] = seam + 0.55;            // first post-compaction step: the window collapses
  const fateStart = arrive[AT + 1] + 0.55;
  const fates = {};
  const order = ['kept', 'changed', 'gone'];
  for (const k of run.canaries) fates[k.id] = fateStart + 0.45 * order.indexOf(k.fate);
  const fatesDone = Math.max(...Object.values(fates)) + 1.0;
  for (let i = AT + 2; i <= N; i++) arrive[i] = fatesDone + 0.13 * (i - AT - 2);
  const plants = Object.fromEntries(run.canaries.map((k) => [k.id, arrive[k.planted_step] + 0.12]));
  return { run, motion, N, AT, arrive, seam, fates, fatesDone, plants, duration: arrive[N] + 0.8 };
}

// The time at which step i is fully shown (used by the scrubber and ?step= deep links).
// Settled as far as possible, but always before step i+1 arrives (late steps arrive faster than they settle).
export function timeForStep(s, i) {
  const next = i < s.N ? s.arrive[i + 1] - 1e-3 : Infinity;
  const settled = i === s.AT + 1 ? s.fatesDone : s.arrive[i] + 0.7;
  return Math.min(settled, next);
}

export function frameAt(s, t) {
  const { step: SP, seam: SS, fall: SF } = s.motion.spring;
  const sp = (dt, c) => spring(dt, c.k, c.d);
  const { run, AT, N } = s;
  const rows = [];
  let step = 0;
  for (let i = 1; i <= N; i++) {
    const dt = t - s.arrive[i];
    if (dt < 0) { rows.push({ scale: 0, opacity: 0 }); continue; }
    step = i;
    if (i === AT + 1) {
      // collapse: the new row starts at the pre-compaction width and settles to its own on the heavy spring
      const from = totalOf(run.steps[AT - 1]) / totalOf(run.steps[AT]);
      rows.push({ scale: from + (1 - from) * sp(dt, SS), opacity: 1 });
    } else {
      rows.push({ scale: sp(dt, SP), opacity: clamp(dt / 0.06) });
    }
  }
  const seamDraw = sp(t - s.seam, SS);
  const canaries = run.canaries.map((k) => {
    const tp = s.plants[k.id], tf = s.fates[k.id];
    const fy = k.fate === 'gone' ? sp(t - tf, SF) : sp(t - tf, SS);
    return {
      id: k.id,
      plant: { scale: sp(t - tp, SP), opacity: t >= tp ? 1 : 0 },
      plantCallout: ramp(t, tp + 0.18, 0.25),
      // x and y settle on different springs, so the marker travels on a curve, not a straight line
      fate: { px: sp(t - tf, SP), py: fy, opacity: t >= tf ? 1 : 0 },
      fateCallout: ramp(t, tf + 0.45, 0.3),
      drop: k.fate === 'gone' ? ramp(t, tf + 0.1, 0.4) : 0,
    };
  });
  const shown = step ? run.steps[step - 1] : null;
  // The limit rule warms from ink-3 to ink as the window passes 85% full; compaction resets it.
  const fill = shown ? totalOf(shown) / run.meta.limit_tokens : 0;
  const limitHeat = step <= AT ? clamp((fill - 0.85) / 0.1) : 0;
  return {
    t, step, rows, canaries, limitHeat,
    // `late` is for compact layouts, where the label sits where the collapsing row passes
    seam: { draw: seamDraw, visible: t >= s.seam, label: ramp(t, s.seam + 0.3, 0.3), late: ramp(t, s.arrive[AT + 1] + 0.7, 0.3) },
    readout: { step, tokens: shown ? totalOf(shown) : 0 },
    ended: t >= s.duration,
  };
}

// Cache element handles once; apply(frame) then only writes transform/opacity.
export function bind(svg) {
  const all = (sel) => [...svg.querySelectorAll(sel)];
  const by = (attr) => Object.fromEntries(all(`[${attr}]`).map((el) => [el.getAttribute(attr), el]));
  return {
    rows: all('[data-row]'),
    rowLabels: by('data-row-label'),
    seamLine: svg.querySelector('[data-seam-line]'),
    seamTicks: all('[data-seam-tick]').map((el) => [el, +el.dataset.seamTick]),
    seamLabel: svg.querySelector('[data-seam-label]'),
    limitHot: svg.querySelector('[data-limit-hot]'),
    plants: by('data-plant'),
    fates: by('data-fate'),
    drops: by('data-drop'),
    leads: by('data-callout-lead'),
    texts: by('data-callout-text'),
  };
}

const set = (el, transform, opacity) => {
  if (!el) return;
  if (transform !== undefined) el.style.transform = transform;
  if (opacity !== undefined) el.style.opacity = String(opacity);
};

export function apply(refs, f) {
  f.rows.forEach((r, i) => {
    set(refs.rows[i], `scaleX(${r.scale.toFixed(4)})`, r.opacity);
    set(refs.rowLabels[String(i + 1)], undefined, r.opacity);
  });
  set(refs.limitHot, undefined, f.limitHeat);
  set(refs.seamLine, `scaleX(${f.seam.draw.toFixed(4)})`, f.seam.visible ? 1 : 0);
  for (const [el, frac] of refs.seamTicks) set(el, undefined, f.seam.visible && f.seam.draw >= frac ? 1 : 0);
  set(refs.seamLabel, undefined, refs.seamLabel?.dataset.seamLabel === 'late' ? f.seam.late : f.seam.label);
  for (const c of f.canaries) {
    set(refs.plants[c.id], `scale(${c.plant.scale.toFixed(4)})`, c.plant.opacity);
    const fe = refs.fates[c.id];
    if (fe) {
      const dx = +fe.dataset.dx * (1 - c.fate.px), dy = +fe.dataset.dy * (1 - c.fate.py);
      set(fe, `translate(${dx.toFixed(2)}px, ${dy.toFixed(2)}px)`, c.fate.opacity);
    }
    set(refs.drops[c.id], undefined, c.drop);
    for (const [key, v] of [[`${c.id}-plant`, c.plantCallout], [`${c.id}-fate`, c.fateCallout]]) {
      set(refs.leads[key], undefined, v);
      set(refs.texts[key], undefined, v);
    }
  }
}
