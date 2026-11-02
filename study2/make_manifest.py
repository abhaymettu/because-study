"""python3 -m study2.make_manifest <study> <n>, or python3 -m study2.make_manifest study2b followup"""

import json
import sys
from pathlib import Path

from .design import ROOT, assign, assign_followup

out = Path(ROOT, "data", sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
rows = assign_followup(sys.argv[1]) if sys.argv[2] == "followup" else assign(sys.argv[1], int(sys.argv[2]))
(out / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
print(out / "manifest.jsonl", len(rows))
