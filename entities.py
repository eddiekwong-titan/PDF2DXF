"""
entities.py
Defines all geometry extracted from a PDF.
"""

from dataclasses import dataclass


# ----------------------------------------------------------------------
# Base Entity
# ----------------------------------------------------------------------

@dataclass(slots=True)
class Entity:
    """Base class for all extracted entities."""

    layer: str


# ----------------------------------------------------------------------
# Line
# ----------------------------------------------------------------------

@dataclass(slots=True)
class LineEntity(Entity):
    x1: float
    y1: float
    x2: float
    y2: float


# ----------------------------------------------------------------------
# Cubic Bezier Curve
# ----------------------------------------------------------------------

@dataclass(slots=True)
class CurveEntity(Entity):
    """
    Cubic Bezier curve extracted from a PDF drawing command.

    Coordinates are converted from PDF space to DXF-oriented space during
    extraction so downstream code never has to know about the PDF Y-axis.
    Points are stored as primitive (x, y) tuples instead of PyMuPDF objects so
    the internal geometry collections stay independent of the extraction
    library.
    """

    start: tuple[float, float]
    control1: tuple[float, float]
    control2: tuple[float, float]
    end: tuple[float, float]


# ----------------------------------------------------------------------
# Curve Group
# ----------------------------------------------------------------------

@dataclass(slots=True)
class CurveGroup:
    """Connected chain of Bezier curves prepared for future recognition."""

    curves: list[CurveEntity]
    closed: bool
    start_point: tuple[float, float]
    end_point: tuple[float, float]


# ----------------------------------------------------------------------
# Quad
# ----------------------------------------------------------------------

@dataclass(slots=True)
class QuadEntity(Entity):
    points: tuple[tuple[float, float], ...]


# ----------------------------------------------------------------------
# Future Entities
# ----------------------------------------------------------------------

@dataclass(slots=True)
class CircleEntity(Entity):
    """
    Circle recognized from an AutoCAD-generated four-curve Bezier group.

    AutoCAD exports native circles as four cubic Bezier segments. The original
    CurveGroup is retained so future revisions can replace or write native CAD
    circle entities without losing the source curves.
    """

    center: tuple[float, float]
    radius: float
    source_group: CurveGroup
    radius_error: float = 0.0
    confidence: float = 1.0


@dataclass(slots=True)
class ArcEntity(Entity):
    center: tuple
    radius: float
    start_angle: float
    end_angle: float


@dataclass(slots=True)
class PolylineEntity(Entity):
    points: list


@dataclass(slots=True)
class TextEntity(Entity):
    insertion: tuple
    height: float
    rotation: float
    text: str
