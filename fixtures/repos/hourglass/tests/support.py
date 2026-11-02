"""Shared bits for the test modules."""

import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def data_file(name: str) -> Path:
    return DATA_DIR / name


def full_suite_enabled() -> bool:
    """The generated-data tests only run under the test environment."""
    return os.environ.get("HOURGLASS_ENV") == "test"


def generated_schedule(workers: int) -> str:
    """Schedule CSV text with every worker on the same two morning shifts."""
    rows = ["worker,day,span"]
    for number in range(workers):
        rows.append(f"worker{number},mon,08:00-12:00")
        rows.append(f"worker{number},tue,08:30-12:30")
    return "\n".join(rows) + "\n"
