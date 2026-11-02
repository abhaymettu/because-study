"""One page with every reported number and where it comes from: python3 -m analysis.numbers > results/NUMBERS.md"""

import json
from pathlib import Path

R = Path("results")


def load(name):
    path = R / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else None


def pts(r):
    return f"{100 * r['estimate']:+.1f} [{100 * r['ci'][0]:+.1f}, {100 * r['ci'][1]:+.1f}]"


def row(label, r):
    holm = f"{r['p_holm']:.3f}" if "p_holm" in r else ""
    return f"| {label} | {pts(r)} | {r['p']:.3f} | {holm} |"


def rate(x, places=3):
    """A rate with no runs behind it is not a number, so it does not print as one."""
    return "n/a" if x is None or x != x else f"{x:.{places}f}"


def plain(d):
    """A flat dictionary as readers want it: 'used 598, missing 0'. Rates keep three decimals."""
    return ", ".join(f"{k} {v if isinstance(v, int) else rate(v)}" for k, v in d.items())


def small_p(p):
    return "under .001" if p < 0.001 else f"{p:.3f}"


def rule_by_factor(b):
    """The cells with raw p under .01 and each factor's largest tick. The whole table is in the JSON."""
    head = ["| Contrast | Rule | Points | Run-clustered SE | Raw p | Holm, 72 cells | Holm, 99 cells |", "|---|---|---|---|---|---|---|"]
    line = lambda c: (f"| {c['contrast']} | {c['rule']} | {100 * c['estimate']:+.1f} | {100 * c['se']:.1f} | {small_p(c['p'])} | "
                      + " | ".join(small_p(c[k]) if k in c else "outside" for k in ("p_holm_72", "p_holm_99")) + " |")
    low = sorted((c for c in b["cells"] if c["p"] < 0.01), key=lambda c: c["p"])
    return ["## Rule by factor, exploratory and post hoc (`results/exploratory.json`, `rule_by_factor`)", "",
            f"Nobody registered these. The rule-level estimates are the ticks in the effects figure. {b['holm_72']} {b['holm_99']} `real_minus_placebo` is a difference of two cells already counted.", "",
            "Cells with raw p under .01.", "", *head, *[line(c) for c in low], "", "The largest tick for each factor.", "", *head, *[line(c) for c in b["extreme_tick_per_factor"].values()], ""]


def how_sure(h):
    q = h["real_vs_filler_across_rules"]
    bar = lambda v: f"[{100 * v[0]:+.2f}, {100 * v[1]:+.2f}]"
    loo = h["real_vs_none_upper_bound_leave_one_rule_out"]
    tost = h["tost_real_minus_placebo"]
    return ["## How sure the reason results are, exploratory and post hoc (`results/exploratory.json`, `how_sure_real_vs_filler`)", "",
            f"- Real vs filler across the nine rules: Cochran Q {q['cochran_q']:.2f} on {q['df']} df, p {q['p']:.3f}. DerSimonian-Laird tau {100 * q['tau']:.2f} points.",
            f"- Random-effects mean {100 * q['mean']:+.2f} points, Hartung-Knapp {bar(q['hartung_knapp_ci'])}. Prediction interval for a new rule {bar(q['prediction_interval'])}.",
            f"- Real vs no clause, upper bound {100 * h['real_vs_none_upper_bound']:+.2f}. Leaving one rule out and refitting moves it from {100 * loo['lowest']:+.2f} to {100 * loo['highest']:+.2f}.",
            f"- TOST on real minus placebo: p {tost['at_4.5_points']:.3f} at a margin of 4.5 points, p {tost['at_5_points']:.3f} at 5.", ""]


def below_and_by_wording(s):
    counts = s["study2b_library_50_generic_prompts"]
    return ["## The trigger list below the budget, exploratory and post hoc (`results/exploratory.json`, `study2_below_and_by_wording`)", "",
            f"- Study 2, trigger vs minimal strictly below the budget (library 0 or 50): {pts(s['study2_trigger_vs_minimal_library_0_or_50'])}.",
            f"- Study 2b, trigger vs minimal at library 50: {pts(s['study2b_trigger_vs_minimal_library_50'])}.",
            "- Study 2b at library 50 on generic prompts: " + ", ".join(f"{w} {c['loads']}/{c['runs']}" for w, c in counts.items()) + ".",
            "- Study 2, raw `aa` minus `zz` at 300 by wording, points: " + ", ".join(f"{w} {100 * v:+.1f}" for w, v in s["study2_raw_aa_minus_zz_at_300"].items()) + ".", ""]


def calls_table(where):
    out = ["| Batch | Description | Runs | Target loaded | Other skill only | No skill |", "|---|---|---|---|---|---|"]
    for batch, cells in where.items():
        for label, c in cells.items():
            out.append(f"| {batch} | {label.replace('_', ' ')} | {c['n']} | {rate(c['target_loaded'])} | {rate(c['other_skill_only'])} | {rate(c['no_skill'])} |")
    return out


