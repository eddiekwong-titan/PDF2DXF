"""
optimizer.py
Geometry optimization stage for PDF2DXF.

Optimization runs after recognition so analysis can inspect the original PDF
geometry before cleanup changes entity counts or segment boundaries. Duplicate
removal runs before merging because repeated segments would otherwise inflate
merge work and can produce misleading continuous members. Layer boundaries are
never crossed because layers carry CAD meaning, and tolerances are configurable
because exported PDF coordinates are approximate.
"""

from __future__ import annotations

from config import (
    ENABLE_DUPLICATE_REMOVAL,
    ENABLE_LINE_MERGING,
    ZERO_LENGTH_TOLERANCE,
)
from entities import CurveEntity, LineEntity, QuadEntity
from geometry import line_length, point_distance, points_equal
from statistics import Statistics
from timer import Timer


class GeometryOptimizer:
    """Clean extracted geometry before DXF writing."""

    def __init__(self, tolerance: float = ZERO_LENGTH_TOLERANCE) -> None:
        self.tolerance = tolerance
        self.lines: list[LineEntity] = []
        self.curves: list[CurveEntity] = []
        self.quads: list[QuadEntity] = []
        self.stats: Statistics | None = None
        self.original_line_count = 0
        self.zero_length_removed = 0
        self.duplicates_removed = 0
        self.lines_merged = 0
        self.zero_length_time = 0.0
        self.duplicate_time = 0.0
        self.merge_time = 0.0
        self.total_optimize_time = 0.0
        self.merge_passes = 0

    def optimize(
        self,
        lines: list[LineEntity],
        curves: list[CurveEntity],
        quads: list[QuadEntity],
        stats: Statistics | None = None,
    ) -> list[LineEntity]:
        """Run line cleanup and return the optimized line collection."""
        self.lines = lines
        self.curves = curves
        self.quads = quads
        self.stats = stats
        self.original_line_count = len(lines)

        with Timer("Geometry Optimization") as total_timer:
            with Timer("Zero Length Removal") as zero_length_timer:
                self.remove_zero_length_lines()
            self.zero_length_time = zero_length_timer.elapsed

            if ENABLE_DUPLICATE_REMOVAL:
                with Timer("Duplicate Removal") as duplicate_timer:
                    self.remove_duplicate_lines()
                self.duplicate_time = duplicate_timer.elapsed

            if ENABLE_LINE_MERGING:
                with Timer("Line Merging") as merge_timer:
                    self.merge_collinear_lines()
                self.merge_time = merge_timer.elapsed

        self.total_optimize_time = total_timer.elapsed

        self._update_statistics()

        return self.lines

    def remove_zero_length_lines(self, tolerance: float | None = None) -> list[LineEntity]:
        """Remove lines shorter than the configured geometry tolerance."""
        tolerance = self.tolerance if tolerance is None else tolerance
        kept_lines = [
            line for line in self.lines if line_length(line) >= tolerance
        ]
        self.zero_length_removed += len(self.lines) - len(kept_lines)
        self.lines = kept_lines
        return self.lines

    def remove_duplicate_lines(self, tolerance: float | None = None) -> list[LineEntity]:
        """Remove duplicate and reversed-duplicate line segments in one pass."""
        tolerance = self.tolerance if tolerance is None else tolerance
        seen_keys: set[
            tuple[
                str,
                tuple[int, int],
                tuple[int, int],
            ]
        ] = set()
        unique_lines: list[LineEntity] = []

        for line in self.lines:
            key = self._line_duplicate_key(line, tolerance)

            if key in seen_keys:
                self.duplicates_removed += 1
                continue

            seen_keys.add(key)
            unique_lines.append(line)

        self.lines = unique_lines
        return self.lines

    def merge_collinear_lines(self, tolerance: float | None = None) -> list[LineEntity]:
        """
        Repeatedly merge indexed endpoint neighbors that satisfy merge rules.

        Endpoint indexing dramatically reduces comparisons by checking only
        lines that share quantized endpoint buckets instead of scanning every
        other line. The index is rebuilt after each merge pass because merged
        lines have new endpoints. Quantized endpoint keys avoid fragile raw
        floating-point dictionary keys while final merge checks still use the
        configured geometry tolerance.
        """
        tolerance = self.tolerance if tolerance is None else tolerance
        self.merge_passes = 0

        while True:
            self.merge_passes += 1
            endpoint_index = self._build_endpoint_index(tolerance)
            removed_indices: set[int] = set()
            pass_merged = 0

            for first_index, first_line in enumerate(self.lines):
                if first_index in removed_indices:
                    continue

                for second_index in self._candidate_line_indices(
                    first_index,
                    first_line,
                    endpoint_index,
                    tolerance,
                ):
                    if second_index in removed_indices:
                        continue
                    if second_index == first_index:
                        continue

                    second_line = self.lines[second_index]

                    if not self._can_merge(first_line, second_line, tolerance):
                        continue

                    merged_line = self._merge_lines(first_line, second_line)
                    if line_length(merged_line) < tolerance:
                        continue

                    self.lines[first_index] = merged_line
                    first_line = merged_line
                    removed_indices.add(second_index)
                    self.lines_merged += 1
                    pass_merged += 1

            if removed_indices:
                self.lines = [
                    line
                    for line_index, line in enumerate(self.lines)
                    if line_index not in removed_indices
                ]

            if pass_merged == 0:
                break

        return self.lines

    def _build_endpoint_index(
        self,
        tolerance: float,
    ) -> dict[tuple[int, int], list[tuple[int, bool]]]:
        index: dict[tuple[int, int], list[tuple[int, bool]]] = {}

        for line_index, line in enumerate(self.lines):
            if line_length(line) < tolerance:
                continue

            for is_start, point in (
                (True, self._line_start(line)),
                (False, self._line_end(line)),
            ):
                index.setdefault(self._endpoint_key(point, tolerance), []).append(
                    (line_index, is_start)
                )

        return index

    def _endpoint_key(
        self,
        point: tuple[float, float],
        tolerance: float,
    ) -> tuple[int, int]:
        return (
            round(point[0] / tolerance),
            round(point[1] / tolerance),
        )

    def _line_duplicate_key(
        self,
        line: LineEntity,
        tolerance: float,
    ) -> tuple[str, tuple[int, int], tuple[int, int]]:
        first_key = self._endpoint_key(self._line_start(line), tolerance)
        second_key = self._endpoint_key(self._line_end(line), tolerance)
        normalized_start, normalized_end = sorted((first_key, second_key))

        return (line.layer, normalized_start, normalized_end)

    def _candidate_line_indices(
        self,
        line_index: int,
        line: LineEntity,
        endpoint_index: dict[tuple[int, int], list[tuple[int, bool]]],
        tolerance: float,
    ) -> list[int]:
        candidates: set[int] = set()

        for point in (self._line_start(line), self._line_end(line)):
            endpoint_key = self._endpoint_key(point, tolerance)

            for neighbor_key in self._neighbor_endpoint_keys(endpoint_key):
                for candidate_index, _is_start in endpoint_index.get(neighbor_key, []):
                    if candidate_index != line_index:
                        candidates.add(candidate_index)

        return sorted(candidates)

    def _neighbor_endpoint_keys(
        self,
        endpoint_key: tuple[int, int],
    ) -> list[tuple[int, int]]:
        key_x, key_y = endpoint_key
        return [
            (key_x + offset_x, key_y + offset_y)
            for offset_x in (-1, 0, 1)
            for offset_y in (-1, 0, 1)
        ]

    def _line_start(self, line: LineEntity) -> tuple[float, float]:
        return (line.x1, line.y1)

    def _line_end(self, line: LineEntity) -> tuple[float, float]:
        return (line.x2, line.y2)

    def _can_merge(
        self,
        first_line: LineEntity,
        second_line: LineEntity,
        tolerance: float,
    ) -> bool:
        if first_line.layer != second_line.layer:
            return False

        if line_length(first_line) < tolerance or line_length(second_line) < tolerance:
            return False

        if not self._share_endpoint(first_line, second_line, tolerance):
            return False

        return self._are_collinear(first_line, second_line, tolerance)

    def _share_endpoint(
        self,
        first_line: LineEntity,
        second_line: LineEntity,
        tolerance: float,
    ) -> bool:
        return any(
            points_equal(first_point, second_point, tolerance)
            for first_point in (self._line_start(first_line), self._line_end(first_line))
            for second_point in (self._line_start(second_line), self._line_end(second_line))
        )

    def _are_collinear(
        self,
        first_line: LineEntity,
        second_line: LineEntity,
        tolerance: float,
    ) -> bool:
        first_start = self._line_start(first_line)
        first_end = self._line_end(first_line)
        second_start = self._line_start(second_line)
        second_end = self._line_end(second_line)

        base_length = point_distance(first_start, first_end)
        if base_length < tolerance:
            return False

        return (
            self._point_line_distance(second_start, first_start, first_end) <= tolerance
            and self._point_line_distance(second_end, first_start, first_end) <= tolerance
        )

    def _point_line_distance(
        self,
        point: tuple[float, float],
        line_start: tuple[float, float],
        line_end: tuple[float, float],
    ) -> float:
        dx = line_end[0] - line_start[0]
        dy = line_end[1] - line_start[1]
        length = point_distance(line_start, line_end)

        if length == 0:
            return point_distance(point, line_start)

        return abs(dx * (line_start[1] - point[1]) - (line_start[0] - point[0]) * dy) / length

    def _merge_lines(self, first_line: LineEntity, second_line: LineEntity) -> LineEntity:
        points = [
            self._line_start(first_line),
            self._line_end(first_line),
            self._line_start(second_line),
            self._line_end(second_line),
        ]
        start_point, end_point = self._farthest_points(points)

        return LineEntity(
            layer=first_line.layer,
            x1=start_point[0],
            y1=start_point[1],
            x2=end_point[0],
            y2=end_point[1],
        )

    def _farthest_points(
        self,
        points: list[tuple[float, float]],
    ) -> tuple[tuple[float, float], tuple[float, float]]:
        farthest_pair = (points[0], points[1])
        farthest_distance = -1.0

        for first_index, first_point in enumerate(points):
            for second_point in points[first_index + 1:]:
                distance = point_distance(first_point, second_point)
                if distance > farthest_distance:
                    farthest_distance = distance
                    farthest_pair = (first_point, second_point)

        return farthest_pair

    def _update_statistics(self) -> None:
        if self.stats is None:
            return

        self.stats.zero_length_removed += self.zero_length_removed
        self.stats.duplicate_lines_removed += self.duplicates_removed
        self.stats.lines_merged += self.lines_merged
        self.stats.removed_short_lines += self.zero_length_removed
        self.stats.duplicate_lines += self.duplicates_removed
        self.stats.merged_lines += self.lines_merged
        self.stats.optimizer_zero_length_time += self.zero_length_time
        self.stats.optimizer_duplicate_time += self.duplicate_time
        self.stats.optimizer_merge_time += self.merge_time
        self.stats.optimizer_merge_passes += self.merge_passes
