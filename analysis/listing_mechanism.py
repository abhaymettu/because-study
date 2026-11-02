"""Which skills keep their description in the budgeted listing: parse a capture, predict the set, run the deciding tests.

Needs a login. Writes a few zz-mech-<tag>-* entries to skillUsage in the account's global config (real Skill calls).

    BECAUSE_ACCOUNT_EMAIL=... python3 -m analysis.listing_mechanism
    python3 -m analysis.listing_mechanism replay    (no model calls, needs the pilot captures and listing_rule.json, which are not in the repo)

A reader's offline check is analysis/listing_check.py.
"""

import gzip
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from harness.agent_run import RUN_ROOT, agent_command, scrubbed_env
from harness.batch import start_proxy

DISTRACTORS = json.loads(Path("fixtures/distractors.json").read_text())
WORK = RUN_ROOT / ".mechanism"
HAIKU, SONNET = "claude-haiku-5-5", "claude-sonnet-5-5"
READY = "Reply with the single word ready."
PILOT_TOOLS = "Skill,Bash,Read,Edit,Write,Glob,Grep"
NOT_BUNDLED = {"init", "security-review"}
LONG = ("Reconcile the quarterly ledger against bank exports and flag every unmatched entry. " * 6).strip()


def listing_block(request):
    """The text of the skill listing in a captured request, or None."""
    for message in request["messages"]:
        content = message["content"]
        for text in [content] if isinstance(content, str) else [p.get("text", "") for p in content if isinstance(p, dict)]:
            start = text.find("following skills are available")
            if start >= 0:
                body = text[text.find("\n\n", start) + 2:text.find("</system-reminder>", start)]
                return body.split("\n\nToday's date")[0].rstrip("\n")
    return None


def described(block, name):
    """True when the listing gives this skill a description, False for a bare name, None when it is not listed."""
    match = re.search(rf"^- {re.escape(name)}(: |$)", block, re.M)
    return None if match is None else match.group(1) == ": "


def entries(block):
    """Listing entries in order as {name: full entry}. A line not starting with '- ' continues the entry above it."""
    out = {}
    last = None
    for line in block.split("\n"):
        match = re.match(r"- ([^:\s]+)(: |$)", line)
        if match:
            last = match.group(1)
            out[last] = line
        else:
            out[last] += "\n" + line
    return out


def width(text):
    return len(text.replace("\n", ""))


def usage_scores(names, now=None):
    """Score for each name from skillUsage in the global config: count * max(0.5 ** (days / 7), 0.1)."""
    config = json.loads((Path(os.environ["CLAUDE_CONFIG_DIR"]) / ".claude.json").read_text())
    table = config.get("skillUsage", {})
    now = now or time.time() * 1000
    scores = {}
    for name in names:
        if name in table:
            days = (now - table[name]["lastUsedAt"]) / 86400000
            scores[name] = table[name]["usageCount"] * max(0.5 ** (days / 7), 0.1)
    return scores


def listed_text(description):
    """A description as the listing prints it: > is escaped, & is not, and over 1536 chars it is cut."""
    text = description.replace(">", "&gt;")
    return text[:1535] + "\u2026" if len(text) > 1536 else text


def predict(skills, builtins, scores, budget=30000, trace=None):
    """The set of names that keep a description, by the shipped rule. builtins is {name: full entry} from a capture."""
    project = {n: f"- {n}: {listed_text(d)}" for n, d in sorted(skills.items())}
    full = {**project, **builtins}
    fixed = [n for n in builtins if n not in NOT_BUNDLED]
    competing = [n for n in full if n not in fixed]
    if sum(width(v) for v in full.values()) + len(full) - 1 <= budget:
        return set(full)
    left = budget - (sum(width(full[n]) for n in fixed) + sum(len(n) + 2 for n in competing) + len(full) - 1)
    kept = set(fixed)
    for name in sorted(competing, key=lambda n: -scores.get(n, 0)):
        cost = width(full[name]) - len(name) - 2
        if trace is not None:
            trace[name] = {"left": left, "cost": cost}
        if cost <= left:
            kept.add(name)
            left -= cost
    return kept


