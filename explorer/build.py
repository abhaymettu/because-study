"""Builds the public explorer: one summary, and one small bundle per run.

    .venv/bin/python -m explorer.build --out explorer/dist [--dev]

A normal build reads a study only once its registered results file exists, so outcomes by arm cannot reach a page while
the batch is blind. --dev builds from the pilots with outcomes shuffled, and its results document is the real analysis
code run on that shuffled data.
"""

import argparse
import base64
import gzip
import hashlib
import inspect
import json
import math
import random
import re
import shutil
import time
import warnings
from contextlib import contextmanager
from pathlib import Path

import numpy as np

import analysis.study1 as A1
import analysis.study2 as A2
from analysis.audit_sample import diff
from analysis.listing_check import CLI_BUDGET
from analysis.pool_table import HIGH, LOW
from study1 import design as D1
from study1.rules import ALL_RULES, FOCAL, POOL_FINAL, score
from study1.rules import BY_ID as RULES
from study2 import design as D2

ROOT = Path(__file__).resolve().parent.parent
SOURCE = "https://github.com/abhaymettu/because-study/blob/main/"
TRIM = 6000
PRIVATE = re.compile(
    r"/Users/[^/\s\"'\\]+|(?<!github\.com/)abhay\w*|(?<!github\.com/abhay)mettu|account_uuid|device_id", re.I
)
LEVELS_1 = {
    "reason": D1.REASONS, "modal": D1.MODALS, "prefix": D1.PREFIXES, "case": D1.CASES, "example": D1.EXAMPLES,
    "position": ("top", "middle", "bottom"), "length": D1.LENGTHS, "pressure": D1.PRESSURES,
    "status": ("ok", "timeout", "max_turns"), "task": tuple(t["id"] for t in D1.tasks()),
}
OBS_FACTORS = ("reason", "modal", "prefix", "case", "example", "position")
LEVELS_2 = {
    "stem": tuple(t["stem"] for t in D2.TARGETS), "wording": D2.WORDINGS, "prefix": D2.NAME_PREFIXES, "prompt": D2.PROMPTS,
}
LEVELS_2B = {**LEVELS_2, "wording": D2.FOLLOWUP_WORDINGS, "prompt": D2.FOLLOWUP_PROMPTS}
LEVELS_2C = {**LEVELS_2B, "wording": D2.BUDGET_WORDINGS}


def write(path, doc):
    """The one way out to disk, so nothing private can reach a public file by any route."""
    text, hits = PRIVATE.subn("[redacted]", json.dumps(doc, separators=(",", ":"), allow_nan=False))
    if hits:
        print(f"{path.name}: redacted {hits} private strings")
    path.write_text(text)


def plain(x):
    """Results documents hold numpy scalars and NaN on thin data; JSON has neither."""
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    if isinstance(x, (float, np.floating)):
        return float(x) if math.isfinite(x) else None
    if isinstance(x, np.bool_):
        return bool(x)
    if isinstance(x, np.integer):
        return int(x)
    return x


def trim(text):
    return text if len(text) <= TRIM else f"{text[:TRIM]}\n\n[Trimmed here, {len(text) - TRIM:,} more characters in the raw file.]"


def transcript(path):
    """Ordered steps from the stream. A result names its call by position, so parallel calls still pair up."""
    steps, calls = [], {}
    if not path.exists():
        return steps
    with gzip.open(path, "rt") as stream:
        for line in stream:
            event = json.loads(line)
            if event.get("type") not in ("assistant", "user"):
                continue
            content = event["message"]["content"]
            for block in [{"type": "text", "text": content}] if isinstance(content, str) else content:
                kind = block["type"]
                if kind == "text" and block["text"].strip():
                    steps.append({"kind": "text" if event["type"] == "assistant" else "context", "text": trim(block["text"])})
                elif kind == "thinking" and block.get("thinking"):
                    steps.append({"kind": "thinking", "text": trim(block["thinking"])})
                elif kind == "tool_use":
                    calls[block["id"]] = len(steps)
                    steps.append({"kind": "call", "name": block["name"], "input": {k: trim(v) if isinstance(v, str) else v for k, v in block["input"].items()}})
                elif kind == "tool_result":
                    body = block.get("content") or ""
                    body = body if isinstance(body, str) else "".join(part.get("text", "") for part in body)
                    steps.append({"kind": "result", "of": calls.get(block["tool_use_id"]), "text": trim(body), "error": bool(block.get("is_error"))})
    return steps


@contextmanager
def patched(module, name, value):
    real = getattr(module, name)
    setattr(module, name, value)
    try:
        yield
    finally:
        setattr(module, name, real)


def manifest(batch):
    rows = (json.loads(line) for line in (batch / "manifest.jsonl").read_text().splitlines())
    return {row["run_id"]: row for row in rows}


def trace_doc(batch, run_id):
    return json.loads((batch / "traces" / f"{run_id}.json").read_text())


