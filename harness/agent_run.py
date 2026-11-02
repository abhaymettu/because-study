"""Run one agent in a clean room: neutral repo, scrubbed environment, no user config, every request captured.

Point it at another agent by replacing `agent_command`. Everything downstream reads the transcript and the repo.
"""

import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path

RUN_ROOT = Path("/private/tmp/because-runs")
NEUTRAL_HOME = RUN_ROOT / ".home"
TEXT_SUFFIXES = (".py", ".txt", ".md", ".toml", ".cfg", ".json", ".ini", "Makefile", "VERSION", ".gitignore")
HOME = str(Path.home())
USER = os.environ.get("USER", "")
CLAUDE_BIN = os.environ.get("BECAUSE_CLAUDE") or shutil.which("claude") or "claude"
# Generic setup strings, plus your own names and projects from an untracked harness/needles.local (one per line).
_local_needles = Path(__file__).with_name("needles.local")
LEAK_NEEDLES = ("agent-memory", ".claude-accounts", "mcp__", "/users/", USER.lower()) + (
    tuple(l.strip().lower() for l in _local_needles.read_text().splitlines() if l.strip()) if _local_needles.exists() else ()
)


def neutral_shell():
    """The login needs the real HOME, but the Bash tool sources the user's shell profile, so aliases and functions
    reach the agent. A wrapper gives the tool shell an empty home; the CLI process keeps its login."""
    wrapper = NEUTRAL_HOME / "bin" / "bash"
    wrapper.parent.mkdir(parents=True, exist_ok=True)
    wrapper.write_text(f'#!/bin/bash\nexport HOME={NEUTRAL_HOME}\nexec /bin/bash "$@"\n')
    wrapper.chmod(0o755)
    return str(wrapper)


