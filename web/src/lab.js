// The Compaction Lab (ADR-022). The reader is the harness: pick a policy, drag the budget, drag
// where the rule is planted, and the window recompacts on every input. Deterministic policies run
// the JS port of src/ctxcheck/policies (checked against the Python in design/tests); the summary
// policy shows the recorded summary for the chosen seed. Nothing here autoplays.
import { assemble, compact, tokensOf } from '../../design/scene/policies.js';
import { asciiTurns, asciiGauge, asciiSeam } from '../../design/scene/ascii.js';
import { POLICY_NAME } from './episode.js';
import { BASE } from './data.js';

const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const nf = new Intl.NumberFormat('en-US');
const cap = (t) => t[0].toUpperCase() + t.slice(1);
const POLICY_LABEL = Object.fromEntries(Object.entries(POLICY_NAME).map(([k, v]) => [k, cap(v)]));
const POLICY_HELP = {
  recency_truncate: 'Drops the oldest turns until the window fits.',
  head_tail: 'Keeps the start and the newest turns, drops the middle.',
  observation_mask: 'Hides old tool outputs, keeps what was said; drops turns only if that is not enough.',
  llm_summary: 'A model rewrites the old turns as a summary. These are recorded summaries, not simulated.',
};
const SUMMARIZER = { mistral: 'Mistral ministral-14b', nvidia: 'NVIDIA gpt-oss-20b' };

