# 2026-10-20 — The ConstraintRot headline figure is 30%, not 37%

*Drafted by Claude Code during the M1 status check; Asmit to review.*

**What happened.** PRIOR_ART, ROADMAP (M1 exit 2) and the committed landing page (`e6d8d84`) used "37% pooled". PRIOR_ART itself flagged it as unverified against the PDF.

**What the primary source says** (arXiv 2606.22528v2 PDF, single author Shiyang Chen, read via PDF text extraction):
- Abstract: "compaction raises violation from 0% to 30% (up to 59%); when the constraint survives the summary violation is 0%, when dropped 38%."
- Results: "a single compaction step raises the pooled violation rate to 30% (up to 59% on DeepSeek-V4 and Kimi-K2.5)."
- The only "37" in the text is one cell of Table 2 (`attack_volume`, GPT-5.4m), unrelated to the headline.

**Also wrong on the committed page.** It attributed the finding to "Karpinska & Iyyer, 2022". That's a different paper. The authors are as above.

**Fixed.** PRIOR_ART and ROADMAP now cite 30%. The landing page is being replaced (design D8), and the new page cites the paper without the number until the README hero uses the verified one.

**Lesson.** A number tagged `[reproduced by third party]` still needs the primary passage quoted in the notebook before it ships. The tag says who measured it; it does not say we checked it.
