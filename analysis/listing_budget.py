"""How many skills keep their description in the listing the model sees, as a library grows. Needs a login.

    python3 -m analysis.listing_budget
"""

import json
import os
import random
import shutil
import subprocess
from pathlib import Path

from harness.agent_run import RUN_ROOT, agent_command, scrubbed_env
from harness.batch import start_proxy

DISTRACTORS = json.loads(Path("fixtures/distractors.json").read_text())
SIZES = (10, 25, 50, 75, 100, 150, 200, 300, 388)
MODELS = ("claude-sonnet-5-5", "claude-haiku-5-5")


def measure(n, model):
    work = RUN_ROOT / ".listing"
    shutil.rmtree(work, ignore_errors=True)
    skills = work / ".claude" / "skills"
    skills.mkdir(parents=True)
    chosen = random.Random(f"listing:{n}").sample(DISTRACTORS, n)
    for s in chosen:
        (skills / s["name"]).mkdir()
        (skills / s["name"] / "SKILL.md").write_text(
            f"---\nname: {s['name']}\ndescription: {json.dumps(s['description'])}\n---\n\nBody.\n"
        )
    subprocess.run(["git", "init", "-q"], cwd=work)
    capture = work / "capture"
    proxy, port = start_proxy(capture)
    try:
        env = scrubbed_env(os.environ.get("CLAUDE_CONFIG_DIR"), port)
        cmd = agent_command("Reply with the single word ready.", model, "low", 1, "Skill,Read")
        subprocess.run(cmd, cwd=work, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
    finally:
        proxy.terminate()
    request = max(capture.glob("*.json"), key=lambda p: p.stat().st_size)
    blob = json.dumps(json.loads(request.read_text())["request"]["messages"], ensure_ascii=False)
    described = [s["name"] for s in chosen if f"- {s['name']}: " in blob]
    named = [s["name"] for s in chosen if f"- {s['name']}\\n" in blob or f"- {s['name']}: " in blob]
    ordered = sorted(s["name"] for s in chosen)
    last = max((ordered.index(x) for x in described), default=-1)
    shutil.rmtree(work, ignore_errors=True)
    return {
        "library": n, "model": model, "listed": len(named), "with_description": len(described),
        "prefix_of_alphabet": last + 1 == len(described),
        "last_described_name": ordered[last] if last >= 0 else None,
        "description_chars": sum(len(s["description"]) for s in chosen if s["name"] in described),
    }


def main():
    rows = [measure(n, m) for m in MODELS for n in SIZES]
    for r in rows:
        print(r)
    Path("results/listing_budget.json").write_text(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
