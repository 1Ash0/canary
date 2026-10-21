// The Canary video (ADR-016, VIDEO_RULES): one continuous frame, every pixel a pure function of
// (t, data). window.seek(t) sets the frame; window.__duration and window.__ready are the render
// contract. The strata chart is the site's own scene (strata.js + timeline.js) on a recorded run.
// Every number and every quoted value comes from the run file or experiments/exp004.json.
import { renderStrata, totalOf, formatTokens } from '../scene/strata.js';
import { buildSchedule, frameAt, bind, apply } from '../scene/timeline.js';
import { spring, clamp, ramp } from '../scene/motion.js';

const q = new URLSearchParams(location.search);
const SQUARE = q.get('format') === 'square';
const DATA = q.get('data') ?? '../../web/public/data';
const RUN = q.get('run') ?? 'exp004-s19-mistral-head_tail-multi_code';
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const load = (p) => fetch(p).then((r) => { if (!r.ok) throw new Error(`${p}: ${r.status}`); return r.json(); });

const [tokens, run, exp] = await Promise.all([
  load('../identity/base.tokens.json'), load(`${DATA}/runs/${RUN}.json`), load(`${DATA}/experiments/exp004.json`)]);
const S = tokens.motion.spring;
const sp = (t, name) => spring(t, S[name].k, S[name].d);

// layout per format (px at 1080 wide)
const L = SQUARE
  ? { h: 1080, stageTop: 262, stageH: 470, readout: 742, facts: 806, call: 806, matrixTop: 452, shrink: 0.4 }
  : { h: 1350, stageTop: 300, stageH: 540, readout: 870, facts: 950, call: 950, matrixTop: 650, shrink: 0.52 };
document.querySelector('[data-frame]').classList.toggle('square', SQUARE);

// ---- the recorded episode ------------------------------------------------------------------
const stage = $('[data-stage]');
stage.style.top = `${L.stageTop}px`;
// drawn at half size and scaled 2x: the scene's labels are sized for the site, and a phone shows
// this frame at about a third of 1080, so every label doubles (vector, so it stays crisp)
const ZOOM = SQUARE ? 1.8 : 2;  // the square frame is shorter: a smaller zoom keeps the chart's rows apart
stage.innerHTML = renderStrata(run, { width: 952 / ZOOM, height: L.stageH / ZOOM, compact: false });
const refs = bind(stage.querySelector('svg'));
const schedule = buildSchedule(run, tokens.motion, { start: 0 });
const SLOW = 1.25;            // the scene plays a quarter slower than on the site: captions need time
const T0 = 0.3;
const sceneT = (t) => clamp((t - T0) / SLOW, 0, schedule.duration);
const N = run.steps.length;
const asked = run.transcript.find((m) => m.role === 'assistant' && m.step === N && m.text.startsWith('[tool_call'));
const call = asked ? { name: asked.text.slice(11).split(' ')[0], args: JSON.parse(asked.text.slice(asked.text.indexOf('{'), asked.text.lastIndexOf('}') + 1)) } : null;
const FACT_NAME = { C1: 'channel rule', I1: 'account code', D1: 'deploy target' };
const graded = run.canaries.find((k) => k.id === 'I1');

// ---- the beats (times in seconds) ----------------------------------------------------------
const tSeam = T0 + schedule.seam * SLOW;
const tFates = T0 + schedule.fatesDone * SLOW;
const B = {
  hook: [0, 3.6], fill: [3.7, tSeam - 0.1], seam: [tSeam + 0.2, tFates - 0.2], fates: [tFates, tFates + 2.6],
  call: [tFates + 2.8, tFates + 7.0], shrink: tFates + 7.2, matrix: [tFates + 7.3, tFates + 16.8], end: [tFates + 17.0, tFates + 20.5],
};
const DURATION = B.end[1];
const kept = run.canaries.filter((k) => k.fate === 'kept').length;
const CAPS = [
  [B.hook, `We hid ${run.canaries.length} facts in an AI agent's context.`],
  [B.fill, 'Then the context filled up, past its budget.'],
  [B.seam, `The harness kept the head and the tail, and cut the middle.`],
  [B.fates, `${run.canaries.length - kept} of the ${run.canaries.length} facts were cut.`],
  [B.call, call ? `Asked for the ${FACT_NAME[graded.id]}, the agent filed the invoice under <span class="q">"${esc(call.args.account_code)}"</span>.` : ''],
  [B.matrix, `Same history, ${exp.matrix[0].n} seeds, four ways to make room. Each loses a different fact.`],
  [B.end, 'The agent fails on exactly the fact that was cut.'],
];

// a caption rises in on the ui spring after its state changes, and is gone before the next one
function caption(t) {
  const cur = CAPS.find(([[a, b]]) => t >= a && t < b);
  const el = $('[data-cap]');
  if (!cur) { el.style.opacity = 0; return; }
  const [[a, b], html] = cur;
  if (el.dataset.html !== html) { el.innerHTML = html; el.dataset.html = html; }
  const inn = sp(t - a, 'ui'), out = ramp(t, b - 0.3, 0.3);
  el.style.opacity = String(clamp(inn) * (1 - out));
  el.style.transform = `translateY(${(1 - inn) * 18}px)`;
}

