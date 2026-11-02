"""Power of the preregistered by-rule test, simulated from the pilot's rule base rates.

    python3 -m analysis.power

Each simulated run shows K rules, draws a run effect, and gives each rule its own true slope around the average
effect. The slope spread is what the by-rule interval has to survive, so it is varied instead of assumed.
"""

import json

import numpy as np
from scipy import stats

BASE = [0.24, 0.49, 0.51, 0.55, 0.69, 0.64, 0.80, 0.80, 0.84, 0.87, 0.88, 0.92, 0.93, 0.90, 0.93]
K = 12
LEVELS = 5


def simulate(n_runs, effect, slope_sd, run_sd=0.08, sims=400, seed=0):
    rng = np.random.default_rng(seed)
    base = np.array(BASE)
    g = len(base)
    hits = 0
    for _ in range(sims):
        slopes = rng.normal(effect, slope_sd, g)
        shown = np.argsort(rng.random((n_runs, g)), axis=1)[:, :K]
        run = rng.normal(0, run_sd, n_runs)[:, None]
        arm = rng.integers(0, LEVELS, (n_runs, K))
        p = base[shown] + run + (arm == 1) * slopes[shown]
        y = rng.random(p.shape) < np.clip(p, 0, 1)
        resid = y - y.mean(axis=1, keepdims=True)
        ests = np.array([resid[(shown == r) & (arm == 1)].mean() - resid[(shown == r) & (arm == 0)].mean() for r in range(g)])
        t = ests.mean() / (ests.std(ddof=1) / np.sqrt(g))
        hits += abs(t) > stats.t.ppf(0.975, g - 1)
    return hits / sims


def main():
    out = {}
    for n in (500, 1000, 1500):
        for effect in (0.03, 0.05, 0.08):
            for slope_sd in (0.03, 0.06):
                out[f"runs={n} effect={effect} slope_sd={slope_sd}"] = simulate(n, effect, slope_sd)
                print(f"runs={n:5} effect={effect:.2f} slope_sd={slope_sd:.2f} power={out[f'runs={n} effect={effect} slope_sd={slope_sd}']:.2f}", flush=True)
    with open("results/power.json", "w") as f:
        json.dump(out, f, indent=1)


if __name__ == "__main__":
    main()
