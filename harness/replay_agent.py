"""Stands in for the agent: re-applies one recorded run's edits to the fresh repo and prints its recorded transcript.

No model and no network, and none of the recorded shell commands run, so it is safe to point at any committed run.
"""

import gzip
import json
import subprocess
import sys
from pathlib import Path


def git(*args):
    subprocess.run(["git", *args], check=True, capture_output=True)


def apply(path, after):
    target = Path(path)
    if path in after:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(after[path])
    elif target.exists():
        target.unlink()


def main():
    trace = json.loads(Path(sys.argv[1]).read_text())["trace"]
    after = trace["after"]
    if trace["commits"] and trace["branch"] != "main":
        git("checkout", "-q", "-b", trace["branch"])
    for commit in trace["commits"]:
        for path in commit["files"]:
            apply(path, after)
            git("add", "-A", "--", path)
        git("commit", "-q", "--allow-empty", "-m", commit["message"] or "(no message)")
    for path in set(trace["before"]) | set(after):
        apply(path, after)
    with gzip.open(sys.argv[2], "rt") as f:
        sys.stdout.write(f.read())


if __name__ == "__main__":
    main()
