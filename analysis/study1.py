"""Study 1 analysis. Every number comes from the manifest and the traces; checkers rerun here, nothing is cached.

    python3 -m analysis.study1 data/study1 [--perms 2000] [--out results/study1.json]

An effect is estimated separately for each rule, then averaged with equal weight, so the interval speaks to new rules
like these and not only to these rules. See PREREG.md for which contrasts are confirmatory.
"""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

from study1.design import render_file
from study1.rules import BY_ID, FOCAL, score
from study1.trace import Trace

REASON_REF = "filler"
RULE_FACTORS = {
    "reason": ("none", "placebo", "norm", "real"),
    "modal": ("must",),
    "prefix": ("important",),
    "case": ("upper",),
    "example": ("present",),
    "position": ("top", "bottom"),
}
CONFIRMATORY = [("real_vs_filler", ("reason", "real"), None), ("placebo_vs_filler", ("reason", "placebo"), None)]
FAMILY_2 = [
    ("norm_vs_filler", ("reason", "norm"), None),
    ("none_vs_filler", ("reason", "none"), None),
    ("must_vs_plain", ("modal", "must"), None),
    ("important_vs_none", ("prefix", "important"), None),
    ("upper_vs_normal", ("case", "upper"), None),
    ("example_vs_absent", ("example", "present"), None),
    ("top_vs_bottom", ("position", "top"), ("position", "bottom")),
]
RUN_LEVEL = [("long_vs_short", "length", "long", "short"), ("urgent_vs_none", "pressure", "urgent", "none")]


def position_of(depth):
    return "top" if depth < 1 / 3 else ("bottom" if depth > 2 / 3 else "middle")


def load(batch):
    """One row per (run, shown rule). Runs lost to infrastructure or flagged by the leak scan are counted, not used."""
    batch = Path(batch)
    obs, baseline, control, runs = [], [], [], {"used": 0, "missing": 0, "error": 0, "leak": 0, "timeout": 0, "max_turns": 0}
    records = []
    for line in (batch / "manifest.jsonl").read_text().splitlines():
        row = json.loads(line)
        path = batch / "traces" / f"{row['run_id']}.json"
        if not path.exists():
            runs["missing"] += 1
            continue
        doc = json.loads(path.read_text())
        rec = doc["record"]
        if rec["status"] == "error":
            runs["error"] += 1
            continue
        if rec["capture"]["leaks"]:
            runs["leak"] += 1
            continue
        runs["timeout"] += rec["status"] == "timeout"
        runs["max_turns"] += rec["status"] == "max_turns"
        runs["used"] += 1
        records.append(rec)
        s = score(Trace.from_json(doc["trace"]))
        _, depth, _ = render_file(row)
        for t in row["targets"]:
            obs.append({
                "run": row["run_id"], "rule": t["rule"], "task": row["task"], "y": float(s[t["rule"]]),
                "reason": t["reason"], "modal": t["modal"], "prefix": t["prefix"], "case": t["case"],
                "example": t["example"], "depth": depth[t["rule"]], "position": position_of(depth[t["rule"]]),
                "length": row["length"], "pressure": row["pressure"], "variant": t["variant"], "status": rec["status"], "cost": BY_ID[t["rule"]].cost,
                "polarity": BY_ID[t["rule"]].polarity, "tests_pass": rec["tests_pass"], "turns": rec["turns"],
            })
        for rule in row["unshown"]:
            (control if rule == row["control_rule"] else baseline).append((rule, float(s[rule]), row["length"], row["pressure"]))
    return obs, baseline, control, runs, records


def rule_level_estimates(obs, rules):
    """OLS with run fixed effects and a separate coefficient for every rule and factor level.
    Returns {(factor, level): array of one estimate per rule}."""
    run_ids = {r: i for i, r in enumerate(sorted({o["run"] for o in obs}))}
    columns = [(r, f, lv) for r in rules for f, lvs in RULE_FACTORS.items() for lv in lvs]
    index = {c: i for i, c in enumerate(columns)}
    rule_index = {r: len(columns) + i for i, r in enumerate(rules[1:])}
    n, p = len(obs), len(columns) + len(rule_index)
    X, y, g = np.zeros((n, p)), np.zeros(n), np.zeros(n, dtype=int)
    for i, o in enumerate(obs):
        y[i], g[i] = o["y"], run_ids[o["run"]]
        if o["rule"] in rule_index:
            X[i, rule_index[o["rule"]]] = 1
        for f, lvs in RULE_FACTORS.items():
            if o[f] in lvs:
                X[i, index[(o["rule"], f, o[f])]] = 1
    counts = np.bincount(g, minlength=len(run_ids)).astype(float)
    y = y - (np.bincount(g, y) / counts)[g]
    for j in range(p):
        X[:, j] -= (np.bincount(g, X[:, j], minlength=len(run_ids)) / counts)[g]
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return {(f, lv): np.array([beta[index[(r, f, lv)]] for r in rules]) for f, lvs in RULE_FACTORS.items() for lv in lvs}


