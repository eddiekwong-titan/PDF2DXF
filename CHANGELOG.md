# Changelog

## Revision 3.8

- Centralized tolerances, feature flags, and output options in `config.py`.
- Added lightweight logging through `logger.py`.
- Added reusable timing infrastructure through `timer.py`.
- Replaced scattered diagnostic output with a structured conversion summary.
- Added benchmark entry point for repeatable performance comparisons.
- Updated project documentation for architecture, capabilities, limitations, and roadmap.

## Revision 3.7

- Added geometry optimizer stage after analysis and before DXF writing.
- Added line cleanup for zero-length, duplicate, reversed duplicate, and collinear segments.
- Added optimizer unit tests.

## Revision 3.6

- Improved AutoCAD circle validation with opposite-point center estimation.
- Added radius and diameter validation for circle candidates.

## Revision 3.5

- Added internal AutoCAD four-Bezier circle recognition.
- Added circle detection unit tests.

## Revision 3.4

- Added curve connectivity grouping.

## Revision 3.3

- Added geometry analyzer framework.

## Revision 3.2

- Added curve and quad extraction into internal dataclasses.

## Revision 3.1

- Added line extraction and DXF line writing.

## Revision 3.0

- Created project structure and modular converter architecture.
