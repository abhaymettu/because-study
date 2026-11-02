"""Write a batch's assignment before any of its runs: python3 -m study1.make_manifest <study> <n> [--pool a,b,c]"""

import argparse
import json

from .design import ROOT, assign


def main():
    p = argparse.ArgumentParser()
    p.add_argument("study")
    p.add_argument("n", type=int)
    p.add_argument("--pool")
    p.add_argument("--k", type=int, default=8)
    a = p.parse_args()
    out = ROOT / "data" / a.study
    out.mkdir(parents=True, exist_ok=True)
    rows = assign(a.study, a.n, a.pool.split(",") if a.pool else None, k=a.k)
    (out / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(out / "manifest.jsonl", len(rows))


if __name__ == "__main__":
    main()
