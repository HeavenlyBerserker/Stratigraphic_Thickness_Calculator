"""Single source of truth for in-app Help & Documentation (desktop and web)."""

from __future__ import annotations

import html
import json
from typing import Any, Literal

APP_NAME = "Stratigraphic Thickness Calculator"
VERSION = "1.0.0"

IMPLEMENTERS = ["Hong Xu"]

REPO_URL = "https://github.com/HeavenlyBerserker/Stratigraphic_Thickness_Calculator"
REPO_LABEL = "GitHub repository"

# Set when the companion paper is published; None shows a “coming soon” label.
PAPER_URL: str | None = None
PAPER_LABEL = "Companion paper (link coming soon)"
PAPER_CITATION = (
    "Xu, H. (forthcoming). Stratigraphic Thickness Calculator — companion manuscript."
)

LICENSE_NAME = "MIT License"
LICENSE_URL = "https://opensource.org/licenses/MIT"

HelpTopic = Literal["calculator", "batch_desktop", "batch_web"]

USAGE_INSTRUCTIONS: list[str] = [
    "Choose the model that matches your geometry assumptions.",
    "Enter measured values and angles using the documented conventions in the README.",
    (
        "Optional: for uncertainty analysis, enter non-zero σ values to enable Monte "
        "Carlo outputs (leave σ = 0 for deterministic runs). On the web app, click the "
        "? icon; on desktop, hover over a σ box for a quick cheatsheet."
    ),
    "Review geometry warnings in fold models before final interpretation.",
    "Export results and plots when needed for reporting and auditability.",
]

BATCH_INSTRUCTIONS_DESKTOP: list[str] = [
    "Optionally download the blank template or the 16-row example workbook.",
    "Choose Monte Carlo plot format (PNG or SVG) for any wells with non-zero σ.",
    "Click Choose File to Batch Process and select an .xlsx workbook (one well per row).",
    "Click Batch Process, then choose where to save the results .xlsx file.",
    (
        "Wait for the run to finish. Progress appears in the status bar. "
        "Results are written to your chosen file; if any row used Monte Carlo, "
        "histogram and cumulative plots are saved in a sibling folder named "
        "{results_stem}_mc_plots."
    ),
    (
        "Review the batch log: green Success with ✅ means all rows OK; "
        "yellow warnings (⚠️) mean geometry warnings; red (❌) means one or "
        "more row errors (other rows still ran)."
    ),
]

BATCH_INSTRUCTIONS_WEB: list[str] = [
    "Optionally download the blank template or the 16-row example workbook.",
    "Choose Monte Carlo plot format (PNG or SVG) for any wells with non-zero σ.",
    "Click Choose File to Batch Process and select an .xlsx workbook (one well per row).",
    (
        "Click Batch Process. The browser downloads batch_results.xlsx automatically "
        "(you do not pick a save path first). If any row used Monte Carlo, a "
        "batch_results_mc_plots.zip file with histogram and cumulative plots also downloads."
    ),
    (
        "Review the batch log: green Success with ✅ means all rows OK; "
        "yellow warnings (⚠️) mean geometry warnings; red (❌) means one or "
        "more row errors (other rows still ran)."
    ),
]

BATCH_BEST_PRACTICES = (
    "Use the template column names (well_id, T, M, sigma_M, …). "
    "T must be 1–8 (or T1–T8). For T₁, leave beta2_deg and phid2_deg blank. "
    "Set σ = 0 for deterministic rows; set one or more σ > 0 to enable Monte Carlo "
    "for that well."
)

BEST_PRACTICES = (
    "For best results, use high-quality field or interpreted inputs "
    "(e.g., calibrated dip/azimuth measurements and validated structural picks)."
)

# Full bibliographic entries cited in the app (expand when the paper is published).
GENERAL_REFERENCES: list[str] = [
    (
        "Berg, R.R. (2011). Cross-validation of geometric models for calculating true "
        "stratigraphic thickness from wellbore data. "
        "<i>AAPG Bulletin</i>, 95(6), 975–992."
    ),
    (
        "Xu, H., Berg, R.R., et al. (2007, 2010). Concentric-fold thickness "
        "correction methods (see companion paper for full citations)."
    ),
    PAPER_CITATION,
]

