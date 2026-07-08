"""
geometry.py
Geometry helper functions for PDF2DXF.
"""

from math import hypot, atan2, degrees


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


def line_length(line):

    return distance(
        line.x1,
        line.y1,
        line.x2,
        line.y2,
    )


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

def is_zero_length(line, tolerance=0.001):

    return line_length(line) < tolerance


def midpoint(line):

    return (

        (line.x1 + line.x2) / 2,

        (line.y1 + line.y2) / 2,

    )


# ----------------------------------------------------------------------
# Future Geometry
# ----------------------------------------------------------------------

def is_parallel(line1, line2, tolerance=0.01):
    """
    Placeholder
    """
    return False


def is_collinear(line1, line2, tolerance=0.01):
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