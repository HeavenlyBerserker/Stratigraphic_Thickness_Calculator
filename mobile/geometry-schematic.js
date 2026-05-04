/**
 * Web-only 3D geometry schematic: left = bed volume + borehole + T + axes;
 * right = separate legend ("vane"). Bed volumes are 3D solids (slab, single
 * bed with two dips, wedge, or folded shells) per model.
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
   * Wedge: two slanted slabs (top / base beds) slightly separated along bisector for clarity.
   */
  function buildWedgeMesh(n1, n2, size, thick, fillA, strokeA, fillB, strokeB) {
    const a1 = V.unit(n1);
    const a2 = V.unit(n2);
    const sum = V.add(a1, a2);
    const spread =
      V.norm(sum) < 1e-5 ? { x: 0, y: 0, z: 0 } : V.scale(size * 0.07, V.unit(sum));
    const s = size * 0.85;
    const t = thick * 0.92;
    return [
      ...buildSlabMesh(V.scale(-0.5, spread), a1, s, t, fillA, strokeA),
      ...buildSlabMesh(V.scale(0.5, spread), a2, s, t, fillB, strokeB),
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

  function faceDepth(f) {
    const c = centroid3(f.verts);
    return c.x + c.y - c.z * 0.9;
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
      case "t8":
        bedNormals = [V.from(res.ud1_vector), V.from(res.ud2_vector)];
        tDir = V.unit(ud1);
        break;
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
    } else if (modelId === "t7" || modelId === "t8") {
      volumeKind = "Wedge (two-bed cut)";
      const u1 = V.from(res.ud1_vector);
      const u2 = V.from(res.ud2_vector);
      meshFaces = buildWedgeMesh(u1, u2, planeSize, slabThick * 1.05, fillTop, strokeTop, fillBase, strokeBase);
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

    const scene = collectScene(modelId, res, M, Tval);
    if (!scene) {
      canvas.style.display = "none";
      return;
    }

    canvas.style.display = "block";
    const dpr = window.devicePixelRatio || 1;
    let cssW = canvas.clientWidth || canvas.offsetWidth;
    if (!cssW && canvas.parentElement) {
      cssW = canvas.parentElement.clientWidth;
    }
    if (!cssW) cssW = 600;
    const cssH = 320;
    canvas.width = Math.floor(cssW * dpr);
    canvas.height = Math.floor(cssH * dpr);
    canvas.style.height = cssH + "px";

    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = "#0b1220";
    ctx.fillRect(0, 0, cssW, cssH);

    const legendW = 134;
    const mainW = Math.max(cssW - legendW, cssW * 0.58);
    const splitX = cssW - legendW;

    ctx.strokeStyle = "#334155";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(splitX + 0.5, 0);
    ctx.lineTo(splitX + 0.5, cssH);
    ctx.stroke();

    ctx.fillStyle = "#0f172a";
    ctx.fillRect(splitX + 1, 0, legendW - 1, cssH);

    const margin = { left: 36, right: 14, top: 34, bottom: 44 };
    const plotW = splitX - margin.left - margin.right;
    const plotH = cssH - margin.top - margin.bottom;
    const cx = margin.left + plotW / 2;
    const cy = margin.top + plotH / 2;

    const origin = { x: 0, y: 0, z: 0 };
    const pts2 = [];

    function addPt(p) {
      pts2.push(project(p));
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
    const scale = Math.min(plotW, plotH) / (span * 1.18);

    function toCanvas(p2) {
      return {
        x: cx + p2.x * scale,
        y: cy - p2.y * scale,
      };
    }

    function drawLine3(a, b, color, width, dash) {
      const pa = toCanvas(project(a));
      const pb = toCanvas(project(b));
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
      const p0 = toCanvas(project(f.verts[0]));
      ctx.moveTo(p0.x, p0.y);
      for (let i = 1; i < f.verts.length; i++) {
        const pi = toCanvas(project(f.verts[i]));
        ctx.lineTo(pi.x, pi.y);
      }
      ctx.closePath();
      ctx.fillStyle = f.fill;
      ctx.fill();
      ctx.strokeStyle = f.stroke;
      ctx.lineWidth = 1.45;
      ctx.stroke();
      ctx.restore();
    }

    const sortedFaces = [...scene.meshFaces].sort((a, b) => faceDepth(a) - faceDepth(b));
    for (const f of sortedFaces) fillFace3(f);

    const O = toCanvas(project(origin));

    function drawAxisArrow(from, vec, color, label) {
      const tip = V.add(from, vec);
      drawLine3(from, tip, color, 2.2);
      const end = toCanvas(project(tip));
      ctx.save();
      ctx.fillStyle = color;
      ctx.font = "11px Arial";
      ctx.textAlign = "left";
      ctx.textBaseline = "middle";
      ctx.fillText(label, Math.min(end.x + 4, splitX - 72), end.y);
      ctx.restore();
    }

    drawAxisArrow(axisOrigin, scene.axes.ex, "#f87171", "x (E)");
    drawAxisArrow(axisOrigin, scene.axes.ey, "#4ade80", "y (N)");
    drawAxisArrow(axisOrigin, scene.axes.ez, "#93c5fd", "z (↓)");

    ctx.save();
    ctx.strokeStyle = "#64748b";
    ctx.lineWidth = 1;
    ctx.setLineDash([3, 3]);
    const AO = toCanvas(project(axisOrigin));
    ctx.beginPath();
    ctx.arc(AO.x, AO.y, 3.5, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = "#64748b";
    ctx.font = "9px Arial";
    ctx.textAlign = "center";
    ctx.fillText("axes", AO.x, AO.y + 14);
    ctx.restore();

    drawLine3(origin, scene.boreholeEnd, "#38bdf8", 3.5);
    drawLine3(origin, scene.tEnd, "#fbbf24", 3.5);

    ctx.save();
    ctx.strokeStyle = "#475569";
    ctx.lineWidth = 1;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.arc(O.x, O.y, 4, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = "#94a3b8";
    ctx.font = "10px Arial";
    ctx.textAlign = "center";
    ctx.fillText("O", O.x, O.y + 18);
    ctx.restore();

    ctx.save();
    ctx.fillStyle = "#cbd5e1";
    ctx.font = "bold 12px Arial";
    ctx.textAlign = "center";
    ctx.fillText("3D cross-section (x East, y North, z Down)", splitX / 2, 16);
    ctx.restore();

    const lx = splitX + 12;
    let ly = 28;
    ctx.save();
    ctx.textAlign = "left";
    ctx.fillStyle = "#e2e8f0";
    ctx.font = "bold 12px Arial";
    ctx.fillText("Legend", lx, ly);
    ly += 22;
    ctx.font = "10px Arial";
    ctx.fillStyle = "#94a3b8";
    const legendLine = (color, text, isSeg) => {
      if (isSeg) {
        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.moveTo(lx, ly - 3);
        ctx.lineTo(lx + 28, ly - 3);
        ctx.stroke();
      } else {
        ctx.fillStyle = color;
        ctx.fillRect(lx, ly - 9, 10, 10);
      }
      ctx.fillStyle = "#e2e8f0";
      ctx.fillText(text, lx + 36, ly);
      ly += 18;
    };
    legendLine("#f87171", "x axis (East)", false);
    legendLine("#4ade80", "y axis (North)", false);
    legendLine("#93c5fd", "z axis (down)", false);
    ly += 4;
    legendLine("#38bdf8", "M (wellbore path)", true);
    legendLine("#fbbf24", "T (stratigraphic)", true);
    ly += 8;
    ctx.fillStyle = "#94a3b8";
    ctx.font = "9px Arial";
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
    const volLines = wordWrap("Bed volume: " + scene.volumeKind, legendW - 24);
    for (const ln of volLines) {
      ctx.fillText(ln, lx, ly);
      ly += 12;
    }
    if (modelId === "t5" || modelId === "t6") {
      ly += 6;
      ctx.font = "8px Arial";
      ctx.fillStyle = "#78716c";
      for (const ln of wordWrap(
        "If η (between poles) is small, the drawn arc opens to ≥28° for visibility.",
        legendW - 20
      )) {
        ctx.fillText(ln, lx, ly);
        ly += 11;
      }
    }
    ctx.restore();

    ctx.save();
    ctx.font = "9px Arial";
    ctx.fillStyle = "#64748b";
    ctx.textAlign = "center";
    ctx.fillText("Schematic only — not to scale.", splitX / 2, cssH - 12);
    ctx.restore();
  }

  global.STC_DRAW_GEOMETRY = drawGeometry;
})(globalThis);
