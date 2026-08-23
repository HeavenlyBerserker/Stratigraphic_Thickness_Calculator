#!/usr/bin/env python3
"""Generate mobile/batch-schema.js from source/batch_schema.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from source.batch_schema import to_js_object  # noqa: E402


def main() -> int:
    out = ROOT / "mobile" / "batch-schema.js"
    payload = json.dumps(to_js_object(), indent=2, ensure_ascii=False)
    out.write_text(
        "// Auto-generated from source/batch_schema.py — do not edit by hand.\n"
        "// Regenerate: python scripts/generate_batch_schema_js.py\n\n"
        f"const BATCH_SCHEMA = {payload};\n",
        encoding="utf-8",
    )
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
