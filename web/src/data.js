// Loads exported data (web/public/data, produced by `make export`). `base` is the page's depth.
import tokens from '../../design/identity/base.tokens.json';

export const motion = tokens.motion;

export async function loadJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`could not load ${path} (${res.status})`);
  return res.json();
}

export const loadIndex = (base) => loadJson(`${base}data/index.json`);
export const loadRun = (base, id) => loadJson(`${base}data/runs/${encodeURIComponent(id)}.json`);
export const loadExperiment = (base, id) => loadJson(`${base}data/experiments/${encodeURIComponent(id)}.json`);
