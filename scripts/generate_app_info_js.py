#!/usr/bin/env python3
"""Generate mobile/app-info.js from source/app_info.py."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source.app_info import to_js_file_content  # noqa: E402


def main() -> int:
    out = ROOT / "mobile" / "app-info.js"
    out.write_text(to_js_file_content(), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
