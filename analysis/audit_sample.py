"""Draws the blind audit sample, stratified by rule and outcome, with every arm label removed.

    python3 -m analysis.audit_sample data/study1 --n 100 --out docs/audit/sample.json

Run before any contrast is computed, so a checker fix cannot follow a look at the results. The key linking items to arms
stays out of the file the reader sees.
"""

import argparse
import json
import random
from pathlib import Path

from study1.design import bare_rule
from study1.rules import BY_ID, score
from study1.trace import Trace


def main():
    p = argparse.ArgumentParser()
    p.add_argument("batch")
    p.add_argument("--n", type=int, default=100)
    p.add_argument("--out", required=True)
    a = p.parse_args()
    batch = Path(a.batch)
    strata = {}
    for line in (batch / "manifest.jsonl").read_text().splitlines():
        row = json.loads(line)
        path = batch / "traces" / f"{row['run_id']}.json"
        if not path.exists():
            continue
        s = score(Trace.from_json(json.loads(path.read_text())["trace"]))
        for t in row["targets"]:
            strata.setdefault((t["rule"], s[t["rule"]]), []).append((row["run_id"], t["reason"]))
    rng = random.Random("audit")
    keys = sorted(strata)
    picks = []
    while len(picks) < a.n and any(strata.values()):
        for k in keys:
            if strata[k] and len(picks) < a.n:
                run_id, reason = strata[k].pop(rng.randrange(len(strata[k])))
                picks.append((k[0], k[1], run_id, reason))
    rng.shuffle(picks)
    items, key = [], []
    for i, (rule, verdict, run_id, reason) in enumerate(picks):
        doc = json.loads((batch / "traces" / f"{run_id}.json").read_text())
        tr = doc["trace"]
        items.append({
            "item": i, "rule_requirement": bare_rule(BY_ID[rule]), "checker_verdict": verdict,
            "commands": tr["commands"], "final_message": tr["final_message"], "commits": tr["commits"],
            "branch": tr["branch"], "tool_calls": tr["calls"], "new_or_changed_files": tr["after"],
        })
        key.append({"item": i, "rule": rule, "run_id": run_id, "reason": reason, "checker_verdict": verdict})
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(items, indent=1))
    out.with_suffix(".key.json").write_text(json.dumps(key, indent=1))
    print(len(items), "items written")


if __name__ == "__main__":
    main()
