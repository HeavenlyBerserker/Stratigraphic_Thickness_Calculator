"""
Matplotlib-based geometry schematic widget (desktop). Matches JS camera, scaling, T5/T6 origin offset.
"""

from __future__ import annotations

import math
import re
from typing import Any

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from matplotlib.patches import Polygon
from matplotlib import colors as mcolors
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget

from source.mpl_schematic_scene import (
    SchematicScene,
    axis_origin_xyz,
    collect_scene,
    face_depth_for_sort,
    project_cam_point,
)


PITCH_LIM = (85.0 * math.pi) / 180.0
ZOOM_MIN = 0.4
ZOOM_MAX = 4.5
# Semi-arch folds (T5/T6): projector origin O shifted up vs center so the arc fits (~JS originYFrac).
ORIGIN_Y_FRAC_T56 = 0.18


def _to_rgba(s: str, default_alpha: float = 1.0) -> tuple[float, float, float, float]:
    raw = str(s).strip()
    m = re.match(
        r"rgba?\(\s*([0-9.]+)\s*,\s*([0-9.]+)\s*,\s*([0-9.]+)\s*(?:,\s*([0-9.]+)\s*)?\)",
        raw,
        re.I,
    )
    if m:
        r255, g255, b255 = float(m.group(1)), float(m.group(2)), float(m.group(3))
        alpha = float(m.group(4)) if m.group(4) is not None else 1.0
        hi = max(r255, g255, b255)
        denom = 255.0 if hi > 1.5 else 1.0
        return (r255 / denom, g255 / denom, b255 / denom, alpha)
    try:
        return mcolors.to_rgba(raw)
    except ValueError:
        return (0.2, 0.5, 0.35, default_alpha)


def _mpl_fill_rgba(face: dict[str, Any], model_id: str) -> tuple[float, float, float, float]:
    """See-through sides; top/base caps stay readable (T1 uses one hue for both caps)."""
    r, g, b, a = _to_rgba(str(face["fill"]))
    surf = str(face.get("surface", ""))
    if surf in ("side", "cap", "end"):
        return (r, g, b, min(a, 0.12))
    if surf in ("top", "base"):
        lo, hi = (0.34, 0.5) if model_id != "t1" else (0.36, 0.52)
        return (r, g, b, min(max(a, lo), hi))
    return (r, g, b, min(a, 0.15))


def _mpl_edge_rgba(face: dict[str, Any]) -> tuple[float, float, float, float]:
    r, g, b, a = _to_rgba(str(face["stroke"]))
    return (r, g, b, max(a, 0.9))


