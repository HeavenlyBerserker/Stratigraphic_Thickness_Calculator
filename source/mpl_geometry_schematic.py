"""
Matplotlib-based geometry schematic widget (desktop). Matches JS camera and framing constants
(``SCHEMATIC_PROJ_SPAN_FACTOR`` / ``STC_PROJ_SPAN_FACTOR``, default zoom); bed mesh is AABB-centered
at the schematic origin with the structural ray origin offset (see ``borehole_ray_o``).
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
    mt_display_endpoints,
    mt_display_single_bed_t234,
    project_cam_point,
    segment_depth_for_sort,
)


PITCH_LIM = (85.0 * math.pi) / 180.0
ZOOM_MIN = 0.4
ZOOM_MAX = 4.5
# Volume is AABB-centered at the schematic origin; vertical framing uses mid-height for all models.
ORIGIN_Y_FRAC = 0.5
# Tighter framing in the main plot: smaller factor = larger default scale (was ~1.12 here).
SCHEMATIC_PROJ_SPAN_FACTOR = 0.92
DEFAULT_SCHEMATIC_ZOOM = 1.10
# Subsegments along M / T for depth-sorted drawing with the bed (approximates a thin rod).
_MT_LINE_SAMPLES = 56


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
    o_vol = (0.0, 0.0, 0.0)
    o_ray = scene.borehole_ray_o
    if model_id in ("t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"):
        m_lo, m_hi = mt_display_single_bed_t234(
            scene.mesh_faces, o_ray, scene.borehole_end, model_id=model_id
        )
        t_lo, t_hi = mt_display_single_bed_t234(
            scene.mesh_faces, o_ray, scene.t_end, model_id=model_id
        )
    else:
        m_lo, m_hi = mt_display_endpoints(
            o_ray, scene.borehole_end, scene.mesh_faces, model_id=scene.model_id
        )
        t_lo, t_hi = mt_display_endpoints(o_ray, scene.t_end, scene.mesh_faces, model_id=scene.model_id)
    pts2.append(proj(o_vol))
    pts2.append(proj(m_lo))
    pts2.append(proj(m_hi))
    pts2.append(proj(t_lo))
    pts2.append(proj(t_hi))
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
    origin_y_frac = ORIGIN_Y_FRAC
    cx = plot_w * 0.5
    cy = plot_h * origin_y_frac
    proj_scale = (min(plot_w, plot_h) / (span * SCHEMATIC_PROJ_SPAN_FACTOR)) * zoom

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
    pad = max(sx1 - sx0, sy1 - sy0) * 0.04 + 8.0

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

    def _lerp3(a: tuple[float, float, float], b: tuple[float, float, float], t: float) -> tuple[float, float, float]:
        return (
            a[0] + t * (b[0] - a[0]),
            a[1] + t * (b[1] - a[1]),
            a[2] + t * (b[2] - a[2]),
        )

    n_samp = _MT_LINE_SAMPLES
    draw_rows: list[tuple[float, int, str, Any]] = []
    for f in scene.mesh_faces:
        draw_rows.append((face_depth_for_sort(f, yaw, pitch), 0, "face", f))
    for i in range(n_samp):
        t0 = i / n_samp
        t1 = (i + 1) / n_samp
        a = _lerp3(m_lo, m_hi, t0)
        b = _lerp3(m_lo, m_hi, t1)
        d = segment_depth_for_sort(a, b, yaw, pitch) + i * 1e-7
        draw_rows.append((d, 1, "mseg", (a, b)))
    for i in range(n_samp):
        t0 = i / n_samp
        t1 = (i + 1) / n_samp
        a = _lerp3(t_lo, t_hi, t0)
        b = _lerp3(t_lo, t_hi, t1)
        d = segment_depth_for_sort(a, b, yaw, pitch) + i * 1e-7
        draw_rows.append((d, 2, "tseg", (a, b)))
    draw_rows.sort(key=lambda r: (r[0], r[1]))

    z_geo = 5.0
    for _depth, _pri, kind, payload in draw_rows:
        if kind == "face":
            f = payload
            poly = [to_canvas(proj(v)) for v in f["verts"]]
            fc = _mpl_fill_rgba(f, model_id)
            ax.add_patch(
                Polygon(
                    poly,
                    closed=True,
                    facecolor=fc,
                    edgecolor="none",
                    linewidth=0,
                    zorder=z_geo,
                )
            )
            z_geo += 0.01
            ec = _mpl_edge_rgba(f)
            xs_p = [p[0] for p in poly] + [poly[0][0]]
            ys_p = [p[1] for p in poly] + [poly[0][1]]
            ax.plot(
                xs_p,
                ys_p,
                color=ec,
                lw=edge_outline,
                zorder=z_geo,
                solid_capstyle="round",
                solid_joinstyle="round",
            )
            z_geo += 0.01
        elif kind == "mseg":
            a, b = payload
            draw_seg_3(a, b, "#dc2626", lw_m, z=z_geo)
            z_geo += 0.01
        else:
            a, b = payload
            draw_seg_3(a, b, "#2563eb", lw_m, z=z_geo)
            z_geo += 0.01

    oc = to_canvas(proj(o_vol))
    z_axes = max(z_geo + 2.0, 50.0)
    ls = max(2.5, (plot_w / 600.0) * 2.5)
    draw_seg_3(ax_origin, v_add(ax_origin, ex), "#ea580c", ls, z=z_axes)
    draw_seg_3(ax_origin, v_add(ax_origin, ey), "#16a34a", ls, z=z_axes)
    draw_seg_3(ax_origin, v_add(ax_origin, ez), "#000000", ls, z=z_axes)

    ao_c = to_canvas(proj(ax_origin))
    ax.scatter([ao_c[0]], [ao_c[1]], s=28, fc="white", ec="#64748b", lw=1, zorder=z_axes + 1)

    ax.scatter([oc[0]], [oc[1]], s=36, fc="white", ec="#475569", lw=1, zorder=z_axes + 1)

    hint_fs = max(8.5, 10.0 * (plot_w / 600.0) ** 0.5)
    foot_fs = max(7.5, 8.2 * (plot_w / 600.0) ** 0.5)
    # Hug axes edges so the 3D content can use almost the full subplot (transAxes stable with adjustable="box").
    ax.text(
        0.5,
        0.998,
        "3D view - drag / wheel zoom / double-click reset",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=hint_fs,
        color="#334155",
        weight="bold",
        clip_on=False,
        zorder=z_axes + 3,
    )
    ax.text(
        0.5,
        0.002,
        "Schematic only - not to scale.",
        transform=ax.transAxes,
        ha="center",
        va="bottom",
        fontsize=foot_fs,
        color="#475569",
        clip_on=False,
        zorder=z_axes + 3,
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
        self._zoom = DEFAULT_SCHEMATIC_ZOOM
        self._drag = False
        self._last_x = 0.0
        self._last_y = 0.0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self._fig = Figure(figsize=(4.8, 3.8), constrained_layout=False)
        self._fig.patch.set_facecolor("#ffffff")

        # Legend column on the right: main schematic keeps full height for orbit/zoom.
        gs = self._fig.add_gridspec(1, 2, width_ratios=[1.0, 0.22], wspace=0.04)
        self._ax = self._fig.add_subplot(gs[0, 0])
        self._ax_leg = self._fig.add_subplot(gs[0, 1])
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
        self._zoom = getattr(self, "_zoom", DEFAULT_SCHEMATIC_ZOOM)
        self._full_redraw()

    def _legend_area_width_frac(self) -> float:
        # Match gridspec ~0.22/(1+0.22) plus small slack for wspace.
        return 0.26

    def _main_plot_px(self) -> tuple[float, float]:
        h = float(self.height() or 360)
        w = float(self.width() or 400)
        leg_frac = self._legend_area_width_frac()
        main_w = w * (1.0 - leg_frac) - 6.0
        return max(main_w, 120.0), max(h - 6.0, 80.0)

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
        fs = max(6.5, min(8.2, (plot_w / 520.0) * 8.2))
        n = len(lines)
        top_m, bot_m = 0.98, 0.04
        if n == 1:
            ys = [(top_m + bot_m) * 0.5]
        else:
            span = top_m - bot_m
            ys = [top_m - span * i / (n - 1) for i in range(n)]
        for ln, y in zip(lines, ys):
            self._ax_leg.text(
                0.04,
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
            self._zoom = DEFAULT_SCHEMATIC_ZOOM
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
