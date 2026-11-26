---
name: linkedin-profile
description: Rewrite the user's LinkedIn profile from career/facts.md — headline, About, experience entries, skills order, Featured picks, and Open-to-Work settings — as paste-ready text with character counts, kept in sync with the resume. Use when the user types /linkedin-profile, asks to optimise or rewrite their LinkedIn profile, headline, About section or Featured section, or wants recruiters to find them. Connection notes and InMails are /great-resume.
---

# /linkedin-profile — A profile recruiters find and can verify

A resume goes to one employer; the profile is read by every recruiter who searches. It can say more than the resume and sound more like a person, but it is public and permanent, so it may never say more than `career/facts.md` does. Every line traces there; titles and dates match the resume exactly, because a recruiter checks one against the other.

## Files

| File | Role |
|---|---|
| `career/facts.md` | Truth. `TODO:` items never go out. |
| `career/blocks.md` | Finished bullets: the experience entries reuse them. |
| `career/targets.yaml` | Target roles and locations: the keyword set comes from these. |
| `career/rules.md` | The review standard. |
| `career/*/03-Job-Description.md` | Saved postings: count which skills and titles recur. |

## Workflow

1. Ask for the current profile text (or a screenshot) if it isn't in the workspace; work from it, not from memory.
2. Build the keyword set: target titles from `targets.yaml`, then the skills that recur across the saved postings. A keyword goes on the profile only if `facts.md` backs it.
3. Write each section below, in English, with its character count.
4. Sync check: every title, company and date on the profile equals the resume's; list each mismatch with the fix.
5. Audit: for each strong claim, the `facts.md` line it comes from. Anything without one is cut, not softened.

## Sections

- **Headline** (≤ 220 chars; only ~60 show in search results, so the target title comes first). `Target title | 2–3 searchable skills | one verifiable anchor` — the anchor is a real result or a named, checkable fact (a shipped product, an accelerator, a merged PR), never an adjective. Never "open to work", "aspiring", or a slogan.
- **About** (≤ 2,600 chars; aim for 1,200–1,800). The first ~300 characters show before "see more": open with what the user builds and the one strongest real result. Then 2–3 short paragraphs (what they own, how they work, what they want next), a plain skills line for search, and one line on how to reach them. First person, conversational, no taglines, no "passionate", no arrows or emoji bullets.
- **Experience**: title and dates exactly as on the resume; 2–4 bullets per role from `blocks.md`, plus one line of context the resume had no room for. Team results are written as team results. Personal projects go under Projects, never inside an employer.
- **Skills**: order by how often the target postings ask for it; the top 3 are the ones the user can defend in a technical interview. A skill the user is still learning is listed only if `rules.md` allows that tier.
- **Featured** (3–5 items): only real, linkable artifacts — the shipped app's store page, public repos with a README, merged PRs, posts the user wrote, a portfolio case study (`/case-study`). Each gets a one-line caption that says what it is and what the user did.
- **Open to Work**: recommend "recruiters only" with the target titles, locations and work types from `targets.yaml`. Whether to show the public frame is the user's call; say what each option shows.

## Boundaries

- Nothing the resume couldn't defend: no number, title, employer, scale or domain that isn't in `facts.md`. Qualitative beats invented.
- Work authorization, salary and visa never go on the profile.
- This skill writes text. Editing the live profile, posting, and changing visibility are done by the user (or with their go-ahead per change), since they are public.
- Connection notes, InMails and cold email → `/great-resume`. Files → `/make-resume`.

## Deliverable order

1. headline (2 options: safe and sharper, each with its count); 2. About (with count, the first 300 chars marked); 3. experience entries; 4. skills top 10 in order + the top 3; 5. Featured list with captions and links; 6. Open-to-Work settings; 7. resume mismatches; 8. claims audit.