def listing_check(lc):
    out = ["## The listing rule, offline (`results/listing_check.json`)", "", "From the manifests and fixtures, with no agent and no capture: does the rule predict `probe_hit`?", "",
           "| Batch | Usage counted | Earlier runs' calls only | No usage | Chars left at a late target's turn at 300: median, p90, max |", "|---|---|---|---|---|"]
    for batch, r in lc["batches"].items():
        left = r["chars_left_at_target_turn_at_300_skills"].get("zz")
        out.append(f"| {batch} | {r['hits']} of {r['total']} | {r['hits_earlier_runs_only']} | {r['hits_no_usage']} | {left['median']:g}, {left['p90']:g}, {left['max']} |")
    return out + [""]


def study2c(c):
    out = ["## Study 2c (`results/study2c.json`)", "", f"Runs: {plain(c['runs'])}. Registered reading: {c['reading']}.", f"Description reached the model when the budget was raised: {rate(c['description_reached_model_when_raised'])}.", "", *HEAD]
    out += [row(k, r) for k, r in c["family"].items()] + [row(f"{k} ({r['g']} targets)", r) for k, r in c["secondary"].items()]
    out += ["", "| Budget / wording | load rate | n | description reached model | other skill only | no skill | cost per run |", "|---|---|---|---|---|---|---|"]
    for k, g in c["grid"].items():
        out.append(f"| {k} | {rate(g['recall'])} | {g['n']} | {rate(g['description_reached_model'])} | {rate(g['other_skill_only'])} | {rate(g['no_skill'])} | ${g['cost_per_run']:.3f} |")
    return out + [""]


def haiku(h):
    runs = h["runs"]
    in_manifest = sum(runs[k] for k in ("used", "missing", "error", "leak"))
    return ["## Haiku replication (`results/study1haiku.json`), sign only", "", f"Runs {runs['used']} used of {in_manifest} in the manifest ({runs['missing']} not run, {runs['leak']} excluded by the leak scan). "
            f"Real vs filler {pts(h['confirmatory']['real_vs_filler'])}, placebo vs filler {pts(h['confirmatory']['placebo_vs_filler'])}.", ""]


HEAD = ["| Contrast | Points [95% CI] | p | Holm p |", "|---|---|---|---|"]


