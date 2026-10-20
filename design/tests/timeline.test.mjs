import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { buildSchedule, frameAt, timeForStep } from '../scene/timeline.js';

const run = JSON.parse(readFileSync(new URL('../d2/strata_sample.json', import.meta.url)));
const motion = JSON.parse(readFileSync(new URL('../identity/base.tokens.json', import.meta.url))).motion;
const s = buildSchedule(run, motion);

test('timeForStep(i) shows exactly step i, for every step', () => {
  for (let i = 1; i <= s.N; i++) assert.equal(frameAt(s, timeForStep(s, i)).readout.step, i, `step ${i}`);
});

test('frames are a pure function of t', () => {
  for (const t of [0, 1.234, s.seam + 0.2, s.duration]) assert.deepEqual(frameAt(s, t), frameAt(s, t));
});

test('nothing is shown before the start; everything settled at the end', () => {
  const first = frameAt(s, -0.01);
  assert.equal(first.readout.step, 0);
  assert.ok(first.rows.every((r) => r.opacity === 0));
  const last = frameAt(s, s.duration);
  assert.equal(last.readout.step, s.N);
  assert.ok(last.rows.every((r) => Math.abs(r.scale - 1) < 0.01 && r.opacity === 1));
  assert.ok(last.canaries.every((c) => c.fate.opacity === 1 && Math.abs(c.fate.px - 1) < 0.01 && Math.abs(c.fate.py - 1) < 0.02));
});

test('the seam happens after step AT and before step AT+1', () => {
  assert.ok(s.seam > s.arrive[s.AT] && s.seam < s.arrive[s.AT + 1]);
  assert.equal(frameAt(s, s.seam - 0.01).seam.visible, false);
  assert.equal(frameAt(s, s.seam + 0.01).seam.visible, true);
});

test('limit heat rises near the limit and drops after compaction', () => {
  assert.equal(frameAt(s, timeForStep(s, 3)).limitHeat, 0);
  assert.ok(frameAt(s, timeForStep(s, s.AT)).limitHeat > 0.5);
  assert.equal(frameAt(s, timeForStep(s, s.AT + 1)).limitHeat, 0);
});
