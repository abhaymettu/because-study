"""Cell counts the paper reports for Study 2 that results/*.json holds only as rates: python -m paper.counts > paper/counts.json

Reads the committed manifest and traces through the registered loader, so the rows are the rows the analysis used.
"""

import json
from collections import Counter
from pathlib import Path

from analysis.study2 import load, visible


def needles(batch):
    found = Counter()
    for path in sorted(Path(batch, "traces").glob("*.json")):
        found.update(json.loads(path.read_text())["record"]["capture"].get("leaks") or [])
    return dict(found)


def tally(rows):
    loads, runs = Counter(), Counter()
    for r in rows:
        runs[r["wording"]] += 1
        loads[r["wording"]] += int(r["y"])
    return {w: {"loads": loads[w], "runs": runs[w]} for w in sorted(runs)}


def main():
    rows, _ = load("data/study2")
    decoy = [r for r in rows if r["prompt"] == "decoy"]
    real = [r for r in rows if r["prompt"] != "decoy"]
    print(json.dumps({
        "study2": {
            "non_decoy_runs": len(real),
            "decoy_runs": len(decoy),
            "false_loads_all_decoy": sum(int(r["y"]) for r in decoy),
            "false_load_cells": [{"wording": r["wording"], "library": r["library"], "prefix": r["prefix"]} for r in decoy if r["y"]],
            "visible_non_decoy": tally([r for r in real if visible(r)]),
            "visible_decoy": tally([r for r in decoy if visible(r)]),
            "leak_needles": needles("data/study2"),
        },
        "study2b": {"leak_needles": needles("data/study2b")},
    }, indent=2))


if __name__ == "__main__":
    main()
