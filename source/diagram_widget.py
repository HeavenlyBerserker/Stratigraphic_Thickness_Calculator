"""Scrollable diagram panel for model tabs (pure Qt, no QSvgWidget).

Renders SVGs with QSvgRenderer into a QImage shown on a QLabel. QSvgWidget is
avoided because on Windows an SVG widget can briefly appear as its own
top-level window during tab construction.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QRectF, Qt, QTimer
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QLabel, QScrollArea, QSizePolicy, QVBoxLayout, QWidget

from source.diagrams import resolve_diagram_path
from source.svg_qt_prep import prepare_svg_for_qt

_DIAGRAM_BG = "#ffffff"
_PREPARED_CACHE: dict[str, bytes] = {}


def _prepared_svg(path: Path) -> bytes:
    key = str(path.resolve())
    cached = _PREPARED_CACHE.get(key)
    if cached is not None:
        return cached
    raw = path.read_bytes()
    prepared = prepare_svg_for_qt(raw) if path.suffix.lower() == ".svg" else raw
    _PREPARED_CACHE[key] = prepared
    return prepared


def _render_svg_pixmap(data: bytes, width: int, height: int) -> QPixmap | None:
    renderer = QSvgRenderer(QByteArray(data))
    if not renderer.isValid() or width < 1 or height < 1:
        return None
    dpr = 2.0
    img_w = max(1, int(width * dpr))
    img_h = max(1, int(height * dpr))
    image = QImage(img_w, img_h, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.white)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter, QRectF(0, 0, img_w, img_h))
    painter.end()
    image.setDevicePixelRatio(dpr)
    return QPixmap.fromImage(image)


class DiagramWidget(QWidget):
    """Shows a static model diagram scaled to the panel."""

    def __init__(self, model_id: str | None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._model_id = model_id
        self._path: Path | None = None
        self._svg_data: bytes | None = None
        self._aspect = 1.0
        self._loaded = False
        # Block loading until the main window has been shown (avoids flashes
        # when QTabWidget briefly shows each page during construction).
        self._startup_ok = False
        self._label: QLabel | None = None
        self._source_pixmap: QPixmap | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._scroll = QScrollArea(self)
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self._holder = QWidget(self._scroll)
        self._holder_layout = QVBoxLayout(self._holder)
        self._holder_layout.setContentsMargins(4, 4, 4, 4)
        self._holder_layout.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )

        self._scroll.setWidget(self._holder)
        layout.addWidget(self._scroll)
        self._apply_white_background()

        self._label = QLabel(self._holder)
        self._label.setAlignment(
            Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter
        )
        self._label.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )
        self._holder_layout.addWidget(self._label)

        if model_id:
            self.set_model(model_id)

    def _apply_white_background(self) -> None:
        self.setStyleSheet(f"background: {_DIAGRAM_BG};")
        self._scroll.setStyleSheet(f"background: {_DIAGRAM_BG};")
        self._scroll.viewport().setStyleSheet(f"background: {_DIAGRAM_BG};")
        self._holder.setStyleSheet(f"background: {_DIAGRAM_BG};")

    def allow_loading(self) -> None:
        """Called once the main window is visible; safe to create diagram content."""
        self._startup_ok = True
        if self.isVisible():
            self._ensure_content()

    def set_model(self, model_id: str | None) -> None:
        self._model_id = model_id
        self._loaded = False
        self._svg_data = None
        self._source_pixmap = None
        if self._label is not None:
            self._label.clear()
        self._path = resolve_diagram_path(model_id)
        if self._path is None:
            self.setVisible(False)
            return
        self.setVisible(True)
        if self._startup_ok and self.isVisible():
            self._ensure_content()

    def ensure_loaded(self) -> None:
        self._ensure_content()

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        if self._loaded:
            QTimer.singleShot(0, self._fit_content)

    def showEvent(self, event) -> None:  # noqa: N802
        super().showEvent(event)
        if self._startup_ok:
            self._ensure_content()
            QTimer.singleShot(0, self._fit_content)

    def _ensure_content(self) -> None:
        if not self._startup_ok or self._loaded or self._path is None:
            return
        if self._path.suffix.lower() == ".svg":
            try:
                self._svg_data = _prepared_svg(self._path)
            except OSError:
                self.setVisible(False)
                return
            renderer = QSvgRenderer(QByteArray(self._svg_data))
            if not renderer.isValid():
                self.setVisible(False)
                return
            vb = renderer.viewBoxF()
            if vb.width() > 1 and vb.height() > 1:
                self._aspect = vb.width() / vb.height()
            else:
                ds = renderer.defaultSize()
                self._aspect = (
                    ds.width() / ds.height() if ds.height() > 0 else 1.0
                )
        else:
            pixmap = QPixmap(str(self._path))
            if pixmap.isNull():
                self.setVisible(False)
                return
            self._source_pixmap = pixmap
            self._aspect = (
                pixmap.width() / pixmap.height() if pixmap.height() > 0 else 1.0
            )
        self._loaded = True
        self._fit_content()

    def _fit_size(self) -> tuple[int, int]:
        available_w = max(80, self._scroll.viewport().width() - 12)
        available_h = max(80, self._scroll.viewport().height() - 12)
        width_limited_h = available_w / self._aspect
        if width_limited_h <= available_h:
            w, h = available_w, width_limited_h
        else:
            h = available_h
            w = h * self._aspect
        return max(1, int(w)), max(1, int(h))

    def _fit_content(self) -> None:
        if not self._loaded or self._label is None:
            return
        w, h = self._fit_size()
        if self._svg_data is not None:
            pixmap = _render_svg_pixmap(self._svg_data, w, h)
            if pixmap is None:
                return
            self._label.setPixmap(pixmap)
            self._label.setFixedSize(w, h)
        elif self._source_pixmap is not None:
            scaled = self._source_pixmap.scaled(
                w,
                h,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._label.setPixmap(scaled)
            self._label.setFixedSize(scaled.size())
