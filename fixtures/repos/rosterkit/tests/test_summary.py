import unittest

from rosterkit.attendance import read_attendance
from rosterkit.reader import read_roster
from rosterkit.summary import (
    attendance_rate,
    chronic_absentees,
    format_summary_row,
    render_section,
    summarize_section,
)
from tests.support import data_file


class RateTests(unittest.TestCase):
    def test_excused_days_are_not_counted(self):
        self.assertEqual(attendance_rate({"present": 2, "excused": 3}), 1.0)

    def test_no_meetings_counts_as_full_attendance(self):
        self.assertEqual(attendance_rate({}), 1.0)

    def test_late_counts_as_attended(self):
        self.assertEqual(attendance_rate({"late": 1, "absent": 1}), 0.5)


class SectionTests(unittest.TestCase):
    def setUp(self):
        self.students = read_roster(data_file("roster.csv"))
        self.marks = read_attendance(data_file("attendance.csv"))
        self.section_a = summarize_section(self.students, self.marks, "A")

    def test_lowest_attendance_comes_first(self):
        ids = [item.student.student_id for item in self.section_a]
        self.assertEqual(ids, ["1003", "1001", "1002"])

    def test_unknown_section(self):
        with self.assertRaises(KeyError):
            summarize_section(self.students, self.marks, "Z")

    def test_chronic_absentees(self):
        flagged = chronic_absentees(self.section_a)
        self.assertEqual(
            [item.student.last_name for item in flagged], ["Quillon", "Thistle"]
        )

    def test_threshold_must_be_a_fraction(self):
        with self.assertRaises(ValueError):
            chronic_absentees(self.section_a, 90)

    def test_row_text(self):
        self.assertEqual(
            format_summary_row(self.section_a[1]),
            "Thistle, Bram         66.7%  absent 1",
        )

    def test_render_starts_with_heading(self):
        text = render_section(self.section_a, "A")
        lines = text.splitlines()
        self.assertEqual(lines[0], "Section A")
        self.assertEqual(len(lines), 4)
