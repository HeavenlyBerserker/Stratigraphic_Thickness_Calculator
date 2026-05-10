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
    """
    Tetrahedral wedge; +z = down so the **shallower** bedding (smaller ``z`` centroid) is stratigraphic
    ``top`` (blue ``fill_base``); the deeper is ``base`` (green ``fill_top``).
    """
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

    # +z = down: shallower (smaller z centroid) = stratigraphic **top** bed. Tag that face ``"top"``
    # and use blue ``fill_base``; the deeper bed is ``"base"`` with green ``fill_top`` (matches JS).
    z_a = _centroid3([v0, v1, v2])[2]
    z_b = _centroid3([v0, v1, v3])[2]
    if z_a <= z_b:
        shallow_a, shallow_b, shallow_c = v0, v1, v2
        deep_a, deep_b, deep_c = v0, v1, v3
    else:
        shallow_a, shallow_b, shallow_c = v0, v1, v3
        deep_a, deep_b, deep_c = v0, v1, v2
    return [
        tri(shallow_a, shallow_b, shallow_c, fill_base, stroke_base, "top"),
        tri(deep_a, deep_b, deep_c, fill_top, stroke_top, "base"),
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
    # Mesh tags: outer annulus (o*) → "top", inner (i*) → "base". Paper Fig. 5: inner = strat. top bed.
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


def mesh_axis_aligned_bounds(
    mesh_faces: list[dict[str, Any]], origin: Vec3 | None = None
) -> tuple[Vec3, Vec3]:
    lo = [float("inf"), float("inf"), float("inf")]
    hi = [-float("inf"), -float("inf"), -float("inf")]
    for f in mesh_faces:
        for v in f["verts"]:
            for i in range(3):
                x = float(v[i])
                lo[i] = min(lo[i], x)
                hi[i] = max(hi[i], x)
    if origin is not None:
        for i in range(3):
            lo[i] = min(lo[i], float(origin[i]))
            hi[i] = max(hi[i], float(origin[i]))
    return (tuple(lo), tuple(hi))


def mesh_aabb_center(mesh_faces: list[dict[str, Any]]) -> Vec3:
    """Midpoint of the axis-aligned bounds of ``mesh_faces`` (volume center for schematic framing)."""
    lo, hi = mesh_axis_aligned_bounds(mesh_faces, origin=None)
    return (
        0.5 * (lo[0] + hi[0]),
        0.5 * (lo[1] + hi[1]),
        0.5 * (lo[2] + hi[2]),
    )


def translate_mesh_faces(mesh_faces: list[dict[str, Any]], delta: Vec3) -> list[dict[str, Any]]:
    """Copy mesh with each vertex shifted by ``delta`` (e.g. ``delta = -center`` to center the volume at origin)."""
    out: list[dict[str, Any]] = []
    for f in mesh_faces:
        nf = dict(f)
        nf["verts"] = [_v_add(_v_from(v), delta) for v in f["verts"]]
        out.append(nf)
    return out


def _ray_aabb_interval(o: Vec3, u: Vec3, lo: Vec3, hi: Vec3) -> tuple[float, float] | None:
    """Infinite ray p(t)=o+t*u (any t) vs axis-aligned box. Returns (t_near, t_far) or None if miss."""
    t_near = -float("inf")
    t_far = float("inf")
    for i in range(3):
        if abs(u[i]) < 1e-14:
            if o[i] < lo[i] - 1e-9 or o[i] > hi[i] + 1e-9:
                return None
            continue
        inv = 1.0 / u[i]
        t1 = (lo[i] - o[i]) * inv
        t2 = (hi[i] - o[i]) * inv
        if t1 > t2:
            t1, t2 = t2, t1
        t_near = max(t_near, t1)
        t_far = min(t_far, t2)
        if t_near > t_far + 1e-12:
            return None
    return (t_near, t_far)


def _plane_nd_from_face(face: dict[str, Any]) -> tuple[Vec3, float]:
    """Unit normal ``n`` and scalar ``d`` with ``n·x = d`` for the plane of the first three vertices."""
    verts = [_v_from(v) for v in face["verts"]]
    if len(verts) < 3:
        return (0.0, 0.0, 1.0), 0.0
    v0, v1, v2 = verts[0], verts[1], verts[2]
    n_raw = _v_cross(_v_sub(v1, v0), _v_sub(v2, v0))
    nn = _v_norm(n_raw)
    if nn < 1e-14 and len(verts) >= 4:
        v3 = verts[3]
        n_raw = _v_cross(_v_sub(v2, v0), _v_sub(v3, v0))
        nn = _v_norm(n_raw)
    if nn < 1e-14:
        return (0.0, 0.0, 1.0), 0.0
    n = (n_raw[0] / nn, n_raw[1] / nn, n_raw[2] / nn)
    d = _v_dot(n, v0)
    return n, d


def _ray_plane_parameter(o: Vec3, u: Vec3, face: dict[str, Any]) -> float | None:
    """Scalar ``t`` with ``o + t*u`` on the plane of ``face``; ``None`` if ray ∥ plane."""
    n_b, d_b = _plane_nd_from_face(face)
    denom = _v_dot(n_b, u)
    if abs(denom) < 1e-12:
        return None
    return (d_b - _v_dot(n_b, o)) / denom


def _closest_point_on_segment_to_point(p: Vec3, a: Vec3, b: Vec3) -> Vec3:
    ab = _v_sub(b, a)
    denom = _v_dot(ab, ab)
    t = 0.0 if denom < 1e-20 else _v_dot(_v_sub(p, a), ab) / denom
    t = max(0.0, min(1.0, t))
    return _v_add(a, _v_scale(t, ab))


def _project_point_to_triangle_plane(a: Vec3, b: Vec3, c: Vec3, p: Vec3) -> Vec3:
    n_raw = _v_cross(_v_sub(b, a), _v_sub(c, a))
    nn = _v_norm(n_raw)
    if nn < 1e-14:
        return a
    nu = _v_scale(1.0 / nn, n_raw)
    return _v_sub(p, _v_scale(_v_dot(_v_sub(p, a), nu), nu))


def _point_in_triangle_barycentric(a: Vec3, b: Vec3, c: Vec3, p: Vec3, eps: float = 1e-6) -> bool:
    v0 = _v_sub(b, a)
    v1 = _v_sub(c, a)
    v2 = _v_sub(p, a)
    d00 = _v_dot(v0, v0)
    d01 = _v_dot(v0, v1)
    d11 = _v_dot(v1, v1)
    d20 = _v_dot(v2, v0)
    d21 = _v_dot(v2, v1)
    denom = d00 * d11 - d01 * d01
    if abs(denom) < 1e-22:
        return False
    v = (d11 * d20 - d01 * d21) / denom
    w = (d00 * d21 - d01 * d20) / denom
    u = 1.0 - v - w
    return u >= -eps and v >= -eps and w >= -eps


def _closest_point_on_triangle_3d(a: Vec3, b: Vec3, c: Vec3, p: Vec3) -> Vec3:
    """Closest point on closed triangle ``ABC`` to point ``P`` (3D)."""
    p0 = _project_point_to_triangle_plane(a, b, c, p)
    if _point_in_triangle_barycentric(a, b, c, p0, eps=1e-5):
        return p0
    c_ab = _closest_point_on_segment_to_point(p, a, b)
    c_bc = _closest_point_on_segment_to_point(p, b, c)
    c_ca = _closest_point_on_segment_to_point(p, c, a)

    def d2(x: Vec3) -> float:
        d = _v_sub(p, x)
        return _v_dot(d, d)

    d_ab = d2(c_ab)
    d_bc = d2(c_bc)
    d_ca = d2(c_ca)
    if d_ab <= d_bc and d_ab <= d_ca:
        return c_ab
    if d_bc <= d_ca:
        return c_bc
    return c_ca


def _wedge_anchor_top_pierce(
    mesh_faces: list[dict[str, Any]], o_ray: Vec3, ub_vec: Vec3
) -> Vec3 | None:
    """
    T7/T8 wedge: pierce point of the borehole line through the stratigraphic **top** bedding Δ.

    ``collect_scene`` then translates the mesh by ``o_ray - q_top`` so this pierce lies on
    ``borehole_ray_o`` without moving ``o_ray`` / M / T endpoints (see wedge block in ``collect_scene``).
    """
    top_face: dict[str, Any] | None = None
    for f in mesh_faces:
        if str(f.get("surface", "")) == "top" and len(f.get("verts", ())) >= 3:
            top_face = f
            break
    if top_face is None:
        return None
    verts = [_v_from(v) for v in top_face["verts"]]
    if len(verts) < 3:
        return None
    ub_u = _v_unit(ub_vec)
    t_hit = _ray_plane_parameter(o_ray, ub_u, top_face)
    if t_hit is None:
        return None
    q_line = _v_add(o_ray, _v_scale(t_hit, ub_u))
    if len(verts) == 3:
        return _closest_point_on_triangle_3d(verts[0], verts[1], verts[2], q_line)
    # Planar quad (degenerate wedge → two-slants mesh): snap to nearer triangle.
    q1 = _closest_point_on_triangle_3d(verts[0], verts[1], verts[2], q_line)
    q2 = _closest_point_on_triangle_3d(verts[0], verts[2], verts[3], q_line)
    d1 = _v_norm(_v_sub(q_line, q1))
    d2 = _v_norm(_v_sub(q_line, q2))
    return q1 if d1 <= d2 else q2


def _face_centroid_vec(face: dict[str, Any]) -> Vec3:
    return _centroid3([_v_from(v) for v in face.get("verts", ())])


def _wedge_mt_segment_tri_beds(
    o: Vec3,
    target: Vec3,
    top_face: dict[str, Any],
    base_face: dict[str, Any],
    past_each_end: float,
    model_id: str | None = None,
) -> tuple[Vec3, Vec3] | None:
    """
    Wedging tetrahedron (tri ``top`` + tri ``base``): stubs along **o → target**.

    The **deeper** bedding face (+z = down ⇒ larger centroid ``z``) is treated as the wedge
    **bottom** for the long stub (``½`` × max longest edge of the two bed triangles). The
    shallower face gets the short stub (``past_each_end * L_in``). Mesh tags ``top``/``base``
    are not used for stub direction — only for plane equations and edge length.
    """
    d_vec = _v_sub(target, o)
    full = _v_norm(d_vec)
    if full < 1e-12:
        return None
    u = _v_unit(d_vec)
    t_top = _ray_plane_parameter(o, u, top_face)
    t_base = _ray_plane_parameter(o, u, base_face)
    if t_top is None or t_base is None:
        return None
    if abs(t_top - t_base) < 1e-12 * max(1.0, full):
        return None
    c_top = _face_centroid_vec(top_face)
    c_base = _face_centroid_vec(base_face)
    # Deeper = larger z (down is +z in this app).
    if c_base[2] >= c_top[2]:
        shallow_face, bottom_face = top_face, base_face
        t_shallow, t_bottom = t_top, t_base
    else:
        shallow_face, bottom_face = base_face, top_face
        t_shallow, t_bottom = t_base, t_top
    t_enter = min(t_shallow, t_bottom)
    t_exit = max(t_shallow, t_bottom)
    l_in = t_exit - t_enter
    if l_in < 1e-12 * max(1.0, full):
        return None
    ext_short = past_each_end * l_in
    le_s = _face_longest_edge_length(shallow_face)
    le_b = _face_longest_edge_length(bottom_face)
    ext_long = 0.5 * max(le_s, le_b)
    if ext_long < 1e-12 * max(1.0, full):
        ext_long = _mt_stub_bottom_frac(model_id) * l_in
    eps = 1e-9 * max(1.0, full)
    bottom_is_exit = t_bottom > t_shallow + eps
    if bottom_is_exit:
        t_lo = max(0.0, t_enter - ext_short)
        t_hi = t_exit + ext_long
    else:
        t_lo = t_enter - ext_long
        t_hi = t_exit + ext_short
    if t_lo > t_hi:
        t_lo, t_hi = t_hi, t_lo
    # Include ray origin ``o`` (wedge top pierce for T7/T8); ``max(0, …)`` can otherwise omit it.
    t_lo = min(t_lo, 0.0)
    t_hi = max(t_hi, 0.0)
    if t_lo > t_hi:
        t_lo, t_hi = t_hi, t_lo
    return (_v_add(o, _v_scale(t_lo, u)), _v_add(o, _v_scale(t_hi, u)))


def _face_longest_edge_length(face: dict[str, Any]) -> float:
    """Longest polygon edge (triangle: max of three sides; n>3: cycle edges only, no diagonals)."""
    verts = [_v_from(v) for v in face.get("verts", ())]
    n = len(verts)
    if n < 2:
        return 0.0
    if n == 3:
        best = 0.0
        for i in range(3):
            for j in range(i + 1, 3):
                best = max(best, _v_norm(_v_sub(verts[i], verts[j])))
        return best
    best = 0.0
    for i in range(n):
        j = (i + 1) % n
        best = max(best, _v_norm(_v_sub(verts[i], verts[j])))
    return best


def _face_polygon_area(face: dict[str, Any]) -> float:
    """Triangle or quad area (quad split by v0,v2 diagonal)."""
    verts = [_v_from(v) for v in face["verts"]]
    if len(verts) < 3:
        return 0.0
    v0, v1, v2 = verts[0], verts[1], verts[2]
    if len(verts) == 3:
        return 0.5 * _v_norm(_v_cross(_v_sub(v1, v0), _v_sub(v2, v0)))
    v3 = verts[3]
    a1 = 0.5 * _v_norm(_v_cross(_v_sub(v1, v0), _v_sub(v2, v0)))
    a2 = 0.5 * _v_norm(_v_cross(_v_sub(v2, v0), _v_sub(v3, v0)))
    return a1 + a2


# M/T schematic ray stubs past bedding (+z down: shallower z = top). Top stub uses ``past_each_end``;
# past the bottom contact the stub is longer (fraction of ``L_in``). T1–T4 use 3× ``L_in`` past-bottom stub.
_MT_STUB_BOTTOM_FRAC = 1.0


def _mt_stub_bottom_frac(model_id: str | None) -> float:
    return 3.0 if model_id in ("t1", "t2", "t3", "t4") else _MT_STUB_BOTTOM_FRAC


def mt_display_single_bed_t234(
    mesh_faces: list[dict[str, Any]],
    o: Vec3,
    target: Vec3,
    *,
    past_each_end: float = 0.25,
    model_id: str | None = None,
) -> tuple[Vec3, Vec3]:
    """
    Slab, single bed, semi-arch fold (T1–T6), or wedging tetrahedron (T7–T8): draw M/T along
    ``unit(target - o)`` through a bedding anchor, with chord ``L_in`` to an opposite cap plane,
    then asymmetric stubs: ``past_each_end * L_in`` before the anchor (top side of the chord) and
    a longer stub past the opposite cap along ``u`` (``_MT_STUB_BOTTOM_FRAC * L_in``, except wedges
    below).

    **Wedge (Fig. 6):** tri ``"top"`` + tri ``"base"`` — borehole ray vs both planes; long stub past
    the **deeper** bed (larger centroid ``z``, +z = down), ``½`` × max longest edge of the two bed
    triangles; short stub on the shallower side. (min/max over ``end``/``cap`` mis-orders
    non-wedge tetrahedra). **T5–T6 (semi-arch / twin slab, Xu et al. Fig. 5):** mesh ``"base"`` is the **inner**
    limb (stratigraphic **top** bed); mesh ``"top"`` is the **outer** limb (stratigraphic bottom).
    Anchor with area-weighted centering on **inner** ``"base"`` faces, chord to the **deepest**
    **outer** ``"top"`` plane, or along ``u`` to that outer patch centroid if ``u`` is nearly parallel
    (same anchor for M and T).
    **Other models:** shallowest centroid among ``top`` / ``base`` / ``cap`` / ``end`` (omitting
    ``side``), chord to the deepest such plane.
    """

    def _segment_from_anchor_plane(
        c_anchor: Vec3, plane_face: dict[str, Any]
    ) -> tuple[Vec3, Vec3] | None:
        n_b, d_b = _plane_nd_from_face(plane_face)
        d_vec = _v_sub(target, o)
        full = _v_norm(d_vec)
        if full < 1e-12:
            return o, target
        u = _v_unit(d_vec)
        denom = _v_dot(n_b, u)
        if abs(denom) < 1e-12:
            return None
        s_b = (d_b - _v_dot(n_b, c_anchor)) / denom
        if s_b < 0:
            u = _v_scale(-1.0, u)
            s_b = -s_b
        l_in = abs(s_b)
        if l_in < 1e-12:
            l_in = max(1e-9 * max(full, 1.0), full * 0.35)
        ext_top = past_each_end * l_in
        ext_bot = _mt_stub_bottom_frac(model_id) * l_in
        s_lo = -ext_top
        s_hi = s_b + ext_bot
        p_lo = _v_add(c_anchor, _v_scale(s_lo, u))
        p_hi = _v_add(c_anchor, _v_scale(s_hi, u))
        return p_lo, p_hi

    def _t56_segment_along_u_to_far_centroid(
        c_anchor: Vec3, c_far: Vec3
    ) -> tuple[Vec3, Vec3]:
        """When ray vs the opposite-bedding plane is degenerate, span along ``u`` to ``c_far``."""
        d_vec = _v_sub(target, o)
        full = _v_norm(d_vec)
        if full < 1e-12:
            return o, target
        u = _v_unit(d_vec)
        s_b = _v_dot(_v_sub(c_far, c_anchor), u)
        if s_b < 0:
            u = _v_scale(-1.0, u)
            s_b = -s_b
        l_in = max(abs(s_b), 1e-9 * max(full, 1.0))
        ext_top = past_each_end * l_in
        ext_bot = _mt_stub_bottom_frac(model_id) * l_in
        s_lo = -ext_top
        s_hi = s_b + ext_bot
        return (
            _v_add(c_anchor, _v_scale(s_lo, u)),
            _v_add(c_anchor, _v_scale(s_hi, u)),
        )

    top_tris = [
        f
        for f in mesh_faces
        if str(f.get("surface", "")) == "top" and len(f.get("verts", ())) == 3
    ]
    base_tris = [
        f
        for f in mesh_faces
        if str(f.get("surface", "")) == "base" and len(f.get("verts", ())) == 3
    ]
    if len(top_tris) == 1 and len(base_tris) == 1:
        seg_w = _wedge_mt_segment_tri_beds(o, target, top_tris[0], base_tris[0], past_each_end, model_id)
        if seg_w is not None:
            return seg_w
        c_top = _centroid3([_v_from(v) for v in top_tris[0]["verts"]])
        seg = _segment_from_anchor_plane(c_top, base_tris[0])
        if seg is not None:
            return seg

    if model_id in ("t5", "t6"):
        # Mesh tags: "top" = outer limb, "base" = inner limb (paper: inner = stratigraphic top bed).
        outer_fs = [f for f in mesh_faces if str(f.get("surface", "")) == "top"]
        inner_fs = [f for f in mesh_faces if str(f.get("surface", "")) == "base"]
        if outer_fs and inner_fs:
            tw = 0.0
            sx = sy = sz = 0.0
            entries: list[tuple[Vec3, float]] = []
            for f in inner_fs:
                ar = _face_polygon_area(f)
                c = _centroid3([_v_from(v) for v in f["verts"]])
                entries.append((c, ar))
                tw += ar
                sx += ar * c[0]
                sy += ar * c[1]
                sz += ar * c[2]
            if tw < 1e-20:
                nf = float(len(entries))
                c_seed = (
                    sum(e[0][0] for e in entries) / nf,
                    sum(e[0][1] for e in entries) / nf,
                    sum(e[0][2] for e in entries) / nf,
                )
            else:
                c_seed = (sx / tw, sy / tw, sz / tw)

            def _d2_to_seed(ff: dict[str, Any]) -> float:
                c = _centroid3([_v_from(v) for v in ff["verts"]])
                d = _v_sub(c, c_seed)
                return _v_dot(d, d)

            anchor_inner = min(inner_fs, key=_d2_to_seed)
            c_anchor = _centroid3([_v_from(v) for v in anchor_inner["verts"]])
            deepest_outer = max(
                outer_fs,
                key=lambda ff: _centroid3([_v_from(v) for v in ff["verts"]])[2],
            )
            seg = _segment_from_anchor_plane(c_anchor, deepest_outer)
            if seg is not None:
                return seg
            c_outer_ctr = _centroid3([_v_from(v) for v in deepest_outer["verts"]])
            return _t56_segment_along_u_to_far_centroid(c_anchor, c_outer_ctr)

    cap_surf = frozenset({"top", "base", "cap", "end"})
    cap_faces = [f for f in mesh_faces if str(f.get("surface", "")) in cap_surf]
    if len(cap_faces) < 2:
        return mt_display_endpoints(o, target, mesh_faces, past_each_end=past_each_end, model_id=model_id)
    best_min: tuple[dict[str, Any], Vec3, float] | None = None
    best_max: tuple[dict[str, Any], Vec3, float] | None = None
    for f in cap_faces:
        c = _centroid3([_v_from(v) for v in f["verts"]])
        z = c[2]
        if best_min is None or z < best_min[2]:
            best_min = (f, c, z)
        if best_max is None or z > best_max[2]:
            best_max = (f, c, z)
    if best_min is None or best_max is None:
        return mt_display_endpoints(o, target, mesh_faces, past_each_end=past_each_end, model_id=model_id)
    z_span = best_max[2] - best_min[2]
    if z_span < 1e-9 * max(1.0, abs(best_min[2]), abs(best_max[2])):
        return mt_display_endpoints(o, target, mesh_faces, past_each_end=past_each_end, model_id=model_id)
    if best_min[0] is best_max[0]:
        return mt_display_endpoints(o, target, mesh_faces, past_each_end=past_each_end, model_id=model_id)
    c_anchor = best_min[1]
    seg = _segment_from_anchor_plane(c_anchor, best_max[0])
    if seg is not None:
        return seg
    return mt_display_endpoints(o, target, mesh_faces, past_each_end=past_each_end, model_id=model_id)


def mt_display_endpoints(
    o: Vec3,
    target: Vec3,
    mesh_faces: list[dict[str, Any]],
    *,
    past_each_end: float = 0.25,
    model_id: str | None = None,
) -> tuple[Vec3, Vec3]:
    """
    Clip M/T for schematic: ray ∩ mesh AABB gives in-volume length ``L_in``.
    With +z = down, the shallower contact is the **top bed**; the deeper is **bottom**.
    Draw from ``(top along ray) - past_each_end * L_in`` to ``(bottom along ray) + stub_frac * L_in``,
    clamped to the segment O→target (``stub_frac`` is 3 for T1–T4, else ``_MT_STUB_BOTTOM_FRAC``).
    """
    d = _v_sub(target, o)
    full = _v_norm(d)
    if full < 1e-12:
        return o, target
    u = _v_unit(d)
    lo, hi = mesh_axis_aligned_bounds(mesh_faces, origin=o)
    slab = _ray_aabb_interval(o, u, lo, hi)
    if slab is None:
        s_a, s_b = 0.25 * full, 0.75 * full
    else:
        t_near, t_far = slab
        s_entry = max(0.0, min(full, t_near))
        s_exit = max(0.0, min(full, t_far))
        if s_exit <= s_entry + 1e-9 * max(full, 1.0):
            s_a, s_b = 0.25 * full, 0.75 * full
        else:
            s_a, s_b = s_entry, s_exit
    l_in = s_b - s_a
    if l_in < 1e-9 * max(full, 1.0):
        s_a, s_b = 0.25 * full, 0.75 * full
        l_in = s_b - s_a
    p_a = _v_add(o, _v_scale(s_a, u))
    p_b = _v_add(o, _v_scale(s_b, u))
    # z increases downward; smaller z = stratigraphically higher (top bed).
    if p_a[2] <= p_b[2]:
        s_top, s_bot = s_a, s_b
    else:
        s_top, s_bot = s_b, s_a
    ext_top = past_each_end * l_in
    ext_bot = _mt_stub_bottom_frac(model_id) * l_in
    s_lo = max(0.0, s_top - ext_top)
    s_hi = min(full, s_bot + ext_bot)
    if s_lo > s_hi:
        s_lo, s_hi = s_hi, s_lo
    p_lo = _v_add(o, _v_scale(s_lo, u))
    p_hi = _v_add(o, _v_scale(s_hi, u))
    return p_lo, p_hi


@dataclass
class SchematicScene:
    borehole_end: Vec3
    t_end: Vec3
    # Borehole / T ray origin in the centered frame (pre-shift world origin).
    borehole_ray_o: Vec3
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

    c_mid = mesh_aabb_center(mesh)
    neg_c = _v_sub((0.0, 0.0, 0.0), c_mid)
    mesh = translate_mesh_faces(mesh, neg_c)
    borehole_end = _v_sub(borehole_end, c_mid)
    t_end = _v_sub(t_end, c_mid)
    borehole_ray_o = neg_c
    if model_id in ("t7", "t8"):
        q_top = _wedge_anchor_top_pierce(mesh, borehole_ray_o, ub)
        if q_top is not None:
            # Slide mesh so the borehole–top pierce sits at ``borehole_ray_o``. Using ``q_top - o``
            # and also shifting ``o`` by the same vector leaves ``o`` off the translated surface
            # (surface point moves by ``2T`` while ``o`` moves by ``T``). Only translate the mesh by
            # ``o - q_top``; keep ``borehole_ray_o``, ``borehole_end``, and ``t_end`` fixed.
            shift_w = _v_sub(borehole_ray_o, q_top)
            mesh = translate_mesh_faces(mesh, shift_w)

    foot = "T8 = T7 cos(η/2); η = angle between U_d1 and U_d2." if model_id == "t8" else None
    return SchematicScene(
        borehole_end=borehole_end,
        t_end=t_end,
        borehole_ray_o=borehole_ray_o,
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
