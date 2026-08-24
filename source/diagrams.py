"""Static model diagram assets (SVG preferred; PNG fallback)."""

from __future__ import annotations

import sys
from pathlib import Path

# Maps calculator model id → diagram file basename (without extension).
MODEL_DIAGRAM_BASENAMES: dict[str, str] = {
    "t1": "Fig_T1",
    "t2": "Fig_T2",
    "t3": "Fig_T3",
    "t4": "Fig_T4",
    "t5": "Fig_T5",
    "t6": "Fig_T6",
    "t7": "Fig_T7",
    "t8": "Fig_T8",
}


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path.cwd()))
    return Path(__file__).resolve().parent.parent


def diagrams_dir() -> Path:
    return project_root() / "diagrams"


def resolve_diagram_path(model_id: str | None) -> Path | None:
    """Return the first existing SVG or PNG for *model_id*, or None."""
    if not model_id:
        return None
    base = MODEL_DIAGRAM_BASENAMES.get(model_id.lower())
    if not base:
        return None
    folder = diagrams_dir()
    for ext in (".svg", ".png"):
        path = folder / f"{base}{ext}"
        if path.is_file():
            return path
    return None


def diagram_web_url(model_id: str | None) -> str | None:
    """URL relative to mobile/index.html."""
    path = resolve_diagram_path(model_id)
    if path is None:
        return None
    return f"../diagrams/{path.name}"