// ---- static markup built once; seek only sets values --------------------------------------
$('[data-facts]').style.top = `${L.facts}px`;
$('[data-facts]').innerHTML = run.canaries.map((k) => `<div class="fact" data-fact="${k.id}"><span class="id">${k.id}</span><span>${FACT_NAME[k.id]}</span><span>${esc(k.text)}</span><span class="st" data-st></span></div>`).join('');
$('[data-call]').style.top = `${L.call}px`;
$('[data-call]').innerHTML = call ? `${esc(call.name)}(${Object.entries(call.args).map(([k, v]) => `${esc(k)}=${k === 'account_code' ? `<span class="bad">"${esc(v)}"</span>` : `"${esc(v)}"`}`).join(', ')})<span class="note">The code planted at turn ${graded.planted_step} was ${esc(graded.text)}. Compaction cut it.</span>` : '';

const facts = exp.facts;
const policies = [...new Set(exp.matrix.map((m) => m.policy))];
const cellOf = (p, f) => exp.matrix.find((m) => m.policy === p && m.fact === f);
$('[data-matrix]').style.top = `${L.matrixTop}px`;
$('[data-matrix]').innerHTML = `
  <div class="mx-row mx-head" data-mx-head><span>27 seeds each</span>${facts.map((f) => `<span>${f.id} ${f.name}<span class="sub">turn ${f.turn}</span></span>`).join('')}</div>
  ${policies.map((p) => `<div class="mx-row${p === run.meta.policy ? ' is-watched' : ''}" data-mx-row><span class="mx-name">${esc(cellOf(p, facts[0].id).name)}</span>${facts.map((f) => {
    const c = cellOf(p, f.id);
    const gone = c.kept === 0;
    return `<span class="mx-cell" data-mx-cell><span class="k${gone ? ' is-gone' : ''}">${gone ? 'gone ↓' : `kept ${c.kept}/${c.kept_n}`}</span><span class="w">${c.k}/${c.n} wrong</span></span>`;
  }).join('')}</div>`).join('')}`;
const cells = [...document.querySelectorAll('[data-mx-cell]')];
const rows = [...document.querySelectorAll('[data-mx-row]')];
$('[data-source]').innerHTML = `<b>recorded</b> · Canary, ${esc(exp.exp_id)} (preregistered) · ${esc(run.meta.model)}, free tier · seed ${run.meta.seed} · ${esc(exp.dates.join(', '))}`;

// ---- seek ---------------------------------------------------------------------------------
function seek(t) {
  const st = sceneT(t);
  const f = frameAt(schedule, st);
  apply(refs, f);
  caption(t);

  // readout under the chart: the turn, the window size, the label
  const step = Math.max(1, f.readout.step);
  const ro = $('[data-readout]');
  const shrink = sp(t - B.shrink, 'seam');
  const scale = 1 - (1 - L.shrink) * shrink;
  stage.style.transform = `scale(${ZOOM * scale})`;
  ro.style.top = `${L.readout}px`;
  ro.style.opacity = String(1 - ramp(t, B.shrink, 0.35));
  ro.innerHTML = `<span>turn <b>${step} / ${N}</b></span><span>window <b>${formatTokens(totalOf(run.steps[step - 1]))} / ${formatTokens(run.meta.limit_tokens)}</b> tokens</span>`;

  // the facts list: each fact appears when planted, then shows its fate once the chart settles it
  const factsEl = $('[data-facts]');
  factsEl.style.opacity = String(1 - ramp(t, B.call[0] - 0.4, 0.4));
  run.canaries.forEach((k, i) => {
    const row = factsEl.querySelector(`[data-fact="${k.id}"]`);
    const planted = st >= schedule.arrive[k.planted_step];
    row.style.opacity = planted ? '1' : '0.25';
    const s = row.querySelector('[data-st]');
    const settled = (f.canaries[i]?.fateCallout ?? 0) > 0.5;
    s.textContent = !planted ? '' : settled ? (k.fate === 'gone' ? 'gone ↓' : 'kept') : 'in the window';
    s.className = `st${settled ? (k.fate === 'gone' ? ' is-gone' : ' is-kept') : ''}`;
  });

  // the recorded call, then out before the chart shrinks
  const callEl = $('[data-call]');
  const cin = sp(t - B.call[0] - 0.4, 'ui');
  callEl.style.opacity = String(clamp(cin) * (1 - ramp(t, B.shrink - 0.2, 0.4)));
  callEl.style.transform = `translateY(${(1 - cin) * 16}px)`;

  // the matrix: header, then cell by cell, row-major; the watched row is the run above
  const head = $('[data-mx-head]');
  const hin = sp(t - B.matrix[0] - 0.6, 'ui');
  head.style.opacity = String(clamp(hin));
  rows.forEach((r, ri) => { r.style.opacity = String(clamp(sp(t - B.matrix[0] - 0.9 - ri * 0.3, 'ui'))); });
  cells.forEach((c, i) => {
    const a = sp(t - B.matrix[0] - 1.6 - i * 0.42, 'step');
    c.style.opacity = String(clamp(a));
    c.style.transform = `translateY(${(1 - clamp(a)) * 10}px)`;
  });
}

window.seek = seek;
// the captions as plain text with their times, for the .srt file the renderer writes
window.__captions = CAPS.filter(([, html]) => html).map(([[a, b], html]) => ({ from: a, to: b, text: html.replace(/<[^>]+>/g, '') }));
window.__duration = DURATION;
window.__ready = document.fonts.ready.then(() => { seek(0); return true; });
seek(0);
