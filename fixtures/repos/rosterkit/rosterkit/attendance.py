"""Attendance files: one row per student per class meeting."""

import csv
from collections import Counter, defaultdict
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Union

from rosterkit.models import VALID_STATUSES, Mark

STATUS_ALIASES = {
    "p": "present",
    "a": "absent",
    "l": "late",
    "t": "late",
    "tardy": "late",
    "e": "excused",
    "x": "excused",
}


def normalize_status(raw: str) -> str:
    """Map whatever a teacher typed onto one of the known statuses."""
    status = raw.strip().lower()
    if status in VALID_STATUSES:
        return status
    if status in STATUS_ALIASES:
        return STATUS_ALIASES[status]
    raise ValueError(f"unknown attendance status: {raw!r}")


def parse_day(text: str) -> date:
    """Accept ISO dates and the M/D/YYYY that spreadsheets like to export."""
    cleaned = text.strip()
    for pattern in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(cleaned, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"could not read date: {text!r}")


def read_attendance(path: Union[str, Path]) -> List[Mark]:
    """Load an attendance CSV with student_id, date and status columns."""
    with open(path, newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    return [
        Mark(
            row["student_id"].strip(),
            parse_day(row["date"]),
            normalize_status(row["status"]),
        )
        for row in rows
    ]


def marks_by_student(marks: Iterable[Mark]) -> Dict[str, List[Mark]]:
    """Group marks by student id, each group ordered by day."""
    grouped = defaultdict(list)
    for mark in marks:
        grouped[mark.student_id].append(mark)
    return {
        student_id: sorted(items, key=lambda mark: mark.day)
        for student_id, items in grouped.items()
    }


def tally_statuses(marks: Iterable[Mark]) -> Dict[str, int]:
    return dict(Counter(mark.status for mark in marks))


def days_missed(marks: Iterable[Mark]) -> List[date]:
    """Days marked absent, oldest first. Excused days do not count."""
    return sorted(mark.day for mark in marks if mark.status == "absent")
