"""Study 2 analysis, from manifest and traces: python3 -m analysis.study2 data/study2 [--out results/study2.json]"""

import argparse
import json
from pathlib import Path

import numpy as np

from analysis.study1 import by_rule, holm
from study2.design import target_name


def loaded(trace, name):
    for tool, target in trace["calls"]:
        if tool == "Skill" and str(target).split(":")[-1] == name:
            return True
        if tool in ("Read", "Bash") and f"skills/{name}/SKILL.md" in str(target):
            return True
    return False


def load(batch):
    batch = Path(batch)
    rows, counts = [], {"used": 0, "missing": 0, "error": 0, "leak": 0, "timeout": 0, "max_turns": 0}
    for line in (batch / "manifest.jsonl").read_text().splitlines():
        row = json.loads(line)
        path = batch / "traces" / f"{row['run_id']}.json"
        if not path.exists():
            counts["missing"] += 1
            continue
        doc = json.loads(path.read_text())
        rec = doc["record"]
        if rec["status"] == "error":
            counts["error"] += 1
            continue
        if rec["capture"]["leaks"]:
            counts["leak"] += 1
            continue
        counts["used"] += 1
        counts["timeout"] += rec["status"] == "timeout"
        counts["max_turns"] += rec["status"] == "max_turns"
        name = target_name(row)
        rows.append({
            "run": row["run_id"], "stem": row["stem"], "wording": row["wording"], "library": row["library"],
            "prefix": row["name_prefix"], "prompt": row["prompt_type"], "y": float(loaded(doc["trace"], name)),
            "described": bool(rec["capture"].get("probe_hit")),
            "any_skill": any(t == "Skill" for t, _ in doc["trace"]["calls"]), "cost": rec["cost_usd"] or 0,
            "turns": rec["turns"] or 0,
        })
    return rows, counts


def visible(r):
    """Set by design, not by the recorded outcome: below the budget, or sorted early enough to fit."""
    return r["library"] < 300 or r["prefix"] == "aa"


def contrast(rows, keep, a, b):
    """Per-target difference a minus b, averaged with equal weight. Targets lacking a cell are dropped and counted."""
    ests = []
    for stem in sorted({r["stem"] for r in rows}):
        ya = [r["y"] for r in rows if r["stem"] == stem and keep(r) and a(r)]
        yb = [r["y"] for r in rows if r["stem"] == stem and keep(r) and b(r)]
        if ya and yb:
            ests.append(np.mean(ya) - np.mean(yb))
    return by_rule(np.array(ests))


def analyze(batch):
    rows, counts = load(batch)
    wants = lambda r: r["prompt"] != "decoy"
    is_w = lambda w: (lambda r: r["wording"] == w)
    family = {
        "C1_trigger_vs_minimal_visible": contrast(rows, lambda r: wants(r) and visible(r), is_w("trigger"), is_w("minimal")),
        "C2_directive_vs_trigger_visible": contrast(rows, lambda r: wants(r) and visible(r), is_w("directive"), is_w("trigger")),
        "C3_not_clause_false_loads_visible": contrast(rows, lambda r: r["prompt"] == "decoy" and visible(r), is_w("trigger_not"), is_w("trigger")),
        "C4_aa_vs_zz_at_300": contrast(rows, lambda r: wants(r) and r["library"] == 300, lambda r: r["prefix"] == "aa", lambda r: r["prefix"] == "zz"),
        "C5_trigger_vs_minimal_described_gone": contrast(rows, lambda r: wants(r) and r["library"] == 300 and r["prefix"] == "zz", is_w("trigger"), is_w("minimal")),
    }
    for name, adj in zip(family, holm([family[n]["p"] for n in family])):
        family[name]["p_holm"] = adj
    secondary = {
        "padded_vs_minimal_visible": contrast(rows, lambda r: wants(r) and visible(r), is_w("padded"), is_w("minimal")),
        "library_300_vs_0_with_aa": contrast(rows, lambda r: wants(r) and r["prefix"] == "aa", lambda r: r["library"] == 300, lambda r: r["library"] == 0),
    }
    grid = {}
    for lib in (0, 50, 300):
        for prefix in ("aa", "zz"):
            for w in ("minimal", "padded", "trigger", "trigger_not", "directive"):
                ys = [r["y"] for r in rows if wants(r) and r["library"] == lib and r["prefix"] == prefix and r["wording"] == w]
                grid[f"{lib}/{prefix}/{w}"] = {"recall": float(np.mean(ys)) if ys else None, "n": len(ys)}
    described = {}
    for prefix in ("aa", "zz"):
        for w in ("minimal", "padded", "trigger", "trigger_not", "directive"):
            ys = [r["described"] for r in rows if r["library"] == 300 and r["prefix"] == prefix and r["wording"] == w]
            described[f"300/{prefix}/{w}"] = float(np.mean(ys)) if ys else None
    by_prompt = {p: float(np.mean([r["y"] for r in rows if r["prompt"] == p])) for p in sorted({r["prompt"] for r in rows})}
    return {
        "runs": counts, "family": family, "secondary": secondary, "grid": grid, "description_reached_model": described, "by_prompt": by_prompt,
        "cost": {"api_equivalent_usd": float(sum(r["cost"] for r in rows)), "turns": float(np.mean([r["turns"] for r in rows]))},
    }


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
    print(res["by_prompt"], res["cost"])


if __name__ == "__main__":
    main()
