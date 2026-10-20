# 2026-10-20 — The ledger and the loop disagreed about when compaction happens

*Drafted by Claude Code during U7; Asmit to review.*

**What happened.** The first loop test that replayed a run through `ledger.replay` and compared with the loop's own final token count failed: 81 (replay) vs 69 (loop).

**Cause.** Two producers used two conventions. The synthetic generator wrote the compaction event *between* steps (before step 32's first message), and the ledger assumed that. The loop adds the new user message first, finds the window over budget, and compacts *inside* that step. The ledger closed the step's row at the compaction event, snapshotting a window the model never saw, and then never updated it.

**Why it hid.** The fixture used the ledger's assumed convention, so every earlier test passed. Only a second, independent producer (the loop) exposed it.

**Fix.** One convention for all three, written down in ARCHITECTURE: the compaction event follows the message that triggered it and precedes the summary it adds. A step's row is the window at the end of the step. `after_step` is the last step closed before the compaction. The generator, the ledger and their tests were changed; the exported site data was regenerated and the design, site and recorder checks re-run (all green).

**Lesson.** A replayed view that has only ever been tested against the data its author generated is untested. Cross-check a derived view against an independent source of the same quantity (here: replay vs the loop's own running count).
