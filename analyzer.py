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

from config import (
    ENABLE_ARC_DETECTION,
    ENABLE_CIRCLE_DETECTION,
    ENABLE_SYMBOL_DETECTION,
    RADIUS_TOLERANCE,
)
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

        if ENABLE_CIRCLE_DETECTION:
            self.detect_circles()
        if ENABLE_ARC_DETECTION:
            self.detect_arcs()

        self.detect_closed_loops()
        self.detect_rectangles()

        if ENABLE_SYMBOL_DETECTION:
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

        return self.curve_groups

    def detect_circles(self, tolerance: float = RADIUS_TOLERANCE) -> list[CircleEntity]:
        """
        Recognize AutoCAD-exported circles from closed four-curve groups.

        This is not general circle fitting. AutoCAD exports native circles as
        four cubic Bezier segments, so this detector only evaluates closed
        CurveGroup objects with exactly four curves. Future revisions may add
        broader support for arbitrary Bezier approximations.
        """
        self.circles.clear()
        candidate_count = 0
        rejected_count = 0

        for group in self.curve_groups:
            if not group.closed or len(group.curves) != 4:
                continue

            candidate_count += 1
            circle_geometry = self._validate_circle_geometry(group, tolerance)

            if circle_geometry is None:
                rejected_count += 1
                continue

            center, radius, radius_error = circle_geometry
            self.circles.append(
                self._create_circle_entity(group, center, radius, radius_error)
            )

        if self.stats is not None:
            self.stats.circle_candidates += candidate_count
            self.stats.circle_accepted += len(self.circles)
            self.stats.circle_rejected += rejected_count
            self.stats.circles_detected += len(self.circles)
            self.stats.circles_recognized += len(self.circles)

        return self.circles

    def _estimate_circle_center(
        self,
        start_points: list[tuple[float, float]],
    ) -> tuple[float, float]:
        """
        Estimate center from opposite AutoCAD circle segment start points.

        For AutoCAD-exported circles, the four cubic Bezier segment starts are
        ordered around the circle. Opposite starts form diameters, so averaging
        midpoint(P1, P3) and midpoint(P2, P4) is more stable than averaging all
        four points when export noise shifts individual points slightly.
        """
        first_midpoint = (
            (start_points[0][0] + start_points[2][0]) / 2,
            (start_points[0][1] + start_points[2][1]) / 2,
        )
        second_midpoint = (
            (start_points[1][0] + start_points[3][0]) / 2,
            (start_points[1][1] + start_points[3][1]) / 2,
        )
        return (
            (first_midpoint[0] + second_midpoint[0]) / 2,
            (first_midpoint[1] + second_midpoint[1]) / 2,
        )

    def _compute_circle_radius(
        self,
        center: tuple[float, float],
        start_points: list[tuple[float, float]],
    ) -> tuple[float, float, float, float]:
        """Return average, minimum, maximum, and maximum radius deviation."""
        radii = [point_distance(center, point) for point in start_points]
        average_radius = sum(radii) / len(radii)
        minimum_radius = min(radii)
        maximum_radius = max(radii)
        maximum_deviation = max(abs(value - average_radius) for value in radii)

        return average_radius, minimum_radius, maximum_radius, maximum_deviation

    def _validate_circle_geometry(
        self,
        group: CurveGroup,
        tolerance: float,
    ) -> tuple[tuple[float, float], float, float] | None:
        """
        Validate radii and opposite diameters for an AutoCAD circle candidate.

        Opposite-point checks reduce false positives because four points can
        have similar radii without representing AutoCAD's four ordered circle
        segments. Native AutoCAD circles export as four cubic Beziers, so P1/P3
        and P2/P4 should each span one diameter.
        """
        start_points = [curve_start(curve) for curve in group.curves]
        center = self._estimate_circle_center(start_points)
        (
            average_radius,
            minimum_radius,
            maximum_radius,
            maximum_deviation,
        ) = self._compute_circle_radius(center, start_points)

        if maximum_deviation > tolerance:
            return None

        expected_diameter = 2 * average_radius
        first_diameter = point_distance(start_points[0], start_points[2])
        second_diameter = point_distance(start_points[1], start_points[3])

        if abs(first_diameter - expected_diameter) > tolerance:
            return None
        if abs(second_diameter - expected_diameter) > tolerance:
            return None
        if abs(first_diameter - second_diameter) > tolerance:
            return None

        return center, average_radius, maximum_radius - minimum_radius

    def _create_circle_entity(
        self,
        group: CurveGroup,
        center: tuple[float, float],
        radius: float,
        radius_error: float,
    ) -> CircleEntity:
        """Create a CircleEntity while preserving the source CurveGroup."""
        return CircleEntity(
            layer=group.curves[0].layer,
            center=center,
            radius=radius,
            source_group=group,
            radius_error=radius_error,
            confidence=1.0,
        )

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
