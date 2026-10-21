// "Same history. Two ways to make room." Two recorded runs of the same seed, drawn with the shared
// strata scene and scrubbed together by scroll (ScrollTrigger pin + scrub, SITE_RULES §4.3). One
// moving picture: both panels follow the same playhead. The pair and the seed come from the shared
// episode (episode.js): pick a preset, a side or a seed and both panels redraw at the same scroll
// position. Small screens and reduced motion get the final state with every note visible.
import { renderStrata, formatTokens, totalOf } from '../../design/scene/strata.js';
import { buildSchedule, timeForStep, frameAt, bind, apply } from '../../design/scene/timeline.js';
import { gsap, ScrollTrigger, MOTION } from './motion-kit.js';
import { motion, BASE } from './data.js';
import { POLICY_NAME, CANARY } from './episode.js';

const PIN = `(min-width: 1024px) and (min-height: 680px) and ${MOTION}`;
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const MECHANISM = {
  recency_truncate: 'drops the earliest turns until the window fits',
  head_tail: 'keeps the opening turns and the newest, and drops the middle',
  observation_mask: 'hides old tool output and keeps every message',
  llm_summary: 'asks the model to summarise everything except the latest turns',
};

const BOTH = {
  recency_truncate: 'Both drop the earliest turns until the window fits.',
  head_tail: 'Both keep the opening turns and the newest, and drop the middle.',
  observation_mask: 'Both hide old tool output and keep every message.',
  llm_summary: 'Both ask the model to summarise everything except the latest turns.',
};

// How a side is named in the notes: by what differs between the two panels.
function namer(A, B) {
  if (A.policy === B.policy) return (s) => s.host;
  if (A.tag === B.tag) return (s) => POLICY_NAME[s.policy];
  return (s) => s.name;
}

const cap = (t) => t[0].toUpperCase() + t.slice(1);

function fateSentence(side, fate, name) {
  name = cap(name);
  const what = CANARY[side.canary].value;
  if (side.policy === 'llm_summary') {
    const who = name === 'Model summary' ? 'The model summary' : `${name}'s summary`;
    return fate === 'kept' ? `${who} keeps the ${what}.` : `${who} never names it.`;
  }
  return fate === 'kept' ? `${name} keeps the rule's turn, word for word.` : `${name} cuts the rule's turn.`;
}

function strip(ep, key, seed, which) {
  const side = ep.side(key);
  const broke = side.seeds.filter((d) => d.grade === 'violated').length;
  const graded = side.seeds.filter((d) => d.grade !== 'not_applicable').length;
  return `<div class="panel-strip">
    <p class="lab-label">This choice on every seed: ${broke} of ${graded} ${CANARY[side.canary].bad}</p>
    <div class="dots dots-mini" role="group" aria-label="${esc(side.name)}: one mark per seed; choose one to compare it">${side.seeds.map((d) => {
      const cls = d.grade === 'violated' ? 'is-broke' : d.grade === 'respected' ? 'is-ok' : 'is-na';
      const what = d.grade === 'violated' ? CANARY[side.canary].bad : d.grade === 'respected' ? CANARY[side.canary].good : 'not graded';
      return `<button type="button" class="dot ${cls}${d.seed === seed ? ' is-current' : ''}" data-seed="${d.seed}" data-which="${which}" aria-pressed="${d.seed === seed}" aria-label="seed ${d.seed}: ${what}"></button>`;
    }).join('')}</div>
  </div>`;
}

function picker(ep, key, which) {
  return `<label class="panel-pick"><span class="visually-hidden">Panel ${which === 'a' ? 'one' : 'two'}</span>
    <select data-pick="${which}">${ep.sides().map((s) => `<option value="${s.key}"${s.key === key ? ' selected' : ''}>${esc(s.name)}</option>`).join('')}</select></label>`;
}

