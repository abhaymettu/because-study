"""Writes one row per (run, shown rule) to a CSV for the mixed model: python3 -m analysis.export_long data/study1 out.csv"""

import csv
import sys

from analysis.study1 import load

obs, *_ = load(sys.argv[1])
cols = ["run", "rule", "task", "y", "reason", "modal", "prefix", "case", "example", "position", "depth", "length", "pressure", "cost", "polarity"]
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(obs)
