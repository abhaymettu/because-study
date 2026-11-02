"""Span and Shift, the two values everything else passes around."""

from dataclasses import dataclass

MINUTES_PER_DAY = 24 * 60
DAYS = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")


@dataclass(frozen=True, order=True)
class Span:
    """A stretch of one day, in minutes since midnight. End is exclusive."""

    start: int
    end: int

    def __post_init__(self):
        if not 0 <= self.start < self.end <= MINUTES_PER_DAY:
            raise ValueError(f"not a valid span: {self.start} to {self.end}")

    @property
    def minutes(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class Shift:
    """One person working one span on one day of the week."""

    worker: str
    day: str
    span: Span
