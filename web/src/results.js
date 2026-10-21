// The experiments on the landing page, one tab each, from experiments/<id>.json only. Every block is
// a model (and canary pack): a row per condition with a Wilson whisker on a fixed 0-100% axis (never
// rescaled to flatter a difference) and one mark per seed. Treatment marks open that exact episode
// in the recorder. Headlines are sentences filled from the same files; no number is typed here.
import { onEnterOnce, gsap, ms, REDUCE } from './motion-kit.js';
import { BASE } from './data.js';
import { goTo } from './sections.js';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const pct = (x) => `${Math.round(x * 100)}%`;
const x = (v) => `${(v * 100).toFixed(2)}%`;
const pfmt = (p) => (p < 0.001 ? p.toExponential(1) : p.toPrecision(2));

// What "failed" means depends on the canary: a channel rule is broken; an account code is wrong.
const VERB = {
  constraint: { bad: 'broke the rule', good: 'followed the rule', kept: 'named the channel', lost: 'lost the channel' },
  identifier: { bad: 'used a wrong code', good: 'used the exact code', kept: 'kept the code', lost: 'lost the code' },
};

function dots(seeds, name, verb, side = null) {
  if (!seeds?.length) return '';
  return `<div class="dots" role="list" aria-label="${esc(name)}: one mark per seed">${seeds.map((d) => {
    const cls = d.grade === 'violated' ? 'is-broke' : d.grade === 'respected' ? 'is-ok' : 'is-na';
    const what = d.grade === 'violated' ? verb.bad : d.grade === 'respected' ? verb.good : 'not graded (no summary, or no post)';
    const ev = d.evidence && d.grade !== 'not_applicable' ? ` (${d.evidence.replace(/'/g, '')})` : '';
    const fate = d.fate ? `; the window ${d.fate === 'kept' ? verb.kept : verb.lost}` : '';
    const info = `seed ${d.seed}: ${what}${ev}${fate}${d.truncated ? '; summary cut off' : ''}${side && d.run ? '. Click to compare it above' : ''}`;
    const attrs = `class="dot ${cls}" role="listitem" data-seed="${d.seed}"${side ? ` data-side="${side}"` : ''} data-info="${esc(info)}" aria-label="${esc(info)}"`;
    return d.run ? `<a ${attrs} href="${BASE}run/?run=${encodeURIComponent(d.run)}"></a>` : `<span ${attrs} tabindex="0"></span>`;
  }).join('')}</div>`;
}

function row(r, verb, side = null) {
  if (r.rate == null) return '';
  return `<div class="cell" data-res-row>
    <div class="cell-name">${esc(r.name)}</div>
    <div class="cell-n">${r.k} / ${r.n} ${verb.bad}${r.na ? ` · ${r.na} not graded` : ''}</div>
    <svg class="whisker" role="img" aria-label="${esc(r.name)}: ${pct(r.rate)}, interval ${pct(r.lo)} to ${pct(r.hi)}">
      <line class="axis" x1="0%" x2="100%" y1="50%" y2="50%"/>
      ${[0, 0.5, 1].map((t) => `<line class="tick" x1="${x(t)}" x2="${x(t)}" y1="30%" y2="70%"/>`).join('')}
      <g class="whisk-range" data-whisk style="transform-origin:${x((r.lo + r.hi) / 2)} 50%"><line class="range" x1="${x(r.lo)}" x2="${x(r.hi)}" y1="50%" y2="50%"/></g>
      <circle class="rate${r.k / r.n >= 0.5 ? ' is-high' : ''}" data-dot cx="${x(r.rate)}" cy="50%" r="4"/>
    </svg>
    <div class="cell-val" data-val>${pct(r.rate)} <span class="note">[${pct(r.lo)}, ${pct(r.hi)}]</span></div>
    ${dots(r.seeds, r.name, verb, side)}
  </div>`;
}

function compare(c, verb) {
  if (c.rd == null) return '';
  return `<li><strong>${esc(c.first)}</strong> against <strong>${esc(c.second)}</strong>: ${c.only_first} seeds ${verb.bad} only under the first, ${c.only_second} only under the second, of ${c.n} pairs. Exact test p = ${pfmt(c.p)}, adjusted q = ${pfmt(c.q)}.</li>`;
}

// EXP-002's channel-rule treatment rows are the episodes the comparison above can show.
const sideOf = (exp, b, r) => (exp.exp_id === 'EXP-002' && r.label.startsWith('treatment(')
  ? `${b.pack}:${b.host.toLowerCase()}.${r.label.slice(10, -1)}` : null);

function block(b, exp, i) {
  const verb = VERB[b.pack] ?? VERB.constraint;
  const prim = b.comparisons.filter((c) => c.role === 'primary');
  const expl = b.comparisons.filter((c) => c.role !== 'primary');
  const multiPack = new Set(exp.blocks.map((y) => y.pack)).size > 1;
  return `<div class="res-model" data-res-model>
    <h3 class="res-name"><span class="panel-host">${esc(b.host)}</span> <span class="mono">${esc(b.model)}</span>${multiPack ? ` <span class="tag">${esc(b.pack)} canary</span>` : ''}</h3>
    <div class="cells" role="group" aria-label="${esc(b.host)}: ${verb.bad}, by condition">
      ${b.rows.map((r) => row(r, verb, sideOf(exp, b, r))).join('')}
      <div class="cell axis-row"><div class="axis-labels" aria-hidden="true"><span>0%</span><span>50%</span><span>100%</span></div></div>
    </div>
    <p class="dot-info" data-dot-info aria-live="polite">${i === 0 ? `Hover or tab through the marks: one per seed. Filled marks ${verb.bad}, dashed ones were not graded; treatment marks open that episode in the recorder.` : ''}</p>
    ${b.note ? `<p class="res-note">${esc(b.note)}</p>` : ''}
    ${prim.length ? `<ul class="res-comps">${prim.map((c) => compare(c, verb)).join('')}</ul>` : ''}
    ${expl.length ? `<details class="res-more"><summary>Exploratory comparisons (${expl.length}, not preregistered)</summary><ul class="res-comps">${expl.map((c) => compare(c, verb)).join('')}</ul></details>` : ''}
  </div>`;
}

const rowOf = (b, label) => b?.rows.find((r) => r.label === label);

// EXP-004's key figure: rows are policies, columns the three facts by depth. Each cell says in words
// whether the fact survived (on how many seeds) and shows how often the agent then failed on it,
// with its interval on a fixed 0-100% axis. A table, so it reads without colour; the loss colour
// only ever sits next to the words "gone" or a failure count. A cell opens that policy on that fact
// in the comparison.
function factMatrix(e) {
  const facts = e.facts;
  const policies = [...new Set(e.matrix.map((m) => m.policy))];
  const cell = (pol, f) => {
    const m = e.matrix.find((x) => x.policy === pol && x.fact === f.id);
    if (!m) return '<td class="empty">n/a</td>';
    const gone = m.kept === 0;
    const surv = m.kept == null ? '' : gone ? `<span class="fm-gone">gone ↓</span> <span class="dim">0/${m.kept_n}</span>`
      : `kept <span class="dim">${m.kept}/${m.kept_n}</span>`;
    const info = `${m.name}, ${f.name} (turn ${f.turn}): the fact was in the window on ${m.kept ?? '?'} of ${m.kept_n ?? '?'} seeds; the agent got it wrong on ${m.k} of ${m.n}`;
    return `<td class="${gone ? 'is-gone' : ''}"><button type="button" class="fm-cell" data-fm-pack="${f.pack}" data-fm-policy="${m.policy}" data-info="${esc(info)}" aria-label="${esc(info)}. Open in the comparison">
      <span class="fm-surv">${surv}</span>
      <span class="fm-rate">${m.k}/${m.n} wrong</span>
      <svg class="fm-bar" aria-hidden="true"><line class="axis" x1="0%" x2="100%" y1="50%" y2="50%"/><line class="range" x1="${x(m.lo)}" x2="${x(m.hi)}" y1="50%" y2="50%"/><circle class="rate${m.rate >= 0.5 ? ' is-high' : ''}" cx="${x(m.rate)}" cy="50%" r="3.5"/></svg>
    </button></td>`;
  };
  return `<div class="table-scroll" tabindex="0" role="region" aria-label="Which fact each policy lost">
    <table class="fact-matrix">
      <caption class="visually-hidden">For each policy and each planted fact: whether the fact was still in the window, and how often the agent got it wrong</caption>
      <thead><tr><th scope="col">policy</th>${facts.map((f) => `<th scope="col"><span class="mono">${f.id}</span> ${esc(f.name)}<span class="dim">turn ${f.turn}</span></th>`).join('')}</tr></thead>
      <tbody>${policies.map((pol) => `<tr><th scope="row">${esc(e.matrix.find((m) => m.policy === pol).name)}</th>${facts.map((f) => cell(pol, f)).join('')}</tr>`).join('')}
        <tr class="fm-floor"><th scope="row">never told <span class="dim">(chance)</span></th>${facts.map((f) => `<td><span class="fm-rate">${f.floor_k ?? '?'}/${f.floor_n ?? '?'} wrong</span></td>`).join('')}</tr>
      </tbody>
    </table></div>
    <p class="dot-info" data-fm-info aria-live="polite">Hover or tab through a cell to read it; choose one to open that policy on that fact in the comparison.</p>`;
}
const srcs = (exp) => exp.source.map((s) => `<span class="mono">${esc(s)}</span>`).join(', ');

const VIEWS = {
  exp001: {
    tab: 'First run', sub: 'EXP-001 · two models',
    claim: (e) => `In the <span class="res-big">${e.audit.judged}</span> summaries read by hand, the agent did what its summary allowed every time: it followed the rule when the summary carried it, and broke it when the summary lost it.`,
    foot: (e) => {
      const t = e.truncation;
      return `${e.other.length ? `<ul class="res-other">${e.other.map((m) => `<li><span class="panel-host">${esc(m.host)}</span> <span class="mono">${esc(m.model)}</span> <span class="dim">${esc(m.note)}</span></li>`).join('')}</ul>` : ''}
        <p class="caveat"><span class="tag">${esc(e.label)}</span> No cross-model replication is claimed from this run: one model shows the published effect, one shows none. For gpt-oss-20b, ${t.truncated} of its summaries were cut off by the token cap (the rule survived in ${t.truncated_present} of those) against ${t.complete_present} of ${t.complete} complete ones, which is why the rerun exists. Recorded ${esc(e.dates.join(' and '))}. Sources: ${srcs(e)}.</p>`;
    },
  },
  exp001b: {
    tab: 'Clean rerun', sub: 'EXP-001b · NVIDIA',
    claim: (e) => {
      const b = e.blocks[0];
      const t = rowOf(b, 'treatment(llm_summary)'), c = rowOf(b, 'control'), l = rowOf(b, 'length_matched(llm_summary)');
      return `After a summary, <span class="res-big">${t.k} of ${t.n}</span> broke the rule. With the full history, ${c.k} of ${c.n}; cut to the same length with no summary, ${l.k} of ${l.n}.`;
    },
    foot: (e) => {
      const t = rowOf(e.blocks[0], 'treatment(llm_summary)');
      const au = e.audit ? ` A blind hand audit agreed with the machine's survival check on ${e.audit.agree} of ${e.audit.summaries} summaries; behaviour matched the audited summary in ${e.audit.followed} of ${e.audit.judged}. The exceptions are seeds where the rule was gone and the agent chose the right channel anyway, which the floor shows happens by chance.` : '';
      return `<p class="caveat"><span class="tag">${esc(e.label)}</span>${au} Preregistered before it ran. The summary call kept its reasoning short, so ${t.truncated} of ${t.truncation_known} summaries were cut off. The length-matched condition shows that a shorter window alone does not explain it: the loss comes from what the summary left out. Recorded ${esc(e.dates.join(' and '))}. Sources: ${srcs(e)}.</p>`;
    },
  },
  exp004: {
    tab: 'Three facts', sub: 'EXP-004 · which fact is lost',
    claim: (e) => {
      const at = (pol, f) => e.matrix.find((m) => m.policy === pol && m.fact === f);
      const ht = at('head_tail', 'I1'), om = at('observation_mask', 'I1');
      return ht && om ? `Keeping the head and tail lost the middle fact: the agent got the account code wrong in <span class="res-big">${ht.k} of ${ht.n}</span> seeds, against ${om.k} of ${om.n} when only tool output was masked.` : 'Three facts at three depths of one history.';
    },
    lead: factMatrix,
    foot: (e) => `<p class="caveat"><span class="tag">${esc(e.label)}</span> One seeded history carries three facts at turns ${e.facts.map((f) => f.turn).join(', ')}; each request tests one of them, so every cell is its own set of episodes. Budget ${e.limit_tokens.toLocaleString('en-US')} tokens, one model (Mistral ministral-14b), preregistered before it ran. Survival counts are mechanical (the value written in the window), not a judgement. Recorded ${esc(e.dates.join(' and '))}. Sources: ${srcs(e)}.</p>`,
  },
  exp002: {
    tab: 'Four policies', sub: 'EXP-002 · same rule',
    claim: (e) => {
      const b = e.blocks[0];
      const rt = rowOf(b, 'treatment(recency_truncate)'), ht = rowOf(b, 'treatment(head_tail)');
      return `With the rule planted at turn 2, dropping the oldest turns broke it in <span class="res-big">${rt.k} of ${rt.n}</span> seeds; keeping the head and the tail, in ${ht.k} of ${ht.n}. Where the fact sits decides which policy is safe.`;
    },
    foot: (e) => `<p class="caveat"><span class="tag">${esc(e.label)}</span> Every policy compacts the same seeded history to the same ${e.limit_tokens.toLocaleString('en-US')}-token budget. The rule is planted early, so a policy that keeps the opening turns keeps it by construction; the policy grid below shows the same thing without any model. Three comparisons per model and canary were preregistered; the rest are exploratory. Recorded ${esc(e.dates.join(' and '))}. Sources: ${srcs(e)}.</p>`,
  },
};

