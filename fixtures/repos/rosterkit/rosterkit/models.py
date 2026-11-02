"""Plain data holders shared by the reader and the summaries."""

from dataclasses import dataclass
from datetime import date
from typing import Optional

VALID_STATUSES = ("present", "absent", "late", "excused")


@dataclass(frozen=True)
class Student:
    """One row of a class roster."""

    student_id: str
    last_name: str
    first_name: str
    section: str
    email: Optional[str] = None

    @property
    def display_name(self) -> str:
        return f"{self.last_name}, {self.first_name}"


@dataclass(frozen=True)
class Mark:
    """One attendance entry for a student on a given day."""

    student_id: str
    day: date
    status: str