export function mountCompare(root, ep, loadRun) {
  const head = root.querySelector('.compare-head');
  head.insertAdjacentHTML('beforeend', `
    <div class="compare-controls">
      <div class="lab-seg" role="radiogroup" aria-label="What the agent was told" data-canaries>
        ${ep.canaries.map((c) => `<label><input type="radio" name="cmp-canary" value="${c}"><span>${CANARY[c].name}</span></label>`).join('')}
      </div>
      <div class="lab-seg" role="radiogroup" aria-label="Pairs to compare" data-presets></div>
      <div class="seed-step" role="group" aria-label="Seed">
        <button type="button" class="replay" data-seed-step="-1" aria-label="Previous seed">←</button>
        <span class="mono" data-seed-label aria-live="polite"></span>
        <button type="button" class="replay" data-seed-step="1" aria-label="Next seed">→</button>
      </div>
    </div>`);
  const list = root.querySelector('[data-compare-notes]');
  const cache = new Map();
  const getRun = (id) => { if (!cache.has(id)) cache.set(id, loadRun(BASE, id)); return cache.get(id); };

  let panels = [], noteEls = [], lastNote = -1, progress = 1, token = 0, pinned = false;

  function show(p) {
    progress = p;
    if (!panels.length) return;
    let seamDown = false, fatesIn = true;
    for (const panel of panels) {
      const t = panel.from + (panel.to - panel.from) * p;
      const f = frameAt(panel.schedule, t);
      apply(panel.refs, f);
      const row = panel.run.steps[Math.max(1, f.readout.step) - 1];
      panel.out('step').textContent = `${f.readout.step} / ${panel.run.steps.length}`;
      panel.out('tokens').textContent = `${formatTokens(totalOf(row))} / ${formatTokens(panel.run.meta.limit_tokens)}`;
      const k = panel.run.canaries[0];
      const settled = f.canaries[0]?.fateCallout > 0.5;
      const fateEl = panel.out('fate');
      fateEl.textContent = settled ? (k.fate === 'gone' ? 'gone ↓' : 'kept') : 'in the window';
      fateEl.classList.toggle('is-gone', settled && k.fate === 'gone');
      seamDown ||= f.seam.draw > 0.6;
      fatesIn &&= settled;
    }
    // each note enters after the state it explains (SITE_RULES 4.1.4), not at a scroll fraction
    const n = fatesIn ? 2 : seamDown ? 1 : 0;
    if (n !== lastNote) {
      lastNote = n;
      noteEls.forEach((el, i) => el.classList.toggle('is-current', i === n));
    }
  }

  async function draw(state) {
    const mine = ++token;
    const keys = [state.a, state.b];
    const runIds = keys.map((k) => ep.outcome(k, state.seed)?.run);
    const runs = await Promise.all(runIds.map(getRun));
    if (mine !== token) return;  // a newer pick arrived while these loaded
    const [A, B] = keys.map((k) => ep.side(k));
    const name = namer(A, B);
    const rule = runs[0].transcript.find((m) => m.origin === 'canary')?.text ?? runs[0].canaries[0].text;

    root.querySelector('[data-compare-lede]').textContent =
      `${CANARY[state.canary].name}, seed ${state.seed} of EXP-002, recorded twice: the same ${runs[0].steps.length - 1} scripted turns, the same rule, ` +
      `the same request. ${A.policy === B.policy ? 'Only the model that writes the summary changes.' : 'Only how the harness makes room changes.'} ` +
      (pinned ? 'Scroll to compact, or pick another pair or seed.' : 'Pick another pair or seed to compare.');
    root.querySelector('[data-seed-label]').textContent = `seed ${state.seed}`;
    const presets = ep.presets();
    root.querySelector('[data-presets]').innerHTML = presets.map((p, i) => `<label><input type="radio" name="cmp-preset" value="${i}"${p.a === state.a && p.b === state.b ? ' checked' : ''}><span>${esc(p.label)}</span></label>`).join('');
    root.querySelectorAll('input[name="cmp-canary"]').forEach((el) => { el.checked = el.value === state.canary; });

    const mech = A.policy === B.policy
      ? BOTH[A.policy]
      : `${cap(POLICY_NAME[A.policy])} ${MECHANISM[A.policy]}; ${POLICY_NAME[B.policy]} ${MECHANISM[B.policy]}.`;
    const notes = [
      `Turn 2 plants it: “${rule}” Both runs carry the same history toward the limit.`,
      `The next request needs a model call and the window is over budget, so the harness makes room. ${mech} That cut is the seam.`,
      `${fateSentence(A, runs[0].canaries[0].fate, name(A))} ${fateSentence(B, runs[1].canaries[0].fate, name(B))}`,
    ];
    list.innerHTML = notes.map((n, i) => `<li data-note="${i}"><span class="note-n">${i + 1}</span><span>${esc(n)}</span></li>`).join('');
    noteEls = [...list.children];
    lastNote = -1;

    panels = runs.map((run, i) => {
      const which = i ? 'b' : 'a';
      const fig = root.querySelector(`[data-panel="${i}"]`);
      fig.innerHTML = `
        <figcaption class="panel-head">${picker(ep, keys[i], which)}<span class="mono">${esc(ep.side(keys[i]).model)}</span></figcaption>
        <div class="panel-stage" data-stage></div>
        <dl class="panel-readout">
          <div><dt>turn</dt><dd data-out="step">–</dd></div>
          <div><dt>tokens</dt><dd data-out="tokens">–</dd></div>
          <div><dt>rule</dt><dd data-out="fate">–</dd></div>
        </dl>
        ${strip(ep, keys[i], state.seed, which)}`;
      const stage = fig.querySelector('[data-stage]');
      const width = Math.max(300, stage.clientWidth);
      // shorter screens get shorter charts, so the pinned section can still fit in one view
      const height = innerHeight < 860 ? 230 : 300;
      stage.innerHTML = renderStrata(run, { width, height, compact: width < 420 });
      const schedule = buildSchedule(run, motion, { start: 0 });
      return {
        run, schedule, refs: bind(stage.querySelector('svg')),
        from: timeForStep(schedule, Math.max(1, schedule.AT - 3)), to: schedule.duration,
        out: (k) => fig.querySelector(`[data-out="${k}"]`),
      };
    });
    show(progress);
    root.dispatchEvent(new CustomEvent('compare:drawn'));
  }

  // one delegated listener each, so redrawn panels need no rebinding
  root.addEventListener('change', (e) => {
    if (e.target.matches('[data-pick]')) ep.set({ [e.target.dataset.pick]: e.target.value });
    if (e.target.name === 'cmp-preset') { const p = ep.presets()[+e.target.value]; ep.set({ a: p.a, b: p.b }); }
    if (e.target.name === 'cmp-canary') ep.set({ canary: e.target.value });
  });
  root.addEventListener('click', (e) => {
    const dot = e.target.closest('[data-seed]');
    if (dot && root.contains(dot)) ep.set({ seed: +dot.dataset.seed });
    const step = e.target.closest('[data-seed-step]');
    if (step) {
      const i = ep.seeds.indexOf(ep.get().seed) + +step.dataset.seedStep;
      ep.set({ seed: ep.seeds[(i + ep.seeds.length) % ep.seeds.length] });
    }
  });
  ep.on(draw);

  // the pin decision needs the drawn panels (it checks that the section fits the viewport)
  const ready = draw(ep.get()).then(() => {
    const mm = gsap.matchMedia();
    mm.add({ pin: PIN, any: 'all' }, (ctx) => {
      const content = root.querySelector('[data-compare-notes]').getBoundingClientRect().bottom
        - root.querySelector('.compare-head').getBoundingClientRect().top;
      if (!ctx.conditions.pin || content > innerHeight - 24) {
        root.classList.add('is-still');
        pinned = false;
        progress = 1;
        show(1);
        return () => root.classList.remove('is-still');
      }
      pinned = true;
      draw(ep.get());  // the lede's hint changes once the section knows it scrubs
      progress = 0;
      show(0);
      const st = ScrollTrigger.create({
        trigger: root, start: 'top top', end: '+=160%', pin: true, scrub: 0.5,
        onUpdate: (self) => show(self.progress),
      });
      return () => st.kill();
    });
  });
  return { show, ready };
}
