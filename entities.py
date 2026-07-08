from dataclasses import dataclass

@dataclass(slots=True)
class LineEntity:
    start: tuple
    end: tuple
    layer: str


@dataclass(slots=True)
class CurveEntity:
    start: tuple
    control1: tuple
    control2: tuple
    end: tuple
    layer: str


@dataclass(slots=True)
class QuadEntity:
    points: list
    layer: str