def study1(batch, results, out, rng):
    if not rng and not results.exists():
        return None
    # The registered loader decides which runs count, so the page cannot disagree with the analysis about exclusions.
    verdicts = []
    with patched(A1, "score", lambda t: verdicts.append(score(t)) or verdicts[-1]):
        loaded = A1.load(batch)
    if rng:
        for rule in verdicts[0]:
            ys = [v[rule] for v in verdicts]
            rng.shuffle(ys)
            for v, y in zip(verdicts, ys):
                v[rule] = y
        feed = iter(verdicts)
        with patched(A1, "score", lambda _: next(feed)):
            loaded = A1.load(batch)
        with patched(A1, "load", lambda _: loaded):
            doc = A1.analyze(batch, perms=20)
    else:
        doc = json.loads(results.read_text())
    obs, _, _, _, records = loaded

    rows = manifest(batch)
    for rec, verdict in zip(records, verdicts):
        write(out / "runs" / f"{rec['run_id']}.json", bundle_1(batch, rows[rec["run_id"]], rec, verdict))

    ordered = [RULES[r] for r in FOCAL] + [RULES[r] for r in POOL_FINAL if r not in FOCAL]
    ordered += [r for r in ALL_RULES if r.id not in POOL_FINAL]
    rule_ix = {r.id: i for i, r in enumerate(ordered)}
    run_ix = {rec["run_id"]: i for i, rec in enumerate(records)}
    at = lambda column, value: LEVELS_1[column].index(value)
    return {
        "results": plain(doc),
        # Computed on the confirmatory data, so a shuffled development build must not carry it.
        "exploratory": None if rng else exploratory_1(),
        "rules": [{
            "id": r.id, "text": D1.bare_rule(r), "real": r.real, "example": r.example, "cost": r.cost, "polarity": r.polarity,
            "focal": r.id in FOCAL, "pool": r.id in POOL_FINAL,
            "link": f"{SOURCE}study1/rules.py#L{inspect.getsourcelines(r.check)[1]}",
        } for r in ordered],
        "clauses": {"filler": D1.FILLERS, "placebo": D1.PLACEBOS, "norm": D1.NORMS, "urgent": D1.URGENT},
        "fixed": {
            "tools": sorted({t for r in records for t in r["init_tools"]}), "tasks": len(LEVELS_1["task"]), "k": D1.K,
            "pool": len(POOL_FINAL), "fillers": [D1.SHORT_FILLERS, D1.LONG_FILLERS], "band": [LOW, HIGH],
        },
        "levels": LEVELS_1,
        "runCols": ["id", "task", "length", "pressure", "status", "turns"],
        "runs": [[
            r["run_id"], at("task", rows[r["run_id"]]["task"]), at("length", rows[r["run_id"]]["length"]),
            at("pressure", rows[r["run_id"]]["pressure"]), at("status", r["status"]), r["turns"],
        ] for r in records],
        "obsCols": ["run", "rule", *OBS_FACTORS, "y"],
        "obs": [[run_ix[o["run"]], rule_ix[o["rule"]], *(at(f, o[f]) for f in OBS_FACTORS), int(o["y"])] for o in obs],
    }


def exploratory_1():
    doc = json.loads((ROOT / "results" / "exploratory.json").read_text())["study1"]
    cells = doc["rule_by_factor"]["cells"]
    return {
        "having_the_rule": doc["having_the_rule_at_all"]["effect"], "rule_identity": doc["rule_identity"],
        "survive_holm_72": sorted((c for c in cells if c.get("p_holm_72", 1) < 0.05), key=lambda c: -abs(c["estimate"])),
        "largest_outside_72": max((c for c in cells if "p_holm_99" in c and "p_holm_72" not in c), key=lambda c: abs(c["estimate"])),
    }


def bundle_1(batch, row, rec, verdict):
    trace = trace_doc(batch, row["run_id"])["trace"]
    text, depth, _ = D1.render_file(row)
    shown = {t["rule"] for t in row["targets"]}
    return {
        "id": row["run_id"], "task": row["task"], "length": row["length"], "pressure": row["pressure"], "status": rec["status"],
        "turns": rec["turns"], "tests_pass": rec["tests_pass"], "control_rule": row["control_rule"],
        "file": text, "prompt": D1.render_prompt(row),
        "targets": [{**t, "text": D1.render_rule(RULES[t["rule"]], t), "position": A1.position_of(depth[t["rule"]])} for t in row["targets"]],
        "steps": transcript(batch / "raw" / f"{row['run_id']}.jsonl.gz"),
        "final": trace["final_message"] or "", "diff": diff(trace),
        "verdicts": {rule: [ok, rule in shown] for rule, ok in verdict.items()},
    }


