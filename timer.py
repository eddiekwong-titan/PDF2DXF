"""
timer.py
Reusable timing context manager for PDF2DXF.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any


class Timer:
    """Measure elapsed time and optionally accumulate it on a stats object."""

    def __init__(self, name: str, stats: Any | None = None, field: str | None = None) -> None:
        self.name = name
        self.stats = stats
        self.field = field
        self.elapsed = 0.0
        self._start = 0.0

    def __enter__(self) -> "Timer":
        self._start = perf_counter()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.elapsed = perf_counter() - self._start

        if self.stats is not None and self.field is not None:
            current_value = getattr(self.stats, self.field, 0.0)
            setattr(self.stats, self.field, current_value + self.elapsed)
