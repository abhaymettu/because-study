import unittest

from hourglass.errors import ProjectError
from hourglass.models import Span
from hourglass.schedule import (
    day_coverage,
    format_day_line,
    load_schedule,
    parse_schedule_text,
    shifts_for_worker,
    worker_minutes,
)
from tests.support import data_file, full_suite_enabled, generated_schedule


class LoadScheduleTests(unittest.TestCase):
    def setUp(self):
        self.shifts = load_schedule(data_file("schedule.csv"))

    def test_sorted_by_day_then_start(self):
        self.assertEqual(self.shifts[0].worker, "Brisa")
        self.assertEqual(self.shifts[-1].day, "wed")
        self.assertEqual(len(self.shifts), 7)

    def test_missing_column(self):
        with self.assertRaises(ProjectError):
            parse_schedule_text("worker,span\nBrisa,09:00-10:00\n")

    def test_bad_day_in_file(self):
        with self.assertRaises(KeyError):
            parse_schedule_text("worker,day,span\nBrisa,someday,09:00-10:00\n")

    @unittest.skipUnless(full_suite_enabled(), "requires HOURGLASS_ENV=test")
    def test_large_generated_schedule(self):
        shifts = parse_schedule_text(generated_schedule(1000))
        self.assertEqual(len(shifts), 2000)
        self.assertEqual(day_coverage(shifts, "tue"), [Span(510, 750)])


class WorkerTests(unittest.TestCase):
    def setUp(self):
        self.shifts = load_schedule(data_file("schedule.csv"))

    def test_minutes_per_worker(self):
        self.assertEqual(
            worker_minutes(self.shifts), {"Brisa": 540, "Odell": 390, "Quill": 450}
        )

    def test_shifts_for_worker(self):
        self.assertEqual(len(shifts_for_worker(self.shifts, "Odell")), 2)

    def test_unknown_worker(self):
        with self.assertRaises(KeyError):
            shifts_for_worker(self.shifts, "Nobody")


class DayLineTests(unittest.TestCase):
    def setUp(self):
        self.shifts = load_schedule(data_file("schedule.csv"))

    def test_merged_coverage(self):
        self.assertEqual(
            format_day_line(self.shifts, "Monday"), "mon: 09:00-17:00"
        )

    def test_gap_stays_visible(self):
        self.assertEqual(
            format_day_line(self.shifts, "wed"), "wed: 10:00-12:00, 13:00-15:00"
        )

    def test_closed_day(self):
        self.assertEqual(format_day_line(self.shifts, "sun"), "sun: closed")
