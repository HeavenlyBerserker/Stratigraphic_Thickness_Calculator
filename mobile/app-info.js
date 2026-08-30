// Auto-generated from source/app_info.py — do not edit by hand.
// Regenerate: python scripts/generate_app_info_js.py

const APP_INFO = {
  "appName": "Stratigraphic Thickness Calculator",
  "version": "1.0.0",
  "implementers": [
    "Hong Xu"
  ],
  "repoUrl": "https://github.com/HeavenlyBerserker/Stratigraphic_Thickness_Calculator",
  "repoLabel": "GitHub repository",
  "paperUrl": null,
  "paperLabel": "Companion paper (link coming soon)",
  "paperCitation": "Xu, H. (forthcoming). Stratigraphic Thickness Calculator — companion manuscript.",
  "licenseName": "MIT License",
  "licenseUrl": "https://opensource.org/licenses/MIT",
  "usageInstructions": [
    "Choose the model that matches your geometry assumptions.",
    "Enter measured values and angles using the documented conventions in the README.",
    "Optional: for uncertainty analysis, enter non-zero σ values to enable Monte Carlo outputs (leave σ = 0 for deterministic runs). On the web app, click the ? icon; on desktop, hover over a σ box for a quick cheatsheet.",
    "Review geometry warnings in fold models before final interpretation.",
    "Export results and plots when needed for reporting and auditability."
  ],
  "batchInstructionsWeb": [
    "Optionally download the blank template or the 16-row example workbook.",
    "Choose Monte Carlo plot format (PNG or SVG) for any wells with non-zero σ.",
    "Click Choose File to Batch Process and select an .xlsx workbook (one well per row).",
    "Click Batch Process. The browser downloads batch_results.xlsx automatically (you do not pick a save path first). If any row used Monte Carlo, a batch_results_mc_plots.zip file with histogram and cumulative plots also downloads.",
    "Review the batch log: green Success with ✅ means all rows OK; yellow warnings (⚠️) mean geometry warnings; red (❌) means one or more row errors (other rows still ran)."
  ],
  "bestPractices": "For best results, use high-quality field or interpreted inputs (e.g., calibrated dip/azimuth measurements and validated structural picks).",
  "batchBestPractices": "Use the template column names (well_id, T, M, sigma_M, …). T must be 1–8 (or T1–T8). For T₁, leave beta2_deg and phid2_deg blank. Set σ = 0 for deterministic rows; set one or more σ > 0 to enable Monte Carlo for that well.",
  "generalReferences": [
    "Berg, R.R. (2011). Cross-validation of geometric models for calculating true stratigraphic thickness from wellbore data. <i>AAPG Bulletin</i>, 95(6), 975–992.",
    "Xu, H., Berg, R.R., et al. (2007, 2010). Concentric-fold thickness correction methods (see companion paper for full citations).",
    "Xu, H. (forthcoming). Stratigraphic Thickness Calculator — companion manuscript."
  ],
  "modelReferences": [
    {
      "id": "t1",
      "label": "T₁ — One-dip",
      "references": [
        "Xu, H. (forthcoming). Stratigraphic Thickness Calculator — companion manuscript. — Eq. T₁ (one-dip correction)."
      ]
    },
    {
      "id": "t2",
      "label": "T₂ — Average-vector",
      "references": [
        "Berg, R.R. (2011) — average dip-pole vector U<sub>av</sub> and T = M (U<sub>av</sub> · U<sub>b</sub>)."
      ]
    },
    {
      "id": "t3",
      "label": "T₃ — Average-thickness",
      "references": [
        "Xu, H. (forthcoming). Stratigraphic Thickness Calculator — companion manuscript. — Eq. T₃ (average of top and base bed projections).",
        "Uses the same U<sub>d</sub> · U<sub>b</sub> dot-product framework as Berg (2011)."
      ]
    },
    {
      "id": "t4",
      "label": "T₄ — Mixed Average",
      "references": [
        "Xu, H. (forthcoming). Stratigraphic Thickness Calculator — companion manuscript. — Eq. T₄ = (T₂ + T₃) / 2.",
        "Combines Berg (2011) average-vector and average-thickness methods."
      ]
    },
    {
      "id": "t5",
      "label": "T₅ — Concentric Fold",
      "references": [
        "Xu et al. (2007, 2010) — corrected β′₂, U′<sub>d2</sub>, N<sub>dc</sub>, and concentric-fold geometry.",
        "Berg, R.R. (2011) — M′ borehole projection onto the fold plane."
      ]
    },
    {
      "id": "t6",
      "label": "T₆ — Plunging Concentric Fold",
      "references": [
        "Xu et al. (2007, 2010) — plunging fold geometry (N<sub>dp</sub>, U<sub>c</sub>, α, γ).",
        "Berg, R.R. (2011) — M′ borehole projection."
      ]
    },
    {
      "id": "t7",
      "label": "T₇ — Top-normal",
      "references": [
        "Xu, H. (forthcoming). Stratigraphic Thickness Calculator — companion manuscript. — Eq. T₇ (M measured normal to the top bed).",
        "Berg, R.R. (2011) — M′ projection; branch selection via S = N<sub>dp</sub> · U′<sub>b</sub>."
      ]
    },
    {
      "id": "t8",
      "label": "T₈ — Equal-angle",
      "references": [
        "Xu, H. (forthcoming). Stratigraphic Thickness Calculator — companion manuscript. — Eq. T₈ = T₇ × cos(η/2) (equal-angle method).",
        "Builds on the Top-normal (T₇) formulation above."
      ]
    }
  ]
};

