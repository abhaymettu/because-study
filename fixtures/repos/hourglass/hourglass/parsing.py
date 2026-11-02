"""Turn the text people write for times and days into values, and back."""

from hourglass.models import DAYS, MINUTES_PER_DAY, Span


def parse_clock(text: str) -> int:
    """Read 9:30 or 17:05 as minutes since midnight. 24:00 is allowed."""
    hours, separator, minutes = text.strip().partition(":")
    if not separator or not hours.isdigit() or not minutes.isdigit():
        raise ValueError(f"bad clock time: {text!r}")
    total = int(hours) * 60 + int(minutes)
    if int(minutes) > 59 or total > MINUTES_PER_DAY:
        raise ValueError(f"clock time out of range: {text!r}")
    return total


def format_clock(minutes: int) -> str:
    hours, remainder = divmod(minutes, 60)
    return f"{hours:02d}:{remainder:02d}"


def parse_span(text: str) -> Span:
    """Read a range such as 09:00-17:30. Overnight ranges are not supported."""
    start, separator, end = text.partition("-")
    if not separator:
        raise ValueError(f"expected start-end, got {text!r}")
    return Span(parse_clock(start), parse_clock(end))


def format_span(span: Span) -> str:
    return f"{format_clock(span.start)}-{format_clock(span.end)}"


def normalize_day(text: str) -> str:
    """Accept mon, Mon or Monday and hand back the short lowercase name."""
    short = text.strip().lower()[:3]
    if short not in DAYS:
        raise KeyError(text)
    return short
