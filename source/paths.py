"""Resolve project root for development and frozen builds."""

from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    """Return the directory that contains ``diagrams/``, ``logo.png``, etc.

    - Development: repository root (parent of ``source/``).
    - PyInstaller: extraction dir (``sys._MEIPASS``).
    - Nuitka / other frozen: directory of the executable (macOS ``.app``
      puts data files next to ``Contents/MacOS/<binary>``).
    """
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent
