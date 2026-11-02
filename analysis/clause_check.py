"""Manipulation check on the clauses: does a blind reader see information in the real reasons and none in the placebos?

    python3 -m analysis.clause_check [--raters 8]

Each rater gets every clause in a fresh random order with no arm labels. This is a check on the stimuli only; no model
judges any outcome in this study.
"""

import argparse
import json
import random
import statistics
import subprocess
from pathlib import Path

from harness.agent_run import CLAUDE_BIN
from study1.design import FILLERS, NORMS, PLACEBOS
from study1.rules import BY_ID, POOL_FINAL

PROMPT = """Below are clauses taken from instructions given to a software engineer. The instruction each one was attached to is not shown.

Give each clause two ratings from 1 to 5.
"info": how much specific information does it give about why the instruction exists? 1 means none at all, 5 means a concrete, specific cause or consequence.
"press": how strongly does it assert that the instruction is obligatory? 1 means not at all, 5 means very strongly.

Reply with only a JSON object mapping each clause number to {"info": n, "press": n}.

"""


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--raters", type=int, default=8)
    a = p.parse_args()
    clauses = [("placebo", c) for c in PLACEBOS] + [("norm", c) for c in NORMS] + [("filler", c) for c in FILLERS]
    clauses += [("real", BY_ID[r].real) for r in POOL_FINAL]
    ratings = {i: [] for i in range(len(clauses))}
    press = {i: [] for i in range(len(clauses))}
    for rater in range(a.raters):
        order = list(range(len(clauses)))
        random.Random(f"clause:{rater}").shuffle(order)
        body = PROMPT + "\n".join(f"{n + 1}. {clauses[i][1]}" for n, i in enumerate(order))
        out = subprocess.run(
            [CLAUDE_BIN, "-p", body, "--model", "claude-haiku-5-5", "--tools", "", "--output-format", "json",
             "--setting-sources", "project", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
             "--settings", json.dumps({"claudeMdExcludes": [f"{Path.home()}/**"], "autoMemoryEnabled": False, "disableAllHooks": True}),
             "--no-session-persistence"],
            capture_output=True, text=True, stdin=subprocess.DEVNULL, cwd="/private/tmp",
        )
        text = json.loads(out.stdout)["result"]
        scores = json.loads(text[text.index("{") : text.rindex("}") + 1])
        for n, i in enumerate(order):
            ratings[i].append(int(scores[str(n + 1)]["info"]))
            press[i].append(int(scores[str(n + 1)]["press"]))
    rows = [{"arm": clauses[i][0], "clause": clauses[i][1], "mean": statistics.mean(ratings[i]), "ratings": ratings[i], "press_mean": statistics.mean(press[i])} for i in ratings]
    Path("results").mkdir(exist_ok=True)
    Path("results/clause_check.json").write_text(json.dumps(rows, indent=1))
    for arm in ("filler", "placebo", "norm", "real"):
        print(arm, "info", round(statistics.mean(r["mean"] for r in rows if r["arm"] == arm), 2),
              "press", round(statistics.mean(r["press_mean"] for r in rows if r["arm"] == arm), 2))
    print("lowest real", round(min(r["mean"] for r in rows if r["arm"] == "real"), 2))


if __name__ == "__main__":
    main()
