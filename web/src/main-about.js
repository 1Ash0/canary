// /about: four beats drawn as text (ADR-022). Each frame is built from a recorded run's real token
// counts, so even the explainer is data. The beats advance once when the section enters, then the
// reader steps through them; reduced motion opens on the last beat with no autoplay.
import { shell } from './shell.js';
import { loadRun } from './data.js';
import { asciiTurns, asciiGauge, asciiSeam } from '../../design/scene/ascii.js';
import { totalOf } from '../../design/scene/strata.js';
import { splitHeading, riseOnEnter, gsap, ScrollTrigger, MOTION, REDUCE } from './motion-kit.js';

shell('../', 'about');
const $ = (s) => document.querySelector(s);
splitHeading($('[data-split]'));

const TEXT = [
  'Plant. Early in the run, the user states a rule: post status updates to one channel and no other. That rule is the canary.',
  'Fill. The agent keeps working: files read, outputs returned, replies written. The window grows past its budget.',
  'Compact. The harness must make room. Here a model summarises the old turns; everything dimmed is gone, and the summary has to carry what mattered.',
  'Probe. A request arrives where the rule matters. The agent answers with one tool call, and that call is graded. This summary never named the channel, so the agent guessed.',
];

function frames(run) {
  const tr = run.transcript;
  const N = run.steps.length, AT = run.compaction.at_step;
  const kind = (m) => (m.role === 'system' ? 'system' : m.origin === 'canary' ? 'rule' : m.origin === 'summary' ? 'summary'
    : m.role === 'tool' ? 'tool' : m.role === 'user' && m.step === N ? 'probe' : 'history');
  const span = Math.max(run.meta.limit_tokens, ...run.steps.map(totalOf));
  const draw = (upTo, after, extra = []) => {
    const rows = [];
    for (const m of tr.filter((x) => x.step <= upTo && (after || x.origin !== 'summary'))) {
      const k = kind(m);
      const key = m.role === 'system' ? 'sys' : k === 'summary' ? 'sum' : k === 'probe' ? 'ask' : `t${String(m.step).padStart(2, '0')}`;
      let row = rows.at(-1);
      if (!row || row.key !== key) { row = { key, tag: key, segments: [], cls: '' }; rows.push(row); }
      row.segments.push({ kind: k, tokens: m.tokens, state: after && !m.kept ? 'out' : 'in' });
      if (k === 'rule') { row.cls = 'ax-rule-row'; row.lost = after; }
      if (k === 'summary') { row.cls = 'ax-summary-row'; row.note = 'no channel named'; }
    }
    const total = totalOf(run.steps[Math.min(upTo, N) - 1]);
    const out = [asciiGauge(total, run.meta.limit_tokens, { label: 'window', span }), ''];
    rows.forEach((r) => { if (after && r.key === 'sum') out.push(asciiSeam(`compaction after step ${AT}`)); out.push(asciiTurns([r])); });
    return [...out, ...extra].join('\n');
  };
  const probe = run.meta.probe;
  return [
    draw(2, false),
    draw(AT, false),
    draw(AT, true),
    draw(N, true, ['', `<span class="ax-row ax-lost">  → post_status(${probe.evidence.replace(/'/g, '"')})  <span class="ax-note">rule broken ↓  the rule said ${run.canaries[0].text}</span></span>`]),
  ];
}

try {
  const run = await loadRun('../', 'exp001-s19-nvidia');
  const fr = frames(run);
  const tabs = [...document.querySelectorAll('[data-beat]')];
  const show = (i) => {
    $('[data-beat-ascii]').innerHTML = fr[i];
    $('[data-beat-text]').textContent = TEXT[i];
    tabs.forEach((t, j) => t.setAttribute('aria-selected', String(i === j)));
  };
  tabs.forEach((t, i) => t.addEventListener('click', () => { autoplay?.kill(); show(i); }));
  let autoplay = null;
  gsap.matchMedia().add({ motion: MOTION, reduce: REDUCE }, (ctx) => {
    if (ctx.conditions.reduce) { show(3); return; }
    show(0);
    ScrollTrigger.create({
      trigger: '.beats', start: 'top 70%', once: true,
      onEnter: () => { autoplay = gsap.timeline().call(show, [1], 1.4).call(show, [2], 3.2).call(show, [3], 5.2); },
    });
  });
} catch (e) {
  $('[data-beat-text]').textContent = `Could not load the run: ${e.message}`;
}

const CMDS = [
  ['Install', 'uv sync --dev'],
  ['Replay the checks offline', 'make check'],
  ['What each policy keeps (no model)', 'uv run ctxcheck survival'],
  ['The whole pipeline with a toy agent', 'uv run ctxcheck run --exp DEMO --simulated --seeds 10'],
  ['Report it, with intervals', 'uv run ctxcheck report results/simulated/DEMO'],
];
$('[data-cmds]').innerHTML = CMDS.map(([label, cmd]) => `
  <div class="cmd" data-rise><span class="lab-label">${label}</span>
    <div class="cmd-row"><code>${cmd}</code><button type="button" class="replay" data-copy-cmd="${cmd}">copy</button></div>
  </div>`).join('');
document.querySelectorAll('[data-copy-cmd]').forEach((b) => b.addEventListener('click', async () => {
  try { await navigator.clipboard.writeText(b.dataset.copyCmd); b.textContent = 'copied'; } catch { b.textContent = 'select the text'; }
  setTimeout(() => { b.textContent = 'copy'; }, 1600);
}));
riseOnEnter(document.querySelectorAll('[data-rise]'));
document.documentElement.dataset.ready = 'true';
