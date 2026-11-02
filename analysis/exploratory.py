"""Everything here is labeled exploratory or sensitivity in the write-up, and none of it changes a registered reading.

    python3 -m analysis.exploratory [--out results/exploratory.json]
"""

import argparse
import json
import re
from pathlib import Path

import numpy as np
from scipy import stats

from analysis.study1 import RULE_FACTORS, by_rule, contrast, holm, load, rule_level_estimates
from analysis import study2
from study1.rules import FOCAL
from study1.trace import Trace

BATCH = "data/study1"
REAL, PLACEBO, FILLER = ("reason", "real"), ("reason", "placebo"), "filler"
# The registered rule-level coefficients. Holm runs across these times the nine rules, the 72 cells of docs/REVIEW-3-final.md.
LEVELS = (
    ("real_vs_filler", ("reason", "real")), ("placebo_vs_filler", ("reason", "placebo")), ("norm_vs_filler", ("reason", "norm")), ("none_vs_filler", ("reason", "none")),
    ("must_vs_plain", ("modal", "must")), ("important_vs_none", ("prefix", "important")), ("upper_vs_normal", ("case", "upper")), ("example_vs_absent", ("example", "present")),
)
WORDINGS = ("minimal", "padded", "trigger", "trigger_not", "directive")


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


def fit_clustered(obs, rules):
    """rule_level_estimates' regression, plus the run-clustered covariance it does not keep. Returns (index, beta, V)."""
    run_ids = {r: i for i, r in enumerate(sorted({o["run"] for o in obs}))}
    columns = [(r, f, lv) for r in rules for f, lvs in RULE_FACTORS.items() for lv in lvs]
    index = {c: i for i, c in enumerate(columns)}
    rule_index = {r: len(columns) + i for i, r in enumerate(rules[1:])}
    X, y, g = np.zeros((len(obs), len(columns) + len(rule_index))), np.zeros(len(obs)), np.zeros(len(obs), dtype=int)
    for i, o in enumerate(obs):
        y[i], g[i] = o["y"], run_ids[o["run"]]
        if o["rule"] in rule_index:
            X[i, rule_index[o["rule"]]] = 1
        for f, lvs in RULE_FACTORS.items():
            if o[f] in lvs:
                X[i, index[(o["rule"], f, o[f])]] = 1
    counts = np.bincount(g).astype(float)
    y = y - (np.bincount(g, y) / counts)[g]
    X = X - np.stack([(np.bincount(g, X[:, j], minlength=len(counts)) / counts)[g] for j in range(X.shape[1])], axis=1)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    meat = np.zeros((X.shape[1], X.shape[1]))
    for k in range(len(counts)):
        score = X[g == k].T @ resid[g == k]
        meat += np.outer(score, score)
    bread = np.linalg.pinv(X.T @ X)
    return index, beta, bread @ meat @ bread


def normal_p(estimate, se):
    return float(2 * stats.norm.sf(abs(estimate / se))) if se else 1.0


