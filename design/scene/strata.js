// Strata scene: builds the context-window SVG for a run at its final state. Pure function of (run, options);
// shared by the site player and the video page (ADR-016). Colours and type come from token CSS variables
// via classes in strata.css. Animatable parts are wrapped in groups with data attributes; timeline.js
// drives them with transform/opacity only.

export const ORDER = ['system', 'tools', 'summary', 'history', 'toolOutput'];
export const LAYER_LABEL = { system: 'system', tools: 'tools', summary: 'summary', history: 'history', toolOutput: 'tool output' };
const LAYER_CLASS = { system: 'system', tools: 'tools', summary: 'summary', history: 'history', toolOutput: 'tool-output' };

const nf = new Intl.NumberFormat('en-US');
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
export const totalOf = (s) => ORDER.reduce((a, l) => a + s.layers[l], 0);
export const formatTokens = (n) => nf.format(n);
const f1 = (n) => n.toFixed(1);

export function layout(run, { width, height, compact = width < 560 }) {
  const N = run.steps.length;
  const AT = run.compaction.at_step;
  const labelW = compact ? 0 : Math.min(260, Math.round(width * 0.38));
  const left = compact ? 28 : 34, top = 22, bottom = 64, gap = 18;
  const limitX = width - labelW - (compact ? 12 : 28);
  const pitch = (height - top - bottom - gap) / N;
  const bar = Math.max(2, Math.round(pitch * 0.68));
  const scale = (limitX - left) / run.meta.limit_tokens;
  const rowY = (i) => top + (i - 1) * pitch + (i > AT ? gap : 0);
  const seamY = rowY(AT) + bar + gap / 2;
  const axisY = rowY(N) + bar + 12;
  return { N, AT, compact, labelW, left, top, bottom, gap, limitX, labelX: limitX + 20, pitch, bar, scale, rowY, seamY, axisY, width, height };
}

