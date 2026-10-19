# 2026-10-19 — EVAL_DESIGN.md corrections

**[reasoned]**

Two errors caught during U2 learning:

## 1. Floor condition sign reversed

**Was:** "If the agent 'violates' here, the rule is not doing anything."

**Problem:** For a prohibition canary, violating at floor *is* the expected outcome — the agent does the forbidden action because no rule was given, which is correct baseline behaviour. The warning sign is the *opposite*: the agent respects the rule at floor, meaning it already avoids this action by default (alignment prior, not the canary). A canary that fires even without being planted measures nothing.

**Fix:** "If the agent 'respects' here… the canary measures nothing."

## 2. length_matched: "long context degrades recall" mis-attributed

**Was:** "Separates 'compaction lost information' from 'long context degrades recall'."

**Problem:** Control is the long-context condition (full filler turns, no compaction). length_matched has the *same size* as treatment, not control. Saying "long context degrades recall" as the thing length_matched separates out makes it sound like length_matched is the long one.

**Fix:** Reframed as size vs content. length_matched changes only *size* (same token count as post-compaction context). Treatment changes both size *and* content (compaction may distort or drop the canary). If treatment fails and length_matched passes, the cause is content loss, not size.

No ADR required — these are wording corrections that clarify existing intent, not direction changes.