def by_rule(estimates):
    g = len(estimates)
    mean = float(np.mean(estimates))
    se = float(np.std(estimates, ddof=1) / np.sqrt(g))
    # All rules agreeing exactly gives a zero SE, which happens at a floor or ceiling. NaN here would break Holm.
    t = mean / se if se else (0.0 if mean == 0 else float("inf"))
    q = stats.t.ppf(0.975, g - 1)
    return {
        "estimate": mean, "se": se, "ci": [mean - q * se, mean + q * se],
        "p": float(2 * stats.t.sf(abs(t), g - 1)), "rule_sd": float(np.std(estimates, ddof=1)),
        "per_rule": [float(x) for x in estimates], "g": g,
    }


def contrast(est, a, b=None):
    return est[a] - est[b] if b else est[a]


def holm(pvals):
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    adj, running = [0.0] * len(pvals), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(pvals) - rank) * pvals[i]))
        adj[i] = running
    return adj


def randomization_p(obs, rules, a_level, b_level, factor, perms, seed=0):
    """Sharp-null test for these rules and tasks: permute a factor's labels within rule and recompute the studentized
    mean contrast on outcomes residualized on run and rule."""
    rng = np.random.default_rng(seed)
    runs = sorted({o["run"] for o in obs})
    run_ix = {r: i for i, r in enumerate(runs)}
    rule_ix = {r: i for i, r in enumerate(rules)}
    y = np.array([o["y"] for o in obs])
    g = np.array([run_ix[o["run"]] for o in obs])
    h = np.array([rule_ix[o["rule"]] for o in obs])
    resid = y.copy()
    for _ in range(25):
        resid -= (np.bincount(g, resid, minlength=len(runs)) / np.bincount(g, minlength=len(runs)))[g]
        resid -= (np.bincount(h, resid, minlength=len(rules)) / np.bincount(h, minlength=len(rules)))[h]
    labels = np.array([o[factor] for o in obs])

    def stat(lab):
        ests = np.empty(len(rules))
        for r in range(len(rules)):
            mask = h == r
            ests[r] = resid[mask & (lab == a_level)].mean() - resid[mask & (lab == b_level)].mean()
        return ests.mean() / (ests.std(ddof=1) / np.sqrt(len(rules)))

    observed = stat(labels)
    pair = (labels == a_level) | (labels == b_level)
    groups = [np.flatnonzero((h == r) & pair) for r in range(len(rules))]
    extreme = 0
    for _ in range(perms):
        lab = labels.copy()
        for ix in groups:
            lab[ix] = rng.permutation(lab[ix])
        extreme += abs(stat(lab)) >= abs(observed)
    return (extreme + 1) / (perms + 1)


def run_level(obs, rules, factor, a, b):
    """A factor set per run cannot use run fixed effects. Rule and run noise both enter, so the SE adds both."""
    ests = []
    for r in rules:
        ya = [o["y"] for o in obs if o["rule"] == r and o[factor] == a]
        yb = [o["y"] for o in obs if o["rule"] == r and o[factor] == b]
        ests.append(np.mean(ya) - np.mean(yb))
    ests = np.array(ests)
    per_run = {}
    for o in obs:
        per_run.setdefault(o["run"], (o[factor], []))[1].append(o["y"])
    ra = [np.mean(v[1]) for v in per_run.values() if v[0] == a]
    rb = [np.mean(v[1]) for v in per_run.values() if v[0] == b]
    se_run = np.sqrt(np.var(ra, ddof=1) / len(ra) + np.var(rb, ddof=1) / len(rb))
    out = by_rule(ests)
    sampling = 0.0
    for r in rules:
        ya = [o["y"] for o in obs if o["rule"] == r and o[factor] == a]
        yb = [o["y"] for o in obs if o["rule"] == r and o[factor] == b]
        sampling += np.var(ya) / len(ya) + np.var(yb) / len(yb)
    excess = max(0.0, out["se"] ** 2 - sampling / len(rules) ** 2)
    out["se_by_rule"] = out["se"]
    out["se_by_run"] = float(se_run)
    # By-run variance already holds the sampling noise, so rules add only their variance beyond it.
    out["se"] = float(np.sqrt(se_run**2 + excess))
    q = stats.t.ppf(0.975, len(rules) - 1)
    out["ci"] = [out["estimate"] - q * out["se"], out["estimate"] + q * out["se"]]
    out["p"] = float(2 * stats.t.sf(abs(out["estimate"] / out["se"]), len(rules) - 1))
    return out