# Which references ground each model tab / formula.
MODEL_REFERENCES: list[dict[str, Any]] = [
    {
        "id": "t1",
        "label": "T₁ — One-dip",
        "references": [
            f"{PAPER_CITATION} — Eq. T₁ (one-dip correction).",
        ],
    },
    {
        "id": "t2",
        "label": "T₂ — Average-vector",
        "references": [
            "Berg, R.R. (2011) — average dip-pole vector U<sub>av</sub> and "
            "T = M (U<sub>av</sub> · U<sub>b</sub>).",
        ],
    },
    {
        "id": "t3",
        "label": "T₃ — Average-thickness",
        "references": [
            f"{PAPER_CITATION} — Eq. T₃ (average of top and base bed projections).",
            "Uses the same U<sub>d</sub> · U<sub>b</sub> dot-product framework as Berg (2011).",
        ],
    },
    {
        "id": "t4",
        "label": "T₄ — Mixed Average",
        "references": [
            f"{PAPER_CITATION} — Eq. T₄ = (T₂ + T₃) / 2.",
            "Combines Berg (2011) average-vector and average-thickness methods.",
        ],
    },
    {
        "id": "t5",
        "label": "T₅ — Concentric Fold",
        "references": [
            "Xu, H., Berg, R.R., et al. (2007, 2010) — corrected β′₂, U′<sub>d2</sub>, "
            "N<sub>dc</sub>, and concentric-fold geometry.",
            (
                "Berg, R.R. (2011). Cross-validation of geometric models for calculating true "
                "stratigraphic thickness from wellbore data. "
                "<i>AAPG Bulletin</i>, 95(6), 975–992. — M′ borehole projection onto the fold plane."
            ),
        ],
    },
    {
        "id": "t6",
        "label": "T₆ — Plunging Concentric Fold",
        "references": [
            "Xu, H., Berg, R.R., et al. (2007, 2010) — plunging fold geometry "
            "(N<sub>dp</sub>, U<sub>c</sub>, α, γ).",
            (
                "Berg, R.R. (2011). Cross-validation of geometric models for calculating true "
                "stratigraphic thickness from wellbore data. "
                "<i>AAPG Bulletin</i>, 95(6), 975–992. — M′ borehole projection."
            ),
        ],
    },
    {
        "id": "t7",
        "label": "T₇ — Top-normal",
        "references": [
            f"{PAPER_CITATION} — Eq. T₇ (M measured normal to the top bed).",
            "Berg, R.R. (2011) — M′ projection; branch selection via S = N<sub>dp</sub> · U′<sub>b</sub>.",
        ],
    },
    {
        "id": "t8",
        "label": "T₈ — Equal-angle",
        "references": [
            f"{PAPER_CITATION} — Eq. T₈ = T₇ × cos(η/2) (equal-angle method).",
            "Builds on the Top-normal (T₇) formulation above.",
        ],
    },
]


def _paper_link_html() -> str:
    if PAPER_URL:
        safe = html.escape(PAPER_URL, quote=True)
        return (
            f'<a href="{safe}" target="_blank" rel="noopener noreferrer">'
            f"{html.escape(PAPER_LABEL)}</a>"
        )
    return f"<span>{html.escape(PAPER_LABEL)}</span>"


def _paper_link_plain() -> str:
    if PAPER_URL:
        return f"{PAPER_LABEL}: {PAPER_URL}"
    return PAPER_LABEL


def _instructions_for_topic(topic: HelpTopic) -> tuple[list[str], str]:
    if topic == "batch_desktop":
        return BATCH_INSTRUCTIONS_DESKTOP, BATCH_BEST_PRACTICES
    if topic == "batch_web":
        return BATCH_INSTRUCTIONS_WEB, BATCH_BEST_PRACTICES
    return USAGE_INSTRUCTIONS, BEST_PRACTICES


