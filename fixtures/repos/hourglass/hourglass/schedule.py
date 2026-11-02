"""Shift schedules stored as CSV with worker, day and span columns."""

import csv
from collections import defaultdict
from io import StringIO
from pathlib import Path
from typing import Dict, Iterable, List, Union

from hourglass.errors import ProjectError
from hourglass.merging import merge_spans
from hourglass.models import DAYS, Shift, Span
from hourglass.parsing import format_span, normalize_day, parse_span

REQUIRED_COLUMNS = ("worker", "day", "span")


def parse_schedule_text(text: str) -> List[Shift]:
    """Parse schedule CSV content that is already in memory."""
    rows = csv.DictReader(StringIO(text))
    missing = [c for c in REQUIRED_COLUMNS if c not in (rows.fieldnames or [])]
    if missing:
        names = ", ".join(missing)
        raise ProjectError(f"schedule is missing columns: {names}")
    return [
        Shift(row["worker"].strip(), normalize_day(row["day"]), parse_span(row["span"]))
        for row in rows
    ]


def load_schedule(path: Union[str, Path]) -> List[Shift]:
    """Read a schedule CSV from disk, ordered by day then start time."""
    shifts = parse_schedule_text(Path(path).read_text(encoding="utf-8"))
    return sorted(shifts, key=lambda shift: (DAYS.index(shift.day), shift.span))


def shifts_for_worker(shifts: Iterable[Shift], worker: str) -> List[Shift]:
    """All shifts for one worker. KeyError when they are not on the schedule."""
    found = [shift for shift in shifts if shift.worker == worker]
    if not found:
        raise KeyError(worker)
    return found


def worker_minutes(shifts: Iterable[Shift]) -> Dict[str, int]:
    """Scheduled minutes per worker, without merging their overlaps."""
    totals = defaultdict(int)
    for shift in shifts:
        totals[shift.worker] += shift.span.minutes
    return dict(totals)


def day_coverage(shifts: Iterable[Shift], day: str) -> List[Span]:
    """Merged spans for a day, regardless of who is working them."""
    wanted = normalize_day(day)
    return merge_spans(shift.span for shift in shifts if shift.day == wanted)


def format_day_line(shifts: Iterable[Shift], day: str) -> str:
    """One line for a day, like mon: 09:00-13:00, 14:00-17:00."""
    spans = day_coverage(shifts, day)
    if not spans:
        return f"{normalize_day(day)}: closed"
    text = ", ".join(format_span(span) for span in spans)
    return f"{normalize_day(day)}: {text}"