def _render_main_ax(
    ax: Any,
    scene: SchematicScene,
    model_id: str,
    yaw: float,
    pitch: float,
    zoom: float,
    plot_w: float,
    plot_h: float,
) -> None:
    ax.clear()
    ax.set_facecolor("#ffffff")
    ax.patch.set_linewidth(0)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)

    proj = lambda p: project_cam_point(p, yaw, pitch)

    pts2: list[tuple[float, float]] = []
    o3 = (0.0, 0.0, 0.0)
    pts2.append(proj(o3))
    pts2.append(proj(scene.borehole_end))
    pts2.append(proj(scene.t_end))
    for f in scene.mesh_faces:
        for vx in f["verts"]:
            pts2.append(proj(vx))

    lr = scene.plane_size
    ax_origin = axis_origin_xyz(scene.plane_size)
    pts2.append(proj(ax_origin))
    ex = scene.axes_ex
    ey = scene.axes_ey
    ez = scene.axes_ez

    def v_add(a: tuple[float, float, float], b: tuple[float, float, float]) -> tuple[float, float, float]:
        return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

    pts2.append(proj(v_add(ax_origin, ex)))
    pts2.append(proj(v_add(ax_origin, ey)))
    pts2.append(proj(v_add(ax_origin, ez)))

    xs = [p[0] for p in pts2]
    ys = [p[1] for p in pts2]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span = max(max_x - min_x, max_y - min_y, 1e-6)
    origin_y_frac = ORIGIN_Y_FRAC_T56 if model_id in ("t5", "t6") else 0.5
    cx = plot_w * 0.5
    cy = plot_h * origin_y_frac
    proj_scale = (min(plot_w, plot_h) / (span * 1.18)) * zoom

    def to_canvas(p2: tuple[float, float]) -> tuple[float, float]:
        return (cx + p2[0] * proj_scale, cy - p2[1] * proj_scale)

    bx_lo = cx - plot_w / 2
    bx_hi = cx + plot_w / 2
    by_lo = cy - plot_h / 2
    by_hi = cy + plot_h / 2
    xs_c = []
    ys_c = []
    for px, py in pts2:
        qx, qy = to_canvas((px, py))
        xs_c.append(qx)
        ys_c.append(qy)

    sx0 = min(xs_c + [bx_lo] if xs_c else [bx_lo])
    sx1 = max(xs_c + [bx_hi] if xs_c else [bx_hi])
    sy0 = min(ys_c + [by_lo] if ys_c else [by_lo])
    sy1 = max(ys_c + [by_hi] if ys_c else [by_hi])
    pad = max(sx1 - sx0, sy1 - sy0) * 0.06 + 16.0

    sorted_faces = sorted(
        scene.mesh_faces, key=lambda f: face_depth_for_sort(f, yaw, pitch)
    )
    edge_outline = max(2.05, 2.5 * (plot_w / 600.0) ** 0.5)

    def draw_seg_3(
        a: tuple[float, float, float],
        b: tuple[float, float, float],
        col: str,
        lw: float,
        *,
        z: float = 5,
    ) -> None:
        pa = to_canvas(proj(a))
        pb = to_canvas(proj(b))
        ax.plot(
            [pa[0], pb[0]],
            [pa[1], pb[1]],
            color=col,
            lw=lw,
            zorder=z,
            solid_capstyle="round",
        )

    lw_m = max(2.0, 3.5 * (plot_w / 600.0) ** 0.5)
    # M / T under translucent fills so alpha occludes segments inside the bed (same idea as JS canvas).
    draw_seg_3(o3, scene.borehole_end, "#dc2626", lw_m, z=1)
    draw_seg_3(o3, scene.t_end, "#2563eb", lw_m, z=1)

    for f in sorted_faces:
        poly = [to_canvas(proj(v)) for v in f["verts"]]
        fc = _mpl_fill_rgba(f, model_id)
        ax.add_patch(
            Polygon(
                poly,
                closed=True,
                facecolor=fc,
                edgecolor="none",
                linewidth=0,
                zorder=2,
            )
        )

    for f in sorted_faces:
        poly = [to_canvas(proj(v)) for v in f["verts"]]
        ec = _mpl_edge_rgba(f)
        xs = [p[0] for p in poly] + [poly[0][0]]
        ys = [p[1] for p in poly] + [poly[0][1]]
        ax.plot(
            xs,
            ys,
            color=ec,
            lw=edge_outline,
            zorder=3,
            solid_capstyle="round",
            solid_joinstyle="round",
        )

    oc = to_canvas(proj(o3))

    ls = max(2.5, (plot_w / 600.0) * 2.5)
    draw_seg_3(ax_origin, v_add(ax_origin, ex), "#ea580c", ls, z=5)
    draw_seg_3(ax_origin, v_add(ax_origin, ey), "#16a34a", ls, z=5)
    draw_seg_3(ax_origin, v_add(ax_origin, ez), "#000000", ls, z=5)

    ao_c = to_canvas(proj(ax_origin))
    ax.scatter([ao_c[0]], [ao_c[1]], s=28, fc="white", ec="#64748b", lw=1, zorder=6)

    ax.scatter([oc[0]], [oc[1]], s=36, fc="white", ec="#475569", lw=1, zorder=6)

    hint_fs = 11 * (plot_w / 600.0) ** 0.5
    foot_fs = 9 * (plot_w / 600.0) ** 0.5
    # transAxes anchors stay stable when adjustable="box" changes data scaling.
    ax.text(
        0.5,
        0.985,
        "3D view - drag / wheel zoom / double-click reset",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=hint_fs,
        color="#334155",
        weight="bold",
        clip_on=False,
        zorder=8,
    )
    ax.text(
        0.5,
        0.015,
        "Schematic only - not to scale.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=foot_fs,
        color="#475569",
        clip_on=False,
        zorder=8,
    )

    ax.set_xlim(sx0 - pad, sx1 + pad)
    ax.set_ylim(sy1 + pad, sy0 - pad)
    # "datalim" fights fixed x/y limits and spams UserWarning on every redraw.
    ax.set_aspect("equal", adjustable="box")


