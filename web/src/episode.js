// The landing page's shared "current episode": a canary, one seed and two recorded ways of making
// room for it (a model and a policy each), all from EXP-002, where every policy and model saw the same
// seeded history. The Lab, the comparison, the consequence and the results read and write it; it
// lives in the URL (?canary=constraint&seed=19&a=mistral.llm_summary&b=nvidia.llm_summary).

// One vocabulary for the policies everywhere on the site (critique: four names for one thing).
export const POLICY_NAME = {
  recency_truncate: 'drop oldest', head_tail: 'keep head and tail',
  observation_mask: 'mask tool output', llm_summary: 'model summary',
};
export const CANARY = {
  constraint: { name: 'Channel rule', value: 'channel', bad: 'broke the rule', good: 'followed the rule' },
  identifier: { name: 'Account code', value: 'code', bad: 'used a wrong code', good: 'used the exact code' },
};
// Preset pairs; a preset is offered only for a canary where both of its sides were recorded.
export const PRESETS = [
  { label: 'Two summarisers', a: 'mistral.llm_summary', b: 'nvidia.llm_summary' },
  { label: 'Drop oldest or keep the head', a: '*.head_tail', b: '*.recency_truncate' },
  { label: 'Mask or summarise', a: '*.observation_mask', b: '*.llm_summary' },
];
const DEFAULT = { canary: 'constraint', seed: 19, a: 'mistral.llm_summary', b: 'nvidia.llm_summary' };

export function createEpisodes(exp) {
  const byCanary = {};
  for (const block of exp.blocks) {
    const tag = block.host.toLowerCase();
    for (const policy of Object.keys(POLICY_NAME)) {
      const row = block.rows.find((r) => r.label === `treatment(${policy})`);
      if (!row) continue;
      (byCanary[block.pack] ??= new Map()).set(`${tag}.${policy}`, {
        key: `${tag}.${policy}`, tag, host: block.host, model: block.model, policy, canary: block.pack,
        name: `${block.host}, ${POLICY_NAME[policy]}`, seeds: row.seeds,
      });
    }
  }
  const canaries = Object.keys(CANARY).filter((c) => byCanary[c]);
  const seeds = [...new Set([...byCanary.constraint.values()].flatMap((s) => s.seeds.map((d) => d.seed)))]
    .sort((x, y) => x - y);
  const sidesOf = (c) => byCanary[c] ?? byCanary.constraint;
  // a preset resolved for a canary: '*' is the model the canary has (gpt-oss-20b where both exist)
  const presetsFor = (c) => {
    const tags = new Set([...sidesOf(c).values()].map((s) => s.tag));
    const star = tags.has('nvidia') ? 'nvidia' : [...tags][0];
    return PRESETS.map((p) => ({ label: p.label, a: p.a.replace('*', star), b: p.b.replace('*', star) }))
      .filter((p) => sidesOf(c).has(p.a) && sidesOf(c).has(p.b));
  };
  const valid = (s) => {
    const canary = canaries.includes(s.canary) ? s.canary : DEFAULT.canary;
    const sides = sidesOf(canary);
    const first = presetsFor(canary)[0];
    return {
      canary,
      seed: seeds.includes(+s.seed) ? +s.seed : DEFAULT.seed,
      a: sides.has(s.a) ? s.a : first.a,
      b: sides.has(s.b) ? s.b : first.b,
    };
  };
  const q = new URLSearchParams(location.search);
  let state = valid({ canary: q.get('canary') ?? DEFAULT.canary, seed: q.get('seed') ?? DEFAULT.seed,
    a: q.get('a') ?? DEFAULT.a, b: q.get('b') ?? DEFAULT.b });
  const listeners = new Set();

  return {
    exp, seeds, canaries,
    get: () => ({ ...state }),
    sides: () => [...sidesOf(state.canary).values()],
    side: (key, canary = state.canary) => sidesOf(canary).get(key),
    presets: () => presetsFor(state.canary),
    // what one side did on one seed: grade, fate, evidence and the recorder run id
    outcome: (key, seed, canary = state.canary) => sidesOf(canary).get(key)?.seeds.find((d) => d.seed === seed),
    set(patch) {
      // switching canary: a side not given in the patch falls back to that canary's first preset
      const switching = patch.canary && patch.canary !== state.canary;
      const next = valid(switching
        ? { ...state, ...patch, a: patch.a ?? null, b: patch.b ?? null } : { ...state, ...patch });
      if (Object.keys(next).every((k) => next[k] === state[k])) return;
      state = next;
      const url = new URL(location.href);
      for (const k of ['canary', 'seed', 'a', 'b']) url.searchParams.set(k, state[k]);
      history.replaceState(null, '', url);
      listeners.forEach((fn) => fn({ ...state }));
    },
    on(fn) { listeners.add(fn); return () => listeners.delete(fn); },
  };
}
