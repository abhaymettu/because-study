"""python3 -m study2.make_manifest <study> <n>"""

import json
import sys
from pathlib import Path

from .design import ROOT, assign

out = Path(ROOT, "data", sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
rows = assign(sys.argv[1], int(sys.argv[2]))
(out / "manifest.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
print(out / "manifest.jsonl", len(rows))