def interaction_reason_pressure(obs, rules, level):
    """Does a clause's effect survive when the user asks for speed? Exactly Langer's small-favor, big-favor moderator."""
    ests = []
    for r in rules:
        cell = lambda reason, pressure: np.mean(
            [o["y"] for o in obs if o["rule"] == r and o["reason"] == reason and o["pressure"] == pressure] or [np.nan]
        )
        ests.append((cell(level, "urgent") - cell(REASON_REF, "urgent")) - (cell(level, "none") - cell(REASON_REF, "none")))
    return by_rule(np.array([e for e in ests if not np.isnan(e)]))


def shown_minus_unshown(obs, baseline, rules, factor_index, a, b):
    """A run-level factor can change behavior with no rule in play. This nets out what the unshown rules did."""
    ests = []
    for r in rules:
        name = {1: "length", 2: "pressure"}[factor_index]
        diff = lambda lv: np.mean([o["y"] for o in obs if o["rule"] == r and o[name] == lv]) - np.mean(
            [x[1] for x in baseline if x[0] == r and x[1 + factor_index] == lv] or [np.nan])
        ests.append(diff(a) - diff(b))
    return by_rule(np.array([e for e in ests if not np.isnan(e)]))


def reading(res):
    """The registered decision table, in code so nobody applies it by hand."""
    h1, h2 = res["confirmatory"]["real_vs_filler"], res["confirmatory"]["placebo_vs_filler"]
    sig = lambda r: r["p_holm"] < 0.05
    above = lambda r: r["p"] < 0.05 and r["estimate"] > 0
    ret = res["retention_placebo_minus_half_real"]
    rmp = res["real_minus_placebo"]
    control = res["positive_control"]
    if control["named_in_prompt"] is None or control["named_in_prompt"] - control["no_rule"] < 0.30:
        return "assay failed: the positive control did not clear 30 points, so nothing below is read"
    h3 = ret["gate_open"] and ret["p_one_sided"] < 0.05
    if sig(h1) and sig(h2) and h1["estimate"] > 0 and h2["estimate"] > 0 and h3 and above(res["real_vs_none"]) and above(res["placebo_vs_none"]):
        base = "the form of a reason moves compliance"
        return base + (", and a placebo does about as much as a real reason" if rmp["tost_p_at_5_points"] < 0.05 else "")
    if sig(h1) and h1["estimate"] > 0 and not sig(h2) and not h3 and rmp["p"] < 0.05 and rmp["estimate"] > 0:
        return "reasons work through their content; a placebo does not substitute"
    if not sig(h1) and not sig(h2) and h1["ci"][1] < 0.05 and h2["ci"][1] < 0.05:
        return "a reason clause does not move compliance by a practically useful amount on these rules"
    return "inconclusive"


