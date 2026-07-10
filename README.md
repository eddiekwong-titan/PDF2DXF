# PDF2DXF

PDF2DXF converts AutoCAD-generated vector PDFs into DXF files for CAD review and cleanup workflows.

## Project Overview

The project extracts primitive vector geometry from PDFs, analyzes higher-level CAD intent, optimizes linework, and writes DXF output. Current production output is intentionally conservative: only `LINE` entities are written to DXF.

## Architecture

```text
main.py
  -> converter.py
      -> PyMuPDF extraction
      -> analyzer.py
      -> optimizer.py
      -> ezdxf writing

Shared modules:
  config.py      Central configuration and feature flags
  entities.py    Internal geometry dataclasses
  geometry.py    Geometry helper functions
  statistics.py  Conversion counters and summary report
  logger.py      Console logging
  timer.py       Stage timing
```

## Current Capabilities

- Batch conversion from `INPUT_PDFS/` to `OUTPUT_DXF/`
- CAD layer preservation
- Line extraction and DXF `LINE` writing
- Curve and quad extraction into internal dataclasses
- Curve grouping for analysis
- AutoCAD four-Bezier circle recognition, stored internally only
- Line optimizer for zero-length removal, duplicate removal, and collinear merging
- Conversion summary with stage timing

## Supported PDF Types

PDF2DXF is designed for AutoCAD-generated vector PDFs. Raster PDFs, scanned drawings, and arbitrary illustration PDFs are not supported.

## Known Limitations

- Circles, arcs, curves, quads, text, hatches, and symbols are not written to DXF yet.
- Circle recognition targets AutoCAD's four cubic Bezier circle export pattern.
- Optimizer tolerances are configurable, but aggressive values can alter linework.
- PDF layer data depends on how the source PDF was exported.

## Performance Example

```text
Extraction                : 3.94 sec
Analysis                  : 0.12 sec
Optimization              : 0.41 sec
DXF Writing               : 1.27 sec
Total                     : 5.74 sec
```

Use `benchmarks/benchmark.py` to compare future revisions on the same input PDFs.

## Roadmap

- Native DXF circle writing
- Arc recognition and DXF arc writing
- Polyline generation from closed loops
- Symbol recognition
- Text extraction
- Hatch cleanup
- GUI workflow
