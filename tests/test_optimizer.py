import unittest
from contextlib import redirect_stdout
from io import StringIO

from entities import LineEntity
from optimizer import GeometryOptimizer


def line(start, end, layer="A-LINE"):
    return LineEntity(
        layer=layer,
        x1=start[0],
        y1=start[1],
        x2=end[0],
        y2=end[1],
    )


def optimize(lines):
    optimizer = GeometryOptimizer()
    with redirect_stdout(StringIO()):
        return optimizer.optimize(lines, [], [])


class GeometryOptimizerTests(unittest.TestCase):
    def test_zero_length_removal(self):
        lines = [
            line((0.0, 0.0), (0.0001, 0.0)),
            line((0.0, 0.0), (1.0, 0.0)),
        ]

        optimized = optimize(lines)

        self.assertEqual(len(optimized), 1)
        self.assertEqual((optimized[0].x2, optimized[0].y2), (1.0, 0.0))

    def test_duplicate_removal(self):
        lines = [
            line((0.0, 0.0), (1.0, 0.0)),
            line((0.0, 0.0), (1.0, 0.0)),
        ]

        optimized = optimize(lines)

        self.assertEqual(len(optimized), 1)

    def test_reversed_duplicate_removal(self):
        lines = [
            line((0.0, 0.0), (1.0, 0.0)),
            line((1.0, 0.0), (0.0, 0.0)),
        ]

        optimized = optimize(lines)

        self.assertEqual(len(optimized), 1)

    def test_simple_collinear_merge(self):
        lines = [
            line((0.0, 0.0), (1.0, 0.0)),
            line((1.0, 0.0), (2.0, 0.0)),
        ]

        optimized = optimize(lines)

        self.assertEqual(len(optimized), 1)
        self.assertEqual((optimized[0].x1, optimized[0].y1), (0.0, 0.0))
        self.assertEqual((optimized[0].x2, optimized[0].y2), (2.0, 0.0))

    def test_different_layer_does_not_merge(self):
        lines = [
            line((0.0, 0.0), (1.0, 0.0), layer="A-WALL"),
            line((1.0, 0.0), (2.0, 0.0), layer="A-DOOR"),
        ]

        optimized = optimize(lines)

        self.assertEqual(len(optimized), 2)

    def test_non_collinear_does_not_merge(self):
        lines = [
            line((0.0, 0.0), (1.0, 0.0)),
            line((1.0, 0.0), (1.0, 1.0)),
        ]

        optimized = optimize(lines)

        self.assertEqual(len(optimized), 2)


if __name__ == "__main__":
    unittest.main()
