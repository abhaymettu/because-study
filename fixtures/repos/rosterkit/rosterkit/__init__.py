"""Read class roster CSV files and summarize attendance."""

from rosterkit.attendance import read_attendance, tally_statuses
from rosterkit.errors import ProjectError
from rosterkit.models import Mark, Student
from rosterkit.reader import read_roster, section_names
from rosterkit.summary import chronic_absentees, render_section, summarize_section

__all__ = [
    "Mark",
    "ProjectError",
    "Student",
    "chronic_absentees",
    "read_attendance",
    "read_roster",
    "render_section",
    "section_names",
    "summarize_section",
    "tally_statuses",
]
