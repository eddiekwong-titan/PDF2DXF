"""
converter.py
Revision 3.2 PDF to DXF conversion logic.

This revision extracts LINE, CURVE, and QUAD entities from AutoCAD-generated
vector PDFs. Only LINE entities are written to DXF output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import ezdxf
import fitz

from config import DXF_VERSION, INPUT_FOLDER, OUTPUT_FOLDER
from entities import CurveEntity, LineEntity, QuadEntity
from geometry import flip_y
from statistics import Statistics


class PDFConverter:
    """Convert vector PDF linework into DXF LINE entities."""

    def __init__(self) -> None:
        self.stats = Statistics()
        self.lines: list[LineEntity] = []
        self.curves: list[CurveEntity] = []
        self.quads: list[QuadEntity] = []
        self.doc: Any | None = None
        self.msp: Any | None = None

    def reset_entities(self) -> None:
        """Clear entities collected for the current PDF."""
        self.lines.clear()
        self.curves.clear()
        self.quads.clear()

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

    def write_lines(self) -> None:
        """Write extracted lines to the current DXF modelspace."""
        if self.msp is None:
            raise RuntimeError("DXF modelspace has not been created.")

        for line in self.lines:
            self.ensure_layer(line.layer)
            self.msp.add_line(
                (line.x1, line.y1),
                (line.x2, line.y2),
                dxfattribs={"layer": line.layer},
            )
            self.stats.dxf_lines += 1

    def write_curves(self) -> None:
        """Placeholder for future DXF curve output."""
        print("Curve writing not implemented.")

    def write_quads(self) -> None:
        """Placeholder for future DXF quad output."""
        print("Quad writing not implemented.")

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

        self.reset_entities()
        self.create_dxf()

        with fitz.open(pdf_path) as pdf:
            for page in pdf:
                self.extract_entities(page)

        self.write_lines()
        self.write_curves()
        self.write_quads()
        self.save(dxf_path)
        self.stats.pdfs += 1

        return dxf_path

    def convert_folder(self) -> None:
        """Convert every PDF in the configured input folder."""
        self.stats.start()

        pdf_files = sorted(INPUT_FOLDER.glob("*.pdf"))
        for pdf_path in pdf_files:
            output_path = OUTPUT_FOLDER / f"{pdf_path.stem}.dxf"
            self.convert_pdf(pdf_path, output_path)

        self.stats.stop()
        self.stats.report()
