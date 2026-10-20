import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spring, track } from '../scene/motion.js';

const regimes = { under: [210, 24], critical: [90, 2 * Math.sqrt(90)], over: [60, 30] };

test('every regime starts at 0 and settles at 1', () => {
  for (const [name, [k, d]] of Object.entries(regimes)) {
    assert.equal(spring(0, k, d), 0, name);
    assert.equal(spring(-1, k, d), 0, name);
    assert.ok(Math.abs(spring(5, k, d) - 1) < 1e-3, `${name} settles`);
  }
});

test('regimes agree near critical damping (no jump between branches)', () => {
  const k = 90, dc = 2 * Math.sqrt(k);
  for (const t of [0.05, 0.2, 0.5]) {
    const below = spring(t, k, dc * 0.9999), at = spring(t, k, dc), above = spring(t, k, dc * 1.0001);
    assert.ok(Math.abs(below - at) < 1e-3 && Math.abs(above - at) < 1e-3, `t=${t}`);
  }
});

test('underdamped overshoots; critical and overdamped never do', () => {
  const peak = (k, d) => Math.max(...Array.from({ length: 400 }, (_, i) => spring(i / 200, k, d)));
  assert.ok(peak(...regimes.under) > 1.001);
  assert.ok(peak(...regimes.critical) <= 1 + 1e-9);
  assert.ok(peak(...regimes.over) <= 1 + 1e-9);
});

test('track stacks one spring per target change', () => {
  const keys = [[0, 0], [1, 10], [2, 4]];
  assert.equal(track(0.5, keys, 210, 24), 0);
  assert.ok(Math.abs(track(1.9, keys, 210, 24) - 10) < 0.05);
  assert.ok(Math.abs(track(6, keys, 210, 24) - 4) < 1e-3);
});