function panel(id, exp) {
  const v = VIEWS[id];
  return `<p class="res-claim" data-res-claim>${v.claim(exp)}</p>
    ${v.lead ? v.lead(exp) : ''}
    <div class="res-models">${exp.blocks.map((b, i) => block(b, exp, i)).join('')}</div>
    ${v.foot(exp)}`;
}

function animate(root, ep) {
  const fm = root.querySelector('.fact-matrix');
  if (fm) {
    const info = root.querySelector('[data-fm-info]');
    const show = (e) => { const c = e.target.closest('.fm-cell'); if (c) info.textContent = c.dataset.info; };
    fm.addEventListener('pointerover', show);
    fm.addEventListener('focusin', show);
    fm.addEventListener('click', (e) => {
      const c = e.target.closest('.fm-cell');
      if (!c || !ep) return;
      const other = c.dataset.fmPolicy === 'observation_mask' ? 'head_tail' : 'observation_mask';
      ep.set({ canary: c.dataset.fmPack, a: `mistral.${other}`, b: `mistral.${c.dataset.fmPolicy}` });
      goTo('#compare', 'compare');
    });
  }
  for (const b of root.querySelectorAll('[data-res-model]')) {
    const info = b.querySelector('[data-dot-info]');
    const show = (e) => { const d = e.target.closest('.dot'); if (d) info.textContent = d.dataset.info; };
    // the same seed lights up in every row of this block: one history, every condition
    const mark = (e) => {
      const d = e.target.closest('.dot');
      b.querySelectorAll('.dot.is-seed').forEach((x) => x.classList.remove('is-seed'));
      if (d) b.querySelectorAll(`.dot[data-seed="${d.dataset.seed}"]`).forEach((x) => x.classList.add('is-seed'));
    };
    b.addEventListener('pointerover', (e) => { show(e); mark(e); });
    b.addEventListener('focusin', (e) => { show(e); mark(e); });
    b.addEventListener('pointerleave', () => b.querySelectorAll('.dot.is-seed').forEach((x) => x.classList.remove('is-seed')));
    b.addEventListener('click', (e) => {
      const d = e.target.closest('.dot[data-side]');
      if (!d || !ep || !d.getAttribute('href') || e.metaKey || e.ctrlKey || e.shiftKey) return;
      e.preventDefault();  // modified clicks still open the recorder; a plain click compares
      const [canary, side] = d.dataset.side.split(':');
      const cur = ep.get();
      // keep panel one when it belongs to the same canary; otherwise that canary's default pair
      const keepA = cur.canary === canary && cur.a !== side;
      ep.set({ canary, seed: +d.dataset.seed, b: side, ...(keepA ? { a: cur.a } : cur.a === side ? { a: cur.b } : { a: null }) });
      goTo('#compare', 'compare');  // on the results page this opens chapter 2 on that episode
    });
    onEnterOnce(b, (tl) => {
      tl.from(b.querySelectorAll('[data-res-row]'), { autoAlpha: 0, y: 8, duration: ms('base'), stagger: 0.08, ease: 'power2.out' });
      tl.from(b.querySelectorAll('[data-whisk]'), { scaleX: 0, duration: ms('slow'), ease: 'power3.out', stagger: 0.08 }, 0.2);
      tl.from(b.querySelectorAll('[data-dot]'), { autoAlpha: 0, duration: ms('micro'), stagger: 0.08 }, 0.5);
      tl.from(b.querySelectorAll('.dots'), { autoAlpha: 0, duration: ms('base'), stagger: 0.08 }, 0.55);
      tl.from(b.querySelectorAll('[data-val]'), { autoAlpha: 0, duration: ms('base'), stagger: 0.08 }, 0.7);
    });
  }
  const claim = root.querySelector('[data-res-claim]');
  onEnterOnce(claim, (tl) => { tl.from(claim, { autoAlpha: 0, y: 12, duration: ms('slow'), ease: 'power2.out' }); });
}

