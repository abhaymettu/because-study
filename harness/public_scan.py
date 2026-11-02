"""Scans what would go public for private strings, including inside gzip files and every commit.

    python3 -m harness.public_scan [--history]

Generic patterns are here. Your own names and projects come from the untracked harness/needles.local, one per line.
"""

import argparse
import collections
import gzip
import re
import subprocess
from pathlib import Path

PATTERNS = [r"/Users/", r"/home/\w+", r"account_uuid", r"device_id", r"[\w.+-]+@(?:gmail|icloud|outlook|yahoo)\.com", r"sk-ant-", r"ghp_"]
ALLOW = (re.compile(r"harness/public_scan\.py$"),)


def needles():
    local = Path(__file__).with_name("needles.local")
    extra = [re.escape(l.strip()) for l in local.read_text().splitlines() if l.strip()] if local.exists() else []
    return re.compile("|".join(PATTERNS + extra), re.I)


def git(*args):
    return subprocess.run(["git", *args], capture_output=True, check=True).stdout


def scan(rev, pattern, hits):
    files = git("ls-tree", "-r", "--name-only", rev).decode().splitlines()
    args = [f"{rev}:{f}" for f in files if not any(a.search(f) for a in ALLOW)]
    for f, spec in zip([s.split(":", 1)[1] for s in args], args):
        blob = git("show", spec)
        if f.endswith(".gz"):
            blob = gzip.decompress(blob)
        for m in pattern.finditer(blob.decode(errors="replace")):
            hits[(m.group(0).lower(), f.split("/")[0] + "/" + (f.split("/")[1] if "/" in f else ""))] += 1
    return len(files)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--history", action="store_true")
    a = p.parse_args()
    pattern = needles()
    revs = git("rev-list", "--all").decode().split() if a.history else ["HEAD"]
    hits, count = collections.Counter(), 0
    for rev in revs:
        count += scan(rev, pattern, hits)
    print(f"{len(revs)} commits, {count} files: {sum(hits.values())} hits")
    for (needle, where), n in hits.most_common(60):
        print(f"{n:6} {needle!r} in {where}")


if __name__ == "__main__":
    main()
