"""Combining and comparing spans within a single day."""

from typing import Iterable, List, Optional

from hourglass.models import Span


def spans_overlap(first: Span, second: Span) -> bool:
    """Touching spans such as 09:00-10:00 and 10:00-11:00 do not overlap."""
    return first.start < second.end and second.start < first.end


def intersect_spans(first: Span, second: Span) -> Optional[Span]:
    """The part two spans share, or None when they share nothing."""
    if not spans_overlap(first, second):
        return None
    return Span(max(first.start, second.start), min(first.end, second.end))


def merge_spans(spans: Iterable[Span]) -> List[Span]:
    """Collapse overlapping and touching spans into a sorted list."""
    ordered = sorted(spans)
    if not ordered:
        return []

    merged = [ordered[0]]
    for span in ordered[1:]:
        last = merged[-1]
        if span.start <= last.end:
            merged[-1] = Span(last.start, max(last.end, span.end))
        else:
            merged.append(span)
    return merged


def total_minutes(spans: Iterable[Span]) -> int:
    """Minutes covered by at least one span, counting overlaps once."""
    return sum(span.minutes for span in merge_spans(spans))
