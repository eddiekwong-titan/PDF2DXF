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
    start: tuple
    control1: tuple
    control2: tuple
    end: tuple


# ----------------------------------------------------------------------
# Quad
# ----------------------------------------------------------------------

@dataclass(slots=True)
class QuadEntity(Entity):
    points: tuple


# ----------------------------------------------------------------------
# Future Entities
# ----------------------------------------------------------------------

@dataclass(slots=True)
class CircleEntity(Entity):
    center: tuple
    radius: float


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