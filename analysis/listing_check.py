"""Does the listing rule predict whose description reached the model? Offline: no agents, no login, no captures.

    python3 -m analysis.listing_check data/study2 data/study2b [--out results/listing_check.json]

The rule is `analysis.listing_mechanism.predict`, as written up in docs/LISTING-MECHANISM.md. Its inputs here are each batch's
manifest, the fixtures, and the bundled skills' widths stored in results/listing_mechanism.json. Each prediction is compared
with `capture.probe_hit` in the run's trace. Usage is counted three ways, since a Skill call promotes that name for later runs.
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

import numpy as np

from analysis.listing_mechanism import predict
from study2.design import BY_STEM, DISTRACTORS, description, target_name

OUT = "results/listing_check.json"
TEXTS = {d["name"]: d["description"] for d in DISTRACTORS}
CLI_BUDGET = 30000
# Usage on the account when each batch began. PREREG-STUDY2B.md names the second. The first is that minus Study 2's own four
# calls of month-end-close, and data/s2pilot/raw holds the one earlier call.
START_USAGE = {
    "study2": {"month-end-close": 1},
    "study2b": {"month-end-close": 5, "sql-database-assistant": 1, "changelog-generator": 1},
    "study2c": {},
}


def bundled_entries():
    """predict reads only the width of a built-in's entry, so a placeholder of that width stands in for its text."""
    widths = json.loads(Path("results/listing_mechanism.json").read_text())["builtins"]
    return {name: "x" * width for name, width in widths.items()}


def load_runs(batch):
    """One row per run with a trace: what the listing held, what the capture recorded, which skills it called."""
    runs = []
    for line in (batch / "manifest.jsonl").read_text().splitlines():
        row = json.loads(line)
        path = batch / "traces" / f"{row['run_id']}.json"
        if not path.exists():
            continue
        doc = json.loads(path.read_text())
        name = target_name(row)
        runs.append({
            "run": row["run_id"], "library": row["library"], "prefix": row["name_prefix"], "target": name, "budget": row.get("list_budget") or CLI_BUDGET,
            "skills": {**{d: TEXTS[d] for d in row["distractors"]}, name: description(BY_STEM[row["stem"]], row["wording"])},
            "recorded": bool(doc["record"]["capture"].get("probe_hit")),
            "called": [str(target).split(":")[-1] for tool, target in doc["trace"]["calls"] if tool == "Skill"],
        })
    return runs


def run_clock(batch, runs):
    """(start, finish) in seconds per run from batch.log, or manifest position when the log is absent. Returns (clock, source)."""
    path = batch / "batch.log"
    if not path.exists():
        return {r["run"]: (i, i) for i, r in enumerate(runs)}, "manifest order"
    clock, day, last = {}, 0, 0
    for line in path.read_text().splitlines():
        match = re.match(r"(\d+):(\d+):(\d+) (\S+) \S+ ([\d.]+)s", line)
        if match:
            now = int(match[1]) * 3600 + int(match[2]) * 60 + int(match[3])
            day += 86400 if now < last else 0
            last = now
            clock[match[4]] = (day + now - float(match[5]), day + now)
    return clock, "batch.log"


def usage_at_start(run, runs, clock, start_usage):
    """Calls by runs that had finished when this run's listing was built, on top of what the account already held."""
    began = clock[run["run"]][0]
    return Counter(start_usage) + Counter(name for other in runs if clock[other["run"]][1] < began for name in other["called"])


def score(runs, builtins, usage):
    """Returns (runs where the rule is wrong, characters left at the target's turn for each run that reached a walk)."""
    wrong, left = [], {}
    for run in runs:
        trace = {}
        kept = run["target"] in predict(run["skills"], builtins, usage(run), budget=run["budget"], trace=trace)
        if kept != run["recorded"]:
            wrong.append(run["run"])
        if run["target"] in trace:
            left[run["run"]] = trace[run["target"]]["left"]
    return wrong, left


def check(batch, builtins):
    runs = load_runs(batch)
    clock, order = run_clock(batch, runs)
    start = START_USAGE.get(batch.name, {})
    wrong, left = score(runs, builtins, lambda r: usage_at_start(r, runs, clock, start))
    wrong_earlier, _ = score(runs, builtins, lambda r: usage_at_start(r, runs, clock, {}))
    wrong_none, _ = score(runs, builtins, lambda r: {})
    at_300 = {}
    for r in runs:
        if r["library"] == 300 and r["run"] in left:
            at_300.setdefault(r["prefix"], []).append(left[r["run"]])
    return {
        "total": len(runs), "hits": len(runs) - len(wrong), "misses": wrong, "start_usage": start, "run_order_from": order,
        "hits_earlier_runs_only": len(runs) - len(wrong_earlier), "misses_earlier_runs_only": wrong_earlier,
        "hits_no_usage": len(runs) - len(wrong_none),
        "chars_left_at_target_turn_at_300_skills": {prefix: {"runs": len(v), "median": float(np.median(v)), "p90": float(np.percentile(v, 90)), "max": max(v)} for prefix, v in at_300.items()},
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("batches", nargs="+")
    p.add_argument("--out", default=OUT)
    a = p.parse_args()
    builtins = bundled_entries()
    res = {"rule": "docs/LISTING-MECHANISM.md, coded in analysis.listing_mechanism.predict", "batches": {b: check(Path(b), builtins) for b in a.batches}}
    Path(a.out).write_text(json.dumps(res, indent=1))
    for name, r in res["batches"].items():
        print(f"{name}: {r['hits']} of {r['total']} with usage counted; {r['hits_earlier_runs_only']} with only earlier runs' calls; {r['hits_no_usage']} with none. Left at 300: {r['chars_left_at_target_turn_at_300_skills']}")


if __name__ == "__main__":
    main()
