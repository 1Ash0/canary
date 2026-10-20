// Static D4 mockup: renders the strata scene at its final state from the fixture. No motion (D4b adds it).
import { renderStrata, ORDER, LAYER_LABEL, totalOf, formatTokens } from '../scene/strata.js';

const run = await (await fetch('../d2/strata_sample.json')).json();
const last = run.steps[run.steps.length - 1];
const $ = (sel) => document.querySelector(sel);

$('[data-out="step"]').textContent = `${last.i} / ${run.steps.length}`;
$('[data-out="tokens"]').textContent = `${formatTokens(totalOf(last))} / ${formatTokens(run.meta.limit_tokens)}`;
$('[data-out="label"]').textContent = run.meta.label;
const scrub = $('[data-scrub]');
scrub.max = run.steps.length;
scrub.value = last.i;

const stage = $('[data-stage]');
const compact = matchMedia('(max-width: 767px)').matches; // = layout.breakpoints.md
const height = compact ? 460 : 376;
stage.innerHTML = renderStrata(run, { width: stage.clientWidth, height, compact });

// Compact layout has no room for on-figure labels; list the fates under the figure instead.
if (compact) {
  $('[data-fates]').innerHTML = run.canaries.map((k) => {
    const detail = k.fate === 'changed' ? `→ ${k.after_text}` : k.fate === 'gone' ? 'absent from the summary' : 'verbatim in summary';
    return `<li class="fate-${k.fate}"><span class="cite">${k.id} · ${k.fate}${k.fate === 'gone' ? ' ↓' : ''}</span> ${k.text} <span class="dim">${detail}</span></li>`;
  }).join('');
}

const head = `<tr><th scope="col">step</th>${ORDER.map((l) => `<th scope="col">${LAYER_LABEL[l]}</th>`).join('')}</tr>`;
const rows = run.steps.map((s) => `<tr><th scope="row">${s.i}</th>${ORDER.map((l) => `<td>${s.layers[l]}</td>`).join('')}</tr>`).join('');
$('[data-table]').insertAdjacentHTML('beforeend', head + rows);
document.documentElement.dataset.ready = 'true';
