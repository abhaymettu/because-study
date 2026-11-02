# How to submit this paper

No action has been taken. Nothing here has been uploaded, pushed, committed or submitted, and no arXiv or Zenodo record exists. This file is a checklist for the author.

## Before anything goes out

1. **Fill in the Haiku replication.** `HAIKUREPLICATION` appears twice in `because.tex`, as a comment and as a visible stub before the Deviations section. The stub is read for sign only. Replace it, delete the comment and rebuild. arXiv publishes source files, comments included.
2. **Make the repository public, which needs the author's explicit yes.** On 2 November 2026 `gh repo view` reports it as PRIVATE. The paper cites `https://github.com/abhaymettu/because` and the tags `prereg-study1`, `prereg-study2` and `prereg-study2b`, and no reader can check them until the repository is public.
3. **Commit `paper/` before the repository goes public.** The paper names `paper/counts.json` and `python -m paper.counts`, and both are untracked today.
4. **Read the whole paper under your own name.** An agent drafted it, and the wording is yours to accept.

## arXiv

- **Primary category:** cs.SE (Software Engineering). The objects under test are instruction files and a coding agent CLI.
- **Cross-lists:** cs.AI, cs.HC and cs.CL. cs.AI fits agent behavior, cs.HC fits how people write instructions, and cs.CL fits prompt wording. Drop any that a moderator or the author finds a stretch.
- **Endorsement may be needed.** arXiv's help page, read on 2 November 2026, says, "arXiv requires that users be endorsed before submitting their first paper to arXiv or a new category." Whether this account already qualifies shows up when the submission form opens. See `https://info.arxiv.org/help/endorsement.html`.
- **Author:** Abhay Mettu. The repository states no affiliation or email, and the paper gives none.
- **Title:** Because: preregistered randomized tests of what makes a coding agent follow its instructions
- **Comments:** 10 pages, 2 figures, 8 tables. Preregistered at git tags prereg-study1, prereg-study2 and prereg-study2b. Code and data: https://github.com/abhaymettu/because. Not peer reviewed.
- **License:** the author chooses on the form.

**Abstract** (1,359 characters, plain ASCII; arXiv's limit is 1,920 characters and its metadata fields take ASCII only):

> People write instruction files for coding agents on folk beliefs: give a reason, write MUST, put the important rule first, phrase a skill's description as a list of triggers. We tested these on Claude Code 2.1.303 with Sonnet 5.5 at medium effort in three preregistered randomized studies, with outcomes decided by code. Study 1 (1,000 runs, 7,072 observations on nine rules) crossed reason clauses with wording features. Its registered reading is inconclusive. The bar for calling a reason null was an upper bound under 5 points, and the real reason reached 5.7 (+0.2, 95% CI -5.2 to +5.7). The data exclude effects above about 6 points for a real reason on rules like these. A placebo reason is +1.1 (-1.2 to +3.5), real and placebo are equivalent within 5 points (TOST p = .040), the Langer analogue does not reproduce, and no wording factor survives Holm. Study 2 (598 runs) finds that a trigger-list description beats one short sentence while the description is in view (+17.6 points) and that an early name beats a late one at 300 skills (+51.3). We measured the CLI's listing rule with no model judgment. Study 2b (534 runs) finds that past the listing budget a short description beats a long trigger list by 29.8 points, and that a short description in trigger form beats it by 29.4 while costing under 10 points below the budget (+2.1, -2.5 to +6.7).

If the Haiku result changes the headline, change this abstract and the one in `because.tex` together.

**Upload set:** `because.tex`, `because.bbl`, `figures/study1-effects.pdf` and `figures/reversal.pdf`, keeping the `figures/` folder. arXiv uses a `.bbl` when one is present, and its name must match the main `.tex` file.

**Check arXiv's preview.** This PDF was built with tectonic, which uses the XeTeX engine. The source has no XeTeX-only packages, so arXiv's pdfLaTeX should accept it, but no pdfLaTeX exists on this machine and that compile has not been tested. Line breaks and the page count may shift there.

To rebuild here and keep the `.bbl`:

```
cd paper && /opt/homebrew/bin/tectonic --keep-intermediates because.tex
```

The filled-in Haiku paragraph has about six lines of room on page 10 before the paper reaches an eleventh page.

## Zenodo

Deposit the preprint after the repository is public, and only a version the author accepts, because a DOI is meant to be permanent.

| Field | Value |
|---|---|
| Resource type | Publication, preprint |
| Title | Because: preregistered randomized tests of what makes a coding agent follow its instructions |
| Creator | Mettu, Abhay (no affiliation or ORCID stated) |
| Description | The abstract above |
| Publication date | The day of deposit |
| Language | English |
| License | The repository's code and data are under MIT (`LICENSE`). Choose the preprint's license at deposit, and match it to arXiv's. |
| Keywords | coding agents; instruction files; CLAUDE.md; AGENTS.md; agent skills; preregistration; randomized experiment; instruction following |
| Related identifier | Is supplemented by `https://github.com/abhaymettu/because` |
| Related identifier | Is identical to the arXiv identifier, once one exists |
| Notes | Preprint, not peer reviewed. Frozen registrations: `PREREG.md`, `PREREG-STUDY2.md` and `PREREG-STUDY2B.md`, at tags `prereg-study1`, `prereg-study2` and `prereg-study2b`. The git history was rewritten once before public release, as Section 8 of the paper discloses, so tag hashes changed and the registration files' blob hashes did not. |

Files to deposit: `because.pdf`. A separate software record for a tagged release of the repository is optional.
