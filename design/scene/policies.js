// The three deterministic compaction policies, ported from src/ctxcheck/policies/ so the site's lab
// can recompute a window as the reader drags. Each function mirrors its Python twin step for step;
// design/tests/lab-parity.test.mjs replays cases computed by the Python and requires identical
// results. A message is { role, kind, tokens, call, callId, masked } (masked = the token count of
// its "[tool output omitted]" placeholder, for tool outputs).

const sum = (ms) => ms.reduce((a, m) => a + m.tokens, 0);

// System prompt and current turn are never dropped; history is cut into units, and a tool call and
// its result are one unit (units.py).
export function split(win) {
  let nSys = 0;
  while (nSys < win.length && win[nSys].role === 'system') nSys++;
  const rest = win.slice(nSys);
  let tailAt = rest.length;
  rest.forEach((m, i) => { if (m.role === 'user' && m.kind !== 'summary') tailAt = i; });
  const history = rest.slice(0, tailAt), tail = rest.slice(tailAt);
  const units = [];
  for (let i = 0; i < history.length; i++) {
    const m = history[i], next = history[i + 1];
    if (m.call && next && next.role === 'tool' && next.callId === m.callId) { units.push([m, next]); i++; }
    else units.push([m]);
  }
  const system = win.slice(0, nSys);
  return { system, units, tail, floor: sum(system) + sum(tail) };
}

export class Irreducible extends Error {}

function prepare(win, budget, ratio) {
  const parts = split(win);
  if (parts.floor > budget) throw new Irreducible(`protected part needs ${parts.floor} > ${budget}`);
  return { parts, target: Math.max(parts.floor, Math.trunc(budget * ratio)) };
}
const flatten = (parts, units) => [...parts.system, ...units.flat(), ...parts.tail];

export function recencyTruncate(win, budget, { targetRatio = 0.6 } = {}) {
  if (sum(win) <= budget) return win;
  const { parts, target } = prepare(win, budget, targetRatio);
  const units = [...parts.units];
  let used = parts.floor + units.reduce((a, u) => a + sum(u), 0);
  while (units.length && used > target) used -= sum(units.shift());
  return flatten(parts, units);
}

export function headTail(win, budget, { targetRatio = 0.6, headRatio = 0.3 } = {}) {
  if (sum(win) <= budget) return win;
  const { parts, target } = prepare(win, budget, targetRatio);
  const room = target - parts.floor, headRoom = Math.trunc(room * headRatio);
  const head = [];
  let used = 0;
  for (const u of parts.units) { if (used + sum(u) > headRoom) break; head.push(u); used += sum(u); }
  const tail = [];
  for (const u of parts.units.slice(head.length).reverse()) { if (used + sum(u) > room) break; tail.push(u); used += sum(u); }
  return flatten(parts, [...head, ...tail.reverse()]);
}

export function observationMask(win, budget, { targetRatio = 0.6, keepRecent = 2 } = {}) {
  if (sum(win) <= budget) return win;
  const { parts, target } = prepare(win, budget, targetRatio);
  const units = parts.units.map((u) => [...u]);
  let used = parts.floor + units.reduce((a, u) => a + sum(u), 0);
  const results = [];
  units.forEach((u, ui) => u.forEach((m, mi) => { if (m.role === 'tool') results.push([ui, mi]); }));
  for (const [ui, mi] of results.slice(0, Math.max(0, results.length - keepRecent))) {
    if (used <= target) break;
    const old = units[ui][mi];
    if (old.masked >= old.tokens) continue;
    units[ui][mi] = { ...old, tokens: old.masked, maskedFrom: old };
    used -= old.tokens - old.masked;
  }
  while (units.length && used > target) used -= sum(units.shift());
  return flatten(parts, units);
}

export const POLICIES = { recency_truncate: recencyTruncate, head_tail: headTail, observation_mask: observationMask };

// Assemble the window the lab shows: system, the filler turns with the rule turn at `position`,
// then the probe. Ids are positions, so results compare directly with the Python parity cases.
export function assemble(history, position) {
  const turns = [...history.filler];
  turns.splice(Math.min(position, turns.length), 0, history.rule);
  const win = [{ role: 'system', kind: 'system', tokens: history.system.tokens, text: history.system.text }];
  turns.forEach((t, ti) => t.forEach((m) => win.push({ ...m, callId: m.role === 'tool' || m.call ? `c${ti}` : null, turn: ti })));
  win.push({ role: 'user', kind: 'probe', tokens: history.probe.tokens, text: history.probe.text });
  return win.map((m, i) => ({ ...m, id: i }));
}

// Run a policy the way the loop does: only when the window plus tool specs exceeds the limit.
export function compact(history, win, policy, limit, options) {
  const total = history.tools_tokens + sum(win);
  if (total <= limit) return { out: win, compacted: false, irreducible: false };
  try {
    return { out: POLICIES[policy](win, limit - history.tools_tokens, options), compacted: true, irreducible: false };
  } catch (e) {
    if (e instanceof Irreducible) return { out: win, compacted: false, irreducible: true };
    throw e;
  }
}

export const tokensOf = sum;
