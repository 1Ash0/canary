import { loadRun, loadIndex } from './data.js';
import { mountPlayer, playerMarkup } from './player.js';
import { shell, fail } from './shell.js';
import { ORDER, LAYER_LABEL, formatTokens, totalOf } from '../../design/scene/strata.js';
import { asciiTurns, asciiGauge, asciiSeam } from '../../design/scene/ascii.js';

shell('../', 'run');
const $ = (sel) => document.querySelector(sel);
const playerEl = $('[data-player]');
playerEl.innerHTML = playerMarkup;

const params = new URLSearchParams(location.search);
const runId = params.get('run') ?? 'exp001-s19-nvidia';

const esc = (x) => String(x).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const kindOf = (m, run) => (m.role === 'system' ? 'system' : m.origin === 'canary' ? 'rule' : m.origin === 'summary' ? 'summary'
  : m.role === 'tool' ? 'tool' : m.role === 'user' && m.step === run.steps.length ? 'probe' : 'history');

// The text view and the transcript: messages up to `step`; after the compaction step, whatever it
// dropped is dimmed (brightness is presence, ADR-022).
function renderText(run, step) {
  const tr = run.transcript ?? [];
  const AT = run.compaction?.at_step ?? Infinity;
  const after = step > AT;
  // Stand-ins a compaction adds (masked tool output) keep the step of what they replace, so a stable
  // sort by step shows each one inside its own turn rather than after the request.
  const shown = tr.filter((m) => m.step <= step && (after || m.origin !== 'summary'))
    .sort((a, b) => a.step - b.step);
  const rows = [];
  for (const m of shown) {
    const kind = kindOf(m, run);
    const key = m.role === 'system' ? 'sys' : kind === 'summary' ? 'sum' : kind === 'probe' ? 'ask' : `t${String(m.step).padStart(2, '0')}`;
    let row = rows.at(-1);
    if (!row || row.key !== key) { row = { key, tag: key, segments: [], cls: '' }; rows.push(row); }
    row.segments.push({ kind, tokens: m.tokens, state: after && !m.kept ? 'out' : 'in' });
    if (kind === 'rule') { row.cls = 'ax-rule-row'; row.lost = after && run.canaries.some((c) => c.fate === 'gone'); }
    if (kind === 'summary') { row.cls = 'ax-summary-row'; row.note = run.canaries.some((c) => c.fate === 'kept') ? 'names the rule' : 'rule not named'; }
  }
  const total = totalOf(run.steps[step - 1]);
  const span = Math.max(run.meta.limit_tokens, ...run.steps.map(totalOf));
  const lines = [asciiGauge(total, run.meta.limit_tokens, { label: 'window', span }), ''];
  rows.forEach((r) => {
    if (after && r.key === 'sum') lines.push(asciiSeam(`compaction after step ${AT}`));
    lines.push(asciiTurns([r]));
  });
  $('[data-rec-ascii]').innerHTML = lines.join('\n');
  const WHO = { system: 'system', rule: 'user, the rule', summary: 'summary', tool: 'tool output', probe: 'user, the request' };
  $('[data-transcript]').innerHTML = shown.map((m) => {
    const kind = kindOf(m, run);
    const who = WHO[kind] ?? (m.role === 'assistant' ? 'agent' : 'user');
    return `<li class="tr-msg tr-${kind}${after && !m.kept ? ' is-out' : ''}"><span class="tr-who">${who} <span class="dim">step ${m.step} · ${m.tokens} tokens</span></span><span class="tr-text">${esc(m.text)}${m.origin !== 'summary' && m.text.length >= 600 ? '…' : ''}</span></li>`;
  }).join('');
  const list = $('[data-transcript]');
  list.scrollTop = list.scrollHeight;  // follow the step: the newest message is the one that matters
}

