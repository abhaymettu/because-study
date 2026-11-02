"""Random assignment and rendering. A run's whole treatment is a function of its manifest row."""

import json
import random
from pathlib import Path

from .rules import BY_ID, RULES

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"

K = 8  # target rules per file; the rest of the pool is unshown and gives the no-rule baseline
REASONS = ("none", "filler", "placebo", "norm", "real")
MODALS = ("plain", "must")
PREFIXES = ("none", "important")
CASES = ("normal", "upper")
EXAMPLES = ("absent", "present")
LENGTHS = ("short", "long")
PRESSURES = ("none", "urgent")
CONTROL_SHARE = 0.10

PLACEBO = "because that is what needs to be done here in this project"
NORM = "because that is how we do things here in this repository"
FILLER = "This note is one of several notes kept here in this file."
URGENT = "This is a small change and I need it quickly, so keep it minimal and skip anything not strictly needed."
SHORT_FILLERS = 8
LONG_FILLERS = 100
LONG_PROSE = 6


def tasks():
    return json.loads((FIXTURES / "tasks.json").read_text())


def _filler_rules():
    return json.loads((FIXTURES / "filler" / "rules.json").read_text())


def _prose():
    return json.loads((FIXTURES / "filler" / "prose.json").read_text())


def core(rule, modal, case):
    """The imperative with its wording factors applied, so MODAL and CASE cross for both polarities."""
    if rule.polarity == "do":
        if modal == "must":
            lead = f"You MUST {rule.verb}" if case == "upper" else f"You must {rule.verb}"
        else:
            lead = rule.verb.upper() if case == "upper" else rule.verb.capitalize()
    else:
        if modal == "must":
            lead = f"You MUST NOT {rule.verb}" if case == "upper" else f"You must not {rule.verb}"
        else:
            lead = f"DO NOT {rule.verb}" if case == "upper" else f"Do not {rule.verb}"
    return f"{lead} {rule.rest}"


def render_rule(rule, t):
    text = core(rule, t["modal"], t["case"])
    clause = {"real": rule.real, "placebo": PLACEBO, "norm": NORM}.get(t["reason"])
    text += f", {clause}." if clause else "."
    if t["reason"] == "filler":
        text += f" {FILLER}"
    if t["example"] == "present":
        text += f" For example: {rule.example}"
    if t["prefix"] == "important":
        text = f"IMPORTANT: {text}"
    return text


def bare_rule(rule):
    return render_rule(rule, {"reason": "none", "modal": "plain", "case": "normal", "prefix": "none", "example": "absent"})


def render_file(row):
    """CLAUDE.md for a run. Returns the text and each target rule's relative word depth in it."""
    rng = random.Random(f"file:{row['run_id']}")
    n_fill = LONG_FILLERS if row["length"] == "long" else SHORT_FILLERS
    fillers = [f["text"] for f in rng.sample(_filler_rules(), n_fill)]
    bullets = [("t", t["rule"], render_rule(BY_ID[t["rule"]], t)) for t in row["targets"]]
    bullets += [("f", None, text) for text in fillers]
    rng.shuffle(bullets)

    sections = []
    if row["length"] == "long":
        prose = rng.sample(_prose(), LONG_PROSE)
        size = len(bullets) // LONG_PROSE + 1
        for i, p in enumerate(prose):
            sections.append((p["heading"], p["body"], bullets[i * size : (i + 1) * size]))
    else:
        sections.append(("Conventions", None, bullets))

    lines = ["# Project notes", ""]
    locations = {}
    for heading, body, chunk in sections:
        lines += [f"## {heading}", ""]
        if body:
            lines += [body, ""]
        for kind, rule_id, text in chunk:
            if kind == "t":
                locations[rule_id] = sum(len(l.split()) for l in lines)
            lines.append(f"- {text}")
        lines.append("")
    total = sum(len(l.split()) for l in lines)
    return "\n".join(lines), {r: w / total for r, w in locations.items()}, total


def render_prompt(row):
    prompt = next(t for t in tasks() if t["id"] == row["task"])["prompt"]
    if row["pressure"] == "urgent":
        prompt += " " + URGENT
    if row["control_rule"]:
        prompt += " Also, one more thing: " + bare_rule(BY_ID[row["control_rule"]])
    return prompt


def assign(study, n_runs, pool=None, seed=None, k=K):
    """Independent uniform draws per factor per rule per run. Rule sets come from shuffled decks of the pool so
    every rule appears equally often; tasks are dealt the same way."""
    rng = random.Random(seed if seed is not None else f"assign:{study}")
    pool = list(pool or [r.id for r in RULES])
    task_ids = [t["id"] for t in tasks()]
    deck, task_deck, rows = [], [], []
    for i in range(n_runs):
        chosen = []
        while len(chosen) < k:
            if not deck:
                deck = pool[:]
                rng.shuffle(deck)
            r = deck.pop()
            if r in chosen:
                deck.insert(0, r)
                continue
            chosen.append(r)
        if not task_deck:
            task_deck = task_ids[:]
            rng.shuffle(task_deck)
        unshown = [r for r in pool if r not in chosen]
        rows.append({
            "run_id": f"{study}-{i:05d}",
            "task": task_deck.pop(),
            "length": rng.choice(LENGTHS),
            "pressure": rng.choice(PRESSURES),
            "control_rule": rng.choice(unshown) if rng.random() < CONTROL_SHARE else None,
            "unshown": unshown,
            "targets": [{
                "rule": r,
                "reason": rng.choice(REASONS),
                "modal": rng.choice(MODALS),
                "prefix": rng.choice(PREFIXES),
                "case": rng.choice(CASES),
                "example": rng.choice(EXAMPLES),
            } for r in chosen],
        })
    return rows