def help_documentation_html(topic: HelpTopic = "calculator") -> str:
    """Rich HTML for QTextBrowser / web Help dialog."""
    instructions, best = _instructions_for_topic(topic)
    parts: list[str] = [
        "<h3>About</h3>",
        f"<p><b>{html.escape(APP_NAME)}</b> v{html.escape(VERSION)}</p>",
        "<p>Implemented by "
        + html.escape(", ".join(IMPLEMENTERS))
        + ".</p>",
        "<p>"
        f'<a href="{html.escape(REPO_URL, quote=True)}" '
        f'target="_blank" rel="noopener noreferrer">{html.escape(REPO_LABEL)}</a>'
        " · "
        + _paper_link_html()
        + "</p>",
        "<h3>Instructions</h3>",
        "<ol>",
    ]
    for step in instructions:
        parts.append(f"<li>{html.escape(step)}</li>")
    parts.append("</ol>")
    parts.append(f"<p>{html.escape(best)}</p>")
    parts.append("<h3>Model references</h3>")
    parts.append("<p>Formulas in each tab are based on:</p>")
    parts.append("<ul>")
    for entry in MODEL_REFERENCES:
        parts.append(f"<li><b>{entry['label']}</b><ul>")
        for ref in entry["references"]:
            parts.append(f"<li>{ref}</li>")
        parts.append("</ul></li>")
    parts.append("</ul>")
    parts.append("<h3>General references</h3>")
    parts.append("<ul>")
    for ref in GENERAL_REFERENCES:
        parts.append(f"<li>{ref}</li>")
    parts.append("</ul>")
    parts.append(
        f'<p>Released under the <a href="{html.escape(LICENSE_URL, quote=True)}" '
        f'target="_blank" rel="noopener noreferrer">{html.escape(LICENSE_NAME)}</a>.</p>'
    )
    return "".join(parts)


def help_documentation_plain(topic: HelpTopic = "calculator") -> str:
    """Plain text fallback (e.g. browsers without &lt;dialog&gt;)."""
    instructions, best = _instructions_for_topic(topic)
    lines = [
        f"{APP_NAME} v{VERSION}",
        f"Implemented by {', '.join(IMPLEMENTERS)}.",
        f"{REPO_LABEL}: {REPO_URL}",
        _paper_link_plain(),
        "",
        "Instructions:",
    ]
    for i, step in enumerate(instructions, start=1):
        lines.append(f"  {i}. {step}")
    lines.extend(["", best, "", "Model references:"])
    for entry in MODEL_REFERENCES:
        lines.append(f"  {entry['label']}:")
        for ref in entry["references"]:
            plain_ref = (
                ref.replace("<sub>", "")
                .replace("</sub>", "")
                .replace("<i>", "")
                .replace("</i>", "")
            )
            lines.append(f"    - {plain_ref}")
    lines.extend(["", "General references:"])
    for ref in GENERAL_REFERENCES:
        plain_ref = (
            ref.replace("<sub>", "")
            .replace("</sub>", "")
            .replace("<i>", "")
            .replace("</i>", "")
        )
        lines.append(f"  - {plain_ref}")
    lines.append(f"\nReleased under the {LICENSE_NAME}.")
    return "\n".join(lines)


def to_js_object() -> dict[str, Any]:
    """JSON-serializable bundle for mobile/app-info.js generation."""
    return {
        "appName": APP_NAME,
        "version": VERSION,
        "implementers": IMPLEMENTERS,
        "repoUrl": REPO_URL,
        "repoLabel": REPO_LABEL,
        "paperUrl": PAPER_URL,
        "paperLabel": PAPER_LABEL,
        "paperCitation": PAPER_CITATION,
        "licenseName": LICENSE_NAME,
        "licenseUrl": LICENSE_URL,
        "usageInstructions": USAGE_INSTRUCTIONS,
        "batchInstructionsWeb": BATCH_INSTRUCTIONS_WEB,
        "bestPractices": BEST_PRACTICES,
        "batchBestPractices": BATCH_BEST_PRACTICES,
        "generalReferences": GENERAL_REFERENCES,
        "modelReferences": MODEL_REFERENCES,
    }