export function renderStrata(run, opts) {
  const L = layout(run, opts);
  const { AT, left, limitX, labelX, bar, scale, rowY, seamY, axisY, compact, width, height } = L;
  const base = [], seam = [], leads = [], marks = [], texts = [];
  const text = (x, y, s, cls, anchor = 'start') => `<text x="${f1(x)}" y="${f1(y)}" class="${cls}" text-anchor="${anchor}">${esc(s)}</text>`;

  // limit rule
  base.push(`<line class="sx-limit" x1="${limitX}" y1="${L.top - 8}" x2="${limitX}" y2="${axisY - 6}"/>`);
  base.push(text(limitX - 4, L.top - 10, `limit ${formatTokens(run.meta.limit_tokens)}`, 'sx-label', 'end'));
  // warm copy of the limit rule, faded in by the timeline as the window nears the limit (opacity 0 at rest)
  base.push(`<g data-limit-hot style="opacity:0"><line class="sx-limit-hot" x1="${limitX}" y1="${L.top - 8}" x2="${limitX}" y2="${axisY - 6}"/>${text(limitX - 4, L.top - 10, `limit ${formatTokens(run.meta.limit_tokens)}`, 'sx-label sx-strong', 'end')}</g>`);

  // rows: bars in a scalable group; step numbers in a separate group so text never stretches
  for (const s of run.steps) {
    const y = rowY(s.i);
    let x = left;
    const rects = [];
    for (const l of ORDER) {
      const w = s.layers[l] * scale;
      if (w > 0) rects.push(`<rect class="sx-${LAYER_CLASS[l]}" x="${f1(x)}" y="${f1(y)}" width="${f1(Math.max(0, w - 1))}" height="${bar}"/>`);
      x += w;
    }
    base.push(`<g class="sx-row" data-row="${s.i}">${rects.join('')}</g>`);
    const nearSeam = Math.abs(s.i - AT) <= 2 && s.i !== AT;
    if ((s.i === 1 || s.i % 10 === 0 || s.i === AT) && !nearSeam) {
      base.push(`<g data-row-label="${s.i}">${text(left - 8, y + bar - 1, String(s.i), s.i === AT ? 'sx-label sx-strong' : 'sx-label', 'end')}</g>`);
    }
  }

  // token axis
  const tick = compact ? 20000 : 10000;
  base.push(`<line class="sx-axis" x1="${left}" y1="${axisY}" x2="${limitX}" y2="${axisY}"/>`);
  for (let v = 0; v <= run.meta.limit_tokens; v += tick) {
    const x = left + v * scale;
    base.push(`<line class="sx-tick" x1="${f1(x)}" y1="${axisY}" x2="${f1(x)}" y2="${axisY + 4}"/>`);
    base.push(text(x, axisY + 16, v === 0 ? '0' : `${v / 1000}k`, 'sx-label', 'middle'));
  }

  // compaction seam (signature device): line, notch ticks, label, each separately animatable
  seam.push(`<g class="sx-sweep" data-seam-line><line class="sx-seam" x1="0" y1="${seamY}" x2="${width}" y2="${seamY}"/></g>`);
  for (let x = 0; x <= width; x += 48) seam.push(`<g data-seam-tick="${f1(x / width)}"><line class="sx-seam" x1="${x}" y1="${seamY - 5}" x2="${x}" y2="${seamY}"/></g>`);
  // compact layouts have no label column, so the step-AT bar reaches the right edge: label under the seam instead
  seam.push(`<g data-seam-label="${compact ? 'late' : 'early'}">${text(width, compact ? seamY + 14 : seamY - 7, `compaction @ step ${AT}`, 'sx-label sx-strong', 'end')}</g>`);

  // canaries
  const after = run.steps[AT];
  const sumCenter = left + (after.layers.system + after.layers.tools + after.layers.summary / 2) * scale;
  const r = compact ? 4.5 : 5.5;
  const dot = (x, y, fate) => {
    const halo = `<circle class="sx-halo" cx="${f1(x)}" cy="${f1(y)}" r="${r + 3}"/>`;
    if (fate === 'gone') return halo + `<circle class="sx-gone" cx="${f1(x)}" cy="${f1(y)}" r="${r}"/>`;
    if (fate === 'changed') return halo + `<circle class="sx-changed" cx="${f1(x)}" cy="${f1(y)}" r="${r - 0.5}"/>`;
    return halo + `<circle class="sx-kept" cx="${f1(x)}" cy="${f1(y)}" r="${r}"/>`;
  };
  const callouts = [];
  const callout = (key, x, y, head, sub, cls = '', leadCls = 'sx-lead') => { if (!compact) callouts.push({ key, x, y, head, sub, cls, leadCls }); };

  for (const k of run.canaries) {
    const s = run.steps[k.planted_step - 1];
    const px = left + (s.layers.system + s.layers.tools + s.layers.summary + s.layers.history) * scale - 4;
    const py = rowY(s.i) + bar / 2;
    const idText = compact ? text(px + r + 5, py + 4, k.id, 'sx-label sx-strong') : '';
    marks.push(`<g class="sx-pop" data-plant="${k.id}" data-step="${k.planted_step}">${dot(px, py, 'kept')}${idText}</g>`);
    callout(`${k.id}-plant`, px + r, py, `${k.id} · ${k.type.replace('_', ' ')} · step ${k.planted_step}`, k.text);

    let fx, fy, extra = '';
    if (k.fate === 'gone') {
      fx = px; fy = axisY + 42;
      leads.push(`<g data-drop="${k.id}"><line class="sx-drop" x1="${f1(px)}" y1="${f1(seamY + 1)}" x2="${f1(px)}" y2="${f1(fy - r - 3)}"/></g>`);
      if (compact) extra = text(fx + r + 5, fy + 4, `${k.id} gone ↓`, 'sx-label sx-loss');
      callout(`${k.id}-fate`, fx + r, fy, `${k.id} · gone ↓`, 'absent from the summary', 'sx-loss', 'sx-lead-loss');
    } else {
      // keep kept/changed markers (halo included) from touching, whatever the row pitch
      const rowsApart = Math.max(2, Math.ceil((2 * (r + 3) + 4) / L.pitch));
      const row = k.fate === 'kept' ? AT + 1 : Math.min(L.N, AT + 1 + rowsApart);
      fx = sumCenter; fy = rowY(row) + bar / 2;
      if (compact) extra = text(fx + r + 5, fy + 4, `${k.id} ${k.fate}`, 'sx-label sx-strong');
      callout(`${k.id}-fate`, fx + r, fy, `${k.id} · ${k.fate}`, k.fate === 'changed' ? `→ ${k.after_text}` : 'verbatim in summary', '', k.fate === 'changed' ? 'sx-lead sx-dashed' : 'sx-lead');
    }
    // dx/dy: offset from the fate position back to the plant position; the marker travels it at compaction
    marks.push(`<g data-fate="${k.id}" data-kind="${k.fate}" data-dx="${f1(px - fx)}" data-dy="${f1(py - fy)}">${dot(fx, fy, k.fate)}${extra}</g>`);
  }

  // callouts placed top-down with a minimum gap; leaders elbow from the anchor to the label
  const MIN_GAP = 38;
  callouts.sort((a, b) => a.y - b.y);
  let prev = -Infinity;
  for (const c of callouts) { c.ly = Math.max(c.y, prev + MIN_GAP); prev = c.ly; }
  const elbow = labelX - 24;
  for (const c of callouts) {
    leads.push(`<g data-callout-lead="${c.key}"><polyline class="${c.leadCls}" fill="none" points="${f1(c.x)},${f1(c.y)} ${elbow},${f1(c.y)} ${labelX - 8},${f1(c.ly)}"/></g>`);
    texts.push(`<g data-callout-text="${c.key}">${text(labelX, c.ly - 2, c.head, `sx-label sx-strong ${c.cls}`)}${c.sub ? text(labelX, c.ly + 14, c.sub, 'sx-fact') : ''}</g>`);
  }

  return `<svg class="sx" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-label="Context window by step for ${esc(run.meta.label)}; compaction at step ${AT}">${base.join('')}${seam.join('')}${leads.join('')}${marks.join('')}${texts.join('')}</svg>`;
}
