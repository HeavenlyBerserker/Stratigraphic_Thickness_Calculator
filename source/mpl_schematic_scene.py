"""
Desktop Matplotlib schematic: 3D geometry matching `mobile/geometry-schematic.js` scene logic
(isometric-style camera, same meshes and colors). Default desktop schematic when
``BACKEND_MPL`` is True (standard build) or when running from source without ``--js``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


Vec3 = tuple[float, float, float]


def _v_from(a: Any) -> Vec3:
    if isinstance(a, (list, tuple)) and len(a) >= 3:
        return (float(a[0]), float(a[1]), float(a[2]))
    raise TypeError("expected length-3 sequence")


def _v_add(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _v_sub(a: Vec3, b: Vec3) -> Vec3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _v_scale(s: float, a: Vec3) -> Vec3:
    return (s * a[0], s * a[1], s * a[2])


def _v_dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _v_cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _v_norm(a: Vec3) -> float:
    return math.hypot(a[0], a[1], a[2])


def _v_unit(a: Vec3) -> Vec3:
    n = _v_norm(a)
    if n < 1e-15:
        return (0.0, 0.0, 1.0)
    return (a[0] / n, a[1] / n, a[2] / n)


def _basis_in_plane(n: Vec3) -> tuple[Vec3, Vec3, Vec3]:
    n1 = _v_unit(n)
    ref: Vec3 = (1.0, 0.0, 0.0) if abs(n1[0]) < 0.85 else (0.0, 1.0, 0.0)
    u = _v_unit(_v_cross(n1, ref))
    v = _v_unit(_v_cross(n1, u))
    return u, v, n1


def _quad_in_bed_plane(center: Vec3, n: Vec3, size: float) -> list[Vec3]:
    u, v, _ = _basis_in_plane(n)
    s = size
    o = center
    p00 = _v_add(o, _v_add(_v_scale(-s, u), _v_scale(-s, v)))
    p10 = _v_add(o, _v_add(_v_scale(s, u), _v_scale(-s, v)))
    p11 = _v_add(o, _v_add(_v_scale(s, u), _v_scale(s, v)))
    p01 = _v_add(o, _v_add(_v_scale(-s, u), _v_scale(s, v)))
    return [p00, p10, p11, p01]


def _box_mesh_from_quads(
    bot: list[Vec3],
    top: list[Vec3],
    fill_base: str,
    stroke_base: str,
    fill_top: str,
    stroke_top: str,
    fill_side: str,
    stroke_side: str,
) -> list[dict[str, Any]]:
    faces: list[dict[str, Any]] = []

    def q(
        a: Vec3, b: Vec3, c: Vec3, d: Vec3, ff: str, ss: str, surf: str
    ) -> dict[str, Any]:
        return {"verts": [a, b, c, d], "fill": ff, "stroke": ss, "surface": surf}

    faces.append(q(bot[0], bot[1], bot[2], bot[3], fill_base, stroke_base, "base"))
    faces.append(q(top[3], top[2], top[1], top[0], fill_top, stroke_top, "top"))
    for i in range(4):
        j = (i + 1) % 4
        faces.append(q(bot[i], bot[j], top[j], top[i], fill_side, stroke_side, "side"))
    return faces


def _build_slab_mesh(
    center: Vec3,
    n: Vec3,
    size: float,
    thickness: float,
    fill_cap: str,
    stroke_cap: str,
    fill_side: str,
    stroke_side: str,
) -> list[dict[str, Any]]:
    n1 = _v_unit(n)
    bot = _quad_in_bed_plane(center, n, size)
    off = _v_scale(thickness, n1)
    top = [_v_add(p, off) for p in bot]
    return _box_mesh_from_quads(
        bot, top, fill_cap, stroke_cap, fill_cap, stroke_cap, fill_side, stroke_side
    )


def _build_single_bed_two_slants_mesh(
    center: Vec3,
    n_top: Vec3,
    n_bottom: Vec3,
    size: float,
    plane_sep: float,
    t_dir: Vec3,
    fill_top: str,
    stroke_top: str,
    fill_base: str,
    stroke_base: str,
) -> list[dict[str, Any]]:
    t = _v_unit(t_dir)
    half = plane_sep * 0.5
    cb = _v_sub(center, _v_scale(half, t))
    ct = _v_add(center, _v_scale(half, t))
    bu_v, bv, _ = _basis_in_plane(n_bottom)
    tu_uv, tv, _ = _basis_in_plane(n_top)
    s = size
    bot = [
        _v_add(cb, _v_add(_v_scale(-s, bu_v), _v_scale(-s, bv))),
        _v_add(cb, _v_add(_v_scale(s, bu_v), _v_scale(-s, bv))),
        _v_add(cb, _v_add(_v_scale(s, bu_v), _v_scale(s, bv))),
        _v_add(cb, _v_add(_v_scale(-s, bu_v), _v_scale(s, bv))),
    ]
    top = [
        _v_add(ct, _v_add(_v_scale(-s, tu_uv), _v_scale(-s, tv))),
        _v_add(ct, _v_add(_v_scale(s, tu_uv), _v_scale(-s, tv))),
        _v_add(ct, _v_add(_v_scale(s, tu_uv), _v_scale(s, tv))),
        _v_add(ct, _v_add(_v_scale(-s, tu_uv), _v_scale(s, tv))),
    ]
    fill_side = "rgba(45, 118, 92, 0.16)"
    stroke_side = "rgba(22, 88, 65, 0.92)"
    faces: list[dict[str, Any]] = []

    def qf(
        a: Vec3, b: Vec3, c: Vec3, d: Vec3, ff: str, ss: str, surf: str
    ) -> None:
        faces.append({"verts": [a, b, c, d], "fill": ff, "stroke": ss, "surface": surf})

    qf(bot[0], bot[1], bot[2], bot[3], fill_base, stroke_base, "base")
    qf(top[3], top[2], top[1], top[0], fill_top, stroke_top, "top")
    for i in range(4):
        j = (i + 1) % 4
        qf(bot[i], bot[j], top[j], top[i], fill_side, stroke_side, "side")
    return faces


def _centroid3(verts: list[Vec3]) -> Vec3:
    if not verts:
        return (0.0, 0.0, 0.0)
    sx = sy = sz = 0.0
    for v in verts:
        sx += v[0]
        sy += v[1]
        sz += v[2]
    n = len(verts)
    return (sx / n, sy / n, sz / n)


def _build_wedging_bed_mesh(
    ud1: Vec3,
    ud2: Vec3,
    ndp_hint: Vec3 | None,
    char_len: float,
    slab_thick: float,
    fill_top: str,
    stroke_top: str,
    fill_base: str,
    stroke_base: str,
) -> list[dict[str, Any]]:
    u1 = _v_unit(ud1)
    u2 = _v_unit(ud2)
    h_raw = ndp_hint if ndp_hint and _v_norm(ndp_hint) > 1e-10 else _v_cross(u1, u2)
    if _v_norm(h_raw) < 1e-8:
        s = _v_add(u1, u2)
        td = _v_unit(u1) if _v_norm(s) < 1e-10 else _v_unit(s)
        return _build_single_bed_two_slants_mesh(
            (0.0, 0.0, 0.0),
            u1,
            u2,
            max(float(char_len), 1.0) * 0.72,
            slab_thick * 1.05,
            td,
            fill_top,
            stroke_top,
            fill_base,
            stroke_base,
        )
    h = _v_unit(h_raw)
    ll = max(float(char_len), 1e-6)
    hinge_len = ll * 0.96
    radial = ll * 0.74
    e_top = _v_unit(_v_cross(h, u1))
    e_base = _v_unit(_v_cross(h, u2))
    v0 = _v_scale(-hinge_len * 0.5, h)
    v1 = _v_scale(hinge_len * 0.5, h)
    v2 = _v_add(v0, _v_scale(radial, e_top))
    v3 = _v_add(v0, _v_scale(radial, e_base))
    ctr = _centroid3([v0, v1, v2, v3])
    shift = (-ctr[0], -ctr[1], -ctr[2])
    v0 = _v_add(v0, shift)
    v1 = _v_add(v1, shift)
    v2 = _v_add(v2, shift)
    v3 = _v_add(v3, shift)
    fill_side = "rgba(40, 120, 95, 0.14)"
    stroke_side = "rgba(22, 88, 66, 0.9)"
    fill_end = "rgba(38, 115, 88, 0.16)"
    stroke_end = "rgba(24, 82, 62, 0.9)"

    def tri(a: Vec3, b: Vec3, c: Vec3, ff: str, ss: str, surf: str) -> dict[str, Any]:
        return {"verts": [a, b, c], "fill": ff, "stroke": ss, "surface": surf}

    return [
        tri(v0, v1, v2, fill_top, stroke_top, "top"),
        tri(v0, v1, v3, fill_base, stroke_base, "base"),
        tri(v0, v2, v3, fill_side, stroke_side, "side"),
        tri(v1, v2, v3, fill_end, stroke_end, "end"),
    ]


def _build_fold_mesh(
    ud_a: Vec3,
    ud_b: Vec3,
    size: float,
    thick: float,
    fill_a: str,
    stroke_a: str,
    fill_b: str,
    stroke_b: str,
) -> list[dict[str, Any]]:
    n1 = _v_unit(ud_a)
    n2 = _v_unit(ud_b)
    bis_u = _v_unit(_v_add(n1, n2))
    spread = (0.0, 0.0, 0.0)
    if _v_norm(_v_add(n1, n2)) >= 1e-5:
        spread = _v_scale(size * 0.07, bis_u)
    s = size * 0.86
    t = thick * 0.88
    fill_side_a = "rgba(28, 135, 85, 0.14)"
    fill_side_b = "rgba(40, 125, 195, 0.14)"
    out: list[dict[str, Any]] = []
    out.extend(
        _build_slab_mesh(
            _v_scale(-0.5, spread), n1, s, t, fill_a, stroke_a, fill_side_a, stroke_a
        )
    )
    out.extend(
        _build_slab_mesh(
            _v_scale(0.5, spread), n2, s, t, fill_b, stroke_b, fill_side_b, stroke_b
        )
    )
    return out


def _slerp_dir_unit(a: Vec3, b: Vec3, t: float) -> Vec3:
    u = _v_unit(a)
    vv = _v_unit(b)
    d = max(-1.0, min(1.0, _v_dot(u, vv)))
    om = math.acos(d)
    if om < 1e-7:
        return u
    so = math.sin(om)
    return _v_unit(
        _v_add(
            _v_scale(math.sin((1.0 - t) * om) / so, u),
            _v_scale(math.sin(t * om) / so, vv),
        )
    )


def _rotate_around_axis(v: Vec3, axis_unit: Vec3, angle_rad: float) -> Vec3:
    k = _v_unit(axis_unit)
    cos = math.cos(angle_rad)
    sin = math.sin(angle_rad)
    kxv = _v_cross(k, v)
    kdv = _v_dot(k, v)
    return _v_add(
        _v_add(_v_scale(cos, v), _v_scale(sin, kxv)),
        _v_scale((1.0 - cos) * kdv, k),
    )


def _build_semi_arch_fold_mesh(
    ud_a: Vec3,
    ud_b: Vec3,
    hinge_hint: Vec3 | None,
    char_len: float,
    slab_thick: float,
    fill_out: str,
    stroke_out: str,
    fill_in: str,
    stroke_in: str,
) -> list[dict[str, Any]]:
    u1 = _v_unit(ud_a)
    u2 = _v_unit(ud_b)
    if hinge_hint and _v_norm(hinge_hint) > 1e-10:
        h_raw = hinge_hint
    else:
        h_raw = _v_cross(u1, u2)
    if _v_norm(h_raw) < 1e-6:
        return _build_fold_mesh(
            ud_a,
            ud_b,
            max(char_len * 0.85, 1.0),
            slab_thick,
            fill_out,
            stroke_out,
            fill_in,
            stroke_in,
        )
    h = _v_unit(h_raw)
    ll = max(float(char_len), 1e-6)
    eta_true = math.acos(max(-1.0, min(1.0, _v_dot(u1, u2))))
    eta_min_vis = (28.0 * math.pi) / 180.0
    eta_arc = max(eta_true, eta_min_vis)
    u_end = u2 if eta_true >= eta_min_vis else _v_unit(_rotate_around_axis(u1, h, eta_arc))

    rr = ll * 0.88
    dr = max(ll * 0.14, slab_thick * 1.45)
    hw = ll * 0.34
    n_arc = 22
    hm = _v_scale(-hw, h)
    hp = _v_scale(hw, h)
    fill_cap = "rgba(34, 130, 100, 0.18)"
    stroke_cap = "rgba(18, 95, 72, 0.9)"

    def quad_faces(
        aa: Vec3, bb: Vec3, cc: Vec3, dd: Vec3, ff: str, ss: str, surf: str
    ) -> dict[str, Any]:
        return {"verts": [aa, bb, cc, dd], "fill": ff, "stroke": ss, "surface": surf}

    faces: list[dict[str, Any]] = []
    for k in range(n_arc):
        t0 = k / n_arc
        t1 = (k + 1) / n_arc
        d0 = _slerp_dir_unit(u1, u_end, t0)
        d1 = _slerp_dir_unit(u1, u_end, t1)
        o0 = _v_scale(rr, d0)
        o1 = _v_scale(rr, d1)
        i0 = _v_scale(rr - dr, d0)
        i1 = _v_scale(rr - dr, d1)
        o0m, o0p = _v_add(o0, hm), _v_add(o0, hp)
        o1m, o1p = _v_add(o1, hm), _v_add(o1, hp)
        i0m, i0p = _v_add(i0, hm), _v_add(i0, hp)
        i1m, i1p = _v_add(i1, hm), _v_add(i1, hp)
        faces.append(quad_faces(o0m, o0p, o1p, o1m, fill_out, stroke_out, "top"))
        faces.append(quad_faces(i0m, i1m, i1p, i0p, fill_in, stroke_in, "base"))

    d_s = _slerp_dir_unit(u1, u_end, 0)
    d_e = _slerp_dir_unit(u1, u_end, 1)
    o_s, o_e = _v_scale(rr, d_s), _v_scale(rr, d_e)
    i_s, i_e = _v_scale(rr - dr, d_s), _v_scale(rr - dr, d_e)
    faces.append(
        quad_faces(
            _v_add(i_s, hm),
            _v_add(i_s, hp),
            _v_add(o_s, hp),
            _v_add(o_s, hm),
            fill_cap,
            stroke_cap,
            "cap",
        )
    )
    faces.append(
        quad_faces(
            _v_add(i_e, hm),
            _v_add(o_e, hm),
            _v_add(o_e, hp),
            _v_add(i_e, hp),
            fill_cap,
            stroke_cap,
            "cap",
        )
    )
    return faces


def _make_camera_basis(yaw: float, pitch: float) -> tuple[Vec3, Vec3, Vec3]:
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    right = (cy, sy, 0.0)
    up = (-sy * sp, cy * sp, -cp)
    forward = (-sy * cp, cy * cp, sp)
    return right, up, forward


def project_cam_point(p: Vec3, yaw: float, pitch: float) -> tuple[float, float]:
    right, up, _f = _make_camera_basis(yaw, pitch)
    return (_v_dot(p, right), _v_dot(p, up))


def face_depth_for_sort(f: dict[str, Any], yaw: float, pitch: float) -> float:
    _r, _u, forward = _make_camera_basis(yaw, pitch)
    c = _centroid3(list(f["verts"]))
    return _v_dot(c, forward)


def segment_depth_for_sort(a: Vec3, b: Vec3, yaw: float, pitch: float) -> float:
    """Camera-depth key for a short 3D segment (midpoint · forward), for painter-style sorting with faces."""
    _r, _u, forward = _make_camera_basis(yaw, pitch)
    mid = (
        (a[0] + b[0]) * 0.5,
        (a[1] + b[1]) * 0.5,
        (a[2] + b[2]) * 0.5,
    )
    return _v_dot(mid, forward)


@dataclass
class SchematicScene:
    borehole_end: Vec3
    t_end: Vec3
    axes_ex: Vec3
    axes_ey: Vec3
    axes_ez: Vec3
    plane_size: float
    mesh_faces: list[dict[str, Any]]
    volume_kind: str
    wedge_footnote: str | None
    model_id: str


def collect_scene(model_id: str, res: dict[str, Any], m_len: float, t_val: float) -> SchematicScene | None:
    ub = _v_from(res["ub_vector"])
    ud1 = _v_from(res["ud1_vector"])

    t_dir: Vec3
    if model_id == "t1":
        t_dir = _v_unit(ud1)
    elif model_id in ("t2", "t4"):
        t_dir = _v_unit(_v_from(res["uav_vector"]))
    elif model_id == "t3":
        u1 = _v_from(res["ud1_vector"])
        u2 = _v_from(res["ud2_vector"])
        s = _v_add(u1, u2)
        t_dir = _v_unit(u1) if _v_norm(s) < 1e-10 else _v_unit(s)
    elif model_id == "t5":
        t_dir = _v_unit(ud1)
    elif model_id in ("t6", "t7"):
        t_dir = _v_unit(ud1)
    elif model_id == "t8":
        ua = _v_from(res["ud1_vector"])
        ub2 = _v_from(res["ud2_vector"])
        s = _v_add(ua, ub2)
        t_dir = _v_unit(ua) if _v_norm(s) < 1e-10 else _v_unit(s)
    else:
        return None

    borehole_end = _v_scale(m_len, _v_unit(ub))
    t_end = _v_scale(t_val, t_dir)
    ll = max(m_len, t_val, 1.0)
    axis_len = ll * 0.38
    axes_ex = (axis_len, 0.0, 0.0)
    axes_ey = (0.0, axis_len, 0.0)
    axes_ez = (0.0, 0.0, axis_len)
    plane_size = ll * 0.52
    slab_thick = ll * 0.14

    fill_top = "rgba(26, 158, 68, 0.44)"
    stroke_top = "rgba(12, 92, 38, 0.95)"
    fill_base = "rgba(48, 124, 232, 0.42)"
    stroke_base = "rgba(18, 72, 168, 0.95)"
    fill_t1_side = "rgba(34, 145, 82, 0.14)"
    stroke_t1_side = "rgba(16, 88, 48, 0.9)"

    mesh: list[dict[str, Any]] = []
    vol = ""

    if model_id == "t1":
        vol = "Slanted slab"
        mesh = _build_slab_mesh(
            (0.0, 0.0, 0.0),
            ud1,
            plane_size,
            slab_thick,
            fill_top,
            stroke_top,
            fill_t1_side,
            stroke_t1_side,
        )
    elif model_id in ("t2", "t3", "t4"):
        vol = "Single bed (top / base dips)"
        u1 = _v_from(res["ud1_vector"])
        u2 = _v_from(res["ud2_vector"])
        mesh = _build_single_bed_two_slants_mesh(
            (0.0, 0.0, 0.0),
            u1,
            u2,
            plane_size * 0.72,
            slab_thick * 1.05,
            t_dir,
            fill_top,
            stroke_top,
            fill_base,
            stroke_base,
        )
    elif model_id == "t5":
        vol = "Semi-arch (concentric fold)"
        u1 = _v_from(res["ud1_vector"])
        u2 = _v_from(res["ud2_prime_vector"])
        hint = _v_from(res["ndc_vector"]) if res.get("ndc_vector") is not None else None
        mesh = _build_semi_arch_fold_mesh(u1, u2, hint, ll, slab_thick, fill_top, stroke_top, fill_base, stroke_base)
    elif model_id == "t6":
        vol = "Semi-arch (plunging fold)"
        u1 = _v_from(res["ud1_vector"])
        u2 = _v_from(res["ud2_vector"])
        hint = _v_from(res["ndp_vector"]) if res.get("ndp_vector") is not None else None
        mesh = _build_semi_arch_fold_mesh(u1, u2, hint, ll, slab_thick, fill_top, stroke_top, fill_base, stroke_base)
    elif model_id == "t7":
        vol = "Wedging bed (top-normal, Fig. 6a)"
        u1 = _v_from(res["ud1_vector"])
        u2 = _v_from(res["ud2_vector"])
        hint = _v_from(res["ndp_vector"]) if res.get("ndp_vector") is not None else None
        mesh = _build_wedging_bed_mesh(u1, u2, hint, ll, slab_thick, fill_top, stroke_top, fill_base, stroke_base)
    elif model_id == "t8":
        vol = "Wedging bed (equal-angle, Fig. 6b)"
        u1 = _v_from(res["ud1_vector"])
        u2 = _v_from(res["ud2_vector"])
        hint = _v_from(res["ndp_vector"]) if res.get("ndp_vector") is not None else None
        mesh = _build_wedging_bed_mesh(u1, u2, hint, ll, slab_thick, fill_top, stroke_top, fill_base, stroke_base)
    else:
        return None

    foot = "T8 = T7 cos(η/2); η = angle between U_d1 and U_d2." if model_id == "t8" else None
    return SchematicScene(
        borehole_end=borehole_end,
        t_end=t_end,
        axes_ex=axes_ex,
        axes_ey=axes_ey,
        axes_ez=axes_ez,
        plane_size=plane_size,
        mesh_faces=mesh,
        volume_kind=vol,
        wedge_footnote=foot,
        model_id=model_id,
    )


def axis_origin_xyz(plane_size: float) -> Vec3:
    lref = plane_size
    return (lref * 2.02, -lref * 1.09, lref * 0.13)
