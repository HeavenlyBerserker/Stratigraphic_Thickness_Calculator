// Batch processing for the web PWA (uses BATCH_SCHEMA, XLSX, Pyodide, JSZip).

(function (global) {
  "use strict";

  const T1_FIELD_MAP = {
    M: "measured_thickness",
    delta_deg: "wellbore_inclination_deg",
    phib_deg: "wellbore_azimuth_deg",
    beta1_deg: "formation_dip_deg",
    phid1_deg: "dip_azimuth_deg",
  };

  const TWO_BED_FIELD_MAP = {
    M: "measured_thickness",
    delta_deg: "wellbore_inclination_deg",
    phib_deg: "wellbore_azimuth_deg",
    beta1_deg: "formation_dip1_deg",
    phid1_deg: "dip_azimuth1_deg",
    beta2_deg: "formation_dip2_deg",
    phid2_deg: "dip_azimuth2_deg",
  };

  const MC_OUTPUT_COLUMNS = [
    "MC_N",
    "MC_mean",
    "MC_std",
    "MC_P10",
    "MC_P25",
    "MC_P50",
    "MC_P75",
    "MC_P90",
  ];

  function cellEmpty(v) {
    return v === null || v === undefined || String(v).trim() === "";
  }

  function parseT(raw) {
    if (cellEmpty(raw)) throw new Error("Missing T model number.");
    const text = String(raw).trim().toUpperCase();
    const m = text.match(/^T?([1-8])$/);
    if (!m) throw new Error(`Invalid T value ${raw}; use 1–8 or T1–T8.`);
    return Number(m[1]);
  }

  function fieldMapForModel(modelId) {
    return modelId === "t1" ? T1_FIELD_MAP : TWO_BED_FIELD_MAP;
  }

  function requiredValueColumns(modelId) {
    return modelId === "t1" ? BATCH_SCHEMA.t1Required : BATCH_SCHEMA.twoBedRequired;
  }

  function buildInputs(row, modelId) {
    const fmap = fieldMapForModel(modelId);
    const values = {};
    const sigmas = {};
    for (const pair of BATCH_SCHEMA.inputSigmaPairs) {
      const valueCol = pair.value;
      const sigmaCol = pair.sigma;
      const field = fmap[valueCol];
      if (!field) continue;
      if (requiredValueColumns(modelId).includes(valueCol)) {
        if (cellEmpty(row[valueCol])) throw new Error(`Missing ${valueCol}.`);
        values[field] = Number(row[valueCol]);
      } else if (!cellEmpty(row[valueCol])) {
        values[field] = Number(row[valueCol]);
      }
      sigmas[field] = cellEmpty(row[sigmaCol]) ? 0 : Math.max(0, Number(row[sigmaCol]));
    }
    return { values, sigmas };
  }

  function validateRow(row) {
    const wellId = String(row.well_id || "").trim();
    if (!wellId) throw new Error("Missing well_id.");
    const tNumber = parseT(row.T);
    const modelId = BATCH_SCHEMA.modelIdByT[tNumber];
    if (modelId === "t1") {
      for (const col of BATCH_SCHEMA.t1Unused) {
        if (!cellEmpty(row[col])) throw new Error(`T1 row must leave ${col} blank.`);
      }
    }
    for (const col of requiredValueColumns(modelId)) {
      if (cellEmpty(row[col])) throw new Error(`Missing required column ${col} for T${tNumber}.`);
    }
    const { values, sigmas } = buildInputs(row, modelId);
    return { wellId, tNumber, modelId, values, sigmas };
  }

  function vec3Lines(prefix, v) {
    if (!Array.isArray(v) || v.length < 3) return [];
    return [
      `${prefix}_x=${Number(v[0]).toFixed(6)}`,
      `${prefix}_y=${Number(v[1]).toFixed(6)}`,
      `${prefix}_z=${Number(v[2]).toFixed(6)}`,
    ];
  }

  function vectorPrefix(key) {
    const base = key.replace(/_vector$/, "");
    return {
      ud1: "Ud1",
      ud2: "Ud2",
      ud2_prime: "Ud2_prime",
      uav: "Uav",
      ub: "Ub",
      ndc: "Ndc",
      ndp: "Ndp",
      c: "Uc",
      ub_prime: "Ub_prime",
    }[base] || base;
  }

  function formatIntermediates(modelId, res) {
    if (!res || typeof res !== "object") return "";
    const lines = [];
    const tKey = String(modelId || "").toUpperCase();
    if (res.true_stratigraphic_thickness != null) {
      lines.push(`${tKey}=${Number(res.true_stratigraphic_thickness).toFixed(6)}`);
    }
    const skip = new Set(["true_stratigraphic_thickness", "geometry_warnings"]);
    for (const [key, value] of Object.entries(res)) {
      if (skip.has(key)) continue;
      if (key.endsWith("_vector") && Array.isArray(value) && value.length >= 3) {
        lines.push(...vec3Lines(vectorPrefix(key), value));
      } else if (typeof value === "boolean") {
        lines.push(`${key}=${value ? 1 : 0}`);
      } else if (typeof value === "number" && Number.isFinite(value)) {
        lines.push(`${key}=${Number(value).toFixed(6)}`);
      }
    }
    if (Array.isArray(res.geometry_warnings) && res.geometry_warnings.length) {
      lines.push(`geometry_warnings=${res.geometry_warnings.join("; ")}`);
    }
    // Single-line cell content so Excel does not wrap.
    return lines.join("; ");
  }

  function readWorkbookRows(arrayBuffer) {
    const wb = XLSX.read(arrayBuffer, { type: "array" });
    const ws = wb.Sheets[wb.SheetNames[0]];
    const table = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });
    if (!table.length) throw new Error("Batch workbook is empty.");
    const headers = table[0].map((h) => String(h || "").trim());
    const index = {};
    headers.forEach((h, i) => {
      if (h) index[h] = i;
    });
    for (const h of BATCH_SCHEMA.headers) {
      if (!(h in index)) throw new Error(`Batch workbook missing column: ${h}`);
    }
    const rows = [];
    for (let r = 1; r < table.length; r++) {
      const line = table[r];
      if (!line || line.every((v) => cellEmpty(v))) continue;
      const row = {};
      for (const h of BATCH_SCHEMA.headers) {
        row[h] = line[index[h]];
      }
      rows.push(row);
    }
    if (!rows.length) throw new Error("Batch workbook has no data rows.");
    return rows;
  }

  function sheetFromRows(rows) {
    const aoa = [BATCH_SCHEMA.headers];
    for (const row of rows) {
      aoa.push(BATCH_SCHEMA.headers.map((h) => row[h] ?? ""));
    }
    return XLSX.utils.aoa_to_sheet(aoa);
  }

  function downloadWorkbook(wb, filename) {
    XLSX.writeFile(wb, filename);
  }

  function templateWorkbook() {
    const row = {};
    for (const h of BATCH_SCHEMA.headers) row[h] = "";
    row.well_id = "WELL-001";
    row.T = 1;
    Object.assign(row, BATCH_SCHEMA.defaultValues);
    Object.assign(row, BATCH_SCHEMA.defaultSigmas);
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, sheetFromRows([row]), "BatchInput");
    return wb;
  }

  function exampleWorkbook() {
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, sheetFromRows(BATCH_SCHEMA.exampleRows), "BatchInput");
    return wb;
  }

  function mcStatsFromPayload(mc) {
    if (!mc) return null;
    return {
      MC_N: mc.n,
      MC_mean: mc.mean,
      MC_std: mc.std,
      MC_P10: mc.p10,
      MC_P25: mc.p25,
      MC_P50: mc.p50,
      MC_P75: mc.p75,
      MC_P90: mc.p90,
    };
  }

  function wrapFieldsForModel(modelId) {
    if (modelId === "t1") return ["wellbore_azimuth_deg", "dip_azimuth_deg"];
    return ["wellbore_azimuth_deg", "dip_azimuth1_deg", "dip_azimuth2_deg"];
  }

  async function computeRow(pyodide, modelId, values, sigmas) {
    const wrapFields = wrapFieldsForModel(modelId);
    const sampleCount = BATCH_SCHEMA.mcSampleCountWeb;
    const txt = await pyodide.runPythonAsync(
      `compute_payload(${JSON.stringify(modelId)}, ${JSON.stringify(values)}, ${JSON.stringify(sigmas)}, ${JSON.stringify(wrapFields)}, ${sampleCount})`
    );
    return JSON.parse(txt);
  }

  function safeStem(wellId, tNumber) {
    return `${String(wellId).replace(/[^\w\-]+/g, "_") || "well"}_T${tNumber}`;
  }

  function renderPlotCanvas(drawFn, width, height) {
    const canvas = document.createElement("canvas");
    const dpr = window.devicePixelRatio || 1;
    canvas.width = width * dpr;
    canvas.height = height * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    drawFn(ctx, width, height);
    return canvas;
  }

  function drawHistogramPlot(ctx, w, h, thicknesses, title) {
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, w, h);
    const pad = { l: 52, r: 16, t: 36, b: 42 };
    const pw = w - pad.l - pad.r;
    const ph = h - pad.t - pad.b;
    const sorted = thicknesses.slice().sort((a, b) => a - b);
    const min = sorted[0];
    const max = sorted[sorted.length - 1];
    const bins = 60;
    const counts = new Array(bins).fill(0);
    const width = max === min ? 1 : (max - min) / bins;
    for (const t of thicknesses) {
      let idx = width === 0 ? 0 : Math.floor((t - min) / width);
      if (idx >= bins) idx = bins - 1;
      if (idx < 0) idx = 0;
      counts[idx]++;
    }
    const maxCount = Math.max(...counts, 1);
    ctx.fillStyle = "#4C78A8";
    for (let i = 0; i < bins; i++) {
      const x0 = pad.l + (i / bins) * pw;
      const barW = pw / bins - 1;
      const barH = (counts[i] / maxCount) * ph;
      ctx.fillRect(x0, pad.t + ph - barH, barW, barH);
    }
    ctx.strokeStyle = "#333";
    ctx.strokeRect(pad.l, pad.t, pw, ph);
    ctx.fillStyle = "#111";
    ctx.font = "12px Arial";
    ctx.fillText(title, pad.l, 20);
    ctx.fillText("Thickness", pad.l + pw / 2 - 30, h - 8);
  }

  function drawCumulativePlot(ctx, w, h, thicknesses, title) {
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, w, h);
    const pad = { l: 52, r: 16, t: 36, b: 42 };
    const pw = w - pad.l - pad.r;
    const ph = h - pad.t - pad.b;
    const sorted = thicknesses.slice().sort((a, b) => a - b);
    const min = sorted[0];
    const max = sorted[sorted.length - 1];
    ctx.strokeStyle = "#4C78A8";
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < sorted.length; i++) {
      const x = pad.l + ((sorted[i] - min) / (max - min || 1)) * pw;
      const y = pad.t + ph - ((i + 1) / sorted.length) * ph;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.strokeStyle = "#333";
    ctx.lineWidth = 1;
    ctx.strokeRect(pad.l, pad.t, pw, ph);
    ctx.fillStyle = "#111";
    ctx.font = "12px Arial";
    ctx.fillText(title, pad.l, 20);
    ctx.fillText("Thickness", pad.l + pw / 2 - 30, h - 8);
  }

  async function canvasToBlob(canvas, plotFormat) {
    const fmt = (plotFormat || "png").toLowerCase();
    if (fmt === "svg") {
      const w = canvas.width / (window.devicePixelRatio || 1);
      const h = canvas.height / (window.devicePixelRatio || 1);
      const pngData = canvas.toDataURL("image/png");
      const svg = [
        `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}">`,
        `<image href="${pngData}" width="${w}" height="${h}" />`,
        `</svg>`,
      ].join("");
      return new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    }
    return new Promise((resolve) => canvas.toBlob(resolve, "image/png"));
  }

  async function buildMcPlotsZip(results, plotFormat) {
    const zip = new JSZip();
    let count = 0;
    const fmt = (plotFormat || "png").toLowerCase();
    const ext = fmt === "svg" ? "svg" : "png";
    for (const result of results) {
      if (result.status !== "OK" || !result.mc_thicknesses || !result.mc_thicknesses.length) continue;
      const stem = safeStem(result.well_id, result.t_number);
      const titleBase = `${result.well_id} — T${result.t_number}`;
      const histCanvas = renderPlotCanvas(
        (ctx, w, h) => drawHistogramPlot(ctx, w, h, result.mc_thicknesses, `${titleBase} Monte Carlo histogram`),
        800,
        450
      );
      const cumulativeCanvas = renderPlotCanvas(
        (ctx, w, h) => drawCumulativePlot(ctx, w, h, result.mc_thicknesses, `${titleBase} Monte Carlo cumulative`),
        800,
        450
      );
      const histBlob = await canvasToBlob(histCanvas, fmt);
      const cumulativeBlob = await canvasToBlob(cumulativeCanvas, fmt);
      zip.file(`${stem}_histogram.${ext}`, histBlob);
      zip.file(`${stem}_cumulative.${ext}`, cumulativeBlob);
      count++;
    }
    if (!count) return null;
    return zip.generateAsync({ type: "blob" });
  }

  function writeResultsWorkbook(results) {
    const headers = BATCH_SCHEMA.headers.concat([
      "T_result",
      "status",
      ...MC_OUTPUT_COLUMNS,
      "error",
      "intermediate_values",
    ]);
    const aoa = [headers];
    const tResultCol = BATCH_SCHEMA.headers.length;
    const interCol = headers.length - 1;
    for (const result of results) {
      const line = BATCH_SCHEMA.headers.map((h) => result.inputs[h] ?? "");
      line.push(result.t_result ?? "");
      line.push(result.status);
      for (const key of MC_OUTPUT_COLUMNS) {
        line.push(result.mc_stats ? result.mc_stats[key] ?? "" : "");
      }
      line.push(String(result.error || "").replace(/\r?\n/g, " "));
      line.push(
        String(result.intermediate_values || "")
          .replace(/\r\n/g, "; ")
          .replace(/\n/g, "; ")
          .replace(/\r/g, "; ")
      );
      aoa.push(line);
    }
    const ws = XLSX.utils.aoa_to_sheet(aoa);
    for (let r = 0; r < aoa.length; r++) {
      for (let c = 0; c < headers.length; c++) {
        const addr = XLSX.utils.encode_cell({ r, c });
        if (!ws[addr]) continue;
        const style = {
          alignment: { wrapText: false, vertical: "center" },
        };
        if (r === 0 || c === tResultCol) {
          style.font = { bold: true };
        }
        ws[addr].s = style;
      }
    }
    if (!ws["!cols"]) ws["!cols"] = [];
    ws["!cols"][interCol] = { wch: 48 };
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "BatchResults");
    return wb;
  }

  async function runBatch(pyodide, rows, progressCb) {
    const results = [];
    const total = rows.length;
    for (let i = 0; i < rows.length; i++) {
      const row = rows[i];
      const inputs = {};
      for (const h of BATCH_SCHEMA.headers) inputs[h] = row[h];
      progressCb(i + 1, total, `Processing ${row.well_id || `row ${i + 1}`} (${i + 1}/${total})...`);
      try {
        const { wellId, tNumber, modelId, values, sigmas } = validateRow(row);
        const payload = await computeRow(pyodide, modelId, values, sigmas);
        const mcStats = mcStatsFromPayload(payload.monte_carlo);
        const intermediates =
          payload.intermediate_values ||
          formatIntermediates(modelId, payload.result);
        results.push({
          inputs,
          well_id: wellId,
          t_number: tNumber,
          model_id: modelId,
          t_result: payload.result.true_stratigraphic_thickness,
          status: "OK",
          error: "",
          intermediate_values: intermediates,
          warnings: Array.isArray(payload.result.geometry_warnings)
            ? payload.result.geometry_warnings.map(String)
            : [],
          mc_stats: mcStats,
          mc_thicknesses: payload.monte_carlo ? payload.monte_carlo.thicknesses : null,
        });
      } catch (err) {
        results.push({
          inputs,
          well_id: String(row.well_id || ""),
          t_number: 0,
          model_id: "",
          t_result: null,
          status: "ERROR",
          error: String(err.message || err),
          intermediate_values: "",
          warnings: [],
          mc_stats: null,
          mc_thicknesses: null,
        });
      }
    }
    return results;
  }

  global.STCBatch = {
    readWorkbookRows,
    templateWorkbook,
    exampleWorkbook,
    downloadWorkbook,
    writeResultsWorkbook,
    runBatch,
    buildMcPlotsZip,
    safeStem,
  };
})(typeof window !== "undefined" ? window : globalThis);
