"""Packaging entry point for pyside6-deploy / Nuitka.

Development continues to use: ``python -m source.main``

Deploy needs a root-level script so ``from source...`` resolves and is
included in the macOS app bundle.
"""

from __future__ import annotations

from source.main import main


if __name__ == "__main__":
    raise SystemExit(main())