def study2(batch, results, out, rng, levels=LEVELS_2):
    """Study 2 and its follow-ups share a trace format and a run sheet, so only their levels differ."""
    if not rng and not results.exists():
        return None
    rows, counts = A2.load(batch)
    if rng:
        for stem in sorted({r["stem"] for r in rows}):
            group = [r for r in rows if r["stem"] == stem]
            for field in ("y", "described"):
                values = [r[field] for r in group]
                rng.shuffle(values)
                for r, v in zip(group, values):
                    r[field] = v
        with patched(A2, "load", lambda _: (rows, counts)):
            doc = A2.analyze(batch)
    else:
        doc = json.loads(results.read_text())

    planned, table = manifest(batch), []
    at = lambda column, value: levels[column].index(value)
    for r in rows:
        row, source = planned[r["run"]], trace_doc(batch, r["run"])
        name = D2.target_name(row)
        # A record from before the probe existed says nothing about reach, which is not the same as "did not reach".
        reached = r["described"] if "probe_hit" in source["record"]["capture"] else None
        call = next((c for c in source["trace"]["calls"] if A2.loaded({"calls": [c]}, name)), None)
        write(out / "runs" / f"{r['run']}.json", {
            "id": r["run"], "stem": r["stem"], "wording": r["wording"], "prefix": r["prefix"], "prompt_type": r["prompt"],
            "status": source["record"]["status"], "turns": r["turns"], "library": r["library"], "prompt": D2.BY_STEM[r["stem"]][r["prompt"]],
            "name": name, "description": D2.description(D2.BY_STEM[r["stem"]], r["wording"]), "reached": reached, "budget": r["budget"],
            "loaded": bool(r["y"]), "call": call if r["y"] else None,
            "steps": transcript(batch / "raw" / f"{r['run']}.jsonl.gz"), "final": source["trace"]["final_message"] or "", "diff": diff(source["trace"]),
        })
        table.append([
            r["run"], at("stem", r["stem"]), at("wording", r["wording"]), r["library"], at("prefix", r["prefix"]), at("prompt", r["prompt"]),
            int(r["y"]), None if reached is None else int(reached), r["turns"], r["budget"],
        ])
    return {
        "results": plain(doc),
        "targets": [{
            "stem": t["stem"], "wordings": {w: D2.description(t, w) for w in levels["wording"]}, "prompts": {p: t[p] for p in levels["prompt"]},
        } for t in D2.TARGETS],
        "checker": f"{SOURCE}analysis/study2.py#L{inspect.getsourcelines(A2.loaded)[1]}",
        "levels": levels,
        "runCols": ["id", "stem", "wording", "library", "prefix", "prompt", "loaded", "described", "turns", "budget"],
        "runs": table,
    }


def build(out, dev):
    for sub in ("runs", "data"):
        shutil.rmtree(out / sub, ignore_errors=True)
        (out / sub).mkdir(parents=True)
    rng = random.Random("explorer dev build") if dev else None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # empty cells on thin pilots become NaN, then null, then "n/a"
        studies = {
            "study1": study1(ROOT / "data" / ("p5" if dev else "study1"), ROOT / "results" / "study1.json", out, rng),
            "study2": study2(ROOT / "data" / ("s2pilot" if dev else "study2"), ROOT / "results" / "study2.json", out, rng),
        }
        # A development build shuffles a pilot, and only Study 1 and Study 2 are wired to one.
        if not dev:
            studies["study2b"] = study2(ROOT / "data" / "study2b", ROOT / "results" / "study2b.json", out, None, LEVELS_2B)
            studies["study2c"] = study2(ROOT / "data" / "study2c", ROOT / "results" / "study2c.json", out, None, LEVELS_2C)
    write(out / "data" / "summary.json", {"dev": dev, "budget": {"own": CLI_BUDGET, "raised": D2.RAISED_BUDGET}, **studies})
    (out / "index.html").write_text(with_policy((Path(__file__).parent / "index.html").read_text()))
    return studies


def with_policy(page):
    """Other sites on this origin hold keys and this page renders transcripts, so only its own scripts may run."""
    scripts = " ".join(
        f"'sha256-{base64.b64encode(hashlib.sha256(s.encode()).digest()).decode()}'"
        for s in re.findall(r"<script>(.*?)</script>", page, re.S)
    )
    policy = f"default-src 'none'; script-src {scripts}; style-src 'unsafe-inline'; img-src data:; connect-src 'self'; base-uri 'none'; form-action 'none'"
    return page.replace("<head>", f'<head>\n<meta http-equiv="Content-Security-Policy" content="{policy}">', 1)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--dev", action="store_true", help="pilots with outcomes shuffled; safe while batches are blind")
    a = p.parse_args()
    start = time.time()
    studies = build(a.out, a.dev)
    size = sum(f.stat().st_size for f in a.out.rglob("*") if f.is_file())
    blind = [name for name, s in studies.items() if s is None]
    print(f"{len(list((a.out / 'runs').iterdir()))} run bundles, {size / 1e6:.1f} MB, {time.time() - start:.1f} s")
    if blind:
        print(f"no registered results yet, left out unread: {', '.join(blind)}")


if __name__ == "__main__":
    main()
