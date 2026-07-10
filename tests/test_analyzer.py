import unittest

from analyzer import GeometryAnalyzer
from entities import CurveEntity


def curve(start, end):
    return CurveEntity(
        layer="A-CURVE",
        start=start,
        control1=start,
        control2=end,
        end=end,
    )


class GeometryAnalyzerTests(unittest.TestCase):
    def test_connected_curves_create_closed_group(self):
        analyzer = GeometryAnalyzer()
        analyzer.curves = [
            curve((0.0, 0.0), (1.0, 0.0)),
            curve((1.0, 0.0), (1.0, 1.0)),
            curve((1.0, 1.0), (0.0, 0.0)),
        ]

        groups = analyzer.group_connected_curves()

        self.assertEqual(len(groups), 1)
        self.assertEqual(len(groups[0].curves), 3)
        self.assertTrue(groups[0].closed)

    def test_disconnected_curves_create_separate_groups(self):
        analyzer = GeometryAnalyzer()
        analyzer.curves = [
            curve((0.0, 0.0), (1.0, 0.0)),
            curve((10.0, 0.0), (11.0, 0.0)),
        ]

        groups = analyzer.group_connected_curves()

        self.assertEqual(len(groups), 2)
        self.assertFalse(groups[0].closed)
        self.assertFalse(groups[1].closed)


if __name__ == "__main__":
    unittest.main()
