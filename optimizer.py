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

from entities import CurveEntity, LineEntity, QuadEntity
from geometry import line_length, point_distance, points_equal
from statistics import Statistics


class GeometryOptimizer:
    """Clean extracted geometry before DXF writing."""

    def __init__(self, tolerance: float = 0.001) -> None:
        self.tolerance = tolerance
        self.lines: list[LineEntity] = []
        self.curves: list[CurveEntity] = []
        self.quads: list[QuadEntity] = []
        self.stats: Statistics | None = None
        self.original_line_count = 0
        self.zero_length_removed = 0
        self.duplicates_removed = 0
        self.lines_merged = 0

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

        self.remove_zero_length_lines()
        self.remove_duplicate_lines()
        self.merge_collinear_lines()
        self._update_statistics()
        self._print_report()

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
        """Remove duplicate and reversed-duplicate line segments."""
        tolerance = self.tolerance if tolerance is None else tolerance
        unique_lines: list[LineEntity] = []

        for line in self.lines:
            if any(self._lines_duplicate(line, existing, tolerance) for existing in unique_lines):
                self.duplicates_removed += 1
                continue

            unique_lines.append(line)

        self.lines = unique_lines
        return self.lines

    def merge_collinear_lines(self, tolerance: float | None = None) -> list[LineEntity]:
        """Repeatedly merge same-layer collinear lines that share an endpoint."""
        tolerance = self.tolerance if tolerance is None else tolerance
        changed = True

        while changed:
            changed = False

            for first_index, first_line in enumerate(self.lines):
                for second_index in range(first_index + 1, len(self.lines)):
                    second_line = self.lines[second_index]

                    if not self._can_merge(first_line, second_line, tolerance):
                        continue

                    merged_line = self._merge_lines(first_line, second_line)
                    self.lines[first_index] = merged_line
                    del self.lines[second_index]
                    self.lines_merged += 1
                    changed = True
                    break

                if changed:
                    break

        return self.lines

    def _line_start(self, line: LineEntity) -> tuple[float, float]:
        return (line.x1, line.y1)

    def _line_end(self, line: LineEntity) -> tuple[float, float]:
        return (line.x2, line.y2)

    def _lines_duplicate(
        self,
        first_line: LineEntity,
        second_line: LineEntity,
        tolerance: float,
    ) -> bool:
        if first_line.layer != second_line.layer:
            return False

        first_start = self._line_start(first_line)
        first_end = self._line_end(first_line)
        second_start = self._line_start(second_line)
        second_end = self._line_end(second_line)

        same_direction = (
            points_equal(first_start, second_start, tolerance)
            and points_equal(first_end, second_end, tolerance)
        )
        reversed_direction = (
            points_equal(first_start, second_end, tolerance)
            and points_equal(first_end, second_start, tolerance)
        )

        return same_direction or reversed_direction

    def _can_merge(
        self,
        first_line: LineEntity,
        second_line: LineEntity,
        tolerance: float,
    ) -> bool:
        if first_line.layer != second_line.layer:
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

    def _print_report(self) -> None:
        print("Optimizer")
        print("-------------------------")
        print("Original Lines:")
        print(self.original_line_count)
        print()
        print("Zero-Length Removed:")
        print(self.zero_length_removed)
        print()
        print("Duplicates Removed:")
        print(self.duplicates_removed)
        print()
        print("Merged Lines:")
        print(self.lines_merged)
        print()
        print("Final Lines:")
        print(len(self.lines))
