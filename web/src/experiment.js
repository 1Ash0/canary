// Renders a result as: rate, Wilson interval whisker, n, and the paired comparison. Works from the
// exported experiment JSON only. The whisker's axis is 0-100%, never rescaled to flatter a difference.
const pct = (x) => `${Math.round(x * 100)}%`;
const fixed = (x) => x.toFixed(2);

function cellRow(name, c) {
  const x = (v) => `${(v * 100).toFixed(2)}%`;
  return `<div class="cell">
    <div class="cell-name">${name}</div>
    <div class="cell-n">${c.k} / ${c.n} violated</div>
    <svg class="whisker" role="img" aria-label="${name}: ${pct(c.rate)}, interval ${pct(c.wilson_lo)} to ${pct(c.wilson_hi)}">
      <line class="axis" x1="0%" x2="100%" y1="50%" y2="50%"/>
      ${[0, 0.5, 1].map((t) => `<line class="tick" x1="${x(t)}" x2="${x(t)}" y1="30%" y2="70%"/>`).join('')}
      <line class="range" x1="${x(c.wilson_lo)}" x2="${x(c.wilson_hi)}" y1="50%" y2="50%"/>
      <circle class="rate" cx="${x(c.rate)}" cy="50%" r="4"/>
    </svg>
    <div class="cell-val">${pct(c.rate)} <span class="note">[${fixed(c.wilson_lo)}, ${fixed(c.wilson_hi)}]</span></div>
  </div>`;
}

export function renderExperiment(root, exp) {
  const names = Object.keys(exp.cells);
  const p = exp.paired;
  root.innerHTML = `
    <div class="cells" role="group" aria-label="Violation rate by condition, with 95% Wilson interval">
      ${names.map((n) => cellRow(n, exp.cells[n])).join('')}
      <div class="cell" style="border-top:0;padding-block:var(--space-xs) 0"><div class="axis-labels" aria-hidden="true"><span>0%</span><span>50%</span><span>100%</span></div></div>
    </div>
    <dl class="paired" aria-label="Paired outcomes by seed">
      <div><dt>violated under both</dt><dd>${p.both_violated}</dd></div>
      <div><dt>respected under both</dt><dd>${p.both_respected}</dd></div>
      <div><dt>only ${names[1]} violated</dt><dd>${p.only_treatment_violated}</dd></div>
      <div><dt>only ${names[0]} violated</dt><dd>${p.only_control_violated}</dd></div>
    </dl>
    <p class="caveat">Same ${names.length === 2 ? exp.cells[names[0]].n : ''} seeds under both conditions. Only the two right-hand counts say anything about the difference; seeds where both conditions agree cancel out. Whiskers are 95% Wilson intervals. <span class="tag">${exp.label}</span>: outcomes are seeded random draws at assumed rates (${names.map((n) => `${n} ${pct(exp.assumed_rates[n])}`).join(', ')}). No model was called. Source: <span class="mono">${exp.source}</span>.</p>`;
}