def main():
    s1, s2, s2b, ex, cal, h, c, lc = (load(n) for n in ("study1", "study2", "study2b", "exploratory", "calibration", "study1haiku", "study2c", "listing_check"))
    out = ["# Every reported number", "", "Generated by `python3 -m analysis.numbers` from `results/*.json`. Do not edit by hand.", "",
           "`+0.0 [+0.0, +0.0]` with p 1.000 is a tie at a bound across targets, where every target sits at 0% or at 100%, and not a precise estimate.", ""]
    pc = s1["positive_control"]
    out += ["## Study 1 (`results/study1.json`)", "", f"Runs {s1['runs']['used']}, focal observations {s1['observations']}, overall focal compliance {s1['compliance']:.3f}.",
            f"Positive control: named in the prompt {pc['named_in_prompt']:.3f} (n {pc['n_named']}), no rule {pc['no_rule']:.3f} (n {pc['n_no_rule']}).",
            f"Registered reading: {s1['reading']}.", "", *HEAD]
    for k, r in s1["confirmatory"].items():
        out.append(row(k, r))
    out += [row("placebo minus half of real (H3, gated)", s1["retention_placebo_minus_half_real"]), row("real minus placebo", s1["real_minus_placebo"]),
            row("real vs no clause", s1["real_vs_none"]), row("placebo vs no clause", s1["placebo_vs_none"])]
    out += ["", f"TOST on real minus placebo at 5 points: p = {s1['real_minus_placebo']['tost_p_at_5_points']:.3f}. Randomization p: {s1['randomization_p']['real_vs_filler']:.3f} (real), {s1['randomization_p']['placebo_vs_filler']:.3f} (placebo).",
            "", "Family 2, Holm across nine.", "", *HEAD]
    out += [row(k, r) for k, r in s1["family_2"].items()]
    out += ["", "Moderator, reason by pressure (secondary, no significance claim).", ""] + [f"- {k}: {pts(r)}" for k, r in s1["moderator_pressure"].items()]
    out += ["", "Run-level factors net of unshown rules.", ""] + [f"- {k}: {pts(r)}" for k, r in s1["run_level_net_of_unshown"].items()]
    out += ["", "| Rule | Shown | No rule | Named in prompt | n shown |", "|---|---|---|---|---|"]
    for k, v in s1["per_rule"].items():
        out.append(f"| {k} | {v['shown']:.2f} | {v['no_rule']:.2f} | {v['named_in_prompt']:.2f} | {v['n']} |")
    out += ["", "Ballast rule compliance, not analyzed: " + ", ".join(f"{k} {v:.2f}" for k, v in s1["ballast_compliance"].items()) + ".",
            f"Cost: ${s1['cost']['api_equivalent_usd']:.2f} API-equivalent, mean {s1['cost']['turns']:.1f} turns, {s1['cost']['seconds']:.1f} s per run, tests pass {s1['cost']['tests_pass']:.3f}.", ""]
    out += ["## Study 2 (`results/study2.json`)", "", f"Runs: {plain(s2['runs'])}.", "", *HEAD] + [row(k, r) for k, r in s2["family"].items()] + [row(f"{k} ({r['g']} targets)", r) for k, r in s2["secondary"].items()]
    out += ["", "`C5`'s key is historical: it compares trigger and minimal at 300 with a late name, where a short description can still fit.",
            "", f"Load rate by prompt: {plain(s2['by_prompt'])}.", f"Description reached the model at 300 skills: {plain(s2['description_reached_model'])}.", "", "| Library / prefix | minimal | padded | trigger | trigger_not | directive |", "|---|---|---|---|---|---|"]
    for lib in (0, 50, 300):
        for pre in ("aa", "zz"):
            cells = [s2["grid"][f"{lib}/{pre}/{w}"] for w in ("minimal", "padded", "trigger", "trigger_not", "directive")]
            out.append(f"| {lib} / {pre} | " + " | ".join(f"{c['recall']:.2f} (n {c['n']})" for c in cells) + " |")
    out += ["", "Prompt type by wording, description in view (secondary).", "", "| Prompt | minimal | padded | trigger | trigger_not | directive |", "|---|---|---|---|---|---|"]
    for prompt in ("keyword", "generic", "indirect"):
        cells = [s2["prompt_by_wording_visible"][f"{prompt}/{w}"] for w in ("minimal", "padded", "trigger", "trigger_not", "directive")]
        out.append(f"| {prompt} | " + " | ".join(f"{c['recall']:.2f} (n {c['n']})" for c in cells) + " |")
    out += ["", "## Study 2b (`results/study2b.json`)", "", f"Runs: {plain(s2b['runs'])}. Registered reading: {s2b['reading']}.", "", *HEAD] + [row(k, r) for k, r in s2b["family"].items()]
    out += ["", "The same contrasts within each prompt type (secondary, no correction, no significance claim).", "", *HEAD] + [row(f"{k} ({r['g']} targets)", r) for k, r in s2b["secondary"].items()]
    out += ["", "| Library / wording | load rate | n | description reached model | load when reached | load when not |", "|---|---|---|---|---|---|"]
    for k, g in s2b["grid"].items():
        out.append(f"| {k} | {rate(g['recall'])} | {g['n']} | {rate(g['description_reached_model'])} | {rate(g['recall_described'])} | {rate(g['recall_not_described'])} |")
    e = ex["study1"]
    w = e["sensitivity_write_tool_repo_only"]
    out += ["", "## Exploratory and sensitivity (`results/exploratory.json`), never to be stated as registered", "",
            f"- `write_tool` on repo paths only: {w['verdicts_changed']} verdicts change; real {pts(w['real_vs_filler'])}, placebo {pts(w['placebo_vs_filler'])}.",
            f"- Rule identity: focal compliance from {e['rule_identity']['lowest']:.2f} to {e['rule_identity']['highest']:.2f}, SD {e['rule_identity']['sd']:.2f}.",
            f"- Having the rule at all, shown minus no rule: {pts(e['having_the_rule_at_all']['effect'])}.",
            f"- Named in the prompt minus shown in the file: {pts(e['named_in_prompt_vs_in_file']['effect'])}, higher on {e['named_in_prompt_vs_in_file']['rules_higher']} of 9 rules, 3 to 11 runs per rule.",
            "- Leave one rule out, real vs filler: " + ", ".join(f"{k} {100 * v['real']:+.1f}" for k, v in e["sensitivity_leave_one_rule_out"].items()) + ".",
            "- Mixed model: `results/robust.txt`.", "", "Where calls go at 300 skills.", "", *calls_table(ex["study2_where_calls_go"]), ""]
    out += rule_by_factor(e["rule_by_factor"]) + how_sure(e["how_sure_real_vs_filler"]) + below_and_by_wording(ex["study2_below_and_by_wording"])
    if lc:
        out += listing_check(lc)
    if c:
        out += study2c(c)
    if cal:
        out += ["## Calibration on the real assignment (`results/calibration.json`)", "", f"False positive rate of the registered test at .05 with no planted effect: {cal['no_effect']['p_under_05']:.3f} over {cal['sims']} simulations. Run-level test: {cal['run_level_no_effect_p_under_05']:.3f}.", ""]
        out += [f"- {k}: power {v['p_under_05']:.2f}, Holm worst case {v['p_holm_under_05']:.2f}" for k, v in cal.items() if k.startswith("effect=")]
        out.append("")
    if h:
        out += haiku(h)
    print("\n".join(out))


if __name__ == "__main__":
    main()
