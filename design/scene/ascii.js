// The window as text (ADR-022, SITE_RULES 4.7). One monospace row per message: a role tag, then a
// run of glyphs whose length is the message's tokens and whose glyph is its kind. Brightness is
// presence: rows still in the window are bright, rows compaction removed are dim, a lost rule is
// marked in vermilion with words. Pure function of its inputs; returns HTML for a <pre>.

export const GLYPH = { system: '▪', history: '░', tool: '▒', summary: '▓', rule: '█', probe: '░', masked: '·' };
const TAG = { system: 'sys ', history: null, tool: 'tool', summary: 'sum ', rule: 'rule', probe: 'ask ', masked: 'tool' };
const esc = (s) => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const nf = new Intl.NumberFormat('en-US');
const pad = (s, n) => (s.length >= n ? s.slice(0, n) : s + ' '.repeat(n - s.length));

// rows: [{ kind, role, tokens, state: 'in' | 'out' | 'masked' | 'added', note }]
export function asciiWindow(rows, { cols = 44, tokensPerGlyph } = {}) {
  const biggest = Math.max(...rows.map((r) => r.tokens), 1);
  const per = tokensPerGlyph ?? Math.max(1, Math.ceil(biggest / cols));
  return rows.map((r) => {
    const kind = r.state === 'masked' ? 'masked' : r.kind;
    const tag = TAG[kind] ?? (r.role === 'assistant' ? 'agt ' : 'you ');
    const n = Math.max(1, Math.round(r.tokens / per));
    const bar = GLYPH[kind].repeat(Math.min(n, cols + 6));
    const cls = [`ax-${kind}`, r.state === 'out' ? 'ax-out' : 'ax-in', r.lost ? 'ax-lost' : ''].join(' ');
    const tail = r.lost ? '  ∅ gone' : r.note ? `  ${r.note}` : '';
    return `<span class="ax-row ${cls}"><span class="ax-tag">${tag}</span> <span class="ax-bar">${bar}</span><span class="ax-n">${pad('', 1)}${nf.format(r.tokens)}</span><span class="ax-note">${esc(tail)}</span></span>`;
  }).join('\n');
}

// A token gauge: glyphs up to the window total, a bar at the limit; only the part past the limit is
// marked as loss.
export function asciiGauge(total, limit, { cols = 44, label = '', span: shared } = {}) {
  const span = shared ?? Math.max(total, limit);  // pass one span so two gauges share a scale
  const fill = Math.round((total / span) * cols), mark = Math.round((limit / span) * cols);
  let inside = '', over = '';
  for (let i = 0; i < cols; i++) {
    if (i === mark) continue;
    if (i < mark) inside += i < fill ? '█' : '·';
    else over += i < fill ? '█' : '·';
  }
  const tag = label ? `<span class="ax-tag">${esc(pad(label, 6))}</span> ` : '';
  const isOver = total > limit;
  return `${tag}<span class="ax-gauge">${inside}</span><span class="ax-limit">│</span><span class="ax-gauge is-over">${over}</span> <span class="ax-n">${nf.format(total)} / ${nf.format(limit)}</span>${isOver ? ' <span class="ax-note ax-over">over</span>' : ''}`;
}

export const asciiSeam = (label, cols = 44) => {
  const text = ` ${label} `;
  const side = Math.max(2, Math.floor((cols + 8 - text.length) / 2));
  return `<span class="ax-seam">${'═'.repeat(side)}${esc(text)}${'═'.repeat(side)}</span>`;
};

// One row per turn: each message in the turn is a segment, so a partial drop or a masked output
// shows inside its turn. rows: [{ tag, segments: [{ kind, tokens, state }], lost, note }]
export function asciiTurns(rows, { tokensPerGlyph = 6, maxGlyphs = 52 } = {}) {
  return rows.map((r) => {
    let used = 0;
    const segs = r.segments.map((g) => {
      const kind = g.state === 'masked' ? 'masked' : g.kind;
      const n = Math.max(1, Math.round(g.tokens / tokensPerGlyph));
      const take = Math.max(1, Math.min(n, maxGlyphs - used));
      used += take;
      return `<span class="ax-seg ax-${kind} ${g.state === 'out' ? 'ax-out' : 'ax-in'}">${GLYPH[kind].repeat(take)}</span>`;
    }).join('');
    const total = r.segments.filter((g) => g.state !== 'out').reduce((a, g) => a + g.tokens, 0);
    const tail = r.lost ? '  ∅ rule gone' : r.note ? `  ${r.note}` : '';
    const allOut = r.segments.every((g) => g.state === 'out');
    return `<span class="ax-row ${r.cls ?? ''}${allOut ? ' ax-out' : ''}${r.lost ? ' ax-lost' : ''}"><span class="ax-tag">${esc(pad(r.tag, 4))}</span> ${segs}<span class="ax-n"> ${allOut ? '–' : nf.format(total)}</span><span class="ax-note">${esc(tail)}</span></span>`;
  }).join('\n');
}
