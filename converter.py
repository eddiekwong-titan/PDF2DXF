import fitz
import ezdxf

from config import *
from entities import *
from statistics import Statistics
from geometry import *


class PDFConverter:

    def __init__(self):

        self.stats = Statistics()

        self.lines = []
        self.curves = []
        self.quads = []

        self.doc = None
        self.msp = None

    def reset_entities(self):

        self.lines.clear()
        self.curves.clear()
        self.quads.clear()

    def create_dxf(self):

        self.doc = ezdxf.new(DXF_VERSION)
        self.msp = self.doc.modelspace()

    def ensure_layer(self, layer):

        if not layer:
            layer = "0"

        if layer == "0":
            return

        if layer not in self.doc.layers:
            self.doc.layers.add(layer)

    def extract_entities(self, page):

        height = page.rect.height

        drawings = page.get_drawings()

        self.stats.pages += 1

        for drawing in drawings:

            layer = drawing.get("layer") or "0"

            self.stats.layers.add(layer)

            self.ensure_layer(layer)

            for entity in drawing["items"]:

                t = entity[0]

                if t == "l":

                    p1 = entity[1]
                    p2 = entity[2]

                    self.lines.append(

                        LineEntity(

                            p1.x,
                            flip_y(p1.y, height),

                            p2.x,
                            flip_y(p2.y, height),

                            layer,
                        )
                    )

                    self.stats.lines += 1

                elif t == "c":

                    self.curves.append(

                        CurveEntity(
                            entity[1],
                            entity[2],
                            entity[3],
                            entity[4],
                            layer,
                        )
                    )   

                    self.stats.curves += 1

                elif t == "qu":

                    self.quads.append(
                        QuadEntity(
                            entity[1],
                            layer,
                        )

                    )
                    

                    self.stats.quads += 1


#  **** this is the code
    # def write_lines(self):

    #     for line in self.lines:

    #         self.msp.add_line(

    #             (line.x1, line.y1),

    #             (line.x2, line.y2),

    #             dxfattribs={

    #                 "layer": line.layer
    #             }

    #         )

    # *** this is test code

    def write_lines(self):

        print(f"Writing {len(self.lines):,} lines...")

        for line in self.lines:

            self.msp.add_line(
                (line.x1, line.y1),
                (line.x2, line.y2),
                dxfattribs={
                    "layer": line.layer
                }
            )


    def save(self, filename):

        self.doc.saveas(filename)