def analyze(batch, perms=2000):
    obs, baseline, control, runs, records = load(batch)
    ballast = {}
    for o in obs:
        if o["rule"] not in FOCAL:
            ballast.setdefault(o["rule"], []).append(o["y"])
    obs = [o for o in obs if o["rule"] in FOCAL]
    baseline = [b for b in baseline if b[0] in FOCAL]
    control = [c for c in control if c[0] in FOCAL]
    rules = sorted({o["rule"] for o in obs})
    est = rule_level_estimates(obs, rules)
    res = {"runs": runs, "observations": len(obs), "rules": rules, "compliance": float(np.mean([o["y"] for o in obs]))}

    confirm = {name: by_rule(contrast(est, a, b)) for name, a, b in CONFIRMATORY}
    for name, adj in zip(confirm, holm([confirm[n]["p"] for n in confirm])):
        confirm[name]["p_holm"] = adj
    real, placebo = contrast(est, ("reason", "real")), contrast(est, ("reason", "placebo"))
    retention = by_rule(placebo - 0.5 * real)
    retention["p_one_sided"] = float(stats.t.sf(retention["estimate"] / retention["se"], retention["g"] - 1))
    retention["gate_open"] = confirm["real_vs_filler"]["p_holm"] < 0.05 and confirm["real_vs_filler"]["estimate"] > 0
    real_minus_placebo = by_rule(real - placebo)
    g = real_minus_placebo["g"]
    se = real_minus_placebo["se"]
    margin = 0.05
    real_minus_placebo["tost_p_at_5_points"] = float(max(
        stats.t.sf((real_minus_placebo["estimate"] + margin) / se, g - 1),
        stats.t.sf((margin - real_minus_placebo["estimate"]) / se, g - 1),
    ))
    res["confirmatory"] = confirm
    res["retention_placebo_minus_half_real"] = retention
    res["real_minus_placebo"] = real_minus_placebo
    none = contrast(est, ("reason", "none"))
    res["real_vs_none"] = by_rule(real - none)
    res["placebo_vs_none"] = by_rule(placebo - none)

    family = {name: by_rule(contrast(est, a, b)) for name, a, b in FAMILY_2}
    for name, factor, a, b in RUN_LEVEL:
        family[name] = run_level(obs, rules, factor, a, b)
    names = list(family)
    for name, adj in zip(names, holm([family[n]["p"] for n in names])):
        family[name]["p_holm"] = adj
    res["family_2"] = family

    res["randomization_p"] = {
        "real_vs_filler": randomization_p(obs, rules, "real", "filler", "reason", perms, 1),
        "placebo_vs_filler": randomization_p(obs, rules, "placebo", "filler", "reason", perms, 2),
    }
    res["moderator_pressure"] = {lv: interaction_reason_pressure(obs, rules, lv) for lv in ("real", "placebo", "norm")}

    per_rule = {}
    for r in rules:
        ys = [o["y"] for o in obs if o["rule"] == r]
        per_rule[r] = {"shown": float(np.mean(ys)), "n": len(ys), "cost": BY_ID[r].cost, "polarity": BY_ID[r].polarity}
        base = [v for rr, v, *_ in baseline if rr == r]
        ctrl = [v for rr, v, *_ in control if rr == r]
        per_rule[r]["no_rule"] = float(np.mean(base)) if base else None
        per_rule[r]["named_in_prompt"] = float(np.mean(ctrl)) if ctrl else None
    res["per_rule"] = per_rule
    res["positive_control"] = {
        "named_in_prompt": float(np.mean([c[1] for c in control])) if control else None,
        "no_rule": float(np.mean([b[1] for b in baseline])) if baseline else None,
        "n_named": len(control),
        "n_no_rule": len(baseline),
    }
    levels = {}
    for f in ("reason", "modal", "prefix", "case", "example", "position", "length", "pressure"):
        for lv in sorted({o[f] for o in obs}):
            ys = [o["y"] for o in obs if o[f] == lv]
            levels[f"{f}={lv}"] = {"mean": float(np.mean(ys)), "n": len(ys)}
    res["raw_means"] = levels
    res["counts_by_arm"] = {
        lv: {st: sum(1 for o in obs if o["reason"] == lv and o["status"] == st) for st in ("ok", "timeout", "max_turns")}
        for lv in ("none", "filler", "placebo", "norm", "real")
    }
    res["run_level_net_of_unshown"] = {
        "long_vs_short": shown_minus_unshown(obs, baseline, rules, 1, "long", "short"),
        "urgent_vs_none": shown_minus_unshown(obs, baseline, rules, 2, "urgent", "none"),
    }
    res["ballast_compliance"] = {r: float(np.mean(v)) for r, v in ballast.items()}
    res["reading"] = reading(res)
    res["cost"] = {
        "api_equivalent_usd": float(sum(r["cost_usd"] or 0 for r in records)),
        "tests_pass": float(np.mean([r["tests_pass"] for r in records])),
        "turns": float(np.mean([r["turns"] or 0 for r in records])),
        "seconds": float(np.mean([r["duration_s"] for r in records])),
        "models": sorted({r["model"] or "" for r in records}),
        "cli": sorted({r["cli"] or "" for r in records}),
        "system_prompt_hashes": len({h for r in records for h in r["capture"]["system_hashes"]}),
    }
    return res


def main():
    p = argparse.ArgumentParser()
    p.add_argument("batch")
    p.add_argument("--perms", type=int, default=2000)
    p.add_argument("--out")
    a = p.parse_args()
    res = analyze(a.batch, a.perms)
    text = json.dumps(res, indent=1, default=float)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text)

    def show(name, r):
        extra = f" holm={r['p_holm']:.3f}" if "p_holm" in r else ""
        print(f"{name:24}{100 * r['estimate']:+6.1f} pts  [{100 * r['ci'][0]:+5.1f}, {100 * r['ci'][1]:+5.1f}]  p={r['p']:.3f}{extra}")

    print(f"runs {res['runs']}, observations {res['observations']}, rules {len(res['rules'])}, compliance {res['compliance']:.3f}")
    for name, r in res["confirmatory"].items():
        show(name, r)
    show("placebo minus half real", res["retention_placebo_minus_half_real"])
    show("real minus placebo", res["real_minus_placebo"])
    for name, r in res["family_2"].items():
        show(name, r)
    print("randomization p", res["randomization_p"])
    print("reading:", res["reading"])
    print("positive control", res["positive_control"])


if __name__ == "__main__":
    main()
