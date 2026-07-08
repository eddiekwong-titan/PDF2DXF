class PDFConverter:

    def __init__(self):

        self.lines = []
        self.curves = []
        self.quads = []

    def convert_folder(self):
        ...

    def convert_pdf(self, pdf):
        ...

    def extract_entities(self, page):
        ...

    def convert_lines(self):
        ...

    def convert_curves(self):
        ...

    def save(self):
        ...