def rule_by_factor(obs, rules, index, beta, V):
    """Every rule at every factor level. Position and the run-level factors stay outside the 72-cell family and inside a 99-cell one."""
    cell = lambda name, rule, b, se: {"contrast": name, "rule": rule, "estimate": float(b), "se": float(se), "p": normal_p(b, se)}
    inside = [cell(name, r, beta[index[(r, *lv)]], np.sqrt(V[index[(r, *lv)], index[(r, *lv)]])) for name, lv in LEVELS for r in rules]
    outside = []
    for name, a, b in (("real_minus_placebo", ("reason", "real"), ("reason", "placebo")), ("top_vs_bottom", ("position", "top"), ("position", "bottom"))):
        for r in rules:
            i, j = index[(r, *a)], index[(r, *b)]
            outside.append(cell(name, r, beta[i] - beta[j], np.sqrt(V[i, i] + V[j, j] - 2 * V[i, j])))
    for name, factor, a, b in (("long_vs_short", "length", "long", "short"), ("urgent_vs_none", "pressure", "urgent", "none")):
        for r in rules:
            ya, yb = ([o["y"] for o in obs if o["rule"] == r and o[factor] == lv] for lv in (a, b))
            outside.append(cell(name, r, np.mean(ya) - np.mean(yb), np.sqrt(np.var(ya, ddof=1) / len(ya) + np.var(yb, ddof=1) / len(yb))))
    for c, adj in zip(inside, holm([c["p"] for c in inside])):
        c["p_holm_72"] = adj
    # real_minus_placebo is a difference of two cells already counted, so it adds no test.
    wider = inside + [c for c in outside if c["contrast"] != "real_minus_placebo"]
    for c, adj in zip(wider, holm([c["p"] for c in wider])):
        c["p_holm_99"] = adj
    every = inside + outside
    extremes = {name: max((c for c in every if c["contrast"] == name), key=lambda c: abs(c["estimate"])) for name in dict.fromkeys(c["contrast"] for c in every)}
    return {
        "label": "Exploratory and post hoc. Nobody registered these cells. Raw p is a normal approximation from the run-clustered se.",
        "holm_72": "The 72-cell Holm runs across the 8 rule-level coefficients on each of 9 rules.",
        "holm_99": "The 99-cell Holm adds top_vs_bottom, long_vs_short and urgent_vs_none on each rule.",
        "cells": every, "extreme_tick_per_factor": extremes,
    }


def heterogeneity(estimates, ses):
    """Is real vs filler one effect across rules? Cochran Q, DerSimonian-Laird tau, Hartung-Knapp mean, prediction interval for a new rule."""
    k, w = len(estimates), 1 / ses**2
    fixed = (w * estimates).sum() / w.sum()
    q = float((w * (estimates - fixed) ** 2).sum())
    tau2 = max(0.0, (q - (k - 1)) / (w.sum() - (w**2).sum() / w.sum()))
    w = 1 / (ses**2 + tau2)
    mean = float((w * estimates).sum() / w.sum())
    se = float(np.sqrt((w * (estimates - mean) ** 2).sum() / (k - 1) / w.sum()))
    half, spread = stats.t.ppf(0.975, k - 1) * se, stats.t.ppf(0.975, k - 2) * np.sqrt(tau2 + se**2)
    return {"cochran_q": q, "df": k - 1, "p": float(stats.chi2.sf(q, k - 1)), "tau": float(np.sqrt(tau2)), "mean": mean, "hartung_knapp_ci": [mean - half, mean + half],
            "prediction_interval": [mean - spread, mean + spread]}


def how_sure(obs, rules, loo):
    """The sentences 'no effect above about 6 points' and 'equivalent within 5 points' rest on, measured against their alternatives."""
    index, beta, V = fit_clustered(obs, rules)
    est = rule_level_estimates(obs, rules)
    if not all(np.allclose(est[(f, lv)], [beta[index[(r, f, lv)]] for r in rules], atol=1e-9) for f, lvs in RULE_FACTORS.items() for lv in lvs):
        raise ValueError("the clustered fit does not match the registered estimator")
    real, none, placebo = (contrast(est, ("reason", lv)) for lv in ("real", "none", "placebo"))
    ses = np.sqrt([V[index[(r, *REAL)], index[(r, *REAL)]] for r in rules])
    uppers = {r: loo[r]["real_vs_none_upper"] for r in rules}
    gap = by_rule(real - placebo)
    tost = lambda margin: float(max(stats.t.sf((gap["estimate"] + margin) / gap["se"], gap["g"] - 1), stats.t.sf((margin - gap["estimate"]) / gap["se"], gap["g"] - 1)))
    return rule_by_factor(obs, rules, index, beta, V), {
        "label": "Exploratory and post hoc.",
        "real_vs_filler_across_rules": heterogeneity(real, ses),
        "real_vs_none_upper_bound": by_rule(real - none)["ci"][1],
        "real_vs_none_upper_bound_leave_one_rule_out": {"lowest": min(uppers.values()), "highest": max(uppers.values()), "by_rule_dropped": uppers},
        "tost_real_minus_placebo": {"at_4.5_points": tost(0.045), "at_5_points": tost(0.05)},
    }


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
        est = rule_level_estimates([o for o in obs if o["rule"] != drop], keep)
        h1, h2 = by_rule(contrast(est, REAL)), by_rule(contrast(est, PLACEBO))
        loo[drop] = {"real": h1["estimate"], "real_ci": h1["ci"], "placebo": h2["estimate"], "placebo_ci": h2["ci"],
                     "real_vs_none_upper": by_rule(contrast(est, REAL) - contrast(est, ("reason", "none")))["ci"][1]}
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
    out["rule_by_factor"], out["how_sure_real_vs_filler"] = how_sure(obs, rules, loo)
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


