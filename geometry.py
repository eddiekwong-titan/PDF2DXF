"""
geometry.py
Geometry helper functions for PDF2DXF.
"""

from math import hypot, atan2, degrees

from config import COLLINEAR_TOLERANCE, POINT_TOLERANCE, ZERO_LENGTH_TOLERANCE


# ----------------------------------------------------------------------
# Coordinate Conversion
# ----------------------------------------------------------------------

def flip_y(y: float, page_height: float) -> float:
    """
    Convert PDF Y coordinates to CAD Y coordinates.
    """
    return page_height - y


# ----------------------------------------------------------------------
# Distance
# ----------------------------------------------------------------------

def distance(x1, y1, x2, y2):

    return hypot(x2 - x1, y2 - y1)


def point_distance(point1, point2):
    """
    Return the distance between two primitive (x, y) points.
    """
    return distance(point1[0], point1[1], point2[0], point2[1])


def points_equal(point1, point2, tolerance=POINT_TOLERANCE):
    """
    Compare two primitive points using a configurable tolerance.
    """
    return point_distance(point1, point2) <= tolerance


def line_length(line):

    return distance(
        line.x1,
        line.y1,
        line.x2,
        line.y2,
    )


def curve_start(curve):
    """
    Return the primitive start point of a CurveEntity.
    """
    return curve.start


def curve_end(curve):
    """
    Return the primitive end point of a CurveEntity.
    """
    return curve.end


# ----------------------------------------------------------------------
# Angle
# ----------------------------------------------------------------------

def line_angle(line):

    return degrees(

        atan2(

            line.y2 - line.y1,

            line.x2 - line.x1

        )

    )


# ----------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------

def is_zero_length(line, tolerance=ZERO_LENGTH_TOLERANCE):

    return line_length(line) < tolerance


def midpoint(line):

    return (

        (line.x1 + line.x2) / 2,

        (line.y1 + line.y2) / 2,

    )


# ----------------------------------------------------------------------
# Future Geometry
# ----------------------------------------------------------------------

def is_parallel(line1, line2, tolerance=COLLINEAR_TOLERANCE):
    """
    Placeholder
    """
    return False


def is_collinear(line1, line2, tolerance=COLLINEAR_TOLERANCE):
    """
    Placeholder
    """
    return False


def merge_lines(line1, line2):
    """
    Placeholder
    """
    return None


def circle_from_beziers(curves):
    """
    Placeholder

    Will later detect AutoCAD circles that are exported
    as four cubic Bezier curves.
    """
    return None
