"""Power of the preregistered by-rule test, simulated from the pilot's rule base rates.

    python3 -m analysis.power

Each simulated run shows K rules, draws a run effect, and gives each rule its own true slope around the average
effect. The slope spread is what the by-rule interval has to survive, so it is varied instead of assumed.
"""

import json

import numpy as np
from scipy import stats

# Final-mix pilot rates: nine focal rules, then five ballast rules shown but not analyzed.
BASE = [0.13, 0.23, 0.38, 0.40, 0.45, 0.74, 0.91, 0.94, 0.94, 0.96, 0.96, 0.98, 0.98, 1.00]
FOCAL = 9
K = 11
LEVELS = 5


def simulate(n_runs, effect, slope_sd, run_sd=0.08, sims=400, seed=0):
    rng = np.random.default_rng(seed)
    base = np.array(BASE)
    g = len(base)
    hits, holm_hits = 0, 0
    for _ in range(sims):
        slopes = rng.normal(effect, slope_sd, g)
        shown = np.argsort(rng.random((n_runs, g)), axis=1)[:, :K]
        run = rng.normal(0, run_sd, n_runs)[:, None]
        arm = rng.integers(0, LEVELS, (n_runs, K))
        p = base[shown] + run + (arm == 1) * slopes[shown]
        y = rng.random(p.shape) < np.clip(p, 0, 1)
        resid = y - y.mean(axis=1, keepdims=True)
        ests = np.array([resid[(shown == r) & (arm == 1)].mean() - resid[(shown == r) & (arm == 0)].mean() for r in range(FOCAL)])
        t = ests.mean() / (ests.std(ddof=1) / np.sqrt(FOCAL))
        hits += abs(t) > stats.t.ppf(0.975, FOCAL - 1)
        holm_hits += abs(t) > stats.t.ppf(1 - 0.025 / 2, FOCAL - 1)
    return hits / sims, holm_hits / sims


def main():
    out = {}
    for n in (700, 1000, 1500):
        for effect in (0.03, 0.05, 0.08):
            for slope_sd in (0.03, 0.06):
                raw, strict = simulate(n, effect, slope_sd)
                out[f"runs={n} effect={effect} slope_sd={slope_sd}"] = {"raw": raw, "holm_worst_case": strict}
                print(f"runs={n:5} effect={effect:.2f} slope_sd={slope_sd:.2f} power={raw:.2f} holm_worst={strict:.2f}", flush=True)
    with open("results/power.json", "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
