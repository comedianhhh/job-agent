---
name: case-study
description: Turn one project or job from career/facts.md into a portfolio case study for engineers — problem, constraints, decisions with the options rejected, what broke, measured results, and what the user would change — plus the three follow-up questions it invites. Use when the user types /case-study, asks for a case study, project write-up or portfolio page about their work, or wants a Featured item for LinkedIn. Resume bullets are /great-resume.
---

# /case-study — The project told so the reader asks about it

A resume says what was built; a case study shows how the user thinks: what the problem was, which options they weighed, what broke and what they did about it. A hiring manager who reads one walks into the interview with questions about the user's real work. So it must hold up when they ask: every claim traces to `career/facts.md`, every number has its source.

## Files

| File | Role |
|---|---|
| `career/facts.md` | Truth. `TODO:` items never go out. ⛔ / do-not-use lines stay out. |
| `career/stories.md` | Failures, trade-offs and decisions already told as stories. |
| `career/blocks.md` | The resume version of the same work: the case study may not contradict it. |
| The project's repo, README, results files | Evidence for numbers and decisions, cited by path. |

## Workflow

1. Pick the project with the user and name the reader (the role they're applying for). One case study per project.
2. Gather: the `facts.md` section, related stories, and the repo's README / results files. List what's missing as ≤ 5 questions, and draft the rest meanwhile; a missing piece is left out, never filled in.
3. Write it with the structure below, 600–1,000 words, in the user's voice (first person, plain, short sentences).
4. Check: run `python scripts/check-trace.py --facts career/facts.md <file>` on the draft; fix every untraced number by citing it in `facts.md` (with the user's OK) or removing it.
5. Save to `career/case-studies/<slug>.md` unless the user names their site; on a site, follow that repo's own layout.

## Structure

1. **Overview** — one paragraph: what it is, for whom, the user's role, the stack, and its status (shipped / internal / personal, with dates).
2. **Problem** — what was wrong or missing, for whom, and why it mattered. A picture the reader can see, no jargon in the first sentence.
3. **Constraints** — the limits that shaped the design (latency budget, cost, team size, platform, deadline).
4. **Decisions** — 2–4 decisions, each with the option chosen, the options rejected, and why. This is the core of the piece.
5. **What broke** — the hardest bug or the wrong first approach, how it was found, and the fix. Real failures make the strongest section.
6. **Results** — only what was measured or is public, each with its source (dashboard, test run, store page, merged PR). An estimate says "about" and "estimate". No result → say what shipped and leave it there.
7. **What I'd change** — the honest hindsight, stated as a design the user would build now, never as something that was built.
8. **Links** — repo, demo, store page, PRs.

Then, outside the case study: **three follow-up questions** a reader is likely to ask, each with the `facts.md` line that answers it. `/interview` can drill them.

## Boundaries

- Employer work: no internal code, private numbers, customer names or unreleased plans unless `facts.md` marks them public. Team work stays team work; the user's part is named.
- Personal projects say personal; AI-assisted work follows the user's own rule in `rules.md`.
- No invented metric, quote, user count or screenshot. A diagram is fine if it shows the real design.
- Resume bullets → `/great-resume`. Interview drilling → `/interview`. LinkedIn Featured caption → `/linkedin-profile`.

## Deliverable order

1. the case study (Markdown, saved); 2. the trace check result; 3. three follow-up questions with their sources; 4. a one-line Featured caption; 5. open questions for the user.
