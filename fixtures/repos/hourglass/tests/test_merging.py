import unittest

from hourglass.merging import (
    intersect_spans,
    merge_spans,
    spans_overlap,
    total_minutes,
)
from hourglass.models import Span


class OverlapTests(unittest.TestCase):
    def test_touching_spans_do_not_overlap(self):
        self.assertFalse(spans_overlap(Span(60, 120), Span(120, 180)))

    def test_contained_span_overlaps(self):
        self.assertTrue(spans_overlap(Span(60, 300), Span(120, 180)))

    def test_intersection(self):
        self.assertEqual(
            intersect_spans(Span(60, 180), Span(120, 300)), Span(120, 180)
        )
        self.assertIsNone(intersect_spans(Span(60, 120), Span(200, 300)))


class MergeTests(unittest.TestCase):
    def test_empty(self):
        self.assertEqual(merge_spans([]), [])

    def test_merges_overlapping_and_touching(self):
        spans = [Span(300, 360), Span(60, 120), Span(120, 180), Span(150, 200)]
        self.assertEqual(merge_spans(spans), [Span(60, 200), Span(300, 360)])

    def test_keeps_longer_end_when_contained(self):
        self.assertEqual(merge_spans([Span(60, 300), Span(90, 120)]), [Span(60, 300)])

    def test_total_counts_overlap_once(self):
        self.assertEqual(total_minutes([Span(60, 120), Span(90, 150)]), 90)
