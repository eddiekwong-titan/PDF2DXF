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
# Geometry Settings
# ----------------------------------------------------------------------

MIN_LINE_LENGTH = 0.001
BEZIER_SEGMENTS = 24

# ----------------------------------------------------------------------
# Debug
# ----------------------------------------------------------------------

DEBUG = True