// The same seed, policy and budget as EXP-002: what recorded models actually did with this window.
function recordedLine(exp, policy, seed, position, limit) {
  if (!exp) return '';
  if (limit !== exp.limit_tokens || position !== 1) {
    return `<p class="note">Set the budget to ${nf.format(exp.limit_tokens)} and the rule at turn 2 to see what real models did with this exact window.</p>`;
  }
  const items = exp.blocks.filter((b) => b.pack === 'constraint').map((b) => {
    const d = b.rows.find((r) => r.label === `treatment(${policy})`)?.seeds.find((x) => x.seed === seed);
    if (!d) return '';
    const chan = (d.evidence ?? '').replace(/^channel=/, '').replace(/'/g, '');
    const what = d.grade === 'violated' ? `posted to <span class="mono is-loss">${esc(chan)}</span>, rule broken`
      : d.grade === 'respected' ? `posted to <span class="mono">${esc(chan)}</span>, rule followed` : 'made no post';
    return `<li><span class="panel-host">${esc(b.host)}</span> ${what}. ${d.run ? `<a href="${BASE}run/?run=${encodeURIComponent(d.run)}">Open the episode</a>` : ''}</li>`;
  }).filter(Boolean);
  if (!items.length) return '';
  return `<p class="lab-label"><span class="tag">recorded</span> This exact window, given to real models (${esc(exp.exp_id)})</p><ul class="lab-recorded">${items.join('')}</ul>`;
}

export function mountLab(root, lab, summaries, floor, exp002 = null, onCompare = null) {
  const state = { policy: 'recency_truncate', limit: 2400, position: 1, seed: 0, summarizer: 'nvidia' };
  const seeds = lab.seeds;
  // a seed in the URL (from the comparison or a shared link) opens the Lab on that history
  const asked = seeds.findIndex((h) => h.seed === Number(new URLSearchParams(location.search).get('seed')));
  if (asked >= 0) state.seed = asked;
  root.innerHTML = `
    <div class="lab">
      <div class="lab-controls">
        <fieldset class="lab-seg" role="radiogroup" aria-label="Compaction policy">
          <legend class="lab-label">Policy</legend>
          ${Object.entries(POLICY_LABEL).map(([k, v]) => `<label><input type="radio" name="lab-policy" value="${k}"${k === state.policy ? ' checked' : ''}><span>${v}</span></label>`).join('')}
        </fieldset>
        <p class="lab-help" data-help></p>
        <label class="lab-range"><span class="lab-label">Window budget <output data-out-limit></output></span>
          <input type="range" min="800" max="3800" step="100" value="${state.limit}" data-limit></label>
        <label class="lab-range"><span class="lab-label">Rule planted at turn <output data-out-pos></output></span>
          <input type="range" min="0" max="18" step="1" value="${state.position}" data-pos></label>
        <fieldset class="lab-seg" data-summarizer hidden aria-label="Summarizer">
          <legend class="lab-label">Summarizer</legend>
          ${Object.entries(SUMMARIZER).map(([k, v]) => `<label><input type="radio" name="lab-sum" value="${k}"${k === state.summarizer ? ' checked' : ''}><span>${v}</span></label>`).join('')}
        </fieldset>
        <div class="lab-row">
          <button type="button" class="replay" data-seed>Another history</button>
          <span class="note" data-seed-label></span>
          ${onCompare ? '<button type="button" class="link-quiet lab-compare" data-to-compare>Compare this history below ↓</button>' : ''}
        </div>
        <p class="lab-tag"><span class="tag" data-tag></span> <span class="note" data-tag-note></span></p>
      </div>
      <div class="lab-view">
        <div class="lab-verdict" data-verdict aria-live="polite"></div>
        <pre class="ascii" data-ascii aria-hidden="true"></pre>
        <p class="visually-hidden" data-ascii-text aria-live="polite"></p>
        <div class="lab-summary" data-summary hidden></div>
        <div class="lab-real" data-real aria-live="polite"></div>
        <p class="ascii-key" aria-hidden="true"><span class="ax-rule">█ rule</span> <span class="ax-history">░ conversation</span> <span class="ax-tool">▒ tool output</span> <span class="ax-summary">▓ summary</span> <span class="ax-masked">· masked</span> <span class="ax-out">dim = removed by compaction</span></p>
      </div>
    </div>`;
  const q = (s) => root.querySelector(s);
  const lostStat = `when the rule was never given (the floor condition), agents posted to the wrong channel in ${floor.k} of ${floor.n} recorded episodes`;

  function render() {
    const h = seeds[state.seed];
    const summaryMode = state.policy === 'llm_summary';
    // recorded summaries exist for one configuration only: rule at turn 2, budget 2,400
    if (summaryMode) { state.position = 1; state.limit = 2400; }
    q('[data-limit]').value = state.limit; q('[data-pos]').value = state.position;
    q('[data-limit]').disabled = q('[data-pos]').disabled = summaryMode;
    q('[data-out-limit]').textContent = `${nf.format(state.limit)} tokens`;
    q('[data-out-pos]').textContent = String(state.position + 1);
    q('[data-help]').textContent = POLICY_HELP[state.policy] + (summaryMode
      ? ' They were recorded at a budget of 2,400 with the rule at turn 2, so both sliders are fixed here.' : '');
    q('[data-summarizer]').hidden = !summaryMode;
    q('[data-seed-label]').textContent = `history ${h.seed} of ${seeds.length}`;

    const win = assemble(h, state.position);
    const before = h.tools_tokens + tokensOf(win);
    let rows, after, compacted, ruleIn, verdictNote = '', summary = null, irreducible = false;
    if (!summaryMode) {
      const res = compact(h, win, state.policy, state.limit);
      irreducible = res.irreducible;
      compacted = res.compacted;
      const keptIds = new Set(res.out.filter((m) => !m.maskedFrom).map((m) => m.id));
      const maskedIds = new Set(res.out.filter((m) => m.maskedFrom).map((m) => m.id));
      ruleIn = win.filter((m) => m.kind === 'rule').every((m) => keptIds.has(m.id));
      rows = win.map((m) => ({
        ...m, state: maskedIds.has(m.id) ? 'masked' : keptIds.has(m.id) ? 'in' : 'out',
        tokens: maskedIds.has(m.id) ? res.out.find((o) => o.id === m.id).tokens : m.tokens,
        lost: m.kind === 'rule' && m.role === 'user' && !keptIds.has(m.id),
      }));
      after = h.tools_tokens + tokensOf(res.out);
    } else {
      summary = summaries.seeds[String(h.seed)]?.[state.summarizer];
      // llm_summary keeps the last two units and the current turn; everything older is summarised
      const units = []; let cur = null;
      win.forEach((m) => { if (m.role === 'system' || m.kind === 'probe') return; if (m.turn !== cur) { units.push([]); cur = m.turn; } units.at(-1).push(m); });
      const keepTurns = new Set(units.slice(-2).map((u) => u[0].turn));
      ruleIn = summary ? summary.fate === 'kept' : false;
      compacted = true;
      rows = win.map((m) => ({ ...m, state: m.role === 'system' || m.kind === 'probe' || keepTurns.has(m.turn) ? 'in' : 'out',
        lost: m.kind === 'rule' && m.role === 'user' && !ruleIn }));
      const sumRow = { kind: 'summary', role: 'user', tokens: summary?.tokens ?? 0, state: 'added', note: ruleIn ? `names ${h.value}` : 'no channel named', lost: false };
      const sysAt = rows.findIndex((r) => r.role !== 'system');
      rows.splice(sysAt, 0, sumRow);
      after = h.tools_tokens + rows.filter((r) => r.state !== 'out').reduce((a, r) => a + r.tokens, 0);
      verdictNote = summary ? (summary.grade === 'violated'
        ? `The agent then posted to <span class="mono is-loss">${esc(summary.chosen)}</span>: behaviour changed ↓`
        : summary.grade === 'respected' ? `The agent then posted to <span class="mono">${esc(summary.chosen)}</span>: rule followed.` : 'The agent made no post.') : '';
    }

    // group messages into one row per turn (system, each turn, the summary if any, the request)
    const out = [];
    for (const r of rows) {
      const key = r.role === 'system' ? 'sys' : r.kind === 'probe' ? 'ask' : r.kind === 'summary' ? 'sum' : `t${String(r.turn + 1).padStart(2, '0')}`;
      let row = out.at(-1);
      if (!row || row.key !== key) {
        row = { key, tag: key, segments: [], cls: '' };
        out.push(row);
      }
      row.segments.push({ kind: r.kind, tokens: r.tokens, state: r.state === 'added' ? 'in' : r.state });
      if (r.kind === 'rule') row.cls = 'ax-rule-row';
      if (r.lost) row.lost = true;
      if (r.kind === 'summary') { row.cls = 'ax-summary-row'; row.note = r.note; }
    }
    const span = Math.max(before, state.limit);
    const lines = [asciiGauge(before, state.limit, { label: 'before', span }), compacted ? asciiGauge(after, state.limit, { label: 'after', span }) : '', ''];
    out.forEach((row) => {
      if (row.key === 'ask' && compacted) lines.push(asciiSeam(`compaction ${nf.format(before)} → ${nf.format(after)} tokens`));
      lines.push(asciiTurns([row]));
    });
    q('[data-ascii]').innerHTML = lines.join('\n');

    const verdict = q('[data-verdict]');
    if (irreducible) {
      verdict.innerHTML = '<p class="lab-big">Cannot fit.</p><p>The system prompt and the current request alone exceed this budget; no policy can help.</p>';
    } else if (!compacted) {
      verdict.innerHTML = `<p class="lab-big">Fits. Nothing compacted.</p><p>The window is under ${nf.format(state.limit)} tokens, so every turn stays.</p>`;
    } else if (ruleIn) {
      verdict.innerHTML = `<p class="lab-big is-ok">Rule still in the window.</p><p>${summaryMode ? 'The summary carried it through.' : 'The agent can still follow it.'} ${verdictNote}</p>`;
    } else {
      verdict.innerHTML = `<p class="lab-big is-loss">Rule gone ↓</p><p>${summaryMode ? 'The summary dropped it.' : `The agent has to guess: ${lostStat}.`} ${verdictNote}</p>`;
    }
    q('[data-ascii-text]').textContent = `${POLICY_LABEL[state.policy]}, budget ${state.limit}, rule at turn ${state.position + 1}: window ${before} tokens before, ${after} after; rule ${ruleIn ? 'kept' : 'gone'}.`;

    const sumEl = q('[data-summary]');
    sumEl.hidden = !summaryMode || !summary;
    if (summaryMode && summary) {
      const plain = esc(summary.text.replace(/\*\*/g, '')).replace(/[‐-―−]/g, '-');
      const marked = plain.includes(h.value) ? plain.split(h.value).join(`<mark>${esc(h.value)}</mark>`) : plain;
      sumEl.innerHTML = `<p class="lab-label">The summary ${esc(SUMMARIZER[state.summarizer])} wrote${summary.truncated ? ' (cut off by the token cap)' : ''}</p><blockquote class="cons-quote">${marked}</blockquote>`;
    }
    q('[data-real]').innerHTML = irreducible ? '' : recordedLine(exp002, state.policy, h.seed, state.position, state.limit);
    q('[data-tag]').textContent = summaryMode ? 'recorded' : 'simulated';
    q('[data-tag-note]').textContent = summaryMode
      ? `${summary?.exp ?? 'EXP-002'}, seed ${h.seed}. Real model output.`
      : 'Real policy code on a real seeded history, run in your browser. No model involved.';
  }

  root.querySelectorAll('input[name="lab-policy"]').forEach((el) => el.addEventListener('change', () => { state.policy = el.value; render(); }));
  root.querySelectorAll('input[name="lab-sum"]').forEach((el) => el.addEventListener('change', () => { state.summarizer = el.value; render(); }));
  q('[data-limit]').addEventListener('input', (e) => { state.limit = +e.target.value; render(); });
  q('[data-pos]').addEventListener('input', (e) => { state.position = +e.target.value; render(); });
  q('[data-seed]').addEventListener('click', () => { state.seed = (state.seed + 1) % seeds.length; render(); });
  q('[data-to-compare]')?.addEventListener('click', () => onCompare(seeds[state.seed].seed, state.policy));
  render();
  // the policy grid below hands a policy and budget to the Lab
  return {
    set(patch) {
      Object.assign(state, patch);
      root.querySelectorAll('input[name="lab-policy"]').forEach((el) => { el.checked = el.value === state.policy; });
      render();
    },
  };
}
