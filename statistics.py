"""
statistics.py
Conversion statistics for PDF2DXF.
"""

from dataclasses import dataclass, field
from time import perf_counter


@dataclass
class Statistics:

    # -------------------------------------------------------------
    # Project
    # -------------------------------------------------------------

    pdfs: int = 0
    pages: int = 0

    # -------------------------------------------------------------
    # Geometry
    # -------------------------------------------------------------

    lines: int = 0
    curves: int = 0
    quads: int = 0

    # -------------------------------------------------------------
    # DXF Output
    # -------------------------------------------------------------

    dxf_lines: int = 0
    dxf_curves: int = 0
    dxf_quads: int = 0

    # -------------------------------------------------------------
    # Optimizer
    # -------------------------------------------------------------

    duplicate_lines: int = 0
    merged_lines: int = 0
    removed_short_lines: int = 0

    # -------------------------------------------------------------
    # Layers
    # -------------------------------------------------------------

    layers: set = field(default_factory=set)

    # -------------------------------------------------------------
    # Timing
    # -------------------------------------------------------------

    start_time: float = 0.0
    end_time: float = 0.0

    # -------------------------------------------------------------
    # Timing Methods
    # -------------------------------------------------------------

    def start(self):
        self.start_time = perf_counter()

    def stop(self):
        self.end_time = perf_counter()

    @property
    def elapsed(self):

        if self.end_time == 0:
            return 0

        return self.end_time - self.start_time

    # -------------------------------------------------------------
    # Reporting
    # -------------------------------------------------------------

    def report(self):

        print()
        print("=" * 60)
        print("PDF2DXF Conversion Report")
        print("=" * 60)

        print(f"PDF Files            : {self.pdfs}")
        print(f"Pages               : {self.pages}")
        print(f"Layers              : {len(self.layers)}")

        print()

        print(f"Lines Found         : {self.lines:,}")
        print(f"Curves Found        : {self.curves:,}")
        print(f"Quads Found         : {self.quads:,}")

        print()

        print(f"DXF Lines Written   : {self.dxf_lines:,}")
        print(f"DXF Curves Written  : {self.dxf_curves:,}")
        print(f"DXF Quads Written   : {self.dxf_quads:,}")

        print()

        print(f"Duplicate Lines     : {self.duplicate_lines:,}")
        print(f"Merged Lines        : {self.merged_lines:,}")
        print(f"Short Lines Removed : {self.removed_short_lines:,}")

        print()

        print(f"Elapsed Time        : {self.elapsed:.2f} seconds")

        print("=" * 60)