def to_js_file_content() -> str:
    """Generate mobile/app-info.js (auto-generated; do not edit by hand)."""
    payload = json.dumps(to_js_object(), indent=2, ensure_ascii=False)
    return f"""// Auto-generated from source/app_info.py — do not edit by hand.
// Regenerate: python scripts/generate_app_info_js.py

const APP_INFO = {payload};

function _helpInstructionsForTopic(topic) {{
  if (topic === "batch" || topic === "batch_web") {{
    return {{
      instructions: APP_INFO.batchInstructionsWeb,
      bestPractices: APP_INFO.batchBestPractices,
    }};
  }}
  return {{
    instructions: APP_INFO.usageInstructions,
    bestPractices: APP_INFO.bestPractices,
  }};
}}

function helpDocumentationHtml(topic) {{
  const esc = (s) => String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
  const {{ instructions, bestPractices }} = _helpInstructionsForTopic(topic || "calculator");
  const paperLink = APP_INFO.paperUrl
    ? `<a href="${{esc(APP_INFO.paperUrl)}}" target="_blank" rel="noopener noreferrer">${{esc(APP_INFO.paperLabel)}}</a>`
    : `<span>${{esc(APP_INFO.paperLabel)}}</span>`;
  let html = "";
  html += "<h3>About</h3>";
  html += `<p><b>${{esc(APP_INFO.appName)}}</b> v${{esc(APP_INFO.version)}}</p>`;
  html += `<p>Implemented by ${{esc(APP_INFO.implementers.join(", "))}}.</p>`;
  html += `<p><a href="${{esc(APP_INFO.repoUrl)}}" target="_blank" rel="noopener noreferrer">${{esc(APP_INFO.repoLabel)}}</a> · ${{paperLink}}</p>`;
  html += "<h3>Instructions</h3><ol>";
  for (const step of instructions) {{
    html += `<li>${{esc(step)}}</li>`;
  }}
  html += "</ol>";
  html += `<p>${{esc(bestPractices)}}</p>`;
  html += "<h3>Model references</h3><p>Formulas in each tab are based on:</p><ul>";
  for (const entry of APP_INFO.modelReferences) {{
    html += `<li><b>${{entry.label}}</b><ul>`;
    for (const ref of entry.references) {{
      html += `<li>${{ref}}</li>`;
    }}
    html += "</ul></li>";
  }}
  html += "</ul>";
  html += "<h3>General references</h3><ul>";
  for (const ref of APP_INFO.generalReferences) {{
    html += `<li>${{ref}}</li>`;
  }}
  html += "</ul>";
  html += `<p>Released under the <a href="${{esc(APP_INFO.licenseUrl)}}" target="_blank" rel="noopener noreferrer">${{esc(APP_INFO.licenseName)}}</a>.</p>`;
  return html;
}}

function helpDocumentationPlain(topic) {{
  const {{ instructions, bestPractices }} = _helpInstructionsForTopic(topic || "calculator");
  const lines = [
    `${{APP_INFO.appName}} v${{APP_INFO.version}}`,
    `Implemented by ${{APP_INFO.implementers.join(", ")}}.`,
    `${{APP_INFO.repoLabel}}: ${{APP_INFO.repoUrl}}`,
    APP_INFO.paperUrl ? `${{APP_INFO.paperLabel}}: ${{APP_INFO.paperUrl}}` : APP_INFO.paperLabel,
    "",
    "Instructions:",
  ];
  instructions.forEach((step, i) => lines.push(`  ${{i + 1}}. ${{step}}`));
  lines.push("", bestPractices, "", "Model references:");
  for (const entry of APP_INFO.modelReferences) {{
    lines.push(`  ${{entry.label}}:`);
    for (const ref of entry.references) {{
      lines.push(`    - ${{ref.replace(/<[^>]+>/g, "")}}`);
    }}
  }}
  lines.push("", "General references:");
  for (const ref of APP_INFO.generalReferences) {{
    lines.push(`  - ${{ref.replace(/<[^>]+>/g, "")}}`);
  }}
  lines.push("", `Released under the ${{APP_INFO.licenseName}}.`);
  return lines.join("\\n");
}}
"""
