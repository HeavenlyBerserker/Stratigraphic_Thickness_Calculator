"""Bundle the libexpat that this Python's pyexpat was built against.

Conda-forge Python 3.12+ links pyexpat against Expat >= 2.7.2, which exports
``XML_SetAllocTrackerActivationThreshold``. PyInstaller's dependency scan often
resolves ``libexpat.so.1`` to the older distro copy instead (Ubuntu 22.04 ships
2.4.x). The frozen app then crashes as soon as xml/openpyxl import.

This helper replaces collected libexpat binaries with the copy from
``CONDA_PREFIX`` / ``sys.prefix``, staged under the SONAME filename so the
dynamic loader can find it.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Iterable

NEEDED_SYMBOL = "XML_SetAllocTrackerActivationThreshold"


def _entry_parts(entry: Any) -> tuple[str, str, Any]:
    if isinstance(entry, (tuple, list)) and len(entry) >= 2:
        dest = str(entry[0])
        src = str(entry[1])
        kind = entry[2] if len(entry) > 2 else "BINARY"
        return dest, src, kind
    dest = str(getattr(entry, "name", None) or getattr(entry, "dest", "") or "")
    src = str(getattr(entry, "path", None) or getattr(entry, "src", "") or "")
    kind = getattr(entry, "typecode", "BINARY")
    return dest, src, kind


def _is_expat_shared_lib(name: str) -> bool:
    base = Path(name).name.lower()
    if base.startswith("pyexpat"):
        return False
    return (
        base.startswith("libexpat.so")
        or base.startswith("libexpat.")
        or base in {"libexpat.dll", "expat.dll", "libexpat.dylib"}
    )


def is_expat_binary_entry(entry: Any) -> bool:
    dest, src, _kind = _entry_parts(entry)
    return _is_expat_shared_lib(dest) or _is_expat_shared_lib(src)


def _has_needed_symbol(lib_path: Path) -> bool:
    if sys.platform == "win32":
        return True
    for cmd in (
        ["nm", "-D", "--defined-only", str(lib_path)],
        ["readelf", "-Ws", str(lib_path)],
    ):
        try:
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        except (FileNotFoundError, subprocess.CalledProcessError, OSError):
            continue
        return NEEDED_SYMBOL in out
    return True


def _candidate_paths() -> Iterable[Path]:
    prefixes: list[Path] = []
    for raw in (os.environ.get("CONDA_PREFIX"), sys.prefix, getattr(sys, "base_prefix", None)):
        if raw:
            path = Path(raw)
            if path not in prefixes:
                prefixes.append(path)

    if sys.platform == "win32":
        names_and_subs = [
            ("libexpat.dll", Path("Library") / "bin"),
            ("expat.dll", Path("Library") / "bin"),
            ("libexpat.dll", Path("DLLs")),
        ]
    elif sys.platform == "darwin":
        names_and_subs = [
            ("libexpat.1.dylib", Path("lib")),
            ("libexpat.dylib", Path("lib")),
        ]
    else:
        names_and_subs = [
            ("libexpat.so.1", Path("lib")),
            ("libexpat.so", Path("lib")),
        ]

    seen: set[Path] = set()
    for prefix in prefixes:
        for name, sub in names_and_subs:
            candidate = prefix / sub / name
            if not candidate.exists():
                continue
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            yield candidate


def find_matching_libexpat() -> Path | None:
    """Return the env libexpat that provides the symbols pyexpat needs."""
    for candidate in _candidate_paths():
        resolved = candidate.resolve()
        if _has_needed_symbol(resolved):
            return candidate
    return None


def dest_basename(src: Path) -> str:
    if sys.platform == "win32":
        return src.resolve().name
    if sys.platform == "darwin":
        return "libexpat.1.dylib"
    return "libexpat.so.1"


def stage_libexpat() -> Path | None:
    """Copy matching libexpat to a temp file named with the expected SONAME."""
    src = find_matching_libexpat()
    if src is None:
        return None
    dest = Path(tempfile.mkdtemp(prefix="pyi-expat-")) / dest_basename(src)
    shutil.copy2(src.resolve(), dest)
    return dest


def replace_expat_in_binaries(binaries: Iterable[Any]) -> list[Any]:
    """Drop scanned libexpat copies and insert the Python-matching one."""
    original = list(binaries)
    staged = stage_libexpat()
    if staged is None:
        print("PyInstaller libexpat: no env copy found; leaving scanned binaries unchanged.")
        return original
    print(f"PyInstaller libexpat: bundling {staged} ({staged.stat().st_size} bytes)")

    kept = [entry for entry in original if not is_expat_binary_entry(entry)]
    extra: list[tuple[str, str, str]] = [(staged.name, str(staged), "BINARY")]

    for entry in original:
        dest, _src, _kind = _entry_parts(entry)
        dest_norm = dest.replace("\\", "/")
        if "pyexpat" not in Path(dest_norm).name.lower():
            continue
        parent = str(Path(dest_norm).parent).replace("\\", "/")
        if parent not in {".", ""}:
            extra.append((f"{parent}/{staged.name}", str(staged), "BINARY"))
        break

    return kept + extra
