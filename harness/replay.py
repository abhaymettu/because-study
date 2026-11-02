"""The whole pipeline with no subscription, in under a minute: fresh repos, the real harness, the real checkers, the real analysis.

    python3 -m harness.replay [--runs 20]

A stand-in agent (`replay_agent.py`) re-applies what the recorded agent did, so the harness builds each run's repo from the
manifest and fixtures, collects a trace and scores it. Those verdicts must match the committed ones. Then the registered
analyses rerun on every committed trace and must match the committed results.
"""

import argparse
import json
import sys
import tempfile
from pathlib import Path

from analysis import study1, study2, study2b
from study1.rules import POOL_FINAL, score
from study1.trace import Trace

from .batch import run_row

ROOT = Path(__file__).resolve().parent.parent


def replay_runs(batch, n, compare):
    """Replays an evenly spaced sample of a batch's committed runs. Returns (runs, agreeing verdicts, verdicts)."""
    rows = [json.loads(l) for l in (batch / "manifest.jsonl").read_text().splitlines()]
    rows = [r for r in rows if (batch / "traces" / f"{r['run_id']}.json").exists()]
    rows = rows[:: max(1, len(rows) // n)][:n]
    agree, total = 0, 0
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        capture = tmp / "capture"
        capture.mkdir()
        for row in rows:
            recorded = batch / "traces" / f"{row['run_id']}.json"
            raw = batch / "raw" / f"{row['run_id']}.jsonl.gz"
            command = lambda *_, recorded=recorded, raw=raw: [sys.executable, str(ROOT / "harness" / "replay_agent.py"), str(recorded), str(raw)]
            opts = {"fixtures": ROOT / "fixtures", "model": "replay", "effort": "", "max_turns": 0, "tools": "", "timeout": 60, "command": command}
            run_row(row, opts, None, capture, tmp)
            new = json.loads((tmp / "traces" / f"{row['run_id']}.json").read_text())["trace"]
            old = json.loads(recorded.read_text())["trace"]
            a, t = compare(row, old, new)
            agree, total = agree + a, total + t
    return len(rows), agree, total


def compare_study1(_, old, new):
    a, b = score(Trace.from_json(old)), score(Trace.from_json(new))
    return sum(a[r] == b[r] for r in POOL_FINAL), len(POOL_FINAL)


def compare_study2(row, old, new):
    name = study2.target_name(row)
    return int(study2.loaded(old, name) == study2.loaded(new, name)), 1


def numbers(tree, prefix=""):
    """Every point estimate in a results document, by path. P-values from permutations vary with their count, so they stay out."""
    out = {}
    if isinstance(tree, dict):
        for k, v in tree.items():
            if k not in ("randomization_p", "cost"):
                out.update(numbers(v, f"{prefix}/{k}"))
    elif isinstance(tree, float):
        out[prefix] = tree
    return out


def compare_results(res, path):
    want = numbers(json.loads(path.read_text()))
    got = numbers(json.loads(json.dumps(res, default=float)))
    wrong = [k for k in want if k not in got or abs(want[k] - got[k]) > 1e-9]
    return len(want) - len(wrong), len(want), wrong


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--runs", type=int, default=20)
    p.add_argument("--data", default=str(ROOT / "data"))
    p.add_argument("--results", default=str(ROOT / "results"))
    a = p.parse_args()
    data, results = Path(a.data).resolve(), Path(a.results)
    failed = False
    for name, compare, n in (("study1", compare_study1, a.runs), ("study2", compare_study2, a.runs // 2), ("study2b", compare_study2, a.runs // 2)):
        runs, agree, total = replay_runs(data / name, n, compare)
        print(f"{name}: replayed {runs} runs through the harness, {agree} of {total} verdicts match the committed traces")
        failed |= agree != total
    for name, analyze in (("study1", lambda b: study1.analyze(b, perms=100)), ("study2", study2.analyze), ("study2b", study2b.analyze)):
        path = results / f"{name}.json"
        if not path.exists():
            print(f"{name}: no committed results yet")
            continue
        res = analyze(data / name)
        same, total, wrong = compare_results(res, path)
        print(f"{name}: reran the registered analysis, {same} of {total} estimates match {path.name}")
        if "reading" in res:
            print(f"reading: {res['reading']}")
        failed |= bool(wrong)
        for k in wrong[:5]:
            print("  differs:", k)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