class MplGeometrySchematicWidget(QWidget):
    """Interactive schematic using Matplotlib Qt backend (same geometry as JS; no WebEngine)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._payload: dict[str, Any] | None = None
        self._model_id: str | None = None
        self._scene: SchematicScene | None = None
        self._yaw = 0.0
        self._pitch = 0.0
        self._zoom = 1.0
        self._drag = False
        self._last_x = 0.0
        self._last_y = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._fig = Figure(figsize=(4.8, 3.8), constrained_layout=False)
        self._fig.patch.set_facecolor("#ffffff")

        # Extra height for legend rows so copy does not overlap (was height_ratios 1 / 0.34).
        gs = self._fig.add_gridspec(2, 1, height_ratios=[1.0, 0.42], hspace=0.1)
        self._ax = self._fig.add_subplot(gs[0])
        self._ax_leg = self._fig.add_subplot(gs[1])
        self._ax_leg.axis("off")
        self._ax_leg.set_facecolor("#ffffff")

        self._canvas = FigureCanvasQTAgg(self._fig)
        self._canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        self._canvas.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        layout.addWidget(self._canvas)

        self._cid_press = self._canvas.mpl_connect("button_press_event", self._on_press)
        self._cid_motion = self._canvas.mpl_connect("motion_notify_event", self._on_motion)
        self._cid_release = self._canvas.mpl_connect("button_release_event", self._on_release)
        self._cid_scroll = self._canvas.mpl_connect("scroll_event", self._on_scroll)
        self._cid_resize = self._canvas.mpl_connect("resize_event", self._on_resize)

        self.setMinimumHeight(160)
        self.setMaximumHeight(16777215)

    def clear(self) -> None:
        self._payload = None
        self._model_id = None
        self._scene = None
        self._ax.clear()
        self._ax_leg.clear()
        self._ax_leg.axis("off")
        self._canvas.draw_idle()

    def set_schematic(self, model_id: str | None, payload: dict[str, Any] | None) -> None:
        if not model_id or not payload:
            self.clear()
            return
        res = payload.get("result")
        inp = payload.get("inputs")
        if not res or not inp:
            self.clear()
            return
        m_len = float(inp.get("measured_thickness", 0))
        t_val = float(res.get("true_stratigraphic_thickness", 0))
        if not math.isfinite(m_len) or not math.isfinite(t_val):
            self.clear()
            return
        self._model_id = model_id
        self._payload = payload
        self._scene = collect_scene(model_id, res, m_len, t_val)
        if self._scene is None:
            self.clear()
            return
        self._zoom = getattr(self, "_zoom", 1.0)
        self._full_redraw()

    def _legend_area_height_frac(self) -> float:
        return 0.30

    def _main_plot_px(self) -> tuple[float, float]:
        h = float(self.height() or 360)
        w = float(self.width() or 400)
        leg_frac = self._legend_area_height_frac()
        main_h = h * (1.0 - leg_frac - 0.06)
        return w - 8.0, max(main_h, 80.0)

    def _full_redraw(self) -> None:
        if self._scene is None or self._model_id is None:
            return
        plot_w, plot_h = self._main_plot_px()
        _render_main_ax(self._ax, self._scene, self._model_id, self._yaw, self._pitch, self._zoom, plot_w, plot_h)

        self._ax_leg.clear()
        self._ax_leg.axis("off")
        sc = self._scene
        lines = [
            "Legend: x (N) orange  y (E) green  z (down) black  M red  T blue",
            "Drag = orbit. Wheel = zoom. Double-click = reset.",
            f"Bed volume: {sc.volume_kind}",
        ]
        if sc.wedge_footnote:
            lines.append(sc.wedge_footnote)
        if self._model_id in ("t5", "t6"):
            lines.append(
                "If η (between poles) is small, the drawn arc opens to ≥28° for visibility."
            )
        fs = max(8.5, min(11.0, (plot_w / 620.0) * 11.0))
        n = len(lines)
        top_m, bot_m = 0.97, 0.05
        if n == 1:
            ys = [(top_m + bot_m) * 0.5]
        else:
            span = top_m - bot_m
            ys = [top_m - span * i / (n - 1) for i in range(n)]
        for ln, y in zip(lines, ys):
            self._ax_leg.text(
                0.02,
                y,
                ln,
                transform=self._ax_leg.transAxes,
                va="center",
                ha="left",
                fontsize=fs,
                color="#334155",
                clip_on=False,
            )

        self._fig.canvas.draw_idle()

    def _in_main_ax(self, x: float, y: float) -> bool:
        return bool(self._ax.bbox.contains(x, y))

    def _rotation_sensitivity(self) -> float:
        w = max(float(self.width() or 400), 260.0)
        return 0.006 * (480.0 / min(960.0, w))

    def _on_press(self, ev: Any) -> None:
        if ev.button != 1 or ev.inaxes != self._ax:
            self._drag = False
            return
        if getattr(ev, "dblclick", False):
            self._yaw = 0.0
            self._pitch = 0.0
            self._zoom = 1.0
            self._drag = False
            self._full_redraw()
            return
        self._drag = True
        self._last_x = ev.x
        self._last_y = ev.y

    def _on_motion(self, ev: Any) -> None:
        if not self._drag or ev.x is None or ev.y is None:
            return
        dx = float(ev.x) - self._last_x
        dy = float(ev.y) - self._last_y
        self._last_x = float(ev.x)
        self._last_y = float(ev.y)
        sens = self._rotation_sensitivity()
        self._yaw -= dx * sens
        self._pitch -= dy * sens
        self._pitch = max(-PITCH_LIM, min(PITCH_LIM, self._pitch))
        self._full_redraw()

    def _on_release(self, ev: Any) -> None:
        if ev.button == 1:
            self._drag = False

    def _on_scroll(self, ev: Any) -> None:
        if ev.inaxes != self._ax:
            return
        f = 0.92 if ev.step > 0 else 1.09
        self._zoom = max(ZOOM_MIN, min(ZOOM_MAX, self._zoom * f))
        self._full_redraw()

    def _on_resize(self, _ev: Any) -> None:
        if self._scene is not None:
            self._full_redraw()
