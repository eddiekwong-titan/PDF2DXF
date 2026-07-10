"""
config.py
PDF2DXF Configuration
"""

from pathlib import Path

# ----------------------------------------------------------------------
# Project Folders
# ----------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent

INPUT_FOLDER = PROJECT_ROOT / "INPUT_PDFS"
OUTPUT_FOLDER = PROJECT_ROOT / "OUTPUT_DXF"
LOG_FOLDER = PROJECT_ROOT / "LOGS"

# Create folders if they don't exist
INPUT_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)
LOG_FOLDER.mkdir(exist_ok=True)

# ----------------------------------------------------------------------
# DXF Settings
# ----------------------------------------------------------------------

DXF_VERSION = "R2018"

# ----------------------------------------------------------------------
# Geometry Tolerances
# ----------------------------------------------------------------------

POINT_TOLERANCE = 0.01
ZERO_LENGTH_TOLERANCE = 0.001
RADIUS_TOLERANCE = 0.01
COLLINEAR_TOLERANCE = 0.001

# ----------------------------------------------------------------------
# Geometry Settings
# ----------------------------------------------------------------------

BEZIER_SEGMENTS = 24

# ----------------------------------------------------------------------
# Optimizer
# ----------------------------------------------------------------------

ENABLE_OPTIMIZER = True
ENABLE_DUPLICATE_REMOVAL = True
ENABLE_LINE_MERGING = True

# ----------------------------------------------------------------------
# Analysis
# ----------------------------------------------------------------------

ENABLE_CIRCLE_DETECTION = True
ENABLE_ARC_DETECTION = False
ENABLE_SYMBOL_DETECTION = False

# ----------------------------------------------------------------------
# Output
# ----------------------------------------------------------------------

WRITE_CURVES = False
WRITE_QUADS = False
VERBOSE = True
DEBUG = False
