"""Study 2b analysis: python3 -m analysis.study2b data/study2b [--out results/study2b.json]"""

import argparse
import json
from pathlib import Path

import numpy as np

from analysis.study1 import holm
from analysis.study2 import contrast, load
from study2.design import FOLLOWUP_WORDINGS


def reading(family):
    """The registered decision table, in code so nobody applies it by hand."""
    d1, d2, d4 = (family[k] for k in ("D1_minimal_vs_trigger_at_300", "D2_short_trigger_vs_trigger_at_300", "D4_short_trigger_vs_trigger_at_50"))
    sig = lambda r: r["p_holm"] < 0.05 and r["estimate"] > 0
    out = []
    if sig(d1):
        out.append("past the budget a short plain description beats a long trigger list")
    if sig(d2) and d4["ci"][0] > -0.10:
        out.append("a short description that says when to use the skill beats a long one past the budget and costs under 10 points below it")
    return "; ".join(out) or "inconclusive"


def analyze(batch):
    rows, counts = load(batch)
    is_w = lambda w: (lambda r: r["wording"] == w)
    at = lambda lib: (lambda r: r["library"] == lib)
    family = {
        "D1_minimal_vs_trigger_at_300": contrast(rows, at(300), is_w("minimal"), is_w("trigger")),
        "D2_short_trigger_vs_trigger_at_300": contrast(rows, at(300), is_w("short_trigger"), is_w("trigger")),
        "D3_short_trigger_vs_minimal_at_300": contrast(rows, at(300), is_w("short_trigger"), is_w("minimal")),
        "D4_short_trigger_vs_trigger_at_50": contrast(rows, at(50), is_w("short_trigger"), is_w("trigger")),
    }
    for name, adj in zip(family, holm([family[n]["p"] for n in family])):
        family[name]["p_holm"] = adj
    secondary = {}
    for prompt in ("keyword", "generic", "indirect"):
        for name, lib, a, b in (("D1", 300, "minimal", "trigger"), ("D2", 300, "short_trigger", "trigger"), ("D3", 300, "short_trigger", "minimal"), ("D4", 50, "short_trigger", "trigger")):
            secondary[f"{name}_{prompt}"] = contrast(rows, lambda r, p=prompt, n=lib: r["prompt"] == p and r["library"] == n, is_w(a), is_w(b))
    grid = {}
    for lib in (50, 300):
        for w in FOLLOWUP_WORDINGS:
            cell = [r for r in rows if r["library"] == lib and r["wording"] == w]
            grid[f"{lib}/{w}"] = {
                "recall": float(np.mean([r["y"] for r in cell])), "n": len(cell), "description_reached_model": float(np.mean([r["described"] for r in cell])),
                "recall_described": float(np.mean([r["y"] for r in cell if r["described"]] or [np.nan])),
                "recall_not_described": float(np.mean([r["y"] for r in cell if not r["described"]] or [np.nan])),
            }
    return {"runs": counts, "family": family, "secondary": secondary, "grid": grid, "reading": reading(family),
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
