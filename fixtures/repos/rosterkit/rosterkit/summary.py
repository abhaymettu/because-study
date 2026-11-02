"""Per-student and per-section attendance summaries."""

from dataclasses import dataclass
from typing import Dict, Iterable, List

from rosterkit.attendance import tally_statuses
from rosterkit.models import Mark, Student


@dataclass(frozen=True)
class StudentSummary:
    student: Student
    counts: Dict[str, int]
    rate: float


def attendance_rate(counts: Dict[str, int]) -> float:
    """Share of countable meetings attended. Excused days drop out entirely."""
    countable = sum(n for status, n in counts.items() if status != "excused")
    if countable == 0:
        return 1.0
    attended = counts.get("present", 0) + counts.get("late", 0)
    return attended / countable


def summarize_student(student: Student, marks: Iterable[Mark]) -> StudentSummary:
    """Summarize one student from a mixed list of marks."""
    own = [mark for mark in marks if mark.student_id == student.student_id]
    counts = tally_statuses(own)
    return StudentSummary(student, counts, attendance_rate(counts))


def summarize_section(
    students: Iterable[Student], marks: Iterable[Mark], section: str
) -> List[StudentSummary]:
    """Summaries for everyone in a section, lowest attendance first."""
    members = [student for student in students if student.section == section]
    if not members:
        raise KeyError(section)
    all_marks = list(marks)
    summaries = [summarize_student(student, all_marks) for student in members]
    return sorted(summaries, key=lambda item: item.rate)


def chronic_absentees(
    summaries: Iterable[StudentSummary], threshold: float = 0.9
) -> List[StudentSummary]:
    """Students whose attendance rate falls below the threshold."""
    if not 0 < threshold <= 1:
        raise ValueError(f"threshold out of range: {threshold}")
    return [item for item in summaries if item.rate < threshold]


def format_summary_row(summary: StudentSummary) -> str:
    absent = summary.counts.get("absent", 0)
    name = summary.student.display_name
    return f"{name:<20} {summary.rate:>6.1%}  absent {absent}"


def render_section(summaries: Iterable[StudentSummary], section: str) -> str:
    """Printable block for one section, heading first."""
    lines = [f"Section {section}"]
    lines.extend(format_summary_row(item) for item in summaries)
    return "\n".join(lines)
