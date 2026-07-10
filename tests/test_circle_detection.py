import unittest

from analyzer import GeometryAnalyzer
from entities import CurveEntity, CurveGroup


def curve(start, end):
    return CurveEntity(
        layer="A-CIRCLE",
        start=start,
        control1=start,
        control2=end,
        end=end,
    )


def group_from_points(points, closed=True):
    curves = [
        curve(points[index], points[(index + 1) % len(points)])
        for index in range(len(points))
    ]
    return CurveGroup(
        curves=curves,
        closed=closed,
        start_point=points[0],
        end_point=points[0] if closed else points[-1],
    )


class CircleDetectionTests(unittest.TestCase):
    def test_valid_four_curve_closed_group_is_recognized(self):
        analyzer = GeometryAnalyzer()
        analyzer.curve_groups = [
            group_from_points([(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)])
        ]

        circles = analyzer.detect_circles()

        self.assertEqual(len(circles), 1)
        self.assertEqual(circles[0].center, (0.0, 0.0))
        self.assertAlmostEqual(circles[0].radius, 1.0)
        self.assertIs(circles[0].source_group, analyzer.curve_groups[0])

    def test_three_curve_group_is_rejected(self):
        analyzer = GeometryAnalyzer()
        analyzer.curve_groups = [
            group_from_points([(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0)])
        ]

        circles = analyzer.detect_circles()

        self.assertEqual(circles, [])

    def test_open_group_is_rejected(self):
        analyzer = GeometryAnalyzer()
        analyzer.curve_groups = [
            group_from_points(
                [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)],
                closed=False,
            )
        ]

        circles = analyzer.detect_circles()

        self.assertEqual(circles, [])

    def test_inconsistent_radii_group_is_rejected(self):
        analyzer = GeometryAnalyzer()
        analyzer.curve_groups = [
            group_from_points([(1.0, 0.0), (0.0, 2.0), (-1.0, 0.0), (0.0, -1.0)])
        ]

        circles = analyzer.detect_circles()

        self.assertEqual(circles, [])


if __name__ == "__main__":
    unittest.main()
