import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

import ezdxf
from analyzer import GeometryAnalyzer
from converter import PDFConverter
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
    def detect(self, analyzer):
        with redirect_stdout(StringIO()):
            return analyzer.detect_circles()

    def test_valid_autocad_circle_is_recognized(self):
        analyzer = GeometryAnalyzer()
        analyzer.curve_groups = [
            group_from_points([(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)])
        ]

        circles = self.detect(analyzer)

        self.assertEqual(len(circles), 1)
        self.assertEqual(circles[0].center, (0.0, 0.0))
        self.assertAlmostEqual(circles[0].radius, 1.0)
        self.assertEqual(circles[0].radius_error, 0.0)
        self.assertEqual(circles[0].confidence, 1.0)
        self.assertIs(circles[0].source_group, analyzer.curve_groups[0])

    def test_wrong_curve_count_is_rejected(self):
        analyzer = GeometryAnalyzer()
        analyzer.curve_groups = [
            group_from_points([(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0)])
        ]

        circles = self.detect(analyzer)

        self.assertEqual(circles, [])

    def test_open_group_is_rejected(self):
        analyzer = GeometryAnalyzer()
        analyzer.curve_groups = [
            group_from_points(
                [(1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)],
                closed=False,
            )
        ]

        circles = self.detect(analyzer)

        self.assertEqual(circles, [])

    def test_inconsistent_radii_group_is_rejected(self):
        analyzer = GeometryAnalyzer()
        analyzer.curve_groups = [
            group_from_points([(1.0, 0.0), (0.0, 2.0), (-1.0, 0.0), (0.0, -1.0)])
        ]

        circles = self.detect(analyzer)

        self.assertEqual(circles, [])

    def test_incorrect_diameter_is_rejected(self):
        analyzer = GeometryAnalyzer()
        analyzer.curve_groups = [
            group_from_points([(1.0, 0.0), (0.0, 1.0), (0.0, -1.0), (-1.0, 0.0)])
        ]

        circles = self.detect(analyzer)

        self.assertEqual(circles, [])

    def test_circle_entity_writes_one_dxf_circle(self):
        doc = self.write_circle_dxf()

        circles = list(doc.modelspace().query("CIRCLE"))

        self.assertEqual(len(circles), 1)

    def test_source_curves_are_not_written(self):
        doc = self.write_circle_dxf()

        self.assertEqual(len(list(doc.modelspace().query("LINE"))), 0)
        self.assertEqual(len(list(doc.modelspace().query("SPLINE"))), 0)

    def test_circle_layer_is_preserved(self):
        doc = self.write_circle_dxf(layer="A-GRID")
        circle = list(doc.modelspace().query("CIRCLE"))[0]

        self.assertEqual(circle.dxf.layer, "A-GRID")

    def test_circle_radius_is_preserved(self):
        doc = self.write_circle_dxf(radius=2.5)
        circle = list(doc.modelspace().query("CIRCLE"))[0]

        self.assertAlmostEqual(circle.dxf.radius, 2.5)

    def test_circle_center_is_preserved(self):
        doc = self.write_circle_dxf(center=(10.0, 20.0))
        circle = list(doc.modelspace().query("CIRCLE"))[0]

        self.assertEqual(tuple(circle.dxf.center), (10.0, 20.0, 0.0))

    def write_circle_dxf(self, layer="A-CIRCLE", center=(0.0, 0.0), radius=1.0):
        points = [
            (center[0] + radius, center[1]),
            (center[0], center[1] + radius),
            (center[0] - radius, center[1]),
            (center[0], center[1] - radius),
        ]
        group = group_from_points(points)
        analyzer = GeometryAnalyzer()
        analyzer.curve_groups = [group]
        circles = analyzer.detect_circles()
        circles[0].layer = layer

        converter = PDFConverter()
        converter.create_dxf()
        converter.curves = group.curves
        converter.circles = circles
        converter.write_lines()
        converter.write_circles()
        converter.write_curves()

        with TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "circle.dxf"
            converter.save(output_path)
            return ezdxf.readfile(output_path)


if __name__ == "__main__":
    unittest.main()
