/**
 * 3D geometry schematic (canvas): bed + borehole + T + axes. Legend layout:
 * ``globalThis.STC_LEGEND_LAYOUT === "side"`` → legend column on the right (Qt WebEngine embed);
 * otherwise (e.g. PWA ``"bottom"``) → legend strip under the 3D view.
 */
(function (global) {
  const V = {
    from(a) {
      return { x: a[0], y: a[1], z: a[2] };
    },
    add(a, b) {
      return { x: a.x + b.x, y: a.y + b.y, z: a.z + b.z };
    },
    sub(a, b) {
      return { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z };
    },
    scale(s, a) {
      return { x: s * a.x, y: s * a.y, z: s * a.z };
    },
    dot(a, b) {
      return a.x * b.x + a.y * b.y + a.z * b.z;
    },
    cross(a, b) {
      return {
        x: a.y * b.z - a.z * b.y,
        y: a.z * b.x - a.x * b.z,
        z: a.x * b.y - a.y * b.x,
      };
    },
    norm(a) {
      return Math.hypot(a.x, a.y, a.z);
    },
    unit(a) {
      const n = V.norm(a);
      return n < 1e-15 ? { x: 0, y: 0, z: 1 } : V.scale(1 / n, a);
    },
  };

  const ISO_C = 0.8660254037844387;
  const ISO_S = 0.5;

  function project(p) {
    return {
      x: (p.x - p.y) * ISO_C,
      y: (p.x + p.y) * ISO_S - p.z,
    };
  }

  /** No-roll turntable camera basis from yaw/pitch. */
  function makeCameraBasis(yaw, pitch) {
    const cy = Math.cos(yaw);
    const sy = Math.sin(yaw);
    const cp = Math.cos(pitch);
    const sp = Math.sin(pitch);
    const right = { x: cy, y: sy, z: 0 };
    const up = { x: -sy * sp, y: cy * sp, z: -cp };
    const forward = { x: -sy * cp, y: cy * cp, z: sp };
    return { right, up, forward };
  }

  function makeProjectCam(yaw, pitch) {
    const basis = makeCameraBasis(yaw, pitch);
    return function projectCam(p) {
      return {
        x: V.dot(p, basis.right),
        y: V.dot(p, basis.up),
      };
    };
  }

  function basisInPlane(n) {
    const n1 = V.unit(n);
    const ref = Math.abs(n1.x) < 0.85 ? { x: 1, y: 0, z: 0 } : { x: 0, y: 1, z: 0 };
    const u = V.unit(V.cross(n1, ref));
    const v = V.unit(V.cross(n1, u));
    return { u, v, n: n1 };
  }

  /** Quad lying in plane ⊥ n through center; extent controlled by size (half-width along u,v). */
  function quadInBedPlane(center, n, size) {
    const { u, v } = basisInPlane(n);
    const s = size;
    const O = center;
    const p00 = V.add(O, V.add(V.scale(-s, u), V.scale(-s, v)));
    const p10 = V.add(O, V.add(V.scale(s, u), V.scale(-s, v)));
    const p11 = V.add(O, V.add(V.scale(s, u), V.scale(s, v)));
    const p01 = V.add(O, V.add(V.scale(-s, u), V.scale(s, v)));
    return [p00, p10, p11, p01];
  }

  /** Slanted rectangular prism: extrude quad along +n̂ by thickness. */
  function buildSlabMesh(center, n, size, thickness, fill, stroke) {
    const n1 = V.unit(n);
    const bot = quadInBedPlane(center, n, size);
    const off = V.scale(thickness, n1);
    const top = bot.map((p) => V.add(p, off));
    return boxMeshFromQuads(bot, top, fill, stroke);
  }

  function boxMeshFromQuads(bot, top, fill, stroke) {
    const faces = [];
    const quad = (a, b, c, d, surface) => ({
      verts: [a, b, c, d],
      fill,
      stroke,
      surface,
    });
    faces.push(quad(bot[0], bot[1], bot[2], bot[3], "base"));
    faces.push(quad(top[3], top[2], top[1], top[0], "top"));
    for (let i = 0; i < 4; i++) {
      const j = (i + 1) % 4;
      faces.push(quad(bot[i], bot[j], top[j], top[i], "side"));
    }
    return faces;
  }

  /**
   * One bed volume: top face in plane ⊥ nTop, base face in plane ⊥ nBottom.
   * Plane centers are offset along tDir by ±halfSep (stratigraphic thickness direction).
   */
  function buildSingleBedTwoSlantsMesh(center, nTop, nBottom, size, planeSep, tDir, fillTop, strokeTop, fillBase, strokeBase) {
    const t = V.unit(tDir);
    const half = planeSep * 0.5;
    const Cb = V.sub(center, V.scale(half, t));
    const Ct = V.add(center, V.scale(half, t));
    const bb = basisInPlane(nBottom);
    const tb = basisInPlane(nTop);
    const s = size;
    const bot = [
      V.add(Cb, V.add(V.scale(-s, bb.u), V.scale(-s, bb.v))),
      V.add(Cb, V.add(V.scale(s, bb.u), V.scale(-s, bb.v))),
      V.add(Cb, V.add(V.scale(s, bb.u), V.scale(s, bb.v))),
      V.add(Cb, V.add(V.scale(-s, bb.u), V.scale(s, bb.v))),
    ];
    const top = [
      V.add(Ct, V.add(V.scale(-s, tb.u), V.scale(-s, tb.v))),
      V.add(Ct, V.add(V.scale(s, tb.u), V.scale(-s, tb.v))),
      V.add(Ct, V.add(V.scale(s, tb.u), V.scale(s, tb.v))),
      V.add(Ct, V.add(V.scale(-s, tb.u), V.scale(s, tb.v))),
    ];
    const fillSide = "rgba(40, 130, 95, 0.42)";
    const strokeSide = "rgba(25, 95, 70, 0.9)";
    const faces = [];
    const quad = (a, b, c, d, fill, stroke, surface) => ({
      verts: [a, b, c, d],
      fill,
      stroke,
      surface,
    });
    faces.push(quad(bot[0], bot[1], bot[2], bot[3], fillBase, strokeBase, "base"));
    faces.push(quad(top[3], top[2], top[1], top[0], fillTop, strokeTop, "top"));
    for (let i = 0; i < 4; i++) {
      const j = (i + 1) % 4;
      faces.push(quad(bot[i], bot[j], top[j], top[i], fillSide, strokeSide, "side"));
    }
    return faces;
  }

  /**
   * Wedging bed (paper §2.2.6 / Fig. 6): upper and lower boundaries are planes ⊥ Ud1 and ⊥ Ud2;
   * they intersect along hinge H ∥ N_dp = Ud1 × Ud2. Solid is a tetrahedron with one edge on the
   * hinge and two triangular faces on the top and base beds — a literal wedge pinching to the hinge.
   * T7 uses thickness ⊥ top; T8 uses the equal-angle construction on the same geometry (tDir differs).
   */
  function buildWedgingBedMesh(ud1, ud2, ndpHint, charLen, slabThick, fillTop, strokeTop, fillBase, strokeBase) {
    const u1 = V.unit(ud1);
    const u2 = V.unit(ud2);
    let Hraw = ndpHint && V.norm(ndpHint) > 1e-10 ? ndpHint : V.cross(u1, u2);
    if (V.norm(Hraw) < 1e-8) {
      const sum = V.add(u1, u2);
      const tDir = V.norm(sum) < 1e-10 ? u1 : V.unit(sum);
      return buildSingleBedTwoSlantsMesh(
        { x: 0, y: 0, z: 0 },
        u1,
        u2,
        Math.max(charLen, 1) * 0.72,
        slabThick * 1.05,
        tDir,
        fillTop,
        strokeTop,
        fillBase,
        strokeBase
      );
    }
    const H = V.unit(Hraw);
    const L = Math.max(Number(charLen) || 1, 1e-6);
    const hingeLen = L * 0.96;
    const radial = L * 0.74;
    const eTop = V.unit(V.cross(H, u1));
    const eBase = V.unit(V.cross(H, u2));
    let V0 = V.scale(-hingeLen * 0.5, H);
    let V1 = V.scale(hingeLen * 0.5, H);
    let V2 = V.add(V0, V.scale(radial, eTop));
    let V3 = V.add(V0, V.scale(radial, eBase));
    const ctr = centroid3([V0, V1, V2, V3]);
    const shift = { x: -ctr.x, y: -ctr.y, z: -ctr.z };
    V0 = V.add(V0, shift);
    V1 = V.add(V1, shift);
    V2 = V.add(V2, shift);
    V3 = V.add(V3, shift);

    const fillSide = "rgba(35, 125, 95, 0.42)";
    const strokeSide = "rgba(22, 95, 72, 0.9)";
    const fillEnd = "rgba(40, 118, 88, 0.38)";
    const strokeEnd = "rgba(25, 88, 65, 0.88)";
    const tri = (a, b, c, fill, stroke, surface) => ({
      verts: [a, b, c],
      fill,
      stroke,
      surface,
    });
    return [
      tri(V0, V1, V2, fillTop, strokeTop, "top"),
      tri(V0, V1, V3, fillBase, strokeBase, "base"),
      tri(V0, V2, V3, fillSide, strokeSide, "side"),
      tri(V1, V2, V3, fillEnd, strokeEnd, "end"),
    ];
  }

  /**
   * Fold package: two thick slabs with poles udA and udB (fallback only).
   */
  function buildFoldMesh(udA, udB, size, thick, fillA, strokeA, fillB, strokeB) {
    const n1 = V.unit(udA);
    const n2 = V.unit(udB);
    const bis = V.unit(V.add(n1, n2));
    const spread = V.norm(V.add(n1, n2)) < 1e-5 ? { x: 0, y: 0, z: 0 } : V.scale(size * 0.07, bis);
    const s = size * 0.86;
    const t = thick * 0.88;
    return [
      ...buildSlabMesh(V.scale(-0.5, spread), n1, s, t, fillA, strokeA),
      ...buildSlabMesh(V.scale(0.5, spread), n2, s, t, fillB, strokeB),
    ];
  }

  /** Unit vector interpolation along the great-circle arc from a to b (0→a, 1→b). */
  function slerpDirUnit(a, b, t) {
    const u = V.unit(a);
    const v = V.unit(b);
    const d = Math.min(1, Math.max(-1, V.dot(u, v)));
    const om = Math.acos(d);
    if (om < 1e-7) return u;
    const so = Math.sin(om);
    return V.unit(V.add(V.scale(Math.sin((1 - t) * om) / so, u), V.scale(Math.sin(t * om) / so, v)));
  }

  /** Rodrigues rotation of v around unit axis k by angle θ (radians). */
  function rotateAroundAxis(v, axisUnit, angleRad) {
    const k = V.unit(axisUnit);
    const cos = Math.cos(angleRad);
    const sin = Math.sin(angleRad);
    const kxv = V.cross(k, v);
    const kdv = V.dot(k, v);
    return V.add(V.add(V.scale(cos, v), V.scale(sin, kxv)), V.scale((1 - cos) * kdv, k));
  }

  /**
   * Semi-arch schematic aligned with Xu et al. §2.2.4–2.2.5 / Fig. 5:
   * – T5 (concentric): arc in the plane of U_d1 and U′_d2; η = arccos(U_d1·U′_d2) (Eq. 22);
   *   thickness of the drawn shell is extruded along **N_dc** (Eq. 11) when provided.
   * – T6 (plunging): same with **U_d1** and **U_d2** (no azimuth correction); **N_dp** (Eq. 23).
   * The arc is a great-circle sweep between the two poles in that plane; shallow η may be
   * opened to ≥28° for visibility. Not to stratigraphic scale.
   */
  function buildSemiArchFoldMesh(udA, udB, hingeHint, charLen, slabThick, fillOut, strokeOut, fillIn, strokeIn) {
    const u1 = V.unit(udA);
    const u2 = V.unit(udB);
    let Hraw;
    if (hingeHint && V.norm(hingeHint) > 1e-10) {
      Hraw = hingeHint;
    } else {
      Hraw = V.cross(u1, u2);
    }
    if (V.norm(Hraw) < 1e-6) {
      return buildFoldMesh(udA, udB, Math.max(charLen * 0.85, 1), slabThick, fillOut, strokeOut, fillIn, strokeIn);
    }
    const H = V.unit(Hraw);
    const L = Math.max(Number(charLen) || 1, 1e-6);

    const etaTrue = Math.acos(Math.min(1, Math.max(-1, V.dot(u1, u2))));
    const ETA_MIN_VIS = (28 * Math.PI) / 180;
    const etaArc = Math.max(etaTrue, ETA_MIN_VIS);
    const uEnd = etaTrue >= ETA_MIN_VIS ? u2 : V.unit(rotateAroundAxis(u1, H, etaArc));

    const R = L * 0.88;
    const dr = Math.max(L * 0.14, slabThick * 1.45);
    const hw = L * 0.34;
    const nArc = 22;
    const Hm = V.scale(-hw, H);
    const Hp = V.scale(hw, H);
    const fillCap = "rgba(30, 150, 110, 0.48)";
    const strokeCap = "rgba(18, 110, 82, 0.92)";
    const quad = (aa, bb, cc, dd, fill, stroke, surface) => ({
      verts: [aa, bb, cc, dd],
      fill,
      stroke,
      surface,
    });

    const faces = [];
    // Outer o* → surface "top", inner i* → "base" (paper Fig. 5: inner = stratigraphic top bed).
    for (let k = 0; k < nArc; k++) {
      const t0 = k / nArc;
      const t1 = (k + 1) / nArc;
      const d0 = slerpDirUnit(u1, uEnd, t0);
      const d1 = slerpDirUnit(u1, uEnd, t1);
      const o0 = V.scale(R, d0);
      const o1 = V.scale(R, d1);
      const i0 = V.scale(R - dr, d0);
      const i1 = V.scale(R - dr, d1);
      const o0m = V.add(o0, Hm);
      const o0p = V.add(o0, Hp);
      const o1m = V.add(o1, Hm);
      const o1p = V.add(o1, Hp);
      const i0m = V.add(i0, Hm);
      const i0p = V.add(i0, Hp);
      const i1m = V.add(i1, Hm);
      const i1p = V.add(i1, Hp);
      faces.push(quad(o0m, o0p, o1p, o1m, fillOut, strokeOut, "top"));
      faces.push(quad(i0m, i1m, i1p, i0p, fillIn, strokeIn, "base"));
    }

    const dS = slerpDirUnit(u1, uEnd, 0);
    const dE = slerpDirUnit(u1, uEnd, 1);
    const oS = V.scale(R, dS);
    const oE = V.scale(R, dE);
    const iS = V.scale(R - dr, dS);
    const iE = V.scale(R - dr, dE);
    faces.push(
      quad(V.add(iS, Hm), V.add(iS, Hp), V.add(oS, Hp), V.add(oS, Hm), fillCap, strokeCap, "cap")
    );
    faces.push(
      quad(V.add(iE, Hm), V.add(oE, Hm), V.add(oE, Hp), V.add(iE, Hp), fillCap, strokeCap, "cap")
    );

    return faces;
  }

  function centroid3(verts) {
    let x = 0,
      y = 0,
      z = 0;
    for (const v of verts) {
      x += v.x;
      y += v.y;
      z += v.z;
    }
    const n = verts.length || 1;
    return { x: x / n, y: y / n, z: z / n };
  }

  function faceDepthRotated(f, yaw, pitch) {
    const basis = makeCameraBasis(yaw, pitch);
    const c = centroid3(f.verts);
    return V.dot(c, basis.forward);
  }

  function segmentDepthRotated(a, b, yaw, pitch) {
    const mid = {
      x: (a.x + b.x) * 0.5,
      y: (a.y + b.y) * 0.5,
      z: (a.z + b.z) * 0.5,
    };
    const basis = makeCameraBasis(yaw, pitch);
    return V.dot(mid, basis.forward);
  }

  function lerpVec3(a, b, t) {
    return {
      x: a.x + t * (b.x - a.x),
      y: a.y + t * (b.y - a.y),
      z: a.z + t * (b.z - a.z),
    };
  }

  function meshAxisAlignedBounds(meshFaces, origin) {
    let lo = { x: Infinity, y: Infinity, z: Infinity };
    let hi = { x: -Infinity, y: -Infinity, z: -Infinity };
    for (const f of meshFaces) {
      for (const v of f.verts) {
        lo.x = Math.min(lo.x, v.x);
        lo.y = Math.min(lo.y, v.y);
        lo.z = Math.min(lo.z, v.z);
        hi.x = Math.max(hi.x, v.x);
        hi.y = Math.max(hi.y, v.y);
        hi.z = Math.max(hi.z, v.z);
      }
    }
    if (origin) {
      lo.x = Math.min(lo.x, origin.x);
      lo.y = Math.min(lo.y, origin.y);
      lo.z = Math.min(lo.z, origin.z);
      hi.x = Math.max(hi.x, origin.x);
      hi.y = Math.max(hi.y, origin.y);
      hi.z = Math.max(hi.z, origin.z);
    }
    return { lo, hi };
  }

  function meshAabbCenter(meshFaces) {
    const { lo, hi } = meshAxisAlignedBounds(meshFaces, null);
    return {
      x: 0.5 * (lo.x + hi.x),
      y: 0.5 * (lo.y + hi.y),
      z: 0.5 * (lo.z + hi.z),
    };
  }

  function rayAabbInterval(o, u, lo, hi) {
    const eps = 1e-14;
    let tNear = -Infinity;
    let tFar = Infinity;
    const axes = ["x", "y", "z"];
    for (let i = 0; i < 3; i++) {
      const ax = axes[i];
      const oi = o[ax];
      const ui = u[ax];
      const loi = lo[ax];
      const hii = hi[ax];
      if (Math.abs(ui) < eps) {
        if (oi < loi - 1e-9 || oi > hii + 1e-9) return null;
        continue;
      }
      const inv = 1 / ui;
      let t1 = (loi - oi) * inv;
      let t2 = (hii - oi) * inv;
      if (t1 > t2) [t1, t2] = [t2, t1];
      tNear = Math.max(tNear, t1);
      tFar = Math.min(tFar, t2);
      if (tNear > tFar + 1e-12) return null;
    }
    return { tNear, tFar };
  }

  /** Past bottom contact along ray: fraction of L_in (T1–T4 use 2; others 1). Top stub still uses ``pastEach``. */
  const MT_STUB_BOTTOM_FRAC = 1.0;

  function mtStubBottomFrac(modelId) {
    if (modelId === "t1" || modelId === "t2" || modelId === "t3" || modelId === "t4") return 2.0;
    return MT_STUB_BOTTOM_FRAC;
  }

  /**
   * Ray ∩ mesh AABB → in-volume length L_in. +z = down: smaller z = top bed.
   * Draw from (top along ray) − pastEach×L_in to (bottom along ray) + stub×L_in, clamped to O→target.
   */
  function mtDisplayEndpoints(o, target, meshFaces, pastEach = 0.25, modelId = null) {
    const d = V.sub(target, o);
    const full = V.norm(d);
    if (full < 1e-12) return { lo: o, hi: target };
    const u = V.unit(d);
    const { lo, hi } = meshAxisAlignedBounds(meshFaces, o);
    const slab = rayAabbInterval(o, u, lo, hi);
    let sA;
    let sB;
    if (!slab) {
      sA = 0.25 * full;
      sB = 0.75 * full;
    } else {
      const sEntry = Math.max(0, Math.min(full, slab.tNear));
      const sExit = Math.max(0, Math.min(full, slab.tFar));
      if (sExit <= sEntry + 1e-9 * Math.max(full, 1)) {
        sA = 0.25 * full;
        sB = 0.75 * full;
      } else {
        sA = sEntry;
        sB = sExit;
      }
    }
    let lIn = sB - sA;
    if (lIn < 1e-9 * Math.max(full, 1)) {
      sA = 0.25 * full;
      sB = 0.75 * full;
      lIn = sB - sA;
    }
    const pA = V.add(o, V.scale(sA, u));
    const pB = V.add(o, V.scale(sB, u));
    let sTop;
    let sBot;
    if (pA.z <= pB.z) {
      sTop = sA;
      sBot = sB;
    } else {
      sTop = sB;
      sBot = sA;
    }
    const extTop = pastEach * lIn;
    const extBot = mtStubBottomFrac(modelId) * lIn;
    let sLo = Math.max(0, sTop - extTop);
    let sHi = Math.min(full, sBot + extBot);
    if (sLo > sHi) [sLo, sHi] = [sHi, sLo];
    const pLo = V.add(o, V.scale(sLo, u));
    const pHi = V.add(o, V.scale(sHi, u));
    return { lo: pLo, hi: pHi };
  }

  function planeNdFromFace(face) {
    const vs = face.verts;
    const v0 = vs[0];
    const v1 = vs[1];
    const v2 = vs[2];
    let nRaw = V.cross(V.sub(v1, v0), V.sub(v2, v0));
    let nn = V.norm(nRaw);
    if (nn < 1e-14 && vs.length >= 4) {
      const v3 = vs[3];
      nRaw = V.cross(V.sub(v2, v0), V.sub(v3, v0));
      nn = V.norm(nRaw);
    }
    if (nn < 1e-14) return { n: { x: 0, y: 0, z: 1 }, d: 0 };
    const n = V.scale(1 / nn, nRaw);
    const d = V.dot(n, v0);
    return { n, d };
  }

  function centroidVerts(verts) {
    let sx = 0;
    let sy = 0;
    let sz = 0;
    const n = verts.length || 1;
    for (const v of verts) {
      sx += v.x;
      sy += v.y;
      sz += v.z;
    }
    return { x: sx / n, y: sy / n, z: sz / n };
  }

  /** Ray p = o + t*u (u unit); t where p hits plane of face, or null if parallel. */
  function rayPlaneParameter(o, u, face) {
    const { n: nb, d: db } = planeNdFromFace(face);
    const denom = V.dot(nb, u);
    if (Math.abs(denom) < 1e-12) return null;
    return (db - V.dot(nb, o)) / denom;
  }

  /**
   * Wedging tetrahedron: M/T along o→target. Deeper bed (+z = down ⇒ larger centroid z) gets the
   * long stub (½ × max longest edge of the two bed Δ); shallower bed gets the short stub.
   */
  function wedgeMtSegmentTriBeds(o, target, topFace, baseFace, pastEach, modelId = null) {
    const d = V.sub(target, o);
    const full = V.norm(d);
    if (full < 1e-12) return null;
    const u = V.unit(d);
    const tTop = rayPlaneParameter(o, u, topFace);
    const tBase = rayPlaneParameter(o, u, baseFace);
    if (tTop == null || tBase == null) return null;
    if (Math.abs(tTop - tBase) < 1e-12 * Math.max(1, full)) return null;
    const zTop = centroidVerts(topFace.verts).z;
    const zBase = centroidVerts(baseFace.verts).z;
    let shallowFace;
    let bottomFace;
    let tShallow;
    let tBottom;
    if (zBase >= zTop) {
      shallowFace = topFace;
      bottomFace = baseFace;
      tShallow = tTop;
      tBottom = tBase;
    } else {
      shallowFace = baseFace;
      bottomFace = topFace;
      tShallow = tBase;
      tBottom = tTop;
    }
    const tEnter = Math.min(tShallow, tBottom);
    const tExit = Math.max(tShallow, tBottom);
    const lIn = tExit - tEnter;
    if (lIn < 1e-12 * Math.max(1, full)) return null;
    const extShort = pastEach * lIn;
    let extLong =
      0.5 * Math.max(faceLongestEdgeLen(shallowFace), faceLongestEdgeLen(bottomFace));
    if (extLong < 1e-12 * Math.max(1, full)) extLong = mtStubBottomFrac(modelId) * lIn;
    const eps = 1e-9 * Math.max(1, full);
    const bottomIsExit = tBottom > tShallow + eps;
    let tLo;
    let tHi;
    if (bottomIsExit) {
      tLo = Math.max(0, tEnter - extShort);
      tHi = tExit + extLong;
    } else {
      tLo = tEnter - extLong;
      tHi = tExit + extShort;
    }
    if (tLo > tHi) [tLo, tHi] = [tHi, tLo];
    return { lo: V.add(o, V.scale(tLo, u)), hi: V.add(o, V.scale(tHi, u)) };
  }

  /** Longest polygon edge (triangle: three sides; n>3: cycle edges only). */
  function faceLongestEdgeLen(face) {
    const vs = face.verts;
    if (!vs || vs.length < 2) return 0;
    if (vs.length === 3) {
      let best = 0;
      for (let i = 0; i < 3; i++) {
        for (let j = i + 1; j < 3; j++) {
          best = Math.max(best, V.norm(V.sub(vs[j], vs[i])));
        }
      }
      return best;
    }
    let best = 0;
    const n = vs.length;
    for (let i = 0; i < n; i++) {
      const j = (i + 1) % n;
      best = Math.max(best, V.norm(V.sub(vs[j], vs[i])));
    }
    return best;
  }

  /** Triangle or quad area (quad split by v0–v2 diagonal). */
  function polygonAreaFromVerts(verts) {
    if (!verts || verts.length < 3) return 0;
    const v0 = verts[0];
    const v1 = verts[1];
    const v2 = verts[2];
    if (verts.length === 3) {
      return 0.5 * V.norm(V.cross(V.sub(v1, v0), V.sub(v2, v0)));
    }
    const v3 = verts[3];
    const a1 = 0.5 * V.norm(V.cross(V.sub(v1, v0), V.sub(v2, v0)));
    const a2 = 0.5 * V.norm(V.cross(V.sub(v2, v0), V.sub(v3, v0)));
    return a1 + a2;
  }

  /**
   * T1–T8: M/T along O→target. Wedge: tri top + tri base → top centroid, base plane.
   * T5–T6 (Fig. 5): mesh **base** = inner limb (stratigraphic top); mesh **top** = outer limb (bottom).
   * Area-weight center on **inner** faces; chord to deepest **outer** plane or u to that outer centroid if u ∥ plane.
   * Wedging tri+tri (T7/T8): ``wedgeMtSegmentTriBeds`` along borehole; else bottom stub MT_STUB_BOTTOM_FRAC·L_in.
   */
  function mtDisplaySingleBedT234(meshFaces, o, target, pastEach = 0.25, modelId = null) {
    function segmentFromAnchorPlane(cAnchor, planeFace) {
      const { n: nb, d: db } = planeNdFromFace(planeFace);
      const d = V.sub(target, o);
      const full = V.norm(d);
      if (full < 1e-12) return { lo: o, hi: target };
      let u = V.unit(d);
      let denom = V.dot(nb, u);
      if (Math.abs(denom) < 1e-12) return null;
      let sb = (db - V.dot(nb, cAnchor)) / denom;
      if (sb < 0) {
        u = V.scale(-1, u);
        sb = -sb;
      }
      let lIn = Math.abs(sb);
      if (lIn < 1e-12) lIn = Math.max(1e-9 * Math.max(full, 1), full * 0.35);
      const extTop = pastEach * lIn;
      const extBot = mtStubBottomFrac(modelId) * lIn;
      const sLo = -extTop;
      const sHi = sb + extBot;
      return {
        lo: V.add(cAnchor, V.scale(sLo, u)),
        hi: V.add(cAnchor, V.scale(sHi, u)),
      };
    }

    function t56AlongUToFarCentroid(cAnchor, cFar) {
      const d = V.sub(target, o);
      const full = V.norm(d);
      if (full < 1e-12) return { lo: o, hi: target };
      let u = V.unit(d);
      let sb = V.dot(V.sub(cFar, cAnchor), u);
      if (sb < 0) {
        u = V.scale(-1, u);
        sb = -sb;
      }
      const lIn = Math.max(Math.abs(sb), 1e-9 * Math.max(full, 1));
      const extTop = pastEach * lIn;
      const extBot = mtStubBottomFrac(modelId) * lIn;
      return {
        lo: V.add(cAnchor, V.scale(-extTop, u)),
        hi: V.add(cAnchor, V.scale(sb + extBot, u)),
      };
    }

    const topTris = meshFaces.filter(
      (f) => f.surface === "top" && f.verts && f.verts.length === 3
    );
    const baseTris = meshFaces.filter(
      (f) => f.surface === "base" && f.verts && f.verts.length === 3
    );
    if (topTris.length === 1 && baseTris.length === 1) {
      const segW = wedgeMtSegmentTriBeds(o, target, topTris[0], baseTris[0], pastEach, modelId);
      if (segW) return segW;
      const cTop = centroidVerts(topTris[0].verts);
      const seg = segmentFromAnchorPlane(cTop, baseTris[0]);
      if (seg) return seg;
    }

    if (modelId === "t5" || modelId === "t6") {
      const outerFs = meshFaces.filter((f) => f.surface === "top");
      const innerFs = meshFaces.filter((f) => f.surface === "base");
      if (outerFs.length && innerFs.length) {
        let tw = 0;
        let sx = 0;
        let sy = 0;
        let sz = 0;
        const rows = [];
        for (const f of innerFs) {
          const ar = polygonAreaFromVerts(f.verts);
          const c = centroidVerts(f.verts);
          rows.push({ c, ar });
          tw += ar;
          sx += ar * c.x;
          sy += ar * c.y;
          sz += ar * c.z;
        }
        let cSeed;
        if (tw < 1e-20) {
          const n0 = rows.length;
          cSeed = {
            x: rows.reduce((s, e) => s + e.c.x, 0) / n0,
            y: rows.reduce((s, e) => s + e.c.y, 0) / n0,
            z: rows.reduce((s, e) => s + e.c.z, 0) / n0,
          };
        } else {
          cSeed = { x: sx / tw, y: sy / tw, z: sz / tw };
        }
        let anchorFace = innerFs[0];
        let bestD2 = Infinity;
        for (const f of innerFs) {
          const c = centroidVerts(f.verts);
          const dx = c.x - cSeed.x;
          const dy = c.y - cSeed.y;
          const dz = c.z - cSeed.z;
          const d2 = dx * dx + dy * dy + dz * dz;
          if (d2 < bestD2) {
            bestD2 = d2;
            anchorFace = f;
          }
        }
        const cAnchor = centroidVerts(anchorFace.verts);
        let deepestOuter = outerFs[0];
        let maxZ = centroidVerts(deepestOuter.verts).z;
        for (let j = 1; j < outerFs.length; j++) {
          const z = centroidVerts(outerFs[j].verts).z;
          if (z > maxZ) {
            maxZ = z;
            deepestOuter = outerFs[j];
          }
        }
        const seg56 = segmentFromAnchorPlane(cAnchor, deepestOuter);
        if (seg56) return seg56;
        const cOuterCtr = centroidVerts(deepestOuter.verts);
        return t56AlongUToFarCentroid(cAnchor, cOuterCtr);
      }
    }

    const capSurf = new Set(["top", "base", "cap", "end"]);
    const capFaces = meshFaces.filter((f) => capSurf.has(f.surface || ""));
    if (capFaces.length < 2) return mtDisplayEndpoints(o, target, meshFaces, pastEach, modelId);
    let bestMin = null;
    let bestMax = null;
    for (const f of capFaces) {
      const c = centroidVerts(f.verts);
      const z = c.z;
      if (!bestMin || z < bestMin.z) bestMin = { f, c, z };
      if (!bestMax || z > bestMax.z) bestMax = { f, c, z };
    }
    const zSpan = bestMax.z - bestMin.z;
    if (zSpan < 1e-9 * Math.max(1, Math.abs(bestMin.z), Math.abs(bestMax.z)))
      return mtDisplayEndpoints(o, target, meshFaces, pastEach, modelId);
    if (bestMin.f === bestMax.f) return mtDisplayEndpoints(o, target, meshFaces, pastEach, modelId);
    const seg2 = segmentFromAnchorPlane(bestMin.c, bestMax.f);
    if (seg2) return seg2;
    return mtDisplayEndpoints(o, target, meshFaces, pastEach, modelId);
  }

  function collectScene(modelId, res, M, Tval) {
    const ub = V.from(res.ub_vector);
    let bedNormals = [];
    let tDir = { x: 0, y: 0, z: 1 };
    const ud1 = V.from(res.ud1_vector);

    switch (modelId) {
      case "t1":
        bedNormals = [ud1];
        tDir = V.unit(ud1);
        break;
      case "t2":
      case "t4":
        bedNormals = [V.from(res.ud1_vector), V.from(res.ud2_vector)];
        tDir = V.unit(V.from(res.uav_vector));
        break;
      case "t3": {
        const u1 = V.from(res.ud1_vector);
        const u2 = V.from(res.ud2_vector);
        bedNormals = [u1, u2];
        const sum = V.add(u1, u2);
        tDir = V.norm(sum) < 1e-10 ? V.unit(u1) : V.unit(sum);
        break;
      }
      case "t5":
        bedNormals = [V.from(res.ud1_vector), V.from(res.ud2_prime_vector)];
        tDir = V.unit(ud1);
        break;
      case "t6":
        bedNormals = [V.from(res.ud1_vector), V.from(res.ud2_vector)];
        tDir = V.unit(ud1);
        break;
      case "t7":
        bedNormals = [V.from(res.ud1_vector), V.from(res.ud2_vector)];
        tDir = V.unit(ud1);
        break;
      case "t8": {
        const ua = V.from(res.ud1_vector);
        const ub2 = V.from(res.ud2_vector);
        bedNormals = [ua, ub2];
        const sum = V.add(ua, ub2);
        tDir = V.norm(sum) < 1e-10 ? V.unit(ua) : V.unit(sum);
        break;
      }
      default:
        return null;
    }

    let boreholeEnd = V.scale(M, V.unit(ub));
    let tEnd = V.scale(Tval, tDir);
    const L = Math.max(M, Tval, 1);
    const axisLen = L * 0.38;
    const axes = {
      ex: { x: axisLen, y: 0, z: 0 },
      ey: { x: 0, y: axisLen, z: 0 },
      ez: { x: 0, y: 0, z: axisLen },
    };
    const planeSize = L * 0.52;
    const slabThick = L * 0.14;

    let volumeKind = "";
    let meshFaces = [];

    const fillTop = "rgba(22, 140, 55, 0.4)";
    const strokeTop = "rgba(15, 100, 40, 0.92)";
    const fillBase = "rgba(30, 130, 200, 0.38)";
    const strokeBase = "rgba(20, 95, 165, 0.92)";

    if (modelId === "t1") {
      volumeKind = "Slanted slab";
      meshFaces = buildSlabMesh({ x: 0, y: 0, z: 0 }, ud1, planeSize, slabThick, fillTop, strokeTop);
    } else if (modelId === "t2" || modelId === "t3" || modelId === "t4") {
      volumeKind = "Single bed (top / base dips)";
      const u1 = V.from(res.ud1_vector);
      const u2 = V.from(res.ud2_vector);
      meshFaces = buildSingleBedTwoSlantsMesh(
        { x: 0, y: 0, z: 0 },
        u1,
        u2,
        planeSize * 0.72,
        slabThick * 1.05,
        tDir,
        fillTop,
        strokeTop,
        fillBase,
        strokeBase
      );
    } else if (modelId === "t5") {
      volumeKind = "Semi-arch (concentric fold)";
      const u1 = V.from(res.ud1_vector);
      const u2 = V.from(res.ud2_prime_vector);
      const hint = res.ndc_vector ? V.from(res.ndc_vector) : null;
      meshFaces = buildSemiArchFoldMesh(u1, u2, hint, L, slabThick, fillTop, strokeTop, fillBase, strokeBase);
    } else if (modelId === "t6") {
      volumeKind = "Semi-arch (plunging fold)";
      const u1 = V.from(res.ud1_vector);
      const u2 = V.from(res.ud2_vector);
      const hint = res.ndp_vector ? V.from(res.ndp_vector) : null;
      meshFaces = buildSemiArchFoldMesh(u1, u2, hint, L, slabThick, fillTop, strokeTop, fillBase, strokeBase);
    } else if (modelId === "t7") {
      volumeKind = "Wedging bed (top-normal, Fig. 6a)";
      const u1 = V.from(res.ud1_vector);
      const u2 = V.from(res.ud2_vector);
      const hint = res.ndp_vector ? V.from(res.ndp_vector) : null;
      meshFaces = buildWedgingBedMesh(u1, u2, hint, L, slabThick, fillTop, strokeTop, fillBase, strokeBase);
    } else if (modelId === "t8") {
      volumeKind = "Wedging bed (equal-angle, Fig. 6b)";
      const u1 = V.from(res.ud1_vector);
      const u2 = V.from(res.ud2_vector);
      const hint = res.ndp_vector ? V.from(res.ndp_vector) : null;
      meshFaces = buildWedgingBedMesh(u1, u2, hint, L, slabThick, fillTop, strokeTop, fillBase, strokeBase);
    }

    const cMid = meshAabbCenter(meshFaces);
    const negC = V.scale(-1, cMid);
    meshFaces = meshFaces.map((f) => ({
      ...f,
      verts: f.verts.map((v) => V.add(v, negC)),
    }));
    boreholeEnd = V.sub(boreholeEnd, cMid);
    tEnd = V.sub(tEnd, cMid);
    const boreholeRayO = negC;

    return {
      bedNormals,
      boreholeEnd,
      tEnd,
      boreholeRayO,
      axes,
      planeSize,
      tDir,
      meshFaces,
      volumeKind,
      wedgeFootnote: modelId === "t8" ? "T8 = T7 cos(η/2); η = angle between U_d1 and U_d2." : null,
    };
  }

  function bboxProjected(points2d) {
    let minX = Infinity,
      maxX = -Infinity,
      minY = Infinity,
      maxY = -Infinity;
    for (const p of points2d) {
      minX = Math.min(minX, p.x);
      maxX = Math.max(maxX, p.x);
      minY = Math.min(minY, p.y);
      maxY = Math.max(maxY, p.y);
    }
    return { minX, maxX, minY, maxY };
  }

  const STC_PITCH_LIM = (85 * Math.PI) / 180;
  const STC_ZOOM_MIN = 0.4;
  const STC_ZOOM_MAX = 4.5;
  const STC_LEGEND_W_FRAC = 0.24;
  const STC_LEGEND_MIN_W = 100;
  const STC_LEGEND_H = 96;
  const STC_ROT_SENS = 0.006;

  function bindStcCamera(canvas) {
    let raf = 0;
    const schedulePaint = () => {
      if (raf) return;
      raf = requestAnimationFrame(() => {
        raf = 0;
        if (canvas._stcPayload && canvas._stcModelId !== undefined) {
          paintGeometry(canvas);
        }
      });
    };

    /** Use pointer position in **canvas** space (not viewport). Viewport X was wrong on desktop when the page is centered. */
    const inMainPlot = (clientX, clientY) => {
      const rect = canvas.getBoundingClientRect();
      const lx = clientX - rect.left;
      const ly = clientY - rect.top;
      const w = rect.width;
      const h = rect.height;
      if (w < 1 || h < 1) return false;
      if (lx < 0 || ly < 0 || lx >= w || ly >= h) return false;
      const layout = canvas._stcLegendLayout || "bottom";
      if (layout === "side") {
        const lw =
          canvas._stcLegendW != null
            ? canvas._stcLegendW
            : Math.max(STC_LEGEND_MIN_W, Math.floor(w * STC_LEGEND_W_FRAC));
        const splitX = w - lw;
        return lx < splitX - 2;
      }
      const lh =
        canvas._stcLegendH != null ? canvas._stcLegendH : STC_LEGEND_H;
      const splitY = h - lh;
      return ly < splitY - 2;
    };

    const touchPoints = new Map();
    const updateTouchPoint = (e) => {
      if (e.pointerType !== "touch") return;
      touchPoints.set(e.pointerId, { x: e.clientX, y: e.clientY });
    };
    const removeTouchPoint = (e) => {
      if (e.pointerType !== "touch") return;
      touchPoints.delete(e.pointerId);
    };
    const touchDistance = () => {
      const pts = Array.from(touchPoints.values());
      if (pts.length < 2) return null;
      return Math.hypot(pts[1].x - pts[0].x, pts[1].y - pts[0].y);
    };
    const rotationSensPx = () => {
      const rect = canvas.getBoundingClientRect();
      const w = Math.max(260, Math.min(960, rect.width || canvas.clientWidth || 600));
      return STC_ROT_SENS * (480 / w);
    };

    const onPointerMove = (e) => {
      const cam = canvas._stcCam;
      if (!cam) return;

      if (e.pointerType === "touch") {
        if (touchPoints.has(e.pointerId)) touchPoints.set(e.pointerId, { x: e.clientX, y: e.clientY });
        if (touchPoints.size === 2) {
          const d = touchDistance();
          if (d && canvas._stcPinchStartDist) {
            const ratio = d / Math.max(canvas._stcPinchStartDist, 1e-6);
            cam.zoom = Math.max(STC_ZOOM_MIN, Math.min(STC_ZOOM_MAX, canvas._stcPinchStartZoom * ratio));
            schedulePaint();
          }
          return;
        }
      }

      if (!canvas._stcDragging || e.pointerId !== canvas._stcActivePointerId) return;
      const dx = e.clientX - canvas._stcLastX;
      const dy = e.clientY - canvas._stcLastY;
      canvas._stcLastX = e.clientX;
      canvas._stcLastY = e.clientY;
      const sens = rotationSensPx();
      // Turntable: horizontal drag controls yaw only; vertical drag controls pitch only.
      cam.yaw -= dx * sens;
      cam.pitch -= dy * sens;
      cam.pitch = Math.max(-STC_PITCH_LIM, Math.min(STC_PITCH_LIM, cam.pitch));
      schedulePaint();
    };

    const endPointerDrag = (e) => {
      removeTouchPoint(e);
      if (touchPoints.size < 2) {
        canvas._stcPinchStartDist = null;
        canvas._stcPinchStartZoom = null;
      }
      if (e.pointerId === canvas._stcActivePointerId) {
        canvas._stcDragging = false;
        canvas._stcActivePointerId = undefined;
        canvas.style.cursor = "grab";
      }
      try {
        canvas.releasePointerCapture(e.pointerId);
      } catch (_) {
        /* not captured */
      }
    };

    canvas.addEventListener(
      "pointerdown",
      (e) => {
        if (e.pointerType === "mouse" && e.button !== 0) return;
        if (!inMainPlot(e.clientX, e.clientY)) return;
        if (e.pointerType === "touch") {
          e.preventDefault();
          updateTouchPoint(e);
          if (touchPoints.size === 2) {
            canvas._stcDragging = false;
            canvas._stcActivePointerId = undefined;
            canvas._stcPinchStartDist = touchDistance();
            canvas._stcPinchStartZoom = (canvas._stcCam && canvas._stcCam.zoom) || 1;
            return;
          }
        }
        try {
          canvas.setPointerCapture(e.pointerId);
        } catch (_) {
          /* ignore */
        }
        canvas._stcActivePointerId = e.pointerId;
        canvas._stcDragging = true;
        canvas._stcLastX = e.clientX;
        canvas._stcLastY = e.clientY;
        canvas.style.cursor = "grabbing";
      },
      { passive: false }
    );
    canvas.addEventListener("pointermove", onPointerMove);
    canvas.addEventListener("pointerup", endPointerDrag);
    canvas.addEventListener("pointercancel", endPointerDrag);
    canvas.addEventListener(
      "wheel",
      (e) => {
        if (!inMainPlot(e.clientX, e.clientY)) return;
        e.preventDefault();
        const cam = canvas._stcCam;
        if (!cam) return;
        const f = e.deltaY > 0 ? 0.92 : 1.09;
        cam.zoom = Math.max(STC_ZOOM_MIN, Math.min(STC_ZOOM_MAX, cam.zoom * f));
        schedulePaint();
      },
      { passive: false }
    );
    canvas.addEventListener("dblclick", (e) => {
      if (!inMainPlot(e.clientX, e.clientY)) return;
      if (canvas._stcCam) {
        canvas._stcCam.yaw = 0;
        canvas._stcCam.pitch = 0;
        canvas._stcCam.zoom = 1;
        canvas._stcPinchStartDist = null;
        canvas._stcPinchStartZoom = null;
        schedulePaint();
      }
    });
    canvas.style.touchAction = "none";

    if (!canvas._stcResizeObserved) {
      canvas._stcResizeObserved = true;
      const ro = new ResizeObserver(() => {
        schedulePaint();
      });
      ro.observe(canvas);
      if (canvas.parentElement) ro.observe(canvas.parentElement);
    }
  }

  function paintGeometry(canvas) {
    const payload = canvas._stcPayload;
    const modelId = canvas._stcModelId;
    if (!canvas || !payload || !payload.result || !payload.inputs) {
      if (canvas) canvas.style.display = "none";
      return;
    }
    const res = payload.result;
    const M = Number(payload.inputs.measured_thickness);
    const Tval = Number(res.true_stratigraphic_thickness);
    if (!Number.isFinite(M) || !Number.isFinite(Tval)) {
      canvas.style.display = "none";
      return;
    }

    const scene = collectScene(modelId, res, M, Tval);
    if (!scene) {
      canvas.style.display = "none";
      return;
    }

    const cam = canvas._stcCam || { yaw: 0, pitch: 0, zoom: 1 };
    canvas._stcCam = cam;
    const projectCam = makeProjectCam(cam.yaw, cam.pitch);

    canvas.style.display = "block";
    const dpr = window.devicePixelRatio || 1;
    let cssW = canvas.clientWidth || canvas.offsetWidth;
    if (!cssW && canvas.parentElement) {
      cssW = canvas.parentElement.clientWidth;
    }
    if (!cssW) cssW = 600;

    let cssH = canvas.clientHeight || canvas.offsetHeight;
    if (!cssH && canvas.parentElement) {
      cssH = canvas.parentElement.clientHeight;
    }
    if (!cssH) {
      const br = canvas.getBoundingClientRect();
      if (br.height > 1) cssH = br.height;
    }
    if (!cssH || cssH < 32) cssH = 320;

    const refW = 600;
    const refH = 320;
    const layoutS = Math.max(0.5, Math.min(2.5, Math.min(cssW / refW, cssH / refH)));
    const fs = (px) => Math.round(px * layoutS) + "px Arial";
    const fsBold = (px) => "bold " + Math.round(px * layoutS) + "px Arial";

    const legendOnSide = globalThis.STC_LEGEND_LAYOUT === "side";
    let splitX = cssW;
    let splitY = cssH;
    let legendW = 0;
    let legendH = 0;
    if (legendOnSide) {
      legendW = Math.round(cssW * STC_LEGEND_W_FRAC * Math.max(0.85, layoutS));
      legendW = Math.min(legendW, Math.floor(cssW * 0.34));
      legendW = Math.max(STC_LEGEND_MIN_W, legendW);
      splitX = cssW - legendW;
      const minPlotW = Math.max(96, Math.round(140 * layoutS));
      if (splitX < minPlotW) {
        legendW = Math.max(80, cssW - minPlotW);
        splitX = cssW - legendW;
      }
      canvas._stcLegendW = legendW;
      canvas._stcLegendH = undefined;
    } else {
      legendH = Math.round(STC_LEGEND_H * layoutS);
      legendH = Math.min(legendH, Math.floor(cssH * 0.38));
      legendH = Math.max(48, legendH);
      splitY = cssH - legendH;
      const minPlot = Math.max(64, Math.round(90 * layoutS));
      if (splitY < minPlot) {
        legendH = Math.max(40, cssH - minPlot);
        splitY = cssH - legendH;
      }
      canvas._stcLegendH = legendH;
      canvas._stcLegendW = undefined;
    }
    canvas._stcLegendLayout = legendOnSide ? "side" : "bottom";

    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    canvas.style.cursor = "grab";
    canvas.title = "Drag to orbit · wheel zoom (desktop) · pinch zoom (mobile) · double-click reset";

    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, cssW, cssH);

    const plotClipW = legendOnSide ? splitX : cssW;
    const plotClipH = legendOnSide ? cssH : splitY;

    ctx.strokeStyle = "#e2e8f0";
    ctx.lineWidth = Math.max(1, layoutS);
    ctx.beginPath();
    if (legendOnSide) {
      ctx.moveTo(splitX + 0.5, 0);
      ctx.lineTo(splitX + 0.5, cssH);
    } else {
      ctx.moveTo(0, splitY + 0.5);
      ctx.lineTo(cssW, splitY + 0.5);
    }
    ctx.stroke();

    if (!legendOnSide) {
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, splitY + 1, cssW, legendH - 1);
    }

    const margin = legendOnSide
      ? {
          left: Math.round(22 * layoutS),
          right: Math.round(14 * layoutS),
          top: Math.round(34 * layoutS),
          bottom: Math.round(20 * layoutS),
        }
      : {
          left: Math.round(24 * layoutS),
          right: Math.round(24 * layoutS),
          top: Math.round(34 * layoutS),
          bottom: Math.round(20 * layoutS),
        };
    const plotW = plotClipW - margin.left - margin.right;
    const plotH = plotClipH - margin.top - margin.bottom;
    const cx = margin.left + plotW / 2;
    const originYFrac = 0.5;
    const cy = margin.top + plotH * originYFrac;
    const plotLabelMaxX = legendOnSide ? splitX : cssW;
    const titleCenterX = legendOnSide ? splitX / 2 : cssW / 2;

    const oVol = { x: 0, y: 0, z: 0 };
    const oRay = scene.boreholeRayO;
    const pts2 = [];

    function addPt(p) {
      pts2.push(projectCam(p));
    }

    const mtPastEach = 0.25;
    const useSingleBedTopAnchor =
      modelId === "t1" ||
      modelId === "t2" ||
      modelId === "t3" ||
      modelId === "t4" ||
      modelId === "t5" ||
      modelId === "t6" ||
      modelId === "t7" ||
      modelId === "t8";
    const bhDisp = useSingleBedTopAnchor
      ? mtDisplaySingleBedT234(
          scene.meshFaces,
          oRay,
          scene.boreholeEnd,
          mtPastEach,
          modelId
        )
      : mtDisplayEndpoints(oRay, scene.boreholeEnd, scene.meshFaces, mtPastEach, modelId);
    const tDisp = useSingleBedTopAnchor
      ? mtDisplaySingleBedT234(scene.meshFaces, oRay, scene.tEnd, mtPastEach, modelId)
      : mtDisplayEndpoints(oRay, scene.tEnd, scene.meshFaces, mtPastEach, modelId);
    addPt(oVol);
    addPt(bhDisp.lo);
    addPt(bhDisp.hi);
    addPt(tDisp.lo);
    addPt(tDisp.hi);

    for (const f of scene.meshFaces) {
      for (const v of f.verts) addPt(v);
    }

    const Lref = scene.planeSize;
    const axisOrigin = {
      x: Lref * 2.02,
      y: -Lref * 1.09,
      z: Lref * 0.13,
    };
    addPt(axisOrigin);
    addPt(V.add(axisOrigin, scene.axes.ex));
    addPt(V.add(axisOrigin, scene.axes.ey));
    addPt(V.add(axisOrigin, scene.axes.ez));

    const bb = bboxProjected(pts2);
    const span = Math.max(bb.maxX - bb.minX, bb.maxY - bb.minY, 1e-6);
    const projScale = (Math.min(plotW, plotH) / (span * 1.18)) * cam.zoom;

    function toCanvas(p2) {
      return {
        x: cx + p2.x * projScale,
        y: cy - p2.y * projScale,
      };
    }

    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, plotClipW, plotClipH);
    ctx.clip();

    function drawLine3(a, b, color, width, dash) {
      const pa = toCanvas(projectCam(a));
      const pb = toCanvas(projectCam(b));
      ctx.save();
      ctx.strokeStyle = color;
      ctx.lineWidth = width;
      if (dash) ctx.setLineDash(dash);
      ctx.beginPath();
      ctx.moveTo(pa.x, pa.y);
      ctx.lineTo(pb.x, pb.y);
      ctx.stroke();
      ctx.restore();
    }

    function fillFace3(f) {
      ctx.save();
      ctx.beginPath();
      const p0 = toCanvas(projectCam(f.verts[0]));
      ctx.moveTo(p0.x, p0.y);
      for (let i = 1; i < f.verts.length; i++) {
        const pi = toCanvas(projectCam(f.verts[i]));
        ctx.lineTo(pi.x, pi.y);
      }
      ctx.closePath();
      ctx.fillStyle = f.fill;
      ctx.fill();
      ctx.strokeStyle = f.stroke;
      ctx.lineWidth = Math.max(1, 1.45 * layoutS);
      ctx.stroke();
      ctx.restore();
    }

    const nMtSeg = 56;
    const drawRows = [];
    for (const f of scene.meshFaces) {
      drawRows.push({
        kind: "face",
        depth: faceDepthRotated(f, cam.yaw, cam.pitch),
        pri: 0,
        f,
      });
    }
    for (let i = 0; i < nMtSeg; i++) {
      const t0 = i / nMtSeg;
      const t1 = (i + 1) / nMtSeg;
      const a = lerpVec3(bhDisp.lo, bhDisp.hi, t0);
      const b = lerpVec3(bhDisp.lo, bhDisp.hi, t1);
      drawRows.push({
        kind: "mseg",
        depth: segmentDepthRotated(a, b, cam.yaw, cam.pitch) + i * 1e-7,
        pri: 1,
        a,
        b,
      });
    }
    for (let i = 0; i < nMtSeg; i++) {
      const t0 = i / nMtSeg;
      const t1 = (i + 1) / nMtSeg;
      const a = lerpVec3(tDisp.lo, tDisp.hi, t0);
      const b = lerpVec3(tDisp.lo, tDisp.hi, t1);
      drawRows.push({
        kind: "tseg",
        depth: segmentDepthRotated(a, b, cam.yaw, cam.pitch) + i * 1e-7,
        pri: 2,
        a,
        b,
      });
    }
    drawRows.sort((p, q) => (p.depth !== q.depth ? p.depth - q.depth : p.pri - q.pri));

    const mtLineW = Math.max(2, 3.5 * layoutS);
    for (const row of drawRows) {
      if (row.kind === "face") fillFace3(row.f);
      else if (row.kind === "mseg") drawLine3(row.a, row.b, "#dc2626", mtLineW);
      else drawLine3(row.a, row.b, "#2563eb", mtLineW);
    }

    const O = toCanvas(projectCam(oVol));

    function drawAxisArrow(from, vec, color, label) {
      const tip = V.add(from, vec);
      drawLine3(from, tip, color, Math.max(1.2, 2.2 * layoutS));
      const end = toCanvas(projectCam(tip));
      ctx.save();
      ctx.fillStyle = color;
      ctx.font = fs(11);
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(
        label,
        Math.min(
          end.x + Math.round(4 * layoutS),
          plotLabelMaxX - Math.round(10 * layoutS) - ctx.measureText(label).width
        ),
        end.y
      );
      ctx.restore();
    }

    drawAxisArrow(axisOrigin, scene.axes.ex, "#ea580c", "x (N)");
    drawAxisArrow(axisOrigin, scene.axes.ey, "#16a34a", "y (E)");
    drawAxisArrow(axisOrigin, scene.axes.ez, "#000000", "z (↓)");

    ctx.save();
    ctx.strokeStyle = "#64748b";
    ctx.lineWidth = Math.max(1, layoutS);
    ctx.setLineDash([Math.round(3 * layoutS), Math.round(3 * layoutS)]);
    const AO = toCanvas(projectCam(axisOrigin));
    ctx.beginPath();
    ctx.arc(AO.x, AO.y, Math.max(2, 3.5 * layoutS), 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    ctx.save();
    ctx.strokeStyle = "#475569";
    ctx.lineWidth = Math.max(1, layoutS);
    ctx.setLineDash([Math.round(4 * layoutS), Math.round(4 * layoutS)]);
    ctx.beginPath();
    ctx.arc(O.x, O.y, Math.max(2.5, 4 * layoutS), 0, Math.PI * 2);
    ctx.stroke();
    ctx.restore();

    ctx.save();
    ctx.fillStyle = "#334155";
    ctx.font = fsBold(12);
    ctx.textAlign = "center";
    ctx.fillText(
      "3D view — drag to orbit · wheel/pinch zoom · dbl-click reset",
      titleCenterX,
      Math.max(Math.round(14 * layoutS), 12)
    );
    ctx.restore();

    ctx.save();
    ctx.font = fs(9);
    ctx.fillStyle = "#475569";
    ctx.textAlign = "center";
    ctx.fillText(
      "Schematic only — not to scale.",
      titleCenterX,
      legendOnSide ? cssH - Math.round(6 * layoutS) : splitY - Math.round(6 * layoutS)
    );
    ctx.restore();

    ctx.restore();

    const wordWrap = (txt, maxW) => {
      const words = txt.split(" ");
      const lines = [];
      let line = "";
      for (const w of words) {
        const t = line ? line + " " + w : w;
        if (ctx.measureText(t).width > maxW && line) {
          lines.push(line);
          line = w;
        } else {
          line = t;
        }
      }
      if (line) lines.push(line);
      return lines;
    };

    if (legendOnSide) {
      const legPad = Math.round(10 * layoutS);
      const lx = splitX + legPad;
      const legendTextW = Math.max(40, legendW - 2 * legPad);
      const seg = Math.round(18 * layoutS);
      const sw = Math.max(6, Math.round(9 * layoutS));
      let ly = Math.round(18 * layoutS);
      ctx.save();
      ctx.textAlign = "left";
      ctx.fillStyle = "#0f172a";
      ctx.font = fsBold(11);
      ctx.fillText("Legend", lx, ly);
      ly += Math.round(16 * layoutS);
      ctx.font = fs(9);
      ctx.fillStyle = "#475569";
      const legendLineCol = (y, color, text, isSeg) => {
        const x0 = lx;
        if (isSeg) {
          ctx.strokeStyle = color;
          ctx.lineWidth = Math.max(2, 3 * layoutS);
          ctx.beginPath();
          ctx.moveTo(x0, y - Math.round(3 * layoutS));
          ctx.lineTo(x0 + seg, y - Math.round(3 * layoutS));
          ctx.stroke();
        } else {
          ctx.fillStyle = color;
          ctx.fillRect(x0, y - sw, sw, sw);
        }
        ctx.fillStyle = "#1e293b";
        ctx.fillText(text, x0 + Math.round(24 * layoutS), y);
        return y + Math.round(18 * layoutS);
      };
      ly = legendLineCol(ly, "#ea580c", "x axis (North)", false);
      ly = legendLineCol(ly, "#16a34a", "y axis (East)", false);
      {
        const x0 = lx;
        const swZ = Math.max(6, Math.round(9 * layoutS));
        const dz = Math.round(14 * layoutS);
        ctx.save();
        ctx.strokeStyle = "#000000";
        ctx.lineWidth = Math.max(2, 3 * layoutS);
        ctx.beginPath();
        ctx.moveTo(x0 + Math.round(swZ / 2), ly - swZ);
        ctx.lineTo(x0 + Math.round(swZ / 2), ly - swZ + dz);
        ctx.stroke();
        ctx.fillStyle = "#1e293b";
        ctx.textBaseline = "middle";
        ctx.fillText("z axis (down)", x0 + Math.round(24 * layoutS), ly - swZ + dz * 0.5);
        ctx.restore();
        ly += Math.round(18 * layoutS);
      }
      ly = legendLineCol(ly, "#dc2626", "M", true);
      ly = legendLineCol(ly, "#2563eb", "T", true);
      ctx.fillStyle = "#475569";
      ctx.font = fs(8);
      for (const ln of wordWrap(
        "Drag = orbit. Wheel (desktop) / pinch (mobile) = zoom. Double-click = reset.",
        legendTextW
      )) {
        ctx.fillText(ln, lx, ly);
        ly += Math.round(12 * layoutS);
      }
      ly += Math.round(4 * layoutS);
      ctx.fillStyle = "#64748b";
      ctx.font = fs(8);
      const lineGap = Math.round(12 * layoutS);
      const lineGapS = Math.round(11 * layoutS);
      const volLines = wordWrap("Bed volume: " + scene.volumeKind, legendTextW);
      for (const ln of volLines) {
        ctx.fillText(ln, lx, ly);
        ly += lineGap;
      }
      if (scene.wedgeFootnote) {
        ly += Math.round(6 * layoutS);
        ctx.font = fs(8);
        ctx.fillStyle = "#57534e";
        for (const ln of wordWrap(scene.wedgeFootnote, legendTextW)) {
          ctx.fillText(ln, lx, ly);
          ly += lineGapS;
        }
      }
      if (modelId === "t5" || modelId === "t6") {
        ly += Math.round(6 * layoutS);
        ctx.font = fs(8);
        ctx.fillStyle = "#57534e";
        for (const ln of wordWrap(
          "If η (between poles) is small, the drawn arc opens to ≥28° for visibility.",
          legendTextW
        )) {
          ctx.fillText(ln, lx, ly);
          ly += lineGapS;
        }
      }
      ctx.restore();
    } else {
      const lx0 = Math.round(12 * layoutS);
      const textPad = Math.round(24 * layoutS);
      const legendTextW = cssW - textPad;
      const seg = Math.round(18 * layoutS);
      const sw = Math.max(6, Math.round(9 * layoutS));
      let ly = splitY + Math.round(16 * layoutS);
      ctx.save();
      ctx.textAlign = "left";
      ctx.fillStyle = "#0f172a";
      ctx.font = fsBold(11);
      ctx.fillText("Legend", lx0, ly);
      ly += Math.round(14 * layoutS);
      ctx.font = fs(9);
      ctx.fillStyle = "#475569";
      const legendLineRow = (x, y, color, text, isSeg) => {
        if (isSeg) {
          ctx.strokeStyle = color;
          ctx.lineWidth = Math.max(2, 3 * layoutS);
          ctx.beginPath();
          ctx.moveTo(x, y - Math.round(3 * layoutS));
          ctx.lineTo(x + seg, y - Math.round(3 * layoutS));
          ctx.stroke();
        } else {
          ctx.fillStyle = color;
          ctx.fillRect(x, y - sw, sw, sw);
        }
        ctx.fillStyle = "#1e293b";
        ctx.fillText(text, x + Math.round(24 * layoutS), y);
      };
      legendLineRow(lx0, ly, "#ea580c", "x axis (North)", false);
      legendLineRow(lx0 + Math.round(122 * layoutS), ly, "#16a34a", "y axis (East)", false);
      legendLineRow(lx0 + Math.round(238 * layoutS), ly, "#000000", "z axis (down)", false);
      legendLineRow(lx0 + Math.round(348 * layoutS), ly, "#dc2626", "M", true);
      legendLineRow(lx0 + Math.round(398 * layoutS), ly, "#2563eb", "T", true);
      ly += Math.round(16 * layoutS);
      ctx.fillStyle = "#475569";
      ctx.font = fs(8);
      ctx.fillText(
        "Drag = orbit. Wheel (desktop) / pinch (mobile) = zoom. Double-click = reset.",
        lx0,
        ly
      );
      ly += Math.round(14 * layoutS);
      ly += Math.round(2 * layoutS);
      ctx.fillStyle = "#64748b";
      ctx.font = fs(8);
      const lineGap = Math.round(12 * layoutS);
      const lineGapS = Math.round(11 * layoutS);
      for (const ln of wordWrap("Bed volume: " + scene.volumeKind, legendTextW)) {
        ctx.fillText(ln, lx0, ly);
        ly += lineGap;
      }
      if (scene.wedgeFootnote) {
        ly += Math.round(6 * layoutS);
        ctx.font = fs(8);
        ctx.fillStyle = "#57534e";
        for (const ln of wordWrap(scene.wedgeFootnote, legendTextW)) {
          ctx.fillText(ln, lx0, ly);
          ly += lineGapS;
        }
      }
      if (modelId === "t5" || modelId === "t6") {
        ly += Math.round(6 * layoutS);
        ctx.font = fs(8);
        ctx.fillStyle = "#57534e";
        for (const ln of wordWrap(
          "If η (between poles) is small, the drawn arc opens to ≥28° for visibility.",
          legendTextW
        )) {
          ctx.fillText(ln, lx0, ly);
          ly += lineGapS;
        }
      }
      ctx.restore();
    }
  }

  function drawGeometry(canvas, modelId, payload) {
    if (!canvas || !payload || !payload.result || !payload.inputs) {
      if (canvas) canvas.style.display = "none";
      return;
    }
    const res = payload.result;
    const M = Number(payload.inputs.measured_thickness);
    const Tval = Number(res.true_stratigraphic_thickness);
    if (!Number.isFinite(M) || !Number.isFinite(Tval)) {
      canvas.style.display = "none";
      return;
    }

    canvas._stcPayload = payload;
    canvas._stcModelId = modelId;
    if (canvas._stcLastModelId !== modelId) {
      canvas._stcCam = { yaw: 0, pitch: 0, zoom: 1 };
      canvas._stcLastModelId = modelId;
    }
    if (!canvas._stcCam) {
      canvas._stcCam = { yaw: 0, pitch: 0, zoom: 1 };
    }

    if (!canvas._stcCameraBound) {
      canvas._stcCameraBound = true;
      bindStcCamera(canvas);
    }

    paintGeometry(canvas);
  }

  global.STC_DRAW_GEOMETRY = drawGeometry;
})(globalThis);
