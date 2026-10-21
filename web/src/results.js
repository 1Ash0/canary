// The experiments on the landing page, one tab each, from experiments/<id>.json only. Every block is
// a model (and canary pack): a row per condition with a Wilson whisker on a fixed 0-100% axis (never
// rescaled to flatter a difference) and one mark per seed. Treatment marks open that exact episode
// in the recorder. Headlines are sentences filled from the same files; no number is typed here.
import { onEnterOnce, gsap, ms, REDUCE } from './motion-kit.js';

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
    return d.run ? `<a ${attrs} href="./run/?run=${encodeURIComponent(d.run)}"></a>` : `<span ${attrs} tabindex="0"></span>`;
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
const sideOf = (exp, b, r) => (exp.exp_id === 'EXP-002' && b.pack === 'constraint' && r.label.startsWith('treatment(')
  ? `${b.host.toLowerCase()}.${r.label.slice(10, -1)}` : null);

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
const srcs = (exp) => exp.source.map((s) => `<span class="mono">${esc(s)}</span>`).join(', ');

const VIEWS = {
  exp001: {
    tab: 'First run', sub: 'EXP-001 · two models',
    claim: (e) => `<span class="res-big">${e.audit.followed} of ${e.audit.judged}</span> summaries read by hand: whenever a summary still carried the rule, the agent followed it, and whenever it lost the rule, the agent did not.`,
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
      return `<p class="caveat"><span class="tag">${esc(e.label)}</span> Preregistered before it ran. The summary call kept its reasoning short, so ${t.truncated} of ${t.truncation_known} summaries were cut off. The length-matched condition shows that a shorter window alone does not explain it: the loss comes from what the summary left out. Recorded ${esc(e.dates.join(' and '))}. Sources: ${srcs(e)}.</p>`;
    },
  },
  exp002: {
    tab: 'Four policies', sub: 'EXP-002 · same rule',
    claim: (e) => {
      const b = e.blocks[0];
      const rt = rowOf(b, 'treatment(recency_truncate)'), ht = rowOf(b, 'treatment(head_tail)');
      return `Dropping the oldest turns broke the rule in <span class="res-big">${rt.k} of ${rt.n}</span> seeds. Keeping the head and the tail broke it in ${ht.k} of ${ht.n}.`;
    },
    foot: (e) => `<p class="caveat"><span class="tag">${esc(e.label)}</span> Every policy compacts the same seeded history to the same ${e.limit_tokens.toLocaleString('en-US')}-token budget. The rule is planted early, so a policy that keeps the opening turns keeps it by construction; the policy grid below shows the same thing without any model. Three comparisons per model and canary were preregistered; the rest are exploratory. Recorded ${esc(e.dates.join(' and '))}. Sources: ${srcs(e)}.</p>`,
  },
};

function panel(id, exp) {
  const v = VIEWS[id];
  return `<p class="res-claim" data-res-claim>${v.claim(exp)}</p>
    <div class="res-models">${exp.blocks.map((b, i) => block(b, exp, i)).join('')}</div>
    ${v.foot(exp)}`;
}

function animate(root, ep) {
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
      const { a } = ep.get();
      ep.set({ seed: +d.dataset.seed, b: d.dataset.side, ...(a === d.dataset.side ? { a: ep.get().b } : {}) });
      document.querySelector('#compare').scrollIntoView({ behavior: matchMedia(REDUCE).matches ? 'auto' : 'smooth' });
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
  const ids = Object.keys(VIEWS).filter((id) => exps[id]);
  root.innerHTML = `
    <div class="res-tabs" role="tablist" aria-label="Experiments">${ids.map((id, i) => `
      <button type="button" role="tab" id="res-tab-${id}" aria-controls="res-panel-${id}" aria-selected="${i === 0}" tabindex="${i === 0 ? 0 : -1}" data-res-tab="${id}">
        <span class="res-tab-name">${VIEWS[id].tab}</span><span class="res-tab-sub">${VIEWS[id].sub}</span>
      </button>`).join('')}
    </div>
    ${ids.map((id, i) => `<div class="res-panel" role="tabpanel" id="res-panel-${id}" aria-labelledby="res-tab-${id}" data-res-panel="${id}"${i ? ' hidden' : ''}></div>`).join('')}`;

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
  open(ids[0]);
}
