"""
Benchmark PDF2DXF conversion performance.

Usage:
    python benchmarks/benchmark.py INPUT_PDFS/sample.pdf
    python benchmarks/benchmark.py INPUT_PDFS/*.pdf
"""

from __future__ import annotations

import argparse
from glob import glob
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import logger
from config import OUTPUT_FOLDER
from converter import PDFConverter


def run_benchmark(pdf_paths: list[Path]) -> None:
    converter = PDFConverter()
    initial_lines = converter.stats.lines

    for pdf_path in pdf_paths:
        output_path = OUTPUT_FOLDER / f"{pdf_path.stem}.dxf"
        converter.convert_pdf(pdf_path, output_path)

    extracted_lines = converter.stats.lines - initial_lines
    final_lines = converter.stats.dxf_lines
    reduction = extracted_lines - final_lines

    logger.info("")
    logger.info("=" * 52)
    logger.info("PDF2DXF Benchmark")
    logger.info("=" * 52)
    logger.info(f"PDF Files                 : {len(pdf_paths):,}")
    logger.info(f"Lines Extracted           : {extracted_lines:,}")
    logger.info(f"Lines Written             : {final_lines:,}")
    logger.info(f"Line Reduction            : {reduction:,}")
    logger.info(f"Circles Recognized        : {converter.stats.circles_recognized:,}")
    logger.info(f"Extraction                : {converter.stats.extraction_time:.2f} sec")
    logger.info(f"Analysis                  : {converter.stats.analysis_time:.2f} sec")
    logger.info(f"Optimization              : {converter.stats.optimization_time:.2f} sec")
    logger.info(f"DXF Writing               : {converter.stats.dxf_writing_time:.2f} sec")
    logger.info(f"Total                     : {converter.stats.total_time:.2f} sec")
    logger.info("=" * 52)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark PDF2DXF conversion.")
    parser.add_argument("pdfs", nargs="+", type=Path, help="PDF file path(s) to convert")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    pdf_paths: list[Path] = []

    for path in args.pdfs:
        if any(character in str(path) for character in "*?"):
            pdf_paths.extend(Path(match) for match in glob(str(path)))
        elif path.suffix.lower() == ".pdf":
            pdf_paths.append(path)

    if not pdf_paths:
        raise SystemExit("No PDF files provided.")

    run_benchmark(sorted(pdf_paths))


if __name__ == "__main__":
    main()
