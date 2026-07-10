"""
logger.py
Lightweight console logging for PDF2DXF.
"""

from __future__ import annotations

from config import DEBUG, VERBOSE


def info(message: str = "") -> None:
    """Write an informational message when verbose output is enabled."""
    if VERBOSE:
        print(message)


def warning(message: str) -> None:
    """Write a warning message."""
    if VERBOSE:
        print(f"WARNING: {message}")


def debug(message: str) -> None:
    """Write a debug message when debug output is enabled."""
    if DEBUG:
        print(f"DEBUG: {message}")


def error(message: str) -> None:
    """Write an error message."""
    print(f"ERROR: {message}")
