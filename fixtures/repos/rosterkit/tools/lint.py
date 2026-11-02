"""Byte-compile every Python file in the repo and list any syntax errors."""

import sys
from pathlib import Path
from typing import Iterator, Optional

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", ".venv", "__pycache__", "build", "dist"}


def python_files(root: Path) -> Iterator[Path]:
    for path in sorted(root.rglob("*.py")):
        if SKIP_DIRS.isdisjoint(path.relative_to(root).parts):
            yield path


def check_file(path: Path) -> Optional[str]:
    """Return a problem description, or None when the file compiles."""
    try:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
    except SyntaxError as exc:
        return f"{path}:{exc.lineno}: {exc.msg}"
    return None


def main() -> int:
    files = list(python_files(ROOT))
    problems = [item for item in map(check_file, files) if item]
    for problem in problems:
        print(problem)
    print(f"checked {len(files)} files, {len(problems)} with syntax errors")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