function _helpInstructionsForTopic(topic) {
  if (topic === "batch" || topic === "batch_web") {
    return {
      instructions: APP_INFO.batchInstructionsWeb,
      bestPractices: APP_INFO.batchBestPractices,
    };
  }
  return {
    instructions: APP_INFO.usageInstructions,
    bestPractices: APP_INFO.bestPractices,
  };
}

function helpDocumentationHtml(topic) {
  const esc = (s) => String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
  const { instructions, bestPractices } = _helpInstructionsForTopic(topic || "calculator");
  const paperLink = APP_INFO.paperUrl
    ? `<a href="${esc(APP_INFO.paperUrl)}" target="_blank" rel="noopener noreferrer">${esc(APP_INFO.paperLabel)}</a>`
    : `<span>${esc(APP_INFO.paperLabel)}</span>`;
  let html = "";
  html += "<h3>About</h3>";
  html += `<p><b>${esc(APP_INFO.appName)}</b> v${esc(APP_INFO.version)}</p>`;
  html += `<p>Implemented by ${esc(APP_INFO.implementers.join(", "))}.</p>`;
  html += `<p><a href="${esc(APP_INFO.repoUrl)}" target="_blank" rel="noopener noreferrer">${esc(APP_INFO.repoLabel)}</a> · ${paperLink}</p>`;
  html += "<h3>Instructions</h3><ol>";
  for (const step of instructions) {
    html += `<li>${esc(step)}</li>`;
  }
  html += "</ol>";
  html += `<p>${esc(bestPractices)}</p>`;
  html += "<h3>Model references</h3><p>Formulas in each tab are based on:</p><ul>";
  for (const entry of APP_INFO.modelReferences) {
    html += `<li><b>${entry.label}</b><ul>`;
    for (const ref of entry.references) {
      html += `<li>${ref}</li>`;
    }
    html += "</ul></li>";
  }
  html += "</ul>";
  html += "<h3>General references</h3><ul>";
  for (const ref of APP_INFO.generalReferences) {
    html += `<li>${ref}</li>`;
  }
  html += "</ul>";
  html += `<p>Released under the <a href="${esc(APP_INFO.licenseUrl)}" target="_blank" rel="noopener noreferrer">${esc(APP_INFO.licenseName)}</a>.</p>`;
  return html;
}

function helpDocumentationPlain(topic) {
  const { instructions, bestPractices } = _helpInstructionsForTopic(topic || "calculator");
  const lines = [
    `${APP_INFO.appName} v${APP_INFO.version}`,
    `Implemented by ${APP_INFO.implementers.join(", ")}.`,
    `${APP_INFO.repoLabel}: ${APP_INFO.repoUrl}`,
    APP_INFO.paperUrl ? `${APP_INFO.paperLabel}: ${APP_INFO.paperUrl}` : APP_INFO.paperLabel,
    "",
    "Instructions:",
  ];
  instructions.forEach((step, i) => lines.push(`  ${i + 1}. ${step}`));
  lines.push("", bestPractices, "", "Model references:");
  for (const entry of APP_INFO.modelReferences) {
    lines.push(`  ${entry.label}:`);
    for (const ref of entry.references) {
      lines.push(`    - ${ref.replace(/<[^>]+>/g, "")}`);
    }
  }
  lines.push("", "General references:");
  for (const ref of APP_INFO.generalReferences) {
    lines.push(`  - ${ref.replace(/<[^>]+>/g, "")}`);
  }
  lines.push("", `Released under the ${APP_INFO.licenseName}.`);
  return lines.join("\n");
}
