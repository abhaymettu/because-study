# How to submit this paper

A checklist for the author, for arXiv and then Zenodo.

## Before anything goes out

1. **Make the repository public at or before submission.** The paper cites `https://github.com/abhaymettu/because`, the tags `prereg-study1`, `prereg-study2`, `prereg-study2b` and `prereg-study2c`, and in Section 9 a repository creation time and a GitHub Actions run. A reader can check those only once the repository is public.
2. **Rerun what the paper names.** `make test` and `make replay` should pass, and `make reproduce` should leave `results/` unchanged in `git status`.
3. **Read the final PDF page by page**.

## arXiv

- **Primary category:** cs.SE (Software Engineering). The objects under test are instruction files and a coding agent CLI.
- **Cross-lists:** cs.AI, cs.HC and cs.CL. cs.AI fits agent behavior, cs.HC fits how people write instructions, and cs.CL fits prompt wording. Drop any that a moderator or the author finds a stretch.
- **Endorsement may be needed.** arXiv's help page, read on 2 November 2026, says, "arXiv requires that users be endorsed before submitting their first paper to arXiv or a new category." Whether the submitting account qualifies shows up when the submission form opens. See `https://info.arxiv.org/help/endorsement.html`.
- **Author:** Abhay Mettu. The repository states no affiliation or email, and the paper gives none.
- **Title:** Because: preregistered randomized tests of what makes a coding agent follow its instructions
- **Comments:** 12 pages, 2 figures, 10 tables. Preregistered at git tags prereg-study1, prereg-study2, prereg-study2b and prereg-study2c. Code and data: https://github.com/abhaymettu/because. Not peer reviewed.
- **License:** the author chooses on the form.

**Abstract** (1,819 characters, plain ASCII; arXiv's limit is 1,920 characters and its metadata fields take ASCII only):

> People write instruction files for coding agents on folk beliefs: give a reason, write MUST, put the important rule first, phrase a skill's description as a list of triggers. We tested these on Claude Code 2.1.303 with Sonnet 5.5 at medium effort in four preregistered randomized studies, with outcomes decided by code. Study 1 (1,000 runs, 7,072 observations on nine rules) crossed reason clauses with wording features. Its registered reading is inconclusive. The bar for calling a reason null was an upper bound under 5 points, and the real reason reached 5.7 (+0.2, 95% CI -5.2 to +5.7). That interval is for the average across these nine rules against filler, and the prediction interval for a new rule runs from -11.6 to +11.9. A placebo reason is +1.1 (-1.2 to +3.5), the Langer analogue does not reproduce, and no wording factor's average survives Holm. Study 2 (598 runs) finds that a trigger list beats one short sentence with the description in view (+17.6 points) and that an early name beats a late one at 300 skills (+51.3). The vendor documents a character budget on the skill listing, and we measured the exact rule behind it with no model judgment. Study 2b (534 runs) tests never-used skills that sort after that budget is spent. There a short description beats a long trigger list by 29.8 points, and in trigger form by 29.4, and at 50 skills, near the ceiling, that form costs under 10 points (+2.1, -2.5 to +6.7). Study 2c (384 runs) changes only the budget. Raising it until every description fits lifts the trigger list by 69.8 points (+53.7 to +85.8) and puts it 16.7 above the short description (+0.7 to +32.7), with an interaction of +40.6 (+22.7 to +58.6), so raising the budget directly reverses the reversal. The wording of a skill's description matters through whether it reaches the model.

If the Haiku result changes the headline, change this abstract and the one in `because.tex` together.

**Upload set:** `because.tex`, `because.bbl`, `figures/study1-effects.pdf` and `figures/reversal.pdf`, keeping the `figures/` folder. arXiv uses a `.bbl` when one is present, and its name must match the main `.tex` file.

**Check arXiv's preview.** This PDF was built with tectonic, which uses the XeTeX engine. The source has no XeTeX-only packages, so arXiv's pdfLaTeX should accept it, but that compile has not been tested. Line breaks and the page count may shift there.

To rebuild and keep the `.bbl`:

```
cd paper && tectonic -k because.tex
```

The figures are PDFs made from SVGs in a browser, forced to the light scheme. `python3 -m paper.figures.reversal` regenerates `figures/reversal.svg` from the results, and `figures/study1-effects.pdf` comes from `docs/figures/study1-effects.svg`.

The filled-in Haiku paragraph has about five lines of room on page 12 before the paper reaches a thirteenth page.

## Zenodo

Deposit the preprint after the repository is public, and only a version the author accepts, because a DOI is meant to be permanent.

- **Resource type:** Publication, preprint
- **Title:** Because: preregistered randomized tests of what makes a coding agent follow its instructions
- **Creator:** Mettu, Abhay (no affiliation or ORCID stated)
- **Description:** The abstract above
- **Publication date:** The day of deposit
- **Language:** English
- **License:** The repository's code and data are under MIT (`LICENSE`). Choose the preprint's license at deposit, and match it to arXiv's.
- **Keywords:** coding agents; instruction files; CLAUDE.md; AGENTS.md; agent skills; preregistration; randomized experiment; instruction following
- **Related identifier:** Is supplemented by `https://github.com/abhaymettu/because`
- **Related identifier:** Is identical to the arXiv identifier, once one exists
- **Notes:** Preprint, not peer reviewed. Frozen registrations: `PREREG.md`, `PREREG-STUDY2.md`, `PREREG-STUDY2B.md` and `PREREG-STUDY2C.md`, at the tags above. The git history was rewritten once before public release, as Section 9 of the paper discloses, so the first three tags' hashes changed and the registration files' blob hashes did not.

Files to deposit: `because.pdf`. A separate software record for a tagged release of the repository is optional.
