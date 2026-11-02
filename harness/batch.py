"""Run a manifest's rows through isolated agents, resumable, watching the weekly quota.

    python3 -m harness.batch data/pilot/manifest.jsonl --workers 3 [--limit N]

A row whose trace exists is skipped, so an interrupted batch continues where it stopped. Rows lost to infrastructure
(rate limit, API error) leave no trace and rerun; the rerun is blind to arm because it is decided from the error alone.
"""

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from study1.design import FIXTURES, render_file, render_prompt
from study2.design import plan as study2_plan
from study2.run import build_workbench as study2_repo

from .agent_run import RUN_ROOT, is_rate_limited, run_agent

SLOW_BELOW = 0.40
STOP_BELOW = 0.25


class Quota:
    """Reads the seven-day utilization header from captured responses."""

    def __init__(self):
        self.lock = threading.Lock()
        self.remaining = None

    def update(self, ratelimit):
        for k, v in ratelimit.items():
            if "7d-utilization" in k.lower():
                with self.lock:
                    self.remaining = 1 - float(v)


def start_proxy(capture_dir):
    capture_dir.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [sys.executable, str(Path(__file__).parent / "capture_proxy.py"), "--port", "0", "--out", str(capture_dir)],
        stdout=subprocess.PIPE, text=True,
    )
    return proc, int(proc.stdout.readline())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("manifest")
    p.add_argument("--workers", type=int, default=3)
    p.add_argument("--limit", type=int)
    p.add_argument("--model", default="claude-sonnet-5-5")
    p.add_argument("--effort", default="medium")
    p.add_argument("--keep-capture-every", type=int, default=25)
    p.add_argument("--expect-cli", help="abort if a run reports any other Claude Code version")
    p.add_argument("--max-quota-points", type=float, default=15, help="stop after this many points of the seven-day window")
    p.add_argument("--tools", default="Bash,Read,Edit,Write,Glob,Grep")
    p.add_argument("--max-turns", type=int, default=40)
    a = p.parse_args()

    manifest = Path(a.manifest)
    out = manifest.parent
    rows = [json.loads(l) for l in manifest.read_text().splitlines()]
    todo = [r for r in rows if not (out / "traces" / f"{r['run_id']}.json").exists()]
    if a.limit:
        todo = todo[: a.limit]
    print(f"{len(rows)} in manifest, {len(todo)} to run", flush=True)

    opts = {
        "fixtures": FIXTURES,
        "config_dir": os.environ.get("CLAUDE_CONFIG_DIR"),
        "model": a.model,
        "effort": a.effort,
        "max_turns": a.max_turns,
        "timeout": 600,
        "tools": a.tools,
        "email": os.environ.get("BECAUSE_ACCOUNT_EMAIL"),
    }
    quota = Quota()
    stop = threading.Event()
    queue = list(todo)
    qlock = threading.Lock()
    log = open(out / "batch.log", "a")
    counters = {"done": 0, "ok": 0, "cost": 0.0, "lost": 0}

    def worker(i):
        capture = RUN_ROOT / f".capture-{os.getpid()}-{i}"
        proxy, port = start_proxy(capture)
        try:
            while not stop.is_set():
                with qlock:
                    if not queue:
                        return
                    row = queue.pop(0)
                n = int(row["run_id"].rsplit("-", 1)[1])
                if row.get("study") == 2:
                    work_plan = study2_plan(row)
                    rec = run_agent(row["run_id"], None, None, work_plan["prompt"], opts, port, capture, out,
                                    keep_capture=n % a.keep_capture_every == 0, setup=lambda d, e: study2_repo(work_plan, d, e))
                else:
                    text, _, _ = render_file(row)
                    task = next(t for t in json.loads((FIXTURES / "tasks.json").read_text()) if t["id"] == row["task"])
                    rec = run_agent(row["run_id"], task["repo"], text, render_prompt(row), opts, port, capture, out,
                                    keep_capture=n % a.keep_capture_every == 0)
                if a.expect_cli and rec["cli"] and rec["cli"] != a.expect_cli:
                    print(f"cli is {rec['cli']}, expected {a.expect_cli}: stopping", flush=True)
                    stop.set()
                if rec["model"] and rec["model"] != a.model:
                    print(f"model is {rec['model']}, expected {a.model}: stopping", flush=True)
                    stop.set()
                quota.update(rec["capture"]["ratelimit"])
                lost = rec["status"] == "error" or is_rate_limited(rec)
                if lost:
                    (out / "traces" / f"{row['run_id']}.json").rename(out / "traces" / f"{row['run_id']}.lost-{int(time.time())}")
                    with qlock:
                        queue.append(row)
                        counters["lost"] += 1
                    if counters["lost"] > 25:
                        stop.set()
                    time.sleep(120 if is_rate_limited(rec) else 15)
                with qlock:
                    counters["done"] += 1
                    counters["ok"] += rec["status"] == "ok"
                    counters["cost"] += rec["cost_usd"] or 0
                    line = (f"{time.strftime('%H:%M:%S')} {row['run_id']} {rec['status']} {rec['duration_s']}s "
                            f"turns={rec['turns']} ${rec['cost_usd']} leaks={rec['capture']['leaks']} "
                            f"remaining={quota.remaining} total=${counters['cost']:.2f}")
                    print(line, flush=True)
                    log.write(line + "\n")
                    log.flush()
                with qlock:
                    if quota.remaining is not None:
                        counters.setdefault("quota_start", quota.remaining)
                        spent = counters["quota_start"] - quota.remaining
                if quota.remaining is not None and spent * 100 >= a.max_quota_points:
                    print(f"{spent * 100:.0f} points of the seven-day window used, stopping", flush=True)
                    stop.set()
                if quota.remaining is not None and quota.remaining < STOP_BELOW:
                    print("seven-day quota under the stop line, stopping", flush=True)
                    stop.set()
                elif quota.remaining is not None and quota.remaining < SLOW_BELOW:
                    time.sleep(60)
        finally:
            proxy.terminate()

    with ThreadPoolExecutor(a.workers) as pool:
        list(pool.map(worker, range(a.workers)))
    print(json.dumps(counters), flush=True)


if __name__ == "__main__":
    main()
