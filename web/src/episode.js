// The landing page's shared "current episode": one seed and two recorded ways of making room for it
// (a model and a policy each), all from EXP-002's channel-rule cells, where every policy and model
// saw the same seeded history. The comparison, the consequence and the results read and write it;
// it lives in the URL (?seed=19&a=mistral.llm_summary&b=nvidia.llm_summary) so any view is linkable.

export const POLICY_NAME = {
  recency_truncate: 'drop oldest', head_tail: 'keep head and tail',
  observation_mask: 'mask tool output', llm_summary: 'model summary',
};
export const PRESETS = [
  { label: 'Two summarisers', a: 'mistral.llm_summary', b: 'nvidia.llm_summary' },
  { label: 'Drop oldest or keep the head', a: 'nvidia.head_tail', b: 'nvidia.recency_truncate' },
  { label: 'Mask or summarise', a: 'nvidia.observation_mask', b: 'nvidia.llm_summary' },
];
const DEFAULT = { seed: 19, a: PRESETS[0].a, b: PRESETS[0].b };

export function createEpisodes(exp) {
  const sides = new Map();
  for (const block of exp.blocks.filter((b) => b.pack === 'constraint')) {
    const tag = block.host.toLowerCase();
    for (const policy of Object.keys(POLICY_NAME)) {
      const row = block.rows.find((r) => r.label === `treatment(${policy})`);
      if (!row) continue;
      sides.set(`${tag}.${policy}`, {
        key: `${tag}.${policy}`, tag, host: block.host, model: block.model, policy,
        name: `${block.host}, ${POLICY_NAME[policy]}`, seeds: row.seeds,
      });
    }
  }
  const seeds = [...new Set([...sides.values()].flatMap((s) => s.seeds.map((d) => d.seed)))]
    .sort((x, y) => x - y);
  const valid = (s) => ({
    seed: seeds.includes(+s.seed) ? +s.seed : DEFAULT.seed,
    a: sides.has(s.a) ? s.a : DEFAULT.a,
    b: sides.has(s.b) ? s.b : DEFAULT.b,
  });
  const q = new URLSearchParams(location.search);
  let state = valid({ seed: q.get('seed') ?? DEFAULT.seed, a: q.get('a') ?? DEFAULT.a, b: q.get('b') ?? DEFAULT.b });
  const listeners = new Set();

  return {
    exp, seeds, sides: [...sides.values()],
    get: () => ({ ...state }),
    side: (key) => sides.get(key),
    // what one side did on one seed: grade, fate, evidence and the recorder run id
    outcome: (key, seed) => sides.get(key)?.seeds.find((d) => d.seed === seed),
    set(patch) {
      const next = valid({ ...state, ...patch });
      if (next.seed === state.seed && next.a === state.a && next.b === state.b) return;
      state = next;
      const url = new URL(location.href);
      url.searchParams.set('seed', state.seed);
      url.searchParams.set('a', state.a);
      url.searchParams.set('b', state.b);
      history.replaceState(null, '', url);
      listeners.forEach((fn) => fn({ ...state }));
    },
    on(fn) { listeners.add(fn); return () => listeners.delete(fn); },
  };
}
