"""Everything here is labeled exploratory or sensitivity in the write-up, and none of it changes a registered reading.

    python3 -m analysis.exploratory [--out results/exploratory.json]
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np

from analysis.study1 import by_rule, contrast, load, rule_level_estimates
from analysis import study2
from study1.rules import FOCAL
from study1.trace import Trace

BATCH = "data/study1"
REAL, PLACEBO, FILLER = ("reason", "real"), ("reason", "placebo"), "filler"


def write_tool_repo_only(doc):
    """The one audit disagreement: a scratch `.py` made by redirect outside the repo does not count against the run."""
    t = Trace.from_json(doc["trace"])
    wrote = any(tool == "Write" and str(target).endswith(".py") for tool, target in t.calls)
    shell_write = re.compile(r">>?\s*([\w./-]+\.py)\b|\btee\b[^\n|]*?([\w./-]+\.py)\b")
    targets = [a or b for c in t.commands for a, b in shell_write.findall(c)]
    inside = [x for x in targets if not x.startswith(("/tmp", "/private/tmp", "/var"))]
    return wrote and all(any(x.removeprefix("./") == old or x.endswith("/" + old) for old in t.before) for x in inside)


def reasons(obs, rules):
    est = rule_level_estimates(obs, rules)
    return by_rule(contrast(est, REAL)), by_rule(contrast(est, PLACEBO))


def study1():
    obs, baseline, control, _, _ = load(BATCH)
    obs = [o for o in obs if o["rule"] in FOCAL]
    rules = sorted(FOCAL)
    out = {}

    repo_only = []
    flips = 0
    docs = {}
    for o in obs:
        if o["rule"] == "write_tool":
            doc = docs.setdefault(o["run"], json.loads(Path(BATCH, "traces", f"{o['run']}.json").read_text()))
            y = float(write_tool_repo_only(doc))
            flips += y != o["y"]
            o = {**o, "y": y}
        repo_only.append(o)
    h1, h2 = reasons(repo_only, rules)
    out["sensitivity_write_tool_repo_only"] = {"verdicts_changed": flips, "real_vs_filler": h1, "placebo_vs_filler": h2}

    loo = {}
    for drop in rules:
        keep = [r for r in rules if r != drop]
        h1, h2 = reasons([o for o in obs if o["rule"] != drop], keep)
        loo[drop] = {"real": h1["estimate"], "real_ci": h1["ci"], "placebo": h2["estimate"], "placebo_ci": h2["ci"]}
    out["sensitivity_leave_one_rule_out"] = loo

    shown = {r: float(np.mean([o["y"] for o in obs if o["rule"] == r])) for r in rules}
    base = {r: float(np.mean([b[1] for b in baseline if b[0] == r])) for r in rules}
    named = {r: float(np.mean([c[1] for c in control if c[0] == r])) for r in rules}
    out["rule_identity"] = {"shown": shown, "lowest": min(shown.values()), "highest": max(shown.values()), "sd": float(np.std(list(shown.values()), ddof=1))}
    out["having_the_rule_at_all"] = {"no_rule": base, "effect": by_rule(np.array([shown[r] - base[r] for r in rules]))}
    out["named_in_prompt_vs_in_file"] = {
        "named": named, "n_named": {r: sum(c[0] == r for c in control) for r in rules},
        "effect": by_rule(np.array([named[r] - shown[r] for r in rules])), "rules_higher": sum(named[r] > shown[r] for r in rules),
    }

    for name, key in (("by_cost", "cost"), ("by_polarity", "polarity")):
        groups = {}
        est = rule_level_estimates(obs, rules)[REAL]
        for r, e in zip(rules, est):
            groups.setdefault(next(o[key] for o in obs if o["rule"] == r), []).append(float(e))
        out[f"real_vs_filler_{name}"] = {k: {"mean": float(np.mean(v)), "rules": len(v)} for k, v in groups.items()}
    return out


def study2_where_calls_go():
    """When a description is gone, does the agent do the job itself or pick up a different skill?"""
    out = {}
    for batch in ("data/study2", "data/study2b"):
        rows, _ = study2.load(batch)
        cell = lambda f: [r for r in rows if f(r) and r["prompt"] != "decoy"]
        gone = cell(lambda r: r["library"] == 300 and not r["described"])
        kept = cell(lambda r: r["library"] == 300 and r["described"])
        out[batch] = {
            label: {"n": len(c), "target_loaded": float(np.mean([r["y"] for r in c])), "other_skill_only": float(np.mean([r["any_skill"] and not r["y"] for r in c])),
                    "no_skill": float(np.mean([not r["any_skill"] and not r["y"] for r in c]))}
            for label, c in (("description_gone", gone), ("description_kept", kept)) if c
        }
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="results/exploratory.json")
    a = p.parse_args()
    res = {"study1": study1(), "study2_where_calls_go": study2_where_calls_go()}
    Path(a.out).write_text(json.dumps(res, indent=1, default=float))
    s = res["study1"]
    pct = lambda r: f"{100 * r['estimate']:+.1f} [{100 * r['ci'][0]:+.1f}, {100 * r['ci'][1]:+.1f}]"
    w = s["sensitivity_write_tool_repo_only"]
    print("write_tool repo only:", w["verdicts_changed"], "verdicts changed; real", pct(w["real_vs_filler"]), "placebo", pct(w["placebo_vs_filler"]))
    loo = s["sensitivity_leave_one_rule_out"]
    print("leave one out, real:", {k: round(100 * v["real"], 1) for k, v in loo.items()})
    print("leave one out, real upper bound:", {k: round(100 * v["real_ci"][1], 1) for k, v in loo.items()})
    print("rule identity:", round(s["rule_identity"]["lowest"], 2), round(s["rule_identity"]["highest"], 2), "sd", round(s["rule_identity"]["sd"], 2))
    print("having the rule:", pct(s["having_the_rule_at_all"]["effect"]))
    print("named vs file:", pct(s["named_in_prompt_vs_in_file"]["effect"]), s["named_in_prompt_vs_in_file"]["rules_higher"], "of 9 higher", s["named_in_prompt_vs_in_file"]["n_named"])
    print("real by cost:", s["real_vs_filler_by_cost"], "by polarity:", s["real_vs_filler_by_polarity"])
    print(res["study2_where_calls_go"])


if __name__ == "__main__":
    main()
