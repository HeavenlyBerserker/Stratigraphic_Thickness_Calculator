"""
Interactive 3D geometry schematic for the Qt desktop app (PySide6).

Default: Matplotlib/QtAgg (`mpl_geometry_schematic.py`) — smaller bundles, no Chromium.

Optional: Qt WebEngine + `mobile/geometry-schematic.js` (same rendering as the PWA) when
run as ``python -m source.main --js`` or when frozen with ``BACKEND_MPL = False`` from
the ``-js`` / ``--js`` build scripts.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget


def _project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path.cwd()))
    return Path(__file__).resolve().parent.parent


def mobile_dir() -> Path:
    return _project_root() / "mobile"


def geometry_embed_path() -> Path:
    return mobile_dir() / "geometry_embed.html"


# Maps desktop ModelTab input keys → JSON keys expected by mobile `geometry-schematic.js`
_INPUT_ROWS: dict[str, list[tuple[str, str]]] = {
    "t1": [
        ("m", "measured_thickness"),
        ("delta", "wellbore_inclination_deg"),
        ("phib", "wellbore_azimuth_deg"),
        ("beta1", "formation_dip_deg"),
        ("phid1", "dip_azimuth_deg"),
    ],
    "t2": [
        ("m2", "measured_thickness"),
        ("delta2", "wellbore_inclination_deg"),
        ("phib2", "wellbore_azimuth_deg"),
        ("beta1_2", "formation_dip1_deg"),
        ("phid1_2", "dip_azimuth1_deg"),
        ("beta2_2", "formation_dip2_deg"),
        ("phid2_2", "dip_azimuth2_deg"),
    ],
    "t3": [
        ("m3", "measured_thickness"),
        ("delta3", "wellbore_inclination_deg"),
        ("phib3", "wellbore_azimuth_deg"),
        ("beta1_3", "formation_dip1_deg"),
        ("phid1_3", "dip_azimuth1_deg"),
        ("beta2_3", "formation_dip2_deg"),
        ("phid2_3", "dip_azimuth2_deg"),
    ],
    "t4": [
        ("m4", "measured_thickness"),
        ("delta4", "wellbore_inclination_deg"),
        ("phib4", "wellbore_azimuth_deg"),
        ("beta1_4", "formation_dip1_deg"),
        ("phid1_4", "dip_azimuth1_deg"),
        ("beta2_4", "formation_dip2_deg"),
        ("phid2_4", "dip_azimuth2_deg"),
    ],
    "t5": [
        ("m5", "measured_thickness"),
        ("delta5", "wellbore_inclination_deg"),
        ("phib5", "wellbore_azimuth_deg"),
        ("beta1_5", "formation_dip1_deg"),
        ("phid1_5", "dip_azimuth1_deg"),
        ("beta2_5", "formation_dip2_deg"),
        ("phid2_5", "dip_azimuth2_deg"),
    ],
    "t6": [
        ("m6", "measured_thickness"),
        ("delta6", "wellbore_inclination_deg"),
        ("phib6", "wellbore_azimuth_deg"),
        ("beta1_6", "formation_dip1_deg"),
        ("phid1_6", "dip_azimuth1_deg"),
        ("beta2_6", "formation_dip2_deg"),
        ("phid2_6", "dip_azimuth2_deg"),
    ],
    "t7": [
        ("m7", "measured_thickness"),
        ("delta7", "wellbore_inclination_deg"),
        ("phib7", "wellbore_azimuth_deg"),
        ("beta1_7", "formation_dip1_deg"),
        ("phid1_7", "dip_azimuth1_deg"),
        ("beta2_7", "formation_dip2_deg"),
        ("phid2_7", "dip_azimuth2_deg"),
    ],
    "t8": [
        ("m8", "measured_thickness"),
        ("delta8", "wellbore_inclination_deg"),
        ("phib8", "wellbore_azimuth_deg"),
        ("beta1_8", "formation_dip1_deg"),
        ("phid1_8", "dip_azimuth1_deg"),
        ("beta2_8", "formation_dip2_deg"),
        ("phid2_8", "dip_azimuth2_deg"),
    ],
}


def _jsonify(obj: Any) -> Any:
    if is_dataclass(obj):
        return _jsonify(asdict(obj))
    if isinstance(obj, dict):
        return {k: _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonify(v) for v in obj]
    if isinstance(obj, float) and (obj != obj or obj in (float("inf"), float("-inf"))):
        return None
    return obj


def build_geometry_payload(model_id: str, tab: Any, result: object) -> dict[str, Any]:
    """Build `{ result, inputs }` in the same shape the web PWA uses for `STC_DRAW_GEOMETRY`."""
    rows = _INPUT_ROWS.get(model_id)
    if not rows:
        raise ValueError(f"Unknown geometry model_id: {model_id}")
    inputs: dict[str, float] = {}
    for key_tab, key_json in rows:
        inputs[key_json] = float(tab.value(key_tab))
    return {"result": _jsonify(result), "inputs": inputs}


_force_webengine_from_cli = False


def set_desktop_force_webengine(enabled: bool) -> None:
    """Set by ``main.py`` when ``python -m source.main --js`` is used (before app import)."""
    global _force_webengine_from_cli
    _force_webengine_from_cli = bool(enabled)


def desktop_uses_mpl_schematic() -> bool:
    """
    False if ``main`` set ``--js``. When frozen, ``generated_desktop_backend.BACKEND_MPL``
    from the build script; when running from source, default is Matplotlib (True) unless
    ``--js`` forces WebEngine.
    """
    if _force_webengine_from_cli:
        return False
    if not getattr(sys, "frozen", False):
        return True
    try:
        from source import generated_desktop_backend as _gdb

        return bool(_gdb.BACKEND_MPL)
    except ImportError:
        return True


def make_geometry_schematic_widget(parent: QWidget | None = None) -> QWidget:
    """Matplotlib by default; Qt WebEngine + JS when ``--js`` or a ``-js`` PyInstaller build."""
    if desktop_uses_mpl_schematic():
        from source.mpl_geometry_schematic import MplGeometrySchematicWidget

        return MplGeometrySchematicWidget(parent)
    return GeometrySchematicWebEngineWidget(parent)


class GeometrySchematicWebEngineWidget(QWidget):
    """
    Embeds `geometry_embed.html` + `geometry-schematic.js`. If Qt WebEngine is not
    available, shows a short fallback message.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._web_ok = False
        self._view: Any = None
        self._page_loaded = False
        self._embed_path = geometry_embed_path()
        self._pending: tuple[str, dict[str, Any]] | None = None
        self._embed_load_started = False

        try:
            from PySide6.QtWebEngineCore import QWebEngineSettings
            from PySide6.QtWebEngineWidgets import QWebEngineView

            self._view = QWebEngineView(self)
            s = self._view.settings()
            s.setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True
            )
            s.setAttribute(
                QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, False
            )
            _wa = QWebEngineSettings.WebAttribute
            if hasattr(_wa, "ShowScrollBars"):
                s.setAttribute(_wa.ShowScrollBars, False)
            self._view.loadFinished.connect(self._on_load_finished)
            self._view.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            self._web_ok = True
        except Exception:
            self._view = QLabel(
                "Interactive 3D schematic needs Qt WebEngine (PySide6 with QtWebEngine). "
                "Reinstall PySide6 or use the web app for the full schematic.",
                self,
            )
            self._view.setWordWrap(True)
            self._view.setStyleSheet("color: #94a3b8; padding: 8px;")

        self._layout.addWidget(self._view)
        self._apply_visible_slot_size()
        if self._web_ok and self._embed_path.is_file():
            self._embed_load_started = True
            self._view.load(QUrl.fromLocalFile(str(self._embed_path.resolve())))

    def _apply_visible_slot_size(self) -> None:
        """Minimum size for the schematic slot; height grows with layout (e.g. splitters)."""
        self.setMinimumHeight(160)
        self.setMaximumHeight(16777215)

    def _hide_canvas_js(self) -> None:
        if not self._web_ok or not self._page_loaded:
            return
        from PySide6.QtWebEngineWidgets import QWebEngineView

        if not isinstance(self._view, QWebEngineView):
            return
        self._view.page().runJavaScript(
            "(function(){var el=document.getElementById('geometryCanvas');"
            "if(el)el.style.display='none';})();"
        )

    def clear(self) -> None:
        self._pending = None
        self._hide_canvas_js()
        self._apply_visible_slot_size()

    def set_schematic(self, model_id: str | None, payload: dict[str, Any] | None) -> None:
        if not model_id or not payload:
            self.clear()
            return
        if not self._web_ok:
            self._pending = None
            return
        self._pending = (model_id, payload)
        self._apply_visible_slot_size()
        if not self._page_loaded:
            if not self._embed_path.is_file():
                if isinstance(self._view, QLabel):
                    self._view.setText(
                        f"Missing {self._embed_path}. Reinstall the app or add mobile/geometry_embed.html."
                    )
                return
            if not self._embed_load_started:
                self._embed_load_started = True
                self._view.load(QUrl.fromLocalFile(str(self._embed_path.resolve())))
            return
        self._inject()

    def _on_load_finished(self, ok: bool) -> None:
        if ok:
            self._page_loaded = True
        if ok:
            self._inject()

    def _inject(self) -> None:
        if not self._web_ok or self._pending is None:
            return
        model_id, payload = self._pending
        from PySide6.QtWebEngineWidgets import QWebEngineView

        if not isinstance(self._view, QWebEngineView):
            return
        js_payload = json.dumps(payload)
        js_model = json.dumps(model_id)
        script = (
            "(function(){"
            f"if(!globalThis.STC_DRAW_GEOMETRY)return;"
            "var el=document.getElementById('geometryCanvas');"
            "if(el)el.style.display='block';"
            f"globalThis.STC_DRAW_GEOMETRY(el,{js_model},{js_payload});"
            "})();"
        )
        self._view.page().runJavaScript(script)
