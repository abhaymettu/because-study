"""Removes the account and device ids Claude Code puts in each request from captures kept before the harness dropped them.

    python3 -m harness.scrub_captures data

Idempotent, and it writes gzip with a fixed mtime so the same input always gives the same bytes.
"""

import gzip
import io
import json
import sys
from pathlib import Path


def scrub(blob):
    doc = json.loads(gzip.decompress(blob))
    (doc.get("request") or {}).pop("metadata", None)
    out = io.BytesIO()
    with gzip.GzipFile(fileobj=out, mode="wb", mtime=0) as f:
        f.write(json.dumps(doc).encode())
    return out.getvalue()


def main():
    count = 0
    for path in Path(sys.argv[1]).glob("*/captures/*.json.gz"):
        new = scrub(path.read_bytes())
        if new != path.read_bytes():
            path.write_bytes(new)
            count += 1
    print(count, "captures changed")


if __name__ == "__main__":
    main()
