/**
 * Web-only 3D geometry schematic: left = interactive orbit/zoom view (bed + borehole + T + axes);
 * right = separate legend ("vane"). Bed volumes are 3D solids (slab, single
 * bed with two dips, wedging tetrahedron (Fig. 6), or folded shells) per model.
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
    const quad = (a, b, c, d) => ({ verts: [a, b, c, d], fill, stroke });
    faces.push(quad(bot[0], bot[1], bot[2], bot[3]));
    faces.push(quad(top[3], top[2], top[1], top[0]));
    for (let i = 0; i < 4; i++) {
      const j = (i + 1) % 4;
      faces.push(quad(bot[i], bot[j], top[j], top[i]));
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
    const fillSide = "rgba(64, 180, 130, 0.22)";
    const strokeSide = "rgba(64, 180, 130, 0.58)";
    const faces = [];
    const quad = (a, b, c, d, fill, stroke) => ({ verts: [a, b, c, d], fill, stroke });
    faces.push(quad(bot[0], bot[1], bot[2], bot[3], fillBase, strokeBase));
    faces.push(quad(top[3], top[2], top[1], top[0], fillTop, strokeTop));
    for (let i = 0; i < 4; i++) {
      const j = (i + 1) % 4;
      faces.push(quad(bot[i], bot[j], top[j], top[i], fillSide, strokeSide));
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

    const fillSide = "rgba(45, 170, 125, 0.28)";
    const strokeSide = "rgba(45, 170, 125, 0.65)";
    const fillEnd = "rgba(52, 160, 118, 0.24)";
    const strokeEnd = "rgba(52, 160, 118, 0.6)";
    const tri = (a, b, c, fill, stroke) => ({ verts: [a, b, c], fill, stroke });
    return [
      tri(V0, V1, V2, fillTop, strokeTop),
      tri(V0, V1, V3, fillBase, strokeBase),
      tri(V0, V2, V3, fillSide, strokeSide),
      tri(V1, V2, V3, fillEnd, strokeEnd),
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
    const fillCap = "rgba(52, 211, 153, 0.38)";
    const strokeCap = "rgba(52, 211, 153, 0.75)";
    const quad = (aa, bb, cc, dd, fill, stroke) => ({ verts: [aa, bb, cc, dd], fill, stroke });

    const faces = [];
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
      faces.push(quad(o0m, o0p, o1p, o1m, fillOut, strokeOut));
      faces.push(quad(i0m, i1m, i1p, i0p, fillIn, strokeIn));
    }

    const dS = slerpDirUnit(u1, uEnd, 0);
    const dE = slerpDirUnit(u1, uEnd, 1);
    const oS = V.scale(R, dS);
    const oE = V.scale(R, dE);
    const iS = V.scale(R - dr, dS);
    const iE = V.scale(R - dr, dE);
    faces.push(
      quad(V.add(iS, Hm), V.add(iS, Hp), V.add(oS, Hp), V.add(oS, Hm), fillCap, strokeCap)
    );
    faces.push(
      quad(V.add(iE, Hm), V.add(oE, Hm), V.add(oE, Hp), V.add(iE, Hp), fillCap, strokeCap)
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

    const boreholeEnd = V.scale(M, V.unit(ub));
    const tEnd = V.scale(Tval, tDir);
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

    const fillTop = "rgba(34, 197, 94, 0.28)";
    const strokeTop = "rgba(34, 197, 94, 0.85)";
    const fillBase = "rgba(56, 189, 248, 0.22)";
    const strokeBase = "rgba(56, 189, 248, 0.85)";

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

    return {
      bedNormals,
      boreholeEnd,
      tEnd,
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

    let legendH = Math.round(STC_LEGEND_H * layoutS);
    legendH = Math.min(legendH, Math.floor(cssH * 0.38));
    legendH = Math.max(48, legendH);
    let splitY = cssH - legendH;
    const minPlot = Math.max(64, Math.round(90 * layoutS));
    if (splitY < minPlot) {
      legendH = Math.max(40, cssH - minPlot);
      splitY = cssH - legendH;
    }
    canvas._stcLegendH = legendH;

    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    canvas.style.cursor = "grab";
    canvas.title = "Drag to orbit · wheel zoom (desktop) · pinch zoom (mobile) · double-click reset";

    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#0b1220";
    ctx.fillRect(0, 0, cssW, cssH);

    ctx.strokeStyle = "#334155";
    ctx.lineWidth = Math.max(1, layoutS);
    ctx.beginPath();
    ctx.moveTo(0, splitY + 0.5);
    ctx.lineTo(cssW, splitY + 0.5);
    ctx.stroke();

    ctx.fillStyle = "#0f172a";
    ctx.fillRect(0, splitY + 1, cssW, legendH - 1);

    const margin = {
      left: Math.round(24 * layoutS),
      right: Math.round(24 * layoutS),
      top: Math.round(34 * layoutS),
      bottom: Math.round(20 * layoutS),
    };
    const plotW = cssW - margin.left - margin.right;
    const plotH = splitY - margin.top - margin.bottom;
    const cx = margin.left + plotW / 2;
    const cy = margin.top + plotH / 2;

    const origin = { x: 0, y: 0, z: 0 };
    const pts2 = [];

    function addPt(p) {
      pts2.push(projectCam(p));
    }

    addPt(origin);
    addPt(scene.boreholeEnd);
    addPt(scene.tEnd);

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

    const sortedFaces = [...scene.meshFaces].sort(
      (a, b) => faceDepthRotated(a, cam.yaw, cam.pitch) - faceDepthRotated(b, cam.yaw, cam.pitch)
    );
    for (const f of sortedFaces) fillFace3(f);

    const O = toCanvas(projectCam(origin));

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
        Math.min(end.x + Math.round(4 * layoutS), cssW - Math.round(72 * layoutS)),
        end.y
      );
      ctx.restore();
    }

    drawAxisArrow(axisOrigin, scene.axes.ex, "#f87171", "x (N)");
    drawAxisArrow(axisOrigin, scene.axes.ey, "#4ade80", "y (E)");
    drawAxisArrow(axisOrigin, scene.axes.ez, "#93c5fd", "z (↓)");

    ctx.save();
    ctx.strokeStyle = "#64748b";
    ctx.lineWidth = Math.max(1, layoutS);
    ctx.setLineDash([Math.round(3 * layoutS), Math.round(3 * layoutS)]);
    const AO = toCanvas(projectCam(axisOrigin));
    ctx.beginPath();
    ctx.arc(AO.x, AO.y, Math.max(2, 3.5 * layoutS), 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = "#64748b";
    ctx.font = fs(9);
    ctx.textAlign = "center";
    ctx.fillText("axes", AO.x, AO.y + Math.round(14 * layoutS));
    ctx.restore();

    drawLine3(origin, scene.boreholeEnd, "#38bdf8", Math.max(2, 3.5 * layoutS));
    drawLine3(origin, scene.tEnd, "#fbbf24", Math.max(2, 3.5 * layoutS));

    ctx.save();
    ctx.strokeStyle = "#475569";
    ctx.lineWidth = Math.max(1, layoutS);
    ctx.setLineDash([Math.round(4 * layoutS), Math.round(4 * layoutS)]);
    ctx.beginPath();
    ctx.arc(O.x, O.y, Math.max(2.5, 4 * layoutS), 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = "#94a3b8";
    ctx.font = fs(10);
    ctx.textAlign = "center";
    ctx.fillText("O", O.x, O.y + Math.round(18 * layoutS));
    ctx.restore();

    ctx.save();
    ctx.fillStyle = "#cbd5e1";
    ctx.font = fsBold(12);
    ctx.textAlign = "center";
    ctx.fillText(
      "3D view — drag to orbit · wheel/pinch zoom · dbl-click reset",
      cssW / 2,
      Math.max(Math.round(14 * layoutS), 12)
    );
    ctx.restore();

    const lx = Math.round(12 * layoutS);
    const seg = Math.round(18 * layoutS);
    const sw = Math.max(6, Math.round(9 * layoutS));
    let ly = splitY + Math.round(16 * layoutS);
    ctx.save();
    ctx.textAlign = "left";
    ctx.fillStyle = "#e2e8f0";
    ctx.font = fsBold(11);
    ctx.fillText("Legend", lx, ly);
    ly += Math.round(14 * layoutS);
    ctx.font = fs(9);
    ctx.fillStyle = "#94a3b8";
    const legendLine = (x, y, color, text, isSeg) => {
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
      ctx.fillStyle = "#e2e8f0";
      ctx.fillText(text, x + Math.round(24 * layoutS), y);
    };
    legendLine(lx, ly, "#f87171", "x axis (North)", false);
    legendLine(lx + Math.round(122 * layoutS), ly, "#4ade80", "y axis (East)", false);
    legendLine(lx + Math.round(238 * layoutS), ly, "#93c5fd", "z axis (down)", false);
    legendLine(lx + Math.round(348 * layoutS), ly, "#38bdf8", "M", true);
    legendLine(lx + Math.round(398 * layoutS), ly, "#fbbf24", "T", true);
    ly += Math.round(16 * layoutS);
    ctx.fillStyle = "#64748b";
    ctx.font = fs(8);
    ctx.fillText(
      "Drag = orbit. Wheel (desktop) / pinch (mobile) = zoom. Double-click = reset.",
      lx,
      ly
    );
    ly += Math.round(14 * layoutS);
    ly += Math.round(2 * layoutS);
    ctx.fillStyle = "#94a3b8";
    ctx.font = fs(8);
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
    const textPad = Math.round(24 * layoutS);
    const lineGap = Math.round(12 * layoutS);
    const lineGapS = Math.round(11 * layoutS);
    const volLines = wordWrap("Bed volume: " + scene.volumeKind, cssW - textPad);
    for (const ln of volLines) {
      ctx.fillText(ln, lx, ly);
      ly += lineGap;
    }
    if (scene.wedgeFootnote) {
      ly += Math.round(6 * layoutS);
      ctx.font = fs(8);
      ctx.fillStyle = "#78716c";
      for (const ln of wordWrap(scene.wedgeFootnote, cssW - textPad)) {
        ctx.fillText(ln, lx, ly);
        ly += lineGapS;
      }
    }
    if (modelId === "t5" || modelId === "t6") {
      ly += Math.round(6 * layoutS);
      ctx.font = fs(8);
      ctx.fillStyle = "#78716c";
      for (const ln of wordWrap(
        "If η (between poles) is small, the drawn arc opens to ≥28° for visibility.",
        cssW - textPad
      )) {
        ctx.fillText(ln, lx, ly);
        ly += lineGapS;
      }
    }
    ctx.restore();

    ctx.save();
    ctx.font = fs(9);
    ctx.fillStyle = "#64748b";
    ctx.textAlign = "center";
    ctx.fillText(
      "Schematic only — not to scale.",
      cssW / 2,
      splitY - Math.round(6 * layoutS)
    );
    ctx.restore();
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
