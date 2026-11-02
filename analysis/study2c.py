"""Study 2c analysis: python3 -m analysis.study2c data/study2c [--out results/study2c.json]"""

import argparse
import json
from pathlib import Path

import numpy as np

from analysis.study1 import by_rule, holm
from analysis.study2 import contrast, load, per_target
from study2.design import BUDGET_WORDINGS, FOLLOWUP_PROMPTS


def reading(family, reach_when_raised):
    """The registered decision table, in code so nobody applies it by hand."""
    if reach_when_raised < 0.95:
        return "the manipulation failed; nothing is read"
    e1, e3, e4 = (family[k] for k in ("E1_trigger_raised_vs_default", "E3_trigger_vs_minimal_raised", "E4_interaction"))
    sig = lambda r: r["p_holm"] < 0.05 and r["estimate"] > 0
    if sig(e1) and sig(e4) and e3["ci"][0] > -0.10:
        return "the budget causes the reversal: with the budget raised a long trigger list recovers and is within 10 points of a short description or above it"
    if sig(e1):
        return "raising the budget helps a long trigger list, and the reversal is not shown to close"
    return "inconclusive"


def analyze(batch):
    rows, counts = load(batch)
    raised = lambda r: r["budget"] is not None
    default = lambda r: r["budget"] is None
    is_w = lambda w: (lambda r: r["wording"] == w)
    trigger, minimal = is_w("trigger"), is_w("minimal")
    at_raised, at_default = per_target(rows, raised, trigger, minimal), per_target(rows, default, trigger, minimal)
    family = {
        "E1_trigger_raised_vs_default": contrast(rows, trigger, raised, default),
        "E2_minimal_raised_vs_default": contrast(rows, minimal, raised, default),
        "E3_trigger_vs_minimal_raised": contrast(rows, raised, trigger, minimal),
        "E4_interaction": by_rule(np.array([at_raised[s] - at_default[s] for s in sorted(at_raised.keys() & at_default.keys())])),
    }
    for name, adj in zip(family, holm([family[n]["p"] for n in family])):
        family[name]["p_holm"] = adj
    secondary = {"minimal_vs_trigger_default": contrast(rows, default, minimal, trigger)}
    for prompt in FOLLOWUP_PROMPTS:
        secondary[f"E1_{prompt}"] = contrast(rows, lambda r, p=prompt: r["prompt"] == p and trigger(r), raised, default)
    grid = {}
    for name, arm in (("default", default), ("raised", raised)):
        for w in BUDGET_WORDINGS:
            cell = [r for r in rows if arm(r) and r["wording"] == w]
            grid[f"{name}/{w}"] = {
                "recall": float(np.mean([r["y"] for r in cell])), "n": len(cell), "description_reached_model": float(np.mean([r["described"] for r in cell])),
                "other_skill_only": float(np.mean([r["any_skill"] and not r["y"] for r in cell])), "no_skill": float(np.mean([not r["any_skill"] and not r["y"] for r in cell])),
                "cost_per_run": float(np.mean([r["cost"] for r in cell])), "turns": float(np.mean([r["turns"] for r in cell])),
            }
    reach = float(np.mean([r["described"] for r in rows if raised(r)]))
    return {"runs": counts, "family": family, "secondary": secondary, "grid": grid, "description_reached_model_when_raised": reach, "reading": reading(family, reach),
            "cost": {"api_equivalent_usd": float(sum(r["cost"] for r in rows)), "turns": float(np.mean([r["turns"] for r in rows]))}}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("batch")
    p.add_argument("--out")
    a = p.parse_args()
    res = analyze(a.batch)
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, default=float))
    print(res["runs"])
    for name, r in res["family"].items():
        print(f"{name:40}{100 * r['estimate']:+6.1f} pts [{100 * r['ci'][0]:+5.1f}, {100 * r['ci'][1]:+5.1f}] holm={r['p_holm']:.3f}")
    print(res["grid"])
    print("reading:", res["reading"])


if __name__ == "__main__":
    main()
