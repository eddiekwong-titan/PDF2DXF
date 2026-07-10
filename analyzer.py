"""
analyzer.py
Geometry recognition stage for PDF2DXF.

The GeometryAnalyzer is the CAD intelligence layer of the converter. It runs
after PDF extraction has produced project entity dataclasses and before DXF
generation, giving future revisions a place to recognize higher-level CAD
objects without mixing PDF or DXF library concerns into the geometry logic.

Future revisions will replace groups of Bezier curves with native CAD
entities, such as circles, arcs, closed polylines, rectangles, and symbols.
Grouping occurs before recognition so later algorithms can evaluate complete
curve chains instead of isolated Bezier segments.
"""

from __future__ import annotations

from entities import (
    ArcEntity,
    CircleEntity,
    CurveGroup,
    CurveEntity,
    LineEntity,
    PolylineEntity,
    QuadEntity,
)
from geometry import curve_end, curve_start, point_distance, points_equal
from statistics import Statistics


class GeometryAnalyzer:
    """
    Analyze extracted project geometry before DXF generation.

    Recognition belongs before DXF writing because the writer should receive
    geometry that has already been interpreted into the best available CAD
    representation. This module intentionally operates only on PDF2DXF entity
    dataclasses and does not import PyMuPDF or ezdxf.
    """

    def __init__(self) -> None:
        self.lines: list[LineEntity] = []
        self.curves: list[CurveEntity] = []
        self.quads: list[QuadEntity] = []
        self.curve_groups: list[CurveGroup] = []
        self.circles: list[CircleEntity] = []
        self.arcs: list[ArcEntity] = []
        self.polylines: list[PolylineEntity] = []
        self.stats: Statistics | None = None

    def analyze(
        self,
        lines: list[LineEntity],
        curves: list[CurveEntity],
        quads: list[QuadEntity],
        stats: Statistics | None = None,
    ) -> None:
        """Store extracted geometry references and run recognition stages."""
        self.lines = lines
        self.curves = curves
        self.quads = quads
        self.stats = stats

        self.group_connected_curves()
        self.detect_circles()
        self.detect_arcs()
        self.detect_closed_loops()
        self.detect_rectangles()
        self.detect_symbols()

    def group_connected_curves(self) -> list[CurveGroup]:
        """Group CurveEntity objects whose end/start points touch."""
        self.curve_groups.clear()
        processed_indices: set[int] = set()

        for seed_index, seed in enumerate(self.curves):
            if seed_index in processed_indices:
                continue

            processed_indices.add(seed_index)
            group_curves = [seed]
            start_point = curve_start(seed)
            end_point = curve_end(seed)
            changed = True

            while changed:
                changed = False

                for curve_index, curve in enumerate(self.curves):
                    if curve_index in processed_indices:
                        continue

                    curve_first = curve_start(curve)
                    curve_last = curve_end(curve)

                    if points_equal(end_point, curve_first):
                        group_curves.append(curve)
                        end_point = curve_last
                    elif points_equal(start_point, curve_last):
                        group_curves.insert(0, curve)
                        start_point = curve_first
                    else:
                        continue

                    processed_indices.add(curve_index)
                    changed = True

            self.curve_groups.append(
                CurveGroup(
                    curves=group_curves,
                    closed=points_equal(start_point, end_point),
                    start_point=start_point,
                    end_point=end_point,
                )
            )

        closed_groups = sum(1 for group in self.curve_groups if group.closed)

        if self.stats is not None:
            self.stats.curve_groups += len(self.curve_groups)
            self.stats.closed_curve_groups += closed_groups

        print("Curve Groups:")
        print(len(self.curve_groups))
        print()
        print("Closed Groups:")
        print(closed_groups)

        return self.curve_groups

    def detect_circles(self, tolerance: float = 0.01) -> list[CircleEntity]:
        """
        Recognize AutoCAD-exported circles from closed four-curve groups.

        This is not general circle fitting. AutoCAD exports native circles as
        four cubic Bezier segments, so this detector only evaluates closed
        CurveGroup objects with exactly four curves. Future revisions may add
        broader support for arbitrary Bezier approximations.
        """
        self.circles.clear()
        candidate_count = 0

        for group in self.curve_groups:
            if not group.closed or len(group.curves) != 4:
                continue

            candidate_count += 1
            start_points = [curve_start(curve) for curve in group.curves]
            center = (
                sum(point[0] for point in start_points) / len(start_points),
                sum(point[1] for point in start_points) / len(start_points),
            )
            radii = [point_distance(center, point) for point in start_points]
            radius = sum(radii) / len(radii)
            maximum_deviation = max(abs(value - radius) for value in radii)

            if maximum_deviation > tolerance:
                continue

            self.circles.append(
                CircleEntity(
                    layer=group.curves[0].layer,
                    center=center,
                    radius=radius,
                    source_group=group,
                )
            )

        if self.stats is not None:
            self.stats.circles_detected += len(self.circles)
            self.stats.circles_recognized += len(self.circles)

        print("Circle Candidates:")
        print(candidate_count)
        print()
        print("Circles Recognized:")
        print(len(self.circles))

        return self.circles

    def detect_arcs(self) -> None:
        """Future stage for recognizing arcs from Bezier curve chains."""
        pass

    def detect_closed_loops(self) -> None:
        """Future stage for recognizing closed loops as CAD polylines."""
        pass

    def detect_rectangles(self) -> None:
        """Future stage for recognizing rectangular geometry patterns."""
        pass

    def detect_symbols(self) -> None:
        """Future stage for recognizing repeated higher-level CAD symbols."""
        pass
