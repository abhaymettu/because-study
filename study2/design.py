"""Study 2: does a skill's description decide whether it loads, and when can it no longer matter?

Claude Code lists skills alphabetically within a character budget. Past the budget a skill keeps only its name, so the
target's place in the alphabet is randomized along with its wording.
"""

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGETS = json.loads((ROOT / "fixtures" / "skills.json").read_text())
BY_STEM = {t["stem"]: t for t in TARGETS}
DISTRACTORS = json.loads((ROOT / "fixtures" / "distractors.json").read_text())

WORDINGS = ("minimal", "padded", "trigger", "trigger_not", "directive")
LIBRARIES = (0, 0, 50, 50, 300, 300, 300, 300)  # half of runs go to the size where the budget binds
NAME_PREFIXES = ("aa", "zz")
PROMPTS = ("keyword", "generic", "indirect", "decoy")
PADDING = "This skill is one of several kept in this project's skill folder for general use by anyone working here."
REPO_README = "# Workbench\n\nExports and small files people drop here when they need a second pair of eyes.\n"


def description(target, wording):
    if wording == "minimal":
        return f"{target['job']}."
    if wording == "padded":
        return f"{target['job']}. {PADDING}"
    if wording == "trigger":
        return f"Use when {target['when']}."
    if wording == "trigger_not":
        return f"Use when {target['when']}. Not for {target['not_for']}."
    return f"ALWAYS invoke this skill when {target['when']}. You MUST use it before doing this kind of work yourself."


def target_name(row):
    """Unique per run: the CLI ranks skills by past invocations on the account, so a reused name would carry usage
    from earlier runs into this one's listing."""
    return f"{row['name_prefix']}-{row['stem']}-{row['run_id'].rsplit('-', 1)[1]}"


def _skill_file(name, desc, body):
    return f"---\nname: {name}\ndescription: {json.dumps(desc)}\n---\n\n{body}\n"


def plan(row):
    """Everything a run needs: files to place in a fresh repo, the prompt, the skill the outcome looks for."""
    target = BY_STEM[row["stem"]]
    files = {"README.md": REPO_README}
    # Every target's data sits in the workbench, so the files present do not point at the skill in play.
    for t in TARGETS:
        files[t["file"]] = t["content"]
        if "file2" in t:
            files[t["file2"]] = t["content2"]
    skills = {}
    name = target_name(row)
    skills[name] = _skill_file(name, description(target, row["wording"]), f"Follow these steps.\n\n{target['steps']}")
    for d in row["distractors"]:
        skills[d] = _skill_file(d, next(x["description"] for x in DISTRACTORS if x["name"] == d), "Follow the usual procedure for this kind of work.")
    return {"files": files, "skills": skills, "prompt": target[row["prompt_type"]], "target": name, "probe": f"- {name}: "}


def assign(study, n_runs):
    rng = random.Random(f"assign:{study}")
    stems = [t["stem"] for t in TARGETS]
    names = sorted(d["name"] for d in DISTRACTORS)
    deck, rows = [], []
    for i in range(n_runs):
        if not deck:
            deck = stems[:]
            rng.shuffle(deck)
        library = rng.choice(LIBRARIES)
        rows.append({
            "run_id": f"{study}-{i:05d}",
            "study": 2,
            "stem": deck.pop(),
            "wording": rng.choice(WORDINGS),
            "name_prefix": rng.choice(NAME_PREFIXES),
            "library": library,
            "prompt_type": rng.choice(PROMPTS),
            "distractors": rng.sample(names, library),
        })
    return rows
