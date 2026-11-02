"""Shared bits for the test modules."""

import os
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"


def data_file(name: str) -> Path:
    return DATA_DIR / name


def full_suite_enabled() -> bool:
    """The generated-data tests only run under the test environment."""
    return os.environ.get("ROSTERKIT_ENV") == "test"


def generated_roster(size: int) -> str:
    """Roster CSV text with a predictable student on every row."""
    rows = ["id,last_name,first_name,section,email"]
    for number in range(size):
        section = "AB"[number % 2]
        rows.append(f"{number},Last{number},First{number},{section},")
    return "\n".join(rows) + "\n"
