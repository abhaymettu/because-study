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

from .agent_run import is_rate_limited, run_agent

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
        "max_turns": 40,
        "timeout": 600,
        "tools": "Bash,Read,Edit,Write,Glob,Grep",
        "email": os.environ.get("BECAUSE_ACCOUNT_EMAIL"),
    }
    quota = Quota()
    stop = threading.Event()
    queue = list(todo)
    qlock = threading.Lock()
    log = open(out / "batch.log", "a")
    counters = {"done": 0, "ok": 0, "cost": 0.0, "lost": 0}

    def worker(i):
        capture = Path("/private/tmp/because-runs") / f".capture-{os.getpid()}-{i}"
        proxy, port = start_proxy(capture)
        try:
            while not stop.is_set():
                with qlock:
                    if not queue:
                        return
                    row = queue.pop(0)
                text, _, _ = render_file(row)
                task = next(t for t in json.loads((FIXTURES / "tasks.json").read_text()) if t["id"] == row["task"])
                n = int(row["run_id"].rsplit("-", 1)[1])
                rec = run_agent(row["run_id"], task["repo"], text, render_prompt(row), opts, port, capture, out,
                                keep_capture=n % a.keep_capture_every == 0)
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
