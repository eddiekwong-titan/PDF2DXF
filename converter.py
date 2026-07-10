"""
converter.py
Revision 4.0.1 PDF to DXF conversion logic.

This revision extracts LINE, CURVE, and QUAD entities from AutoCAD-generated
vector PDFs, runs geometry analysis, optimizes linework, and writes native DXF
LINE and CIRCLE entities.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import ezdxf
import fitz

from analyzer import GeometryAnalyzer
from config import (
    DXF_VERSION,
    ENABLE_OPTIMIZER,
    INPUT_FOLDER,
    OUTPUT_FOLDER,
    WRITE_CURVES,
    WRITE_QUADS,
)
from entities import CircleEntity, CurveEntity, LineEntity, QuadEntity
from geometry import flip_y
from optimizer import GeometryOptimizer
from statistics import Statistics
from timer import Timer


class PDFConverter:
    """Convert vector PDF geometry into DXF entities."""

    def __init__(self) -> None:
        self.stats = Statistics()
        self.lines: list[LineEntity] = []
        self.curves: list[CurveEntity] = []
        self.quads: list[QuadEntity] = []
        self.circles: list[CircleEntity] = []
        self.doc: Any | None = None
        self.msp: Any | None = None

    def reset_entities(self) -> None:
        """Clear entities collected for the current PDF."""
        self.lines.clear()
        self.curves.clear()
        self.quads.clear()
        self.circles.clear()

    @staticmethod
    def point_tuple(point: Any, page_height: float) -> tuple[float, float]:
        """
        Convert a PyMuPDF point into a primitive project coordinate.

        PDF coordinates place Y=0 at the top of the page. PDF2DXF flips Y at
        extraction time so all stored geometry already matches the DXF-style
        coordinate orientation. Storing plain tuples keeps the converter's
        internal collections free of PyMuPDF geometry objects.
        """
        return (point.x, flip_y(point.y, page_height))

    def create_dxf(self) -> None:
        """Create a fresh DXF document for the current PDF."""
        self.doc = ezdxf.new(DXF_VERSION)
        self.msp = self.doc.modelspace()

    def ensure_layer(self, layer: str | None) -> str:
        """Create the DXF layer if needed and return the usable layer name."""
        layer_name = layer or "0"

        if self.doc is None:
            raise RuntimeError("DXF document has not been created.")

        if layer_name != "0" and layer_name not in self.doc.layers:
            self.doc.layers.add(layer_name)

        return layer_name

    def extract_entities(self, page: fitz.Page) -> None:
        """Extract supported geometry entities from one PDF page."""
        page_height = page.rect.height
        self.stats.pages += 1

        for drawing in page.get_drawings():
            layer = self.ensure_layer(drawing.get("layer"))
            self.stats.layers.add(layer)

            for item in drawing.get("items", []):
                if item[0] == "l":
                    start = self.point_tuple(item[1], page_height)
                    end = self.point_tuple(item[2], page_height)
                    self.lines.append(
                        LineEntity(
                            layer=layer,
                            x1=start[0],
                            y1=start[1],
                            x2=end[0],
                            y2=end[1],
                        )
                    )
                    self.stats.lines += 1
                elif item[0] == "c":
                    self.curves.append(
                        CurveEntity(
                            layer=layer,
                            start=self.point_tuple(item[1], page_height),
                            control1=self.point_tuple(item[2], page_height),
                            control2=self.point_tuple(item[3], page_height),
                            end=self.point_tuple(item[4], page_height),
                        )
                    )
                    self.stats.curves += 1
                elif item[0] == "qu":
                    quad = item[1]
                    self.quads.append(
                        QuadEntity(
                            layer=layer,
                            points=tuple(
                                self.point_tuple(point, page_height)
                                for point in (quad.ul, quad.ur, quad.ll, quad.lr)
                            ),
                        )
                    )
                    self.stats.quads += 1

    def write_line_entities(self) -> None:
        """Write project line entities to the DXF modelspace."""
        if self.msp is None:
            raise RuntimeError("DXF modelspace has not been created.")

        suppressed_entity_ids = self._suppressed_entity_ids()

        for line in self.lines:
            if id(line) in suppressed_entity_ids:
                continue

            self.ensure_layer(line.layer)
            self.msp.add_line(
                (line.x1, line.y1),
                (line.x2, line.y2),
                dxfattribs={"layer": line.layer},
            )
            self.stats.dxf_lines += 1

    def write_circle_entities(self) -> None:
        """Write project circle entities to the DXF modelspace."""
        if self.msp is None:
            raise RuntimeError("DXF modelspace has not been created.")

        for circle in self.circles:
            if not self._valid_circle(circle):
                self.stats.circle_rejected += 1
                continue

            layer = self.ensure_layer(circle.layer)
            self.msp.add_circle(
                center=circle.center,
                radius=circle.radius,
                dxfattribs={"layer": layer},
            )
            self.stats.dxf_circles += 1

    def write_curve_entities(self) -> None:
        """Write project curve entities to the DXF modelspace when enabled."""
        if not WRITE_CURVES:
            return

    def write_quad_entities(self) -> None:
        """Write project quad entities to the DXF modelspace when enabled."""
        if not WRITE_QUADS:
            return

    def _suppressed_entity_ids(self) -> set[int]:
        """
        Return source entity ids that should not be emitted directly.

        Source entities represented by higher-level CAD entities are suppressed
        by the writer, not the analyzer. Currently this collection is usually
        empty because CurveEntity objects are not written to DXF. Future
        versions will suppress CurveEntity, ArcEntity, PolylineEntity,
        SplineEntity, and other source geometry through this same mechanism.
        """
        suppressed_ids: set[int] = set()

        for circle in self.circles:
            for source_entity in circle.source_group.curves:
                if isinstance(source_entity, LineEntity):
                    suppressed_ids.add(id(source_entity))

        return suppressed_ids

    def _valid_circle(self, circle: CircleEntity) -> bool:
        """Validate a recognized circle before writing it to DXF."""
        center_x, center_y = circle.center

        return (
            circle.layer is not None
            and circle.layer != ""
            and circle.radius > 0
            and math.isfinite(circle.radius)
            and math.isfinite(center_x)
            and math.isfinite(center_y)
        )

    def save(self, filename: Path | str) -> None:
        """Save the current DXF document."""
        if self.doc is None:
            raise RuntimeError("DXF document has not been created.")

        filename = Path(filename)
        filename.parent.mkdir(parents=True, exist_ok=True)
        self.doc.saveas(filename)

    def convert_pdf(
        self,
        pdf_path: Path | str,
        output_path: Path | str | None = None,
    ) -> Path:
        """Convert one PDF file to one DXF file and return the DXF path."""
        pdf_path = Path(pdf_path)
        dxf_path = (
            Path(output_path)
            if output_path is not None
            else OUTPUT_FOLDER / f"{pdf_path.stem}.dxf"
        )

        with Timer("Total", self.stats, "total_time"):
            self.reset_entities()
            self.create_dxf()

            with Timer("Entity Extraction", self.stats, "extraction_time"):
                with fitz.open(pdf_path) as pdf:
                    for page in pdf:
                        self.extract_entities(page)

            analyzer = GeometryAnalyzer()
            with Timer("Geometry Analysis", self.stats, "analysis_time"):
                analyzer.analyze(self.lines, self.curves, self.quads, self.stats)
            self.circles = analyzer.circles

            if ENABLE_OPTIMIZER:
                optimizer = GeometryOptimizer()
                with Timer("Geometry Optimization", self.stats, "optimization_time"):
                    self.lines = optimizer.optimize(
                        self.lines,
                        self.curves,
                        self.quads,
                        self.stats,
                    )

            with Timer("DXF Writing", self.stats, "dxf_writing_time"):
                self.write_line_entities()
                self.write_circle_entities()
                self.write_curve_entities()
                self.write_quad_entities()
                self.save(dxf_path)

            self.stats.pdfs += 1

        return dxf_path

    def convert_folder(self) -> None:
        """Convert every PDF in the configured input folder."""
        pdf_files = sorted(INPUT_FOLDER.glob("*.pdf"))
        for pdf_path in pdf_files:
            output_path = OUTPUT_FOLDER / f"{pdf_path.stem}.dxf"
            self.convert_pdf(pdf_path, output_path)

        self.stats.report()
