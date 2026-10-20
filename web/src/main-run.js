import { loadRun, loadIndex } from './data.js';
import { mountPlayer, playerMarkup } from './player.js';
import { shell, fail } from './shell.js';
import { ORDER, LAYER_LABEL, formatTokens, totalOf } from '../../design/scene/strata.js';

shell('../', 'run');
const $ = (sel) => document.querySelector(sel);
const playerEl = $('[data-player]');
playerEl.innerHTML = playerMarkup;

const params = new URLSearchParams(location.search);
const runId = params.get('run') ?? 'exp001-s19-nvidia';

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
    $('[data-runs]').innerHTML = index.runs.map((r) => `<a href="./?run=${encodeURIComponent(r.id)}"${r.id === runId ? ' aria-current="page"' : ''}><span class="tag">${r.label}</span> ${r.title ?? r.id}</a>`).join('');
  } catch { /* the run list is a convenience; the run itself still shows */ }

  let lastStep = 0;
  const player = mountPlayer({
    root: playerEl, run, height: { wide: 520, compact: 460 },
    onStep(step) { if (step !== lastStep) { lastStep = step; renderDetail(run, step); } },
  });
  const requested = Number(params.get('step'));
  player.start({ step: requested, autoplay: false });
  // No ?step=: open at the step before compaction, the moment worth looking at.
  if (!(requested >= 1 && requested <= player.N)) player.goToStep(player.AT || player.N, { writeUrl: false });

  addEventListener('keydown', (e) => {
    if (e.metaKey || e.ctrlKey || e.altKey || e.target instanceof HTMLInputElement) return;
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
