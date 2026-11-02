import unittest

from hourglass.models import Span
from hourglass.parsing import (
    format_clock,
    format_span,
    normalize_day,
    parse_clock,
    parse_span,
)


class ClockTests(unittest.TestCase):
    def test_reads_short_and_long_hours(self):
        self.assertEqual(parse_clock("9:30"), 570)
        self.assertEqual(parse_clock(" 17:05 "), 1025)

    def test_end_of_day_is_allowed(self):
        self.assertEqual(parse_clock("24:00"), 1440)

    def test_rejects_nonsense(self):
        for text in ("9", "nine:30", "9:75", "25:00", ""):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_clock(text)

    def test_format_pads_zeros(self):
        self.assertEqual(format_clock(65), "01:05")


class SpanTextTests(unittest.TestCase):
    def test_round_trip(self):
        span = parse_span("09:00-17:30")
        self.assertEqual(span, Span(540, 1050))
        self.assertEqual(format_span(span), "09:00-17:30")

    def test_missing_separator(self):
        with self.assertRaises(ValueError):
            parse_span("09:00")

    def test_overnight_is_rejected(self):
        with self.assertRaises(ValueError):
            parse_span("22:00-06:00")


class DayTests(unittest.TestCase):
    def test_spellings(self):
        self.assertEqual(normalize_day("Monday"), "mon")
        self.assertEqual(normalize_day(" SAT"), "sat")

    def test_unknown_day(self):
        with self.assertRaises(KeyError):
            normalize_day("someday")