// exps: { exp001, exp001b?, exp002? } — tabs only for the experiments that have data.
export function mountResults(root, exps, ep = null) {
  // chronological tabs; the page opens on the newest experiment, the one that says the most
  const ids = ['exp001', 'exp001b', 'exp002', 'exp004'].filter((id) => exps[id]);
  const first = ids.at(-1);
  root.innerHTML = `
    <div class="res-tabs" role="tablist" aria-label="Experiments">${ids.map((id, i) => `
      <button type="button" role="tab" id="res-tab-${id}" aria-controls="res-panel-${id}" aria-selected="${id === first}" tabindex="${id === first ? 0 : -1}" data-res-tab="${id}">
        <span class="res-tab-name">${VIEWS[id].tab}</span><span class="res-tab-sub">${VIEWS[id].sub}</span>
      </button>`).join('')}
    </div>
    ${ids.map((id, i) => `<div class="res-panel" role="tabpanel" id="res-panel-${id}" aria-labelledby="res-tab-${id}" data-res-panel="${id}"${id === first ? '' : ' hidden'}></div>`).join('')}`;

  const tabs = [...root.querySelectorAll('[data-res-tab]')];
  const filled = new Set();
  const open = (id, focus = false) => {
    tabs.forEach((t) => {
      const on = t.dataset.resTab === id;
      t.setAttribute('aria-selected', String(on));
      t.tabIndex = on ? 0 : -1;
      if (on && focus) t.focus();
    });
    for (const p of root.querySelectorAll('[data-res-panel]')) {
      const on = p.dataset.resPanel === id;
      p.hidden = !on;
      if (on && !filled.has(id)) { p.innerHTML = panel(id, exps[id]); filled.add(id); animate(p, ep); }
      else if (on && !matchMedia(REDUCE).matches) gsap.from(p, { autoAlpha: 0, y: 6, duration: ms('base'), ease: 'power2.out' });
    }
  };
  tabs.forEach((t, i) => {
    t.addEventListener('click', () => open(t.dataset.resTab));
    t.addEventListener('keydown', (e) => {
      const step = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
      if (step) { e.preventDefault(); open(tabs[(i + step + tabs.length) % tabs.length].dataset.resTab, true); }
      if (e.key === 'Home') { e.preventDefault(); open(tabs[0].dataset.resTab, true); }
      if (e.key === 'End') { e.preventDefault(); open(tabs.at(-1).dataset.resTab, true); }
    });
  });
  open(first);
}
