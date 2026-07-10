"""
statistics.py
Conversion statistics and final reporting for PDF2DXF.
"""

from dataclasses import dataclass, field

import logger


@dataclass
class Statistics:
    # Project
    pdfs: int = 0
    pages: int = 0

    # Geometry extracted
    lines: int = 0
    curves: int = 0
    quads: int = 0

    # Geometry analysis
    curve_groups: int = 0
    closed_curve_groups: int = 0
    circles_recognized: int = 0
    circles_detected: int = 0
    circle_candidates: int = 0
    circle_rejected: int = 0
    circle_accepted: int = 0
    arcs_recognized: int = 0
    closed_loops: int = 0
    symbols_recognized: int = 0

    # Geometry optimization
    zero_length_removed: int = 0
    duplicate_lines_removed: int = 0
    lines_merged: int = 0

    # Backward-compatible optimizer counters
    duplicate_lines: int = 0
    merged_lines: int = 0
    removed_short_lines: int = 0

    # DXF output
    dxf_lines: int = 0
    dxf_curves: int = 0
    dxf_quads: int = 0
    dxf_circles: int = 0
    dxf_arcs: int = 0
    dxf_polylines: int = 0

    # Performance
    extraction_time: float = 0.0
    analysis_time: float = 0.0
    optimization_time: float = 0.0
    dxf_writing_time: float = 0.0
    total_time: float = 0.0
    optimizer_zero_length_time: float = 0.0
    optimizer_duplicate_time: float = 0.0
    optimizer_merge_time: float = 0.0
    optimizer_merge_passes: int = 0

    # Layers
    layers: set = field(default_factory=set)

    def start(self) -> None:
        """Deprecated compatibility hook; timing is handled by Timer."""
        return None

    def stop(self) -> None:
        """Deprecated compatibility hook; timing is handled by Timer."""
        return None

    @property
    def elapsed(self) -> float:
        return self.total_time

    def report(self) -> None:
        """Write the final conversion summary."""
        self._line()
        logger.info("PDF2DXF Conversion Summary")
        self._line()
        self._section(
            "Input",
            [
                ("PDF Files", self.pdfs),
                ("Pages", self.pages),
                ("Layers", len(self.layers)),
            ],
        )
        self._section(
            "Geometry Extracted",
            [
                ("Lines", self.lines),
                ("Curves", self.curves),
                ("Quads", self.quads),
            ],
        )
        self._section(
            "Geometry Analysis",
            [
                ("Curve Groups", self.curve_groups),
                ("Closed Groups", self.closed_curve_groups),
                ("Circle Candidates", self.circle_candidates),
                ("Circles Recognized", self.circles_recognized),
            ],
        )
        self._section(
            "Geometry Optimization",
            [
                ("Zero Length Removed", self.zero_length_removed),
                ("Duplicates Removed", self.duplicate_lines_removed),
                ("Merged Lines", self.lines_merged),
            ],
        )
        self._section(
            "DXF Output",
            [
                ("Lines Written", self.dxf_lines),
                ("Circles Written", self.dxf_circles),
                ("Arcs Written", self.dxf_arcs),
                ("Polylines Written", self.dxf_polylines),
            ],
        )
        self._section(
            "Performance",
            [
                ("Extraction", self._seconds(self.extraction_time)),
                ("Analysis", self._seconds(self.analysis_time)),
                ("Optimization", self._seconds(self.optimization_time)),
                ("DXF Writing", self._seconds(self.dxf_writing_time)),
                ("Total", self._seconds(self.total_time)),
            ],
        )
        self._line()

    def _section(self, title: str, rows: list[tuple[str, object]]) -> None:
        logger.info("")
        logger.info(title)
        logger.info("----------------------------------------")

        for label, value in rows:
            logger.info(f"{label:<25} : {self._format_value(value)}")

    def _line(self) -> None:
        logger.info("=" * 52)

    def _format_value(self, value: object) -> str:
        if isinstance(value, int):
            return f"{value:,}"
        return str(value)

    def _seconds(self, value: float) -> str:
        return f"{value:.2f} sec"
