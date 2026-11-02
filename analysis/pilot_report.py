"""Off-ceiling and baseline read for a pilot batch: python3 -m analysis.pilot_report data/pilot1"""

import json
import sys
from collections import defaultdict
from pathlib import Path

from study1.rules import ALL_RULES, score
from study1.trace import Trace


def main():
    out = Path(sys.argv[1])
    rows = [json.loads(l) for l in (out / "manifest.jsonl").read_text().splitlines()]
    ids = {t["rule"] for row in rows for t in row["targets"]}
    pool = [r for r in ALL_RULES if r.id in ids]
    shown, unshown, ctrl = defaultdict(list), defaultdict(list), defaultdict(list)
    by = defaultdict(list)
    cost, turns, secs, tests, leaks, status = [], [], [], [], set(), defaultdict(int)
    for row in rows:
        path = out / "traces" / f"{row['run_id']}.json"
        if not path.exists():
            continue
        doc = json.loads(path.read_text())
        rec = doc["record"]
        status[rec["status"]] += 1
        cost.append(rec["cost_usd"] or 0)
        turns.append(rec["turns"] or 0)
        secs.append(rec["duration_s"])
        tests.append(rec["tests_pass"])
        leaks.update(rec["capture"]["leaks"])
        s = score(Trace.from_json(doc["trace"]))
        targets = {t["rule"]: t for t in row["targets"]}
        for r in pool:
            if r.id in targets:
                t = targets[r.id]
                shown[r.id].append(s[r.id])
                for factor in ("reason", "modal", "prefix", "case", "example"):
                    by[(factor, t[factor])].append(s[r.id])
                by[("length", row["length"])].append(s[r.id])
                by[("pressure", row["pressure"])].append(s[r.id])
                by[("cost", r.cost)].append(s[r.id])
            elif r.id == row["control_rule"]:
                ctrl[r.id].append(s[r.id])
            else:
                unshown[r.id].append(s[r.id])
    mean = lambda x: sum(x) / len(x) if x else float("nan")
    n = len(cost)
    print(f"runs {n} status {dict(status)} cost/run ${mean(cost):.3f} turns {mean(turns):.1f} secs {mean(secs):.0f} "
          f"tests_pass {mean(tests):.2f} leaks {sorted(leaks)}")
    print(f"{'rule':22}{'cost':8}{'shown':>7}{'n':>5}{'base':>7}{'n':>5}{'ctrl':>7}")
    for r in sorted(pool, key=lambda r: mean(shown[r.id])):
        print(f"{r.id:22}{r.cost:8}{mean(shown[r.id]):7.2f}{len(shown[r.id]):5}{mean(unshown[r.id]):7.2f}"
              f"{len(unshown[r.id]):5}{mean(ctrl[r.id]):7.2f}")
    print()
    for key in sorted(by):
        print(f"{key[0]:10}{key[1]:12}{mean(by[key]):6.3f} n={len(by[key])}")
    print("overall", round(mean([v for vals in shown.values() for v in vals]), 3))


if __name__ == "__main__":
    main()
