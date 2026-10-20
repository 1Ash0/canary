// Contract test: the scene, the timeline and the readout must accept the exporter's real output
// (web/public/data, produced by `make export`), not just the hand-made design sample.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { renderStrata, totalOf } from '../scene/strata.js';
import { buildSchedule, frameAt, timeForStep } from '../scene/timeline.js';

const read = (p) => JSON.parse(readFileSync(new URL(p, import.meta.url)));
const run = read('../../web/public/data/runs/synthetic-001.json');
const motion = read('../identity/base.tokens.json').motion;

test('exported run has the fields the scene reads', () => {
  assert.equal(run.meta.label, 'synthetic fixture');
  assert.ok(run.meta.limit_tokens > 0 && run.steps.length === 40);
  assert.equal(run.compaction.at_step, 31);
  assert.ok(run.steps.every((s) => ['system', 'tools', 'history', 'toolOutput', 'summary'].every((l) => Number.isInteger(s.layers[l]))));
  assert.ok(run.canaries.every((c) => ['kept', 'gone'].includes(c.fate)));
});

test('the window never exceeds the limit', () => {
  assert.ok(run.steps.every((s) => totalOf(s) < run.meta.limit_tokens));
});

test('the scene renders the exported run at desktop and phone sizes', () => {
  for (const [width, height, compact] of [[740, 376, false], [358, 460, true]]) {
    const svg = renderStrata(run, { width, height, compact });
    assert.match(svg, /^<svg /);
    assert.equal((svg.match(/data-row="/g) ?? []).length, 40);
    assert.equal((svg.match(/data-plant="/g) ?? []).length, 3);
    assert.equal((svg.match(/data-fate="/g) ?? []).length, 3);
  }
});

test('every exported step can be shown by the timeline, and fates settle', () => {
  const s = buildSchedule(run, motion);
  for (let i = 1; i <= 40; i++) assert.equal(frameAt(s, timeForStep(s, i)).readout.step, i);
  const end = frameAt(s, s.duration);
  assert.ok(end.canaries.every((c) => c.fate.opacity === 1 && Math.abs(c.fate.py - 1) < 0.02));
});
