import unittest
from datetime import date

from rosterkit.attendance import (
    days_missed,
    marks_by_student,
    normalize_status,
    parse_day,
    read_attendance,
    tally_statuses,
)
from rosterkit.models import Mark
from tests.support import data_file


class StatusTests(unittest.TestCase):
    def test_aliases_and_case(self):
        self.assertEqual(normalize_status(" P "), "present")
        self.assertEqual(normalize_status("Tardy"), "late")
        self.assertEqual(normalize_status("excused"), "excused")

    def test_unknown_status(self):
        with self.assertRaises(ValueError):
            normalize_status("maybe")


class ParseDayTests(unittest.TestCase):
    def test_both_spellings(self):
        self.assertEqual(parse_day("2026-09-03"), date(2026, 9, 3))
        self.assertEqual(parse_day("9/3/2026"), date(2026, 9, 3))

    def test_garbage(self):
        with self.assertRaises(ValueError):
            parse_day("third of september")


class MarkHelpersTests(unittest.TestCase):
    def setUp(self):
        self.marks = read_attendance(data_file("attendance.csv"))

    def test_row_count_and_normalizing(self):
        self.assertEqual(len(self.marks), 15)
        self.assertEqual(self.marks[1], Mark("1001", date(2026, 9, 3), "absent"))

    def test_grouping_sorts_by_day(self):
        grouped = marks_by_student(reversed(self.marks))
        days = [mark.day for mark in grouped["1002"]]
        self.assertEqual(days, sorted(days))
        self.assertEqual(len(grouped), 5)

    def test_tally(self):
        self.assertEqual(
            tally_statuses(self.marks),
            {"present": 8, "absent": 4, "late": 2, "excused": 1},
        )

    def test_days_missed(self):
        own = marks_by_student(self.marks)["1003"]
        self.assertEqual(days_missed(own), [date(2026, 9, 1), date(2026, 9, 5)])
