import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';

export const DESIGN = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const read = (p) => JSON.parse(readFileSync(join(DESIGN, p), 'utf8'));

export const LAYERS = ['system', 'tools', 'history', 'toolOutput', 'summary'];

export function loadBase() {
  return read('identity/base.tokens.json');
}

export function loadTheme(name = 'canary') {
  return read(`themes/${name}/tokens.json`);
}

// Theme ground/surface override the base ones (ADR-017: theme = ground + ramp + device).
function resolve(id, label, color, ground, ramp) {
  return { id, label, color: { ...color, ...ground }, ramp };
}

export function loadPalettes() {
  const base = loadBase();
  const theme = loadTheme();
  const recommended = resolve('B', 'B: warm near-black, cream ink (recommended)', base.color, theme.ground, theme.ramp);
  const alts = read('d2/candidates.json').candidates.map((c) => resolve(c.id, c.label, c.color, c.ground, c.ramp));
  return [recommended, ...alts];
}