function renderDetail(run, step) {
  const row = run.steps[step - 1];
  const total = totalOf(row);
  $('[data-detail-title]').textContent = `Step ${step} of ${run.steps.length}`;
  $('[data-layers]').innerHTML =
    ORDER.map((l) => `<li><span>${LAYER_LABEL[l]}</span><span class="v">${formatTokens(row.layers[l])}</span></li>`).join('') +
    `<li><span>total</span><span class="v">${formatTokens(total)} / ${formatTokens(run.meta.limit_tokens)} (${Math.round((total / run.meta.limit_tokens) * 100)}%)</span></li>`;

  const after = run.compaction && step > run.compaction.at_step;
  const planted = run.canaries.filter((c) => c.planted_step <= step);
  $('[data-facts]').innerHTML = planted.length
    ? planted.map((c) => {
        const status = after ? (c.fate === 'gone' ? 'gone ↓' : c.fate) : `planted at step ${c.planted_step}`;
        return `<li><span>${c.id} · ${c.text}</span><span class="st${after && c.fate === 'gone' ? ' gone' : ''}">${status}</span></li>`;
      }).join('')
    : '<li><span>No facts planted yet</span><span class="st"></span></li>';
  // a recorded episode ends with the probe: show what the agent did once the window was compacted
  const probe = run.meta.probe;
  if (probe && after) {
    const broke = probe.grade === 'violated';
    $('[data-facts]').insertAdjacentHTML('beforeend',
      `<li><span>then the agent emitted post_status(${probe.evidence.replace(/'/g, '"')})</span>` +
      `<span class="st${broke ? ' gone' : ''}">${broke ? 'rule broken ↓' : probe.grade === 'respected' ? 'rule followed' : 'no call'}</span></li>`);
  }
}

try {
  const run = await loadRun('../', runId);
  $('[data-title]').textContent = run.meta.model ? `${run.meta.model}, seed ${run.meta.seed}` : `Run ${run.meta.run_id}`;
  $('[data-meta]').innerHTML = [
    `<span class="tag">${run.meta.label}</span>`,
    `<span>policy ${run.meta.policy}</span>`,
    `<span>limit ${formatTokens(run.meta.limit_tokens)} tokens</span>`,
    `<span>source ${run.meta.source}</span>`,
  ].join('');
  document.title = `${run.meta.run_id} · Canary recorder`;
  try {
    const index = await loadIndex('../');
    const groups = {};
    for (const r of index.runs) (groups[r.group ?? (r.label === 'recorded' ? 'Featured' : 'Fixture')] ??= []).push(r);
    const pick = $('[data-runs]');
    pick.innerHTML = Object.entries(groups).map(([g, rs]) => `<optgroup label="${esc(g)}">${rs.map((r) => `<option value="${esc(r.id)}"${r.id === runId ? ' selected' : ''}>${esc(r.title ?? r.id)} · ${esc(r.label)}</option>`).join('')}</optgroup>`).join('');
    pick.addEventListener('change', () => { location.href = `./?run=${encodeURIComponent(pick.value)}`; });
  } catch { /* the run list is a convenience; the run itself still shows */ }

  const setView = (v) => {
    $('[data-player] .stage').hidden = v === 'text';
    $('[data-rec-ascii]').hidden = v !== 'text';
    document.querySelector(`input[name="view"][value="${v}"]`).checked = true;
  };
  document.querySelectorAll('input[name="view"]').forEach((el) => el.addEventListener('change', () => setView(el.value)));
  const help = $('[data-help]');
  $('[data-help-open]').addEventListener('click', () => help.showModal());

  let lastStep = 0;
  const player = mountPlayer({
    root: playerEl, run, height: { wide: 520, compact: 460 },
    onStep(step) { if (step !== lastStep) { lastStep = step; renderDetail(run, step); renderText(run, step); } },
  });
  const requested = Number(params.get('step'));
  player.start({ step: requested, autoplay: false });
  // No ?step=: open at the step before compaction, the moment worth looking at.
  if (!(requested >= 1 && requested <= player.N)) player.goToStep(player.AT || player.N, { writeUrl: false });

  addEventListener('keydown', (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey || e.target instanceof HTMLInputElement || e.target instanceof HTMLSelectElement) return;
    if (e.key === '?') { e.preventDefault(); if (help.open) help.close(); else help.showModal(); return; }
    if (e.key === 't') { e.preventDefault(); setView($('[data-rec-ascii]').hidden ? 'text' : 'bars'); return; }
    const cur = player.currentStep();
    const go = { ArrowRight: cur + 1, ArrowLeft: cur - 1, Home: 1, End: player.N, c: (player.AT || player.N) + 1 }[e.key];
    if (go !== undefined) { e.preventDefault(); player.goToStep(go); }
  });

  $('[data-copy]').addEventListener('click', async () => {
    const url = new URL(location.href);
    url.searchParams.set('run', runId);
    url.searchParams.set('step', String(player.currentStep()));
    let msg = url.toString();
    try { await navigator.clipboard.writeText(url.toString()); msg = `Copied: step ${player.currentStep()}`; } catch { /* clipboard blocked: show the URL instead */ }
    $('[data-copied]').textContent = msg;
  });
} catch (e) {
  fail(playerEl, e);
}
document.documentElement.dataset.ready = 'true';
