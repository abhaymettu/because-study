"""Shows that a study run sees none of the operator's setup, and that the same scan would catch it if it did.

    python3 -m harness.prove_isolation

Two runs of one trivial prompt through the capture proxy: isolated as in the study, then a plain `claude -p` as a
negative control. The canaries are lines from your own instruction files, memory index and skill names. Only counts are
written, so the report holds nothing from those files.
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from .agent_run import CLAUDE_BIN, HOME, RUN_ROOT, agent_command, scrubbed_env
from .batch import start_proxy

PROMPT = "Reply with the single word ready."
MODEL = "claude-haiku-5-5"


def canaries():
    home = Path(HOME)
    config = Path(os.environ.get("CLAUDE_CONFIG_DIR", home / ".claude"))
    lines = set()
    for path in {home / ".claude" / "CLAUDE.md", config / "CLAUDE.md", home / ".claude" / "agent-memory" / "shared" / "MEMORY.md"}:
        if path.exists():
            lines.update(l.strip() for l in path.read_text(errors="replace").splitlines() if len(l.strip()) >= 40)
    skills = set()
    for root in (home / ".claude" / "skills", config / "skills"):
        if root.is_dir():
            skills.update(p.name for p in root.iterdir() if len(p.name) >= 6)
    return lines, skills


def measure(capture, lines, skills):
    requests = sorted(capture.glob("*.json"))
    found_lines, found_skills, tools, mcp_tools = set(), set(), set(), set()
    for path in requests:
        body = json.loads(path.read_text())["request"] or {}
        blob = json.dumps(body)
        text = json.loads(json.dumps(blob))
        found_lines.update(l for l in lines if json.dumps(l)[1:-1] in text)
        found_skills.update(s for s in skills if re.search(rf"\b{re.escape(s)}\b", text))
        names = [t.get("name", "") for t in body.get("tools", [])]
        tools.update(names)
        mcp_tools.update(n for n in names if n.startswith("mcp__"))
        path.unlink()
    return {
        "requests": len(requests),
        "instruction_and_memory_lines_found": len(found_lines),
        "instruction_and_memory_lines_checked": len(lines),
        "skill_names_found": len(found_skills),
        "skill_names_checked": len(skills),
        "tools": len(tools),
        "mcp_tools": len(mcp_tools),
    }


def main():
    lines, skills = canaries()
    work = RUN_ROOT / ".isolation-proof"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    capture = work / "capture"
    proxy, port = start_proxy(capture)
    report = {}
    try:
        env = scrubbed_env(os.environ.get("CLAUDE_CONFIG_DIR"), port)
        cmd = agent_command(PROMPT, MODEL, "low", 2, "Bash,Read,Edit,Write,Glob,Grep")
        subprocess.run(cmd, cwd=work, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
        report["isolated"] = measure(capture, lines, skills)

        plain = dict(os.environ, ANTHROPIC_BASE_URL=f"http://127.0.0.1:{port}")
        subprocess.run([CLAUDE_BIN, "-p", PROMPT, "--model", MODEL, "--no-session-persistence"], cwd=work, env=plain,
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=180)
        report["plain_claude_p"] = measure(capture, lines, skills)
    finally:
        proxy.terminate()
        shutil.rmtree(work, ignore_errors=True)
    Path("results").mkdir(exist_ok=True)
    Path("results/isolation.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))
    ok = report["isolated"]["instruction_and_memory_lines_found"] == 0 and report["isolated"]["mcp_tools"] == 0
    caught = report["plain_claude_p"]["instruction_and_memory_lines_found"] > 0
    print("isolated clean:", ok, "| scan catches a plain run:", caught)
    sys.exit(0 if ok and caught else 1)


if __name__ == "__main__":
    main()
