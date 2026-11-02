"""Read class roster CSV files into Student objects."""

import csv
from io import StringIO
from pathlib import Path
from typing import Dict, Iterable, List, Union

from rosterkit.errors import ProjectError
from rosterkit.models import Student

REQUIRED_COLUMNS = ("id", "last_name", "first_name", "section")


def parse_student_row(row: Dict[str, str]) -> Student:
    """Build a Student from one CSV row, trimming stray whitespace."""
    # csv hands back None for cells missing at the end of a short row
    cleaned = {key: (value or "").strip() for key, value in row.items() if key}
    for column in REQUIRED_COLUMNS:
        if not cleaned.get(column):
            raise ValueError(f"missing value for {column!r} in row: {row}")
    return Student(
        cleaned["id"],
        cleaned["last_name"],
        cleaned["first_name"],
        cleaned["section"],
        cleaned.get("email") or None,
    )


def parse_roster_text(text: str) -> List[Student]:
    """Parse roster CSV content that is already in memory."""
    rows = csv.DictReader(StringIO(text))
    fields = rows.fieldnames or []
    missing = [column for column in REQUIRED_COLUMNS if column not in fields]
    if missing:
        names = ", ".join(missing)
        raise ProjectError(f"roster is missing columns: {names}")

    students = [parse_student_row(row) for row in rows]
    ids = [student.student_id for student in students]
    repeated = sorted({value for value in ids if ids.count(value) > 1})
    if repeated:
        raise ValueError(f"duplicate student ids: {repeated}")
    return students


def read_roster(path: Union[str, Path]) -> List[Student]:
    """Load a roster CSV from disk. Spreadsheet exports may carry a BOM."""
    text = Path(path).read_text(encoding="utf-8-sig")
    return parse_roster_text(text)


def find_student(students: Iterable[Student], student_id: str) -> Student:
    """Look a student up by id, raising KeyError when there is no match."""
    for student in students:
        if student.student_id == student_id:
            return student
    raise KeyError(student_id)


def section_names(students: Iterable[Student]) -> List[str]:
    return sorted({student.section for student in students})