def study2_below_and_by_wording():
    """Post hoc looks at the trigger list's gain below the budget, and at how far the +51.3 varies by wording."""
    s2, _ = study2.load("data/study2")
    s2b, _ = study2.load("data/study2b")
    wants = lambda r: r["prompt"] != "decoy"
    is_w = lambda w: (lambda r: r["wording"] == w)
    generic = [r for r in s2b if r["library"] == 50 and r["prompt"] == "generic"]
    count = lambda w: {"loads": int(sum(r["y"] for r in generic if r["wording"] == w)), "runs": sum(r["wording"] == w for r in generic)}
    rate = lambda w, prefix: float(np.mean([r["y"] for r in s2 if wants(r) and r["library"] == 300 and r["prefix"] == prefix and r["wording"] == w]))
    return {
        "label": "Exploratory and post hoc. No correction.",
        "study2_trigger_vs_minimal_library_0_or_50": study2.contrast(s2, lambda r: wants(r) and r["library"] < 300, is_w("trigger"), is_w("minimal")),
        "study2b_trigger_vs_minimal_library_50": study2.contrast(s2b, lambda r: r["library"] == 50, is_w("trigger"), is_w("minimal")),
        "study2b_library_50_generic_prompts": {w: count(w) for w in ("minimal", "trigger")},
        "study2_raw_aa_minus_zz_at_300": {w: rate(w, "aa") - rate(w, "zz") for w in WORDINGS},
    }


def reversal_cells():
    """Load rate at each point of the reversal figures: the mean across targets and its 95% interval across targets."""
    def point(rows, keep):
        cell = [r for r in rows if keep(r)]
        spread = by_rule(np.array([np.mean([r["y"] for r in cell if r["stem"] == s]) for s in sorted({r["stem"] for r in cell})]))
        return {"target_mean": spread["estimate"], "ci": spread["ci"], "targets": spread["g"], "runs": len(cell), "pooled": float(np.mean([r["y"] for r in cell]))}

    s2, _ = study2.load("data/study2")
    s2b, _ = study2.load("data/study2b")
    in_view = lambda r: r["prompt"] != "decoy" and study2.visible(r)
    late = lambda r: r["prompt"] != "decoy" and r["library"] == 300 and r["prefix"] == "zz"
    return {
        "study2": {w: [point(s2, lambda r, w=w: in_view(r) and r["wording"] == w), point(s2, lambda r, w=w: late(r) and r["wording"] == w)] for w in WORDINGS},
        "study2b": {w: [point(s2b, lambda r, w=w, n=n: r["library"] == n and r["wording"] == w) for n in (50, 300)] for w in ("minimal", "short_trigger", "trigger")},
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="results/exploratory.json")
    a = p.parse_args()
    res = {"study1": study1(), "study2_where_calls_go": study2_where_calls_go(), "study2_below_and_by_wording": study2_below_and_by_wording(), "reversal_cells": reversal_cells()}
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