def scrubbed_env(config_dir, proxy_port):
    env = {
        "PATH": "/opt/homebrew/bin:/usr/bin:/bin",
        "HOME": HOME,
        "USER": USER,
        "SHELL": neutral_shell(),
        "LANG": "en_US.UTF-8",
        "TMPDIR": "/private/tmp/",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "DISABLE_AUTOUPDATER": "1",
    }
    if config_dir:
        env["CLAUDE_CONFIG_DIR"] = config_dir
    if proxy_port:
        env["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{proxy_port}"
    return env


def agent_command(prompt, model, effort, max_turns, tools, skills_allowed=False):
    settings = {
        "claudeMdExcludes": [f"{HOME}/**"],
        "autoMemoryEnabled": False,
        "disableAllHooks": True,
    }
    cmd = [
        CLAUDE_BIN, "-p", prompt,
        "--model", model,
        "--effort", effort,
        "--max-turns", str(max_turns),
        "--output-format", "stream-json", "--verbose",
        "--setting-sources", "project",
        "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
        "--settings", json.dumps(settings),
        "--tools", tools,
        "--no-session-persistence",
        "--dangerously-skip-permissions",
    ]
    return cmd


def build_repo(repo_name, fixtures, dest, env, instruction_text):
    """Replay the fixture's history into a fresh git repo, ending with the run's instruction file. Returns the base sha."""
    src = fixtures / "repos" / repo_name
    work = dest / repo_name
    shutil.copytree(src, work, ignore=shutil.ignore_patterns("HISTORY.json", "__pycache__"))
    history = json.loads((src / "HISTORY.json").read_text())

    def git(*args, **extra):
        return subprocess.run(["git", *args], cwd=work, env={**env, **extra}, check=True, capture_output=True, text=True)

    git("init", "-q")
    # Repo-level, because the CLI reads the git user for its prompt from its own HOME, not the tool shell's.
    git("config", "user.name", "Dev")
    git("config", "user.email", "dev@example.invalid")
    for i, commit in enumerate(history):
        git("add", "--", *commit["paths"])
        when = f"2026-0{i + 3}-14T10:2{i}:00"
        git("commit", "-q", "-m", commit["subject"], GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    (work / "CLAUDE.md").write_text(instruction_text)
    git("add", "-A")
    when = "2026-09-02T09:15:00"
    git("commit", "-q", "-m", "Add project notes", GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    return work, git("rev-parse", "HEAD").stdout.strip()


def _is_text(path):
    return path.endswith(TEXT_SUFFIXES)


def collect_trace(work, base, env, stream):
    def git(*args):
        return subprocess.run(["git", *args], cwd=work, env=env, capture_output=True, text=True).stdout

    head_branch = git("rev-parse", "--abbrev-ref", "HEAD").strip()
    shas = git("rev-list", "--reverse", "--all", f"^{base}").split()
    commits = []
    for sha in shas:
        message = git("log", "-1", "--format=%B", sha).strip()
        files = git("show", "--name-only", "--format=", sha).split()
        commits.append({"subject": message.splitlines()[0] if message else "", "message": message, "files": files})

    main_moved = git("rev-parse", "main").strip() != base
    branch = head_branch
    if head_branch == "main" and not main_moved and shas:
        others = [b.strip() for b in git("for-each-ref", "--format=%(refname:short)", "refs/heads").splitlines()]
        others = [b for b in others if b != "main"]
        if others:
            branch = others[0]
            git("checkout", "-q", branch)
    elif head_branch != "main" and main_moved:
        branch = "main"

    tracked = set(git("ls-tree", "-r", "--name-only", base).splitlines())
    current = set()
    for root, dirs, names in os.walk(work):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for name in names:
            current.add(os.path.relpath(os.path.join(root, name), work))
    before, after = {}, {}
    for path in sorted(tracked | current):
        if path == "CLAUDE.md" or not _is_text(path):
            continue
        old = git("show", f"{base}:{path}") if path in tracked else None
        new = (work / path).read_text(errors="replace") if path in current else None
        if old != new:
            if old is not None:
                before[path] = old
            if new is not None:
                after[path] = new

    calls, commands = [], []
    final, result_event = "", None
    for event in stream:
        if event.get("type") == "assistant":
            for block in event["message"].get("content", []):
                if block.get("type") == "tool_use":
                    inp = block.get("input", {})
                    target = inp.get("command") or inp.get("file_path") or inp.get("pattern") or ""
                    calls.append([block["name"], target])
                    if block["name"] == "Bash":
                        commands.append(target)
        elif event.get("type") == "result":
            result_event = event
            final = event.get("result") or ""
    return {
        "commands": commands, "calls": calls, "final_message": final, "commits": commits, "branch": branch,
        "before": before, "after": after,
    }, result_event


def sanitize(text, email=None):
    text = re.sub(r'"signature":\s*"[^"]*"', '"signature": ""', text)
    text = text.replace(HOME, "~")
    if USER:
        text = re.sub(rf"\b{re.escape(USER)}\b", "dev", text)
    if email:
        text = text.replace(email, "user@example.invalid")
    return text


def scan_captures(capture_dir, keep_first_to=None, email=None):
    """Leak scan over every request the agent sent. Bodies are deleted after the scan unless one is kept as a sample."""
    records = sorted(capture_dir.glob("*.json"))
    leaks, system_hashes, tool_sets, models = set(), set(), set(), set()
    ratelimit = {}
    for rec_path in records:
        rec = json.loads(rec_path.read_text())
        body = rec.get("request") or {}
        # Thinking signatures are opaque base64 and spell short needles by chance.
        blob = re.sub(r'"signature": "[^"]*"', "", json.dumps(body)).lower()
        if email:
            blob = blob.replace(email.lower(), "")
        blob = blob.replace("/private/tmp/because-runs", "")
        for needle in LEAK_NEEDLES:
            if needle in blob:
                leaks.add(needle)
        system = body.get("system")
        if system is not None:
            system_hashes.add(hashlib.sha256(json.dumps(system, sort_keys=True).encode()).hexdigest()[:12])
        tool_sets.add(hashlib.sha256(json.dumps(sorted(t.get("name", "") for t in body.get("tools", []))).encode()).hexdigest()[:12])
        if body.get("model"):
            models.add(body["model"])
        if rec.get("ratelimit"):
            ratelimit = rec["ratelimit"]
    if keep_first_to and records:
        keep_first_to.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(keep_first_to, "wt") as f:
            f.write(sanitize(records[0].read_text(), email))
    for rec_path in records:
        rec_path.unlink()
    return {
        "requests": len(records), "leaks": sorted(leaks), "system_hashes": sorted(system_hashes),
        "tool_sets": sorted(tool_sets), "request_models": sorted(models), "ratelimit": ratelimit,
    }


def run_agent(run_id, repo_name, instruction_text, prompt, opts, proxy_port, capture_dir, out_dir, keep_capture=False):
    """One run. Writes the transcript and the trace; the returned record holds what scoring and costing need."""
    RUN_ROOT.mkdir(parents=True, exist_ok=True)
    dest = RUN_ROOT / run_id
    shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir()
    env = scrubbed_env(opts.get("config_dir"), proxy_port)
    work, base = build_repo(repo_name, opts["fixtures"], dest, env, instruction_text)
    for stale in capture_dir.glob("*.json"):
        stale.unlink()

    start = time.time()
    timed_out = False
    try:
        proc = subprocess.run(
            agent_command(prompt, opts["model"], opts["effort"], opts["max_turns"], opts["tools"]),
            cwd=work, env=env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=opts["timeout"],
        )
        raw, stderr, rc = proc.stdout, proc.stderr, proc.returncode
    except subprocess.TimeoutExpired as e:
        raw = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        stderr, rc, timed_out = "", -1, True
    duration = time.time() - start

    stream = []
    for line in raw.splitlines():
        try:
            stream.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    trace, result = collect_trace(work, base, env, stream)
    tests = subprocess.run(["make", "check"], cwd=work, env=env, capture_output=True, text=True)

    (out_dir / "raw").mkdir(parents=True, exist_ok=True)
    (out_dir / "traces").mkdir(parents=True, exist_ok=True)
    email = opts.get("email")
    with gzip.open(out_dir / "raw" / f"{run_id}.jsonl.gz", "wt") as f:
        f.write(sanitize(raw, email))
    keep = out_dir / "captures" / f"{run_id}.json.gz" if keep_capture else None
    capture = scan_captures(capture_dir, keep, email)
    init = next((e for e in stream if e.get("type") == "system" and e.get("subtype") == "init"), {})
    record = {
        "run_id": run_id,
        "status": "timeout" if timed_out else ("ok" if result and not result.get("is_error") else "error"),
        "error_text": (result or {}).get("result", "")[:300] if result and result.get("is_error") else stderr[:300],
        "rc": rc,
        "duration_s": round(duration, 1),
        "turns": (result or {}).get("num_turns"),
        "cost_usd": (result or {}).get("total_cost_usd"),
        "usage": (result or {}).get("usage"),
        "stop": (result or {}).get("stop_reason"),
        "cli": init.get("claude_code_version"),
        "model": init.get("model"),
        "init_tools": init.get("tools"),
        "init_mcp": init.get("mcp_servers"),
        "init_skills": init.get("skills"),
        "tests_pass": tests.returncode == 0,
        "base": base,
        "capture": capture,
    }
    trace_doc = json.loads(sanitize(json.dumps({"record": record, "trace": trace}), email))
    (out_dir / "traces" / f"{run_id}.json").write_text(json.dumps(trace_doc))
    shutil.rmtree(dest, ignore_errors=True)
    return record


def is_rate_limited(record):
    text = (record.get("error_text") or "").lower()
    return record["status"] == "error" and bool(re.search(r"rate limit|usage limit|hit your|overloaded|529|429", text))
