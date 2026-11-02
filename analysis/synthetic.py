"""Made-up outcomes on the real assignment, so the analyses can be tested where the right answer is known."""

import json
from pathlib import Path

import numpy as np

from analysis.study1 import position_of
from study1.design import render_file
from study1.rules import FOCAL

ROOT = Path(__file__).resolve().parent.parent
# Final-mix pilot compliance, in FOCAL's order.
PILOT = dict(zip(FOCAL, (0.13, 0.23, 0.38, 0.40, 0.45, 0.74, 0.91, 0.94, 0.94)))
# Pulled toward the middle, where a planted effect is not cut off by a ceiling.
MIDDLE = {r: 0.5 * (p + 0.5) for r, p in PILOT.items()}
RULES = sorted(FOCAL)


def assignment():
    """The shape `analysis.study1.load` builds, before any outcome is attached."""
    obs = []
    for line in (ROOT / "data" / "study1" / "manifest.jsonl").read_text().splitlines():
        row = json.loads(line)
        _, depth, _ = render_file(row)
        for t in row["targets"]:
            if t["rule"] in FOCAL:
                obs.append({
                    "run": row["run_id"], "rule": t["rule"], "reason": t["reason"], "modal": t["modal"], "prefix": t["prefix"],
                    "case": t["case"], "example": t["example"], "position": position_of(depth[t["rule"]]),
                    "length": row["length"], "pressure": row["pressure"],
                })
    return obs


def simulate(obs, plant, seed, base=MIDDLE, slope_sd=0.0, run_sd=0.08):
    """Bernoulli outcomes from base rates plus planted effects. `plant` maps (factor, level) to a mean effect on the
    probability scale, and each rule draws its own slope around that mean."""
    rng = np.random.default_rng(seed)
    runs = sorted({o["run"] for o in obs})
    run_effect = dict(zip(runs, rng.normal(0, run_sd, len(runs))))
    slopes = {key: dict(zip(RULES, rng.normal(mean, slope_sd, len(RULES)))) for key, mean in plant.items()}
    out = []
    for o in obs:
        p = base[o["rule"]] + run_effect[o["run"]]
        for (factor, level), per_rule in slopes.items():
            p += per_rule[o["rule"]] * (o[factor] == level)
        out.append({**o, "y": float(rng.random() < np.clip(p, 0, 1))})
    return out
