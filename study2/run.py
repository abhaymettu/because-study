"""Places a Study 2 run's workbench and skill library in a fresh repo."""

import subprocess


def build_workbench(work_plan, dest, env):
    work = dest / "workbench"
    work.mkdir()

    def git(*args, **extra):
        return subprocess.run(["git", *args], cwd=work, env={**env, **extra}, check=True, capture_output=True, text=True)

    git("init", "-q")
    git("config", "user.name", "Dev")
    git("config", "user.email", "dev@example.invalid")
    for path, text in work_plan["files"].items():
        (work / path).write_text(text)
    git("add", "-A")
    when = "2026-09-02T09:15:00"
    git("commit", "-q", "-m", "Add exports", GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    skills = work / ".claude" / "skills"
    for name, text in work_plan["skills"].items():
        (skills / name).mkdir(parents=True)
        (skills / name / "SKILL.md").write_text(text)
    return work, git("rev-parse", "HEAD").stdout.strip()
