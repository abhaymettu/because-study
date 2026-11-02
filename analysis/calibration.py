"""Does the registered test hold its error rate, and what power does it really have, on the real assignment?

    python3 -m analysis.calibration [--sims 1000] [--out results/calibration.json]

`analysis/power.py` set the sample size with a simplified estimator before the assignment existed. This uses the fielded
assignment, the registered estimator and pilot base rates, so ceilings shrink the effects as they would in the study.
"""

import argparse
import json
from pathlib import Path

import numpy as np

from analysis.study1 import by_rule, holm, rule_level_estimates, run_level
from analysis.synthetic import PILOT, RULES, assignment, simulate

REAL, PLACEBO = ("reason", "real"), ("reason", "placebo")


def rates(obs, plant, slope_sd, sims, offset):
    raw, adjusted, estimates = 0, 0, []
    for seed in range(sims):
        est = rule_level_estimates(simulate(obs, plant, offset + seed, base=PILOT, slope_sd=slope_sd), RULES)
        h1, h2 = by_rule(est[REAL]), by_rule(est[PLACEBO])
        raw += h1["p"] < 0.05
        adjusted += holm([h1["p"], h2["p"]])[0] < 0.05
        estimates.append(h1["estimate"])
    return {"p_under_05": raw / sims, "p_holm_under_05": adjusted / sims, "mean_estimate": float(np.mean(estimates))}


def run_level_false_positives(obs, sims, offset):
    hits = sum(
        run_level(simulate(obs, {}, offset + seed, base=PILOT), RULES, "pressure", "urgent", "none")["p"] < 0.05 for seed in range(sims)
    )
    return hits / sims


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sims", type=int, default=1000)
    p.add_argument("--out", default="results/calibration.json")
    a = p.parse_args()
    obs = assignment()
    out = {"sims": a.sims, "observations": len(obs)}
    out["no_effect"] = rates(obs, {}, 0.0, a.sims, 0)
    out["run_level_no_effect_p_under_05"] = run_level_false_positives(obs, a.sims // 5, 10**6)
    for effect in (0.03, 0.05, 0.08):
        for slope_sd in (0.03, 0.06):
            out[f"effect={effect} slope_sd={slope_sd}"] = rates(obs, {REAL: effect}, slope_sd, a.sims // 2, 10**7)
            print(f"effect={effect} slope_sd={slope_sd}", out[f"effect={effect} slope_sd={slope_sd}"], flush=True)
    print({k: v for k, v in out.items() if "no_effect" in k})
    Path(a.out).write_text(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