def run(skills, prompt=READY, model=HAIKU, tools="Skill,Read", env_extra=None, reverse=False, mtimes=None):
    """One claude -p over a fresh project holding these skills. Returns the listing block from the first request."""
    shutil.rmtree(WORK, ignore_errors=True)
    root = WORK / ".claude" / "skills"
    root.mkdir(parents=True)
    for name in sorted(skills, reverse=reverse):
        (root / name).mkdir()
        (root / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {json.dumps(skills[name])}\n---\n\nBody.\n")
        if mtimes:
            stamp = mtimes(name)
            os.utime(root / name / "SKILL.md", (stamp, stamp))
            os.utime(root / name, (stamp, stamp))
    subprocess.run(["git", "init", "-q"], cwd=WORK)
    capture = WORK / "capture"
    proxy, port = start_proxy(capture)
    try:
        env = {**scrubbed_env(os.environ.get("CLAUDE_CONFIG_DIR"), port), **(env_extra or {})}
        subprocess.run(agent_command(prompt, model, "low", 1, tools), cwd=WORK, env=env, stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, timeout=240)
    finally:
        proxy.terminate()
    for path in sorted(capture.glob("*.json")):
        block = listing_block(json.loads(path.read_text())["request"])
        if block:
            return block
    raise RuntimeError("no listing captured")


def library(seed, n):
    return {s["name"]: s["description"] for s in random.Random(seed).sample(DISTRACTORS, n)}


def kept_set(block):
    return {n for n, e in entries(block).items() if e.startswith(f"- {n}: ")}


def compare(block, skills, builtins, scores):
    """Observed against predicted for one run."""
    seen, want = kept_set(block), predict(skills, builtins, scores)
    return {"listed": len(entries(block)), "kept": len(seen), "predicted": len(want), "wrong": sorted(seen ^ want)}


def implied_budget(block, skills, builtins, tail_cost=3):
    """Read the budget off a crafted library: chars spent, plus up to tail_cost - 1 left over."""
    full = {**{n: f"- {n}: {d}" for n, d in skills.items()}, **builtins}
    kept = kept_set(block)
    fixed = [n for n in builtins if n not in NOT_BUNDLED]
    spent = sum(width(full[n]) for n in fixed) + sum(len(n) + 2 for n in full if n not in fixed) + len(full) - 1
    spent += sum(width(full[n]) - len(n) - 2 for n in kept if n not in fixed)
    if not kept - set(fixed):
        return {"below": spent}
    return {"lower": spent, "upper": spent + tail_cost - 1}


def invoke(skills, name):
    """A real Skill call. Returns the change in that name's usage count."""
    def count():
        table = json.loads((Path(os.environ["CLAUDE_CONFIG_DIR"]) / ".claude.json").read_text()).get("skillUsage", {})
        return table.get(name, {}).get("usageCount", 0)
    before = count()
    run(skills, f'Call the Skill tool now with skill "{name}" and no args. Do nothing else.')
    return count() - before


def replay():
    """No model calls: predict the pilot captures and the two earlier result files from their inputs."""
    from study2.design import BY_STEM, assign, description, plan

    if not Path("data/s2pilot/captures").exists():
        sys.exit("replay needs the pilot captures, which are not in the repo. The offline check is: python3 -m analysis.listing_check data/study2 data/study2b")

    def frontmatter(text):
        return json.loads(re.search(r"^description: (.*)$", text, re.M).group(1))

    rows = [json.loads(line) for line in open("data/s2pilot/manifest.jsonl")]
    runs = []
    for row in rows:
        record = json.load(gzip.open(f"data/s2pilot/captures/{row['run_id']}.json.gz"))
        raw = gzip.open(f"data/s2pilot/raw/{row['run_id']}.jsonl.gz", "rt").read()
        plan_row = plan(row)
        runs.append({"row": row, "t": record["t"], "block": listing_block(record["request"]), "target": plan_row["target"],
                     "skills": {n: frontmatter(t) for n, t in plan_row["skills"].items()},
                     "called": re.findall(r'"name":"Skill","input":\{"skill":"([^"]+)"', raw)})
    runs.sort(key=lambda r: r["t"])
    small = next(r for r in runs if r["row"]["library"] == 0)
    builtins = {n: e for n, e in entries(small["block"]).items() if n not in small["skills"]}
    out = {"pilot": [], "usage_after_pilot": {}}
    usage = {}
    for run in runs:
        trace = {}
        seen, want = kept_set(run["block"]), predict(run["skills"], builtins, usage, trace=trace)
        blind = predict(run["skills"], builtins, {})
        step = trace.get(run["target"], {})
        out["pilot"].append({"run": run["row"]["run_id"], "library": run["row"]["library"], "target": run["target"],
                             "wording": run["row"]["wording"], "usage": usage.get(run["target"], 0), "target_kept": run["target"] in seen,
                             "left_at_target": step.get("left"), "target_cost": step.get("cost"), "skills": len(seen | set(entries(run["block"]))),
                             "wrong": sorted(seen ^ want), "wrong_without_usage": sorted(seen ^ blind)})
        for name in run["called"]:
            usage[name] = usage.get(name, 0) + 1
    out["usage_after_pilot"] = usage

    out["listing_budget"] = []
    for row in json.loads(Path("results/listing_budget.json").read_text()):
        chosen = library(f"listing:{row['library']}", row["library"])
        kept = predict(chosen, builtins, {}) & set(chosen)
        ordered = sorted(chosen)
        last = max(ordered.index(n) for n in kept)
        out["listing_budget"].append({"library": row["library"], "model": row["model"], "kept": len(kept), "observed": row["with_description"],
                                      "prefix": last + 1 == len(kept), "observed_prefix": row["prefix_of_alphabet"]})

    bases = [r for r in assign("listing", 40) if r["library"] == 300][:2]
    texts = {s["name"]: s["description"] for s in DISTRACTORS}
    tally = {"rows": 0, "with_usage": {"target": 0, "distractors": 0}, "without_usage": {"target": 0, "distractors": 0}}
    for row in json.loads(Path("results/listing_rule.json").read_text()):
        target = f"{row['prefix']}-{row['stem']}"
        distractors = bases[row["library"]]["distractors"]
        skills = {**{d: texts[d] for d in distractors}, target: description(BY_STEM[row["stem"]], row["wording"])}
        tally["rows"] += 1
        for label, scores in (("with_usage", usage), ("without_usage", {})):
            kept = predict(skills, builtins, scores)
            tally[label]["target"] += (target in kept) == row["described"]
            tally[label]["distractors"] += sum(d in kept for d in distractors) == row["lines_described"]
    out["listing_rule"] = tally
    Path("results/listing_replay.json").write_text(json.dumps(out, indent=1))
    print(json.dumps({"pilot_wrong": sum(len(r["wrong"]) for r in out["pilot"]), "pilot_wrong_without_usage": sum(len(r["wrong_without_usage"]) for r in out["pilot"]),
                      "budget_rows_right": sum(r["kept"] == r["observed"] and r["prefix"] == r["observed_prefix"] for r in out["listing_budget"]),
                      "rule": tally, "usage": usage}))
    for r in out["pilot"]:
        if r["library"] == 300:
            print(r["run"], r["target"], r["wording"], "usage", r["usage"], "kept", r["target_kept"], "left", r["left_at_target"], "cost", r["target_cost"], "wrong", r["wrong"], "blind", len(r["wrong_without_usage"]))


def main():
    tag = str(int(time.time()) % 100000)
    out = {"tag": tag}
    path = Path("results/listing_mechanism.json")

    def save(key, value):
        out[key] = value
        print(key, json.dumps(value), flush=True)
        path.write_text(json.dumps(out, indent=1))

    builtins = {n: e for n, e in entries(run({})).items()}
    save("builtins", {n: width(e) for n, e in builtins.items()})

    # Everything except usage: one library, one never-used late name, one change at a time.
    a, b, c = (f"zz-mech-{tag}-{x}" for x in "abc")
    lib = {**library("mech:300", 300), a: LONG}
    base = run(lib)
    scores = usage_scores(lib)
    save("base", {**compare(base, lib, builtins, scores), "probe": described(base, a), "used_in_sample": sorted(scores)})
    base_set = kept_set(base)
    variants = {
        "repeat": {},
        "prompt_names_the_skill": {"prompt": f"Reply with the single word ready. Do not call any tool. Later I will need {a} to reconcile the quarterly ledger against bank exports."},
        "pilot_tools": {"tools": PILOT_TOOLS},
        "sonnet": {"model": SONNET},
        "sonnet_pilot_tools": {"model": SONNET, "tools": PILOT_TOOLS},
        "reverse_creation": {"reverse": True},
        "probe_newest_mtime": {"mtimes": lambda n: time.time() if n == a else time.time() - 864000},
        "probe_oldest_mtime": {"mtimes": lambda n: time.time() - 864000 if n == a else time.time()},
    }
    for label, kwargs in variants.items():
        block = run(lib, **kwargs)
        seen = kept_set(block)
        save(f"variant:{label}", {"same_set": seen == base_set, "diff": sorted(seen ^ base_set)[:8], "probe": described(block, a),
                                  "same_order": list(entries(block)) == list(entries(base))})

    # Fresh samples: the whole set, not one name.
    for n, seed in ((120, "s1"), (200, "s2"), (300, "s3"), (300, "s4"), (388, "s5")):
        sample = library(f"mech:{seed}", n)
        block = run(sample)
        save(f"sample:{n}:{seed}", compare(block, sample, builtins, usage_scores(sample)))

    # Crafted costs: 100 chars each, then 3 chars each, so the budget reads off to within 3 and skipping shows directly.
    crafted = {f"cal-{i:03d}": "x" * 98 for i in range(330)}
    crafted.update({f"zcal-{i:02d}": "y" for i in range(40)})
    for label, kwargs in {"haiku": {}, "sonnet": {"model": SONNET}, "haiku_pilot_tools": {"tools": PILOT_TOOLS},
                          "env_12000": {"env_extra": {"SLASH_COMMAND_TOOL_CHAR_BUDGET": "12000"}},
                          "env_20000": {"env_extra": {"SLASH_COMMAND_TOOL_CHAR_BUDGET": "20000"}},
                          "older_model": {"model": "claude-sonnet-4-6"}}.items():
        try:
            block = run(crafted, **kwargs)
            seen = kept_set(block)
            save(f"budget:{label}", {**implied_budget(block, crafted, builtins), "kept_100": sum(n.startswith("cal") for n in seen),
                                     "kept_3": sum(n.startswith("zcal") for n in seen)})
        except RuntimeError as error:
            save(f"budget:{label}", {"error": str(error)})

    # Usage, on its own. b sorts before c and is used last, c is used twice: name order and recency favour b, count favours c.
    lib2 = {**lib, b: LONG, c: LONG}
    before = run(lib2)
    save("usage:before", {"a": described(before, a), "b": described(before, b), "c": described(before, c)})
    save("usage:invoke", {"a": invoke({a: LONG}, a), "c1": invoke({c: LONG}, c), "c2": invoke({c: LONG}, c), "b": invoke({b: LONG}, b)})
    after = run(lib2)
    scores = usage_scores(lib2)
    save("usage:after", {"a": described(after, a), "b": described(after, b), "c": described(after, c),
                         **compare(after, lib2, builtins, scores), "scores": {k: round(v, 3) for k, v in scores.items()}})
    repeat_a = run(lib)
    save("usage:after_base_library", {"a": described(repeat_a, a), **compare(repeat_a, lib, builtins, usage_scores(lib)),
                                      "lost_from_base": sorted(base_set - kept_set(repeat_a))[:8]})
    # Budget that leaves room for exactly one LONG after the fixed entries and names, so only the top score can have it.
    full = {**{n: f"- {n}: {d}" for n, d in lib2.items()}, **builtins}
    fixed = [n for n in builtins if n not in NOT_BUNDLED]
    floor = sum(width(full[n]) for n in fixed) + sum(len(n) + 2 for n in full if n not in fixed) + len(full) - 1
    tight = run(lib2, env_extra={"SLASH_COMMAND_TOOL_CHAR_BUDGET": str(floor + len(LONG) + 2)})
    save("usage:one_slot", {"a": described(tight, a), "b": described(tight, b), "c": described(tight, c),
                            "kept_outside_fixed": sorted(kept_set(tight) - set(fixed))[:6]})

    shutil.rmtree(WORK, ignore_errors=True)


if __name__ == "__main__":
    replay() if sys.argv[1:] == ["replay"] else main()
