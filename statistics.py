from dataclasses import dataclass, field

@dataclass
class Statistics:

    pages: int = 0

    lines: int = 0
    curves: int = 0
    quads: int = 0

    dxf_lines: int = 0
    dxf_curves: int = 0

    duplicate_lines: int = 0
    merged_lines: int = 0

    layers: set = field(default_factory=set)