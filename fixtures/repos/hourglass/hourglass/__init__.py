"""Parse and merge time ranges and shift schedules."""

from hourglass.errors import ProjectError
from hourglass.merging import merge_spans, total_minutes
from hourglass.models import Shift, Span
from hourglass.parsing import format_span, parse_span
from hourglass.schedule import day_coverage, load_schedule, worker_minutes

__all__ = [
    "ProjectError",
    "Shift",
    "Span",
    "day_coverage",
    "format_span",
    "load_schedule",
    "merge_spans",
    "parse_span",
    "total_minutes",
    "worker_minutes",
]
