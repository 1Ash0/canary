### Verdict by the preregistered rules
- **Instrument check (H2): passed.** Summaries cut off by the cap: none (see the table), against 9 of 24 judged summaries in EXP-001 under the 400-token cap. No summary failed to be produced.
- **H1 for `gpt-oss-20b`: replicates.** Both primary comparisons have a positive paired difference whose bootstrap interval excludes zero, and an adjusted exact McNemar q below 0.05. Validity checks hold: floor broke the rule in {gpt_oss_20b_floor_rate}, control in {gpt_oss_20b_control_rate}, and no cell had episodes without a summary.
- **Groq `gpt-oss-120b`: no episodes yet.** Its daily token limit was spent on the same day by earlier runs; the design allows later days to add seeds. Nothing is claimed for it.

### What it means
- EXP-001's NVIDIA effect was not an artefact of truncation. With every summary complete, the treatment rate is still {gpt_oss_20b_treatmentllm_summary_rate}, while the same-length uncompacted window broke the rule in {gpt_oss_20b_length_matchedllm_summary_rate}: the loss comes from what the summary leaves out, not from a shorter window.
- Exploratory: the channel name survived in {gpt_oss_20b_treatmentllm_summary_kept} summaries, and behaviour matched survival in {gpt_oss_20b_treatmentllm_summary_fate} episodes; the mismatches are agents that lost the rule and still picked the right channel, which the floor condition says happens by chance about one time in four.
- Together with EXP-001: a generic summary prompt carries the rule through for Mistral almost every time and for `gpt-oss-20b` about half the time. Whether a rule survives compaction depends on the model that writes the summary.

### Not shown
One pack, one prompt, one free model at 27 seeds; the owner's hand audit of these summaries is still to come.
