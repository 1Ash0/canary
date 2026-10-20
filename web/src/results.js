// EXP-001 results on the landing page, from experiments/exp001.json only. Each usable model gets a
// control row and a treatment row with a Wilson whisker on a fixed 0-100% axis (never rescaled to
// flatter a difference). Whiskers draw out from their centre, then the numbers appear.
import { onEnterOnce, ms } from './motion-kit.js';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const pct = (x) => `${Math.round(x * 100)}%`;
const x = (v) => `${(v * 100).toFixed(2)}%`;
const pfmt = (p) => (p < 0.001 ? p.toExponential(1) : p.toPrecision(2));

// One dot per seed: hollow = followed the rule, filled vermilion = broke it, dash = no summary.
// Treatment dots link to that exact episode in the recorder.
function dots(list, condition) {
  if (!list) return '';
  return `<div class="dots" role="list" aria-label="${condition}: one mark per seed">${list.map((d) => {
    const cls = d.grade === 'violated' ? 'is-broke' : d.grade === 'respected' ? 'is-ok' : 'is-na';
    const what = d.grade === 'violated' ? 'broke the rule' : d.grade === 'respected' ? 'followed the rule' : 'no summary';
    const info = `seed ${d.seed}: ${what}${d.evidence && d.grade !== 'not_applicable' ? ` (${d.evidence.replace(/'/g, '')})` : ''}${d.fate ? `; the summary ${d.fate === 'kept' ? 'named' : 'lost'} the channel` : ''}${d.truncated ? '; summary cut off' : ''}`;
    const attrs = `class="dot ${cls}" role="listitem" data-info="${esc(info)}" aria-label="${esc(info)}"`;
    return d.run ? `<a ${attrs} href="./run/?run=${encodeURIComponent(d.run)}"></a>` : `<span ${attrs} tabindex="0"></span>`;
  }).join('')}</div>`;
}

function row(name, c, list) {
  if (c.rate == null) return '';
  return `<div class="cell" data-res-row>
    <div class="cell-name">${name}</div>
    <div class="cell-n">${c.k} / ${c.n} broke the rule${c.na ? ` · ${c.na} no summary` : ''}</div>
    <svg class="whisker" role="img" aria-label="${name}: ${pct(c.rate)}, interval ${pct(c.lo)} to ${pct(c.hi)}">
      <line class="axis" x1="0%" x2="100%" y1="50%" y2="50%"/>
      ${[0, 0.5, 1].map((t) => `<line class="tick" x1="${x(t)}" x2="${x(t)}" y1="30%" y2="70%"/>`).join('')}
      <g class="whisk-range" data-whisk style="transform-origin:${x((c.lo + c.hi) / 2)} 50%"><line class="range" x1="${x(c.lo)}" x2="${x(c.hi)}" y1="50%" y2="50%"/></g>
      <circle class="rate" data-dot cx="${x(c.rate)}" cy="50%" r="4"/>
    </svg>
    <div class="cell-val" data-val>${pct(c.rate)} <span class="note">[${pct(c.lo)}, ${pct(c.hi)}]</span></div>
    ${dots(list, name)}
  </div>`;
}

function model(m) {
  const p = m.pairs;
  const diff = p.rd == null ? '' : `Paired by seed: ${p.only_treatment} seeds broke the rule only after compaction, ${p.only_control} only without it; exact test p = ${pfmt(p.p)}.`;
  return `<div class="res-model" data-res-model>
    <h3 class="res-name"><span class="panel-host">${esc(m.host)}</span> <span class="mono">${esc(m.model)}</span></h3>
    <div class="cells" role="group" aria-label="${esc(m.host)}: rule broken, by condition">
      ${row('control', m.control, m.seeds?.control)}${row('treatment', m.treatment, m.seeds?.treatment)}
      <div class="cell axis-row"><div class="axis-labels" aria-hidden="true"><span>0%</span><span>50%</span><span>100%</span></div></div>
    </div>
    <p class="dot-info" data-dot-info aria-live="polite">Hover or tab through the marks: one per seed. Treatment marks open that episode in the recorder.</p>
    <p class="res-note">${esc(m.note)} ${diff}</p>
  </div>`;
}

export function mountResults(root, exp) {
  const usable = exp.models.filter((m) => m.usable);
  const other = exp.models.filter((m) => !m.usable);
  const t = exp.truncation;
  root.innerHTML = `
    <p class="res-claim" data-res-claim><span class="res-big">${exp.audit.followed} of ${exp.audit.judged}</span> summaries read by hand: whenever a summary still carried the rule, the agent followed it, and whenever it lost the rule, the agent did not.</p>
    <div class="res-models">${usable.map(model).join('')}</div>
    <ul class="res-other">${other.map((m) => `<li><span class="panel-host">${esc(m.host)}</span> <span class="mono">${esc(m.model)}</span> <span class="dim">${esc(m.note)}</span></li>`).join('')}</ul>
    <p class="caveat"><span class="tag">${esc(exp.label)}</span> No cross-model replication is claimed: one model shows the published effect, one shows none, and the result depends on which model writes the summary. For gpt-oss-20b, ${t.truncated} of its summaries were cut off by the token cap (the rule survived in ${t.truncated_present} of those) against ${t.complete_present} of ${t.complete} complete ones. Recorded ${esc(exp.dates.join(' and '))}. Sources: ${exp.source.map((s) => `<span class="mono">${esc(s)}</span>`).join(', ')}.</p>`;

  for (const block of root.querySelectorAll('[data-res-model]')) {
    const info = block.querySelector('[data-dot-info]');
    const show = (e) => { const d = e.target.closest('.dot'); if (d) info.textContent = d.dataset.info; };
    block.addEventListener('pointerover', show);
    block.addEventListener('focusin', show);
    onEnterOnce(block, (tl) => {
      tl.from(block.querySelectorAll('[data-res-row]'), { autoAlpha: 0, y: 8, duration: ms('base'), stagger: 0.1, ease: 'power2.out' });
      tl.from(block.querySelectorAll('[data-whisk]'), { scaleX: 0, duration: ms('slow'), ease: 'power3.out', stagger: 0.1 }, 0.2);
      tl.from(block.querySelectorAll('[data-dot]'), { autoAlpha: 0, duration: ms('micro'), stagger: 0.1 }, 0.55);
      tl.from(block.querySelectorAll('[data-val]'), { autoAlpha: 0, duration: ms('base'), stagger: 0.1 }, 0.7);
    });
  }
  onEnterOnce(root.querySelector('[data-res-claim]'), (tl) => {
    tl.from('[data-res-claim]', { autoAlpha: 0, y: 12, duration: ms('slow'), ease: 'power2.out' });
  });
}
