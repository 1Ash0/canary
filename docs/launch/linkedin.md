# LinkedIn launch kit (EXP-004 video)

Files (rendered by `node design/scripts/render-video.mjs --format portrait|square`, deterministic):
- `design/video/out/canary-portrait.mp4`: 1080x1350 (4:5), 31 s, H.264 + silent AAC. Post this one: 4:5 takes the most room in the mobile feed.
- `design/video/out/canary-square.mp4`: 1080x1080, for anywhere 4:5 is cropped.
- `design/video/out/canary-portrait.srt` (and `-square.srt`): upload as captions (accessibility, and muted autoplay).
- `design/video/out/cover-portrait.png`: the last frame (the table), as the thumbnail.

Everything in the video is a recorded episode (EXP-004, seed 19) and the EXP-004 table; every number in the post below is checked against `results/EXP-004/summary.json` by `scripts/check_claims.py`.

## Post

When an AI agent's context fills up, the harness compacts it. What does the agent stop knowing, and does it notice?

I hid three facts in one agent's history (a channel rule, a billing code, a deploy target), compacted the context four different ways, and asked for each fact. 27 seeds per cell, preregistered before the first call, recorded on a free model.

Each way of compacting lost a different fact, and the agent failed on exactly the one that was cut. Keeping the head and the tail of the history got the account code wrong in 27 of 27 runs; masking old tool output got it right in all 27. Asked for a code it no longer had, one run filed the invoice under "overage".

Which compaction does your agent stack use, and have you checked what it drops?

#AIagents #LLM #ContextEngineering #Evals

## First comment (post it yourself, right after)

How it was measured: three facts planted at turns 2, 9 and 16 of a scripted history; one request per fact, graded by the tool call the agent makes; a "never told" condition gives the guessing rate; survival of each fact is checked mechanically in the window the agent saw. Limits: one model, one budget, synthetic facts, one compaction. Code, recordings and the full write-up: (repository link once it is public).

## Notes for posting
- Upload the video natively (not a link): LinkedIn plays native video inline, muted, with captions.
- Attach the .srt so the captions are real subtitles, not only burned in.
- The post asks the question the video answers; do not paste the video's text into the post.
- Reply to early comments in the first hour; that is when the post is shown to the most people.
