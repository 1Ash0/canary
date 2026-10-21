# LinkedIn launch kit (EXP-004 video)

Files (rendered by `node design/scripts/render-video.mjs --format portrait|square`, deterministic):
- `design/video/out/canary-portrait.mp4`: 1080x1350 (4:5), 31 s, H.264 + silent AAC. Post this one: 4:5 takes the most room in the mobile feed.
- `design/video/out/canary-square.mp4`: 1080x1080, for anywhere 4:5 is cropped.
- `design/video/out/canary-portrait.srt`: upload as captions (accessibility, and muted autoplay).
- `design/video/out/cover-portrait.png`: the last frame (the table), as the thumbnail.

Every number in the posts below is checked against `results/EXP-004/summary.json` by `scripts/check_claims.py`. The strategy notes are common practice, not measured facts; nothing here claims a reach or engagement number.

## The strategy in one paragraph
One idea per post, told as a surprise with a receipt: "each compaction loses a different fact, and the agent fails on exactly that one", backed by a video of a real recorded run and a 27-seed table. The first two lines must earn the "see more" click on their own; the video must make sense muted; the post ends on a question practitioners can answer from their own stack, because comments from builders are what carries a post to more builders. The link goes in the first comment, not the post. One post: anything more lives in the replies and the repository.

## The post (main)

My AI agent filed an invoice under the account code "overage".

The real code was in its context. Compaction cut it.

When an agent's context fills up, the harness has to make room. I wanted to know what it stops knowing, so I hid three facts in one history (a channel rule, a billing code, a deploy target), compacted it four different ways, and asked for each fact.

Each way of compacting lost a different fact, and the agent failed on exactly the one that was cut:
→ Keep the head and tail of the history: wrong account code in 27 of 27 runs.
→ Mask old tool output instead: right in all 27.
→ Drop the oldest turns: the early rule goes first.

27 seeds per cell, preregistered before the first call, recorded on a free model, every run replayable.

Which compaction does your agent use, and have you checked what it drops?

#AIagents #LLM #ContextEngineering #Evals

### Why it is written this way
- **Line 1 is the hook** (what shows before "see more"): a concrete, slightly absurd failure, not a claim about AI. Line 2 turns it into the finding.
- **Arrows, not a wall of text:** three results a reader can scan in two seconds; each is a number with its condition.
- **Credibility in one line** (seeds, preregistered, free model, replayable) instead of a methods section; the method goes in the first comment.
- **The question is answerable** by anyone who has built an agent, which invites comments from exactly the people you want.
- **No link in the post body** (link posts are commonly reported to be shown less; this is practice, not a measured fact here). It goes in the first comment.
- **Four hashtags**, all specific. No tagging people who are not involved.

### Alternative hooks (pick one before posting)
- "Context compaction did not make my agent forget everything. It made it forget exactly one thing, and I could predict which."
- "'Keep the head and the tail' is the most common way to trim an agent's context. It lost the middle fact 27 times out of 27."
- "I tested what an AI agent forgets when its context is compacted. The answer depends on where the fact sat."

## First comment (post it yourself within a minute)

How it was measured: three facts planted at turns 2, 9 and 16 of a scripted history; one request per fact, graded by the tool call the agent makes (no LLM judge); a "never told" condition gives the guessing rate; whether each fact survived is checked mechanically in the window the agent saw. Limits: one model, one budget, synthetic facts, one compaction. Code, recordings and the full write-up (MIT): https://github.com/1Ash0/canary

## Posting checklist
- Upload the 4:5 video natively, attach the .srt, set the cover to the table frame.
- Post on a weekday morning in the time zone where most of your network is; stay available for the first hour to reply to every comment with substance (a fact, a question back), not "thanks!".
- Pin the first comment.
- Do not edit the post in the first hour (edits are commonly reported to reset distribution; practice, not measured here).
- Reshare to relevant groups or communities only with a line of your own, not a bare share.

## Replies ready for the likely comments
- **"Isn't this just lost in the middle?"** Close cousin. Lost in the Middle is about attention inside a long context; this is about what a compaction policy deletes before the model sees anything. Here "keep head and tail" removes the middle outright, so the agent cannot recover it at all.
- **"Which model?"** Mistral's ministral-14b on the free tier for this experiment; earlier experiments add gpt-oss-20b, and the summary policy's quality depends a lot on which model writes the summary.
- **"What about summarising?"** In this run the model summary kept the code and the deploy target every time and the channel rule in 23 of 27, and the agent failed exactly on the 4 it dropped.
- **"How do I test my own policy?"** The repo runs offline from recordings; adding a policy is one class, and `ctxcheck run` gives you the same table.
- **"n=27 is small."** Agreed, and every rate in the repo carries its 95% interval; the large effects here (27 of 27 against 0 of 27) are not close calls, the small ones are labelled inconclusive.

## One post, so make it complete
There is no follow-up, so this post and its first comment carry everything:
- **Alternative hooks are for choosing, not testing:** pick the one you like best before posting; there is no second post to try another.
- **The first comment is the whole methods section** and the only link; pin it.
- **Your replies are the follow-ups.** The findings you would otherwise post later go into answers when they fit: the two summarisers (one model's summary kept the rule and the other's did not), masking losing the rule once the request pushed it over budget, and the blind audit where the machine's check was right where you disagreed. Each makes a reply worth reading, and replies keep the post alive.
- **Make the repo the place people continue:** the README already leads with the findings; anyone who wants more goes there, not to a next post.

## What to watch after posting
Comments from practitioners, profile visits, repository stars and clones in the following days. Reactions alone say little; a comment that asks a technical question is the signal that the post reached the right people.
