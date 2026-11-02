"""python3 -m study2.make_manifest <study> <n>, or <study> followup, or <study> budget <per cell> <first run number>"""

import json
import sys
from pathlib import Path

from .design import ROOT, assign, assign_budget, assign_followup

out = Path(ROOT, "data", sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
if sys.argv[2] == "followup":
    rows = assign_followup(sys.argv[1])
elif sys.argv[2] == "budget":
    rows = assign_budget(sys.argv[1], int(sys.argv[3]), int(sys.argv[4]))
else:
    rows = assign(sys.argv[1], int(sys.argv[2]))
(out / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
print(out / "manifest.jsonl", len(rows))
