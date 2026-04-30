# Stratigraphic_Thickness_Calculator
Calculates true stratigraphic thickness using 3D borehole data, with both desktop and mobile/web interfaces that support result export workflows (including figures/plots).
The web app can be accessed at [https://heavenlyberserker.github.io/Stratigraphic_Thickness_Calculator/mobile/index.html](https://heavenlyberserker.github.io/Stratigraphic_Thickness_Calculator/mobile/index.html) in computer or phone browsers; it can be used when internet service is available or when the site is already cached on the device. The desktop app can be used anywhere after download/install, without requiring active internet access.

This software is based on and intended as a companion to a coming-soon paper ([paper link coming soon](#)). Use the **Index** below as a navigation guide: go to **Windows Desktop App** for model formulas/conventions and outputs, **Run Locally** for desktop setup, **Build Portable Executables** for release binaries, **Mobile App (PWA)** for browser deployment/use, and **Software Guidelines** for methodological guidance, assumptions, limits, and best practices.

## Index

- [README (Top)](#stratigraphic_thickness_calculator)
- [Windows Desktop App (PySide6)](#windows-desktop-app-pyside6)
- [Run Locally (Conda: `geo_stc`)](#run-locally-conda-geo_stc)
- [Build Portable Executables](#build-portable-executables)
- [Mobile App (PWA)](#mobile-app-pwa)
- [Software Guidelines](#software-guidelines)

## Windows Desktop App (PySide6)

**Input angle conventions:** dip azimuths φ and wellbore azimuth φ_b are clockwise from north with **0° ≤ φ ≤ 360°**; bed dips β with **0° ≤ β ≤ 90°**; borehole inclination δ is the angle from vertical down with **0° ≤ δ ≤ 180°**. Intermediate angles in the fold models satisfy **0° ≤ β′ ≤ 90°**, **0° < α < 180°**, **0° < γ < 180°**, and **0° < η < 180°** where those quantities appear.

Code lives in `source/` and provides tabs for:
- One-dip
- Average-vector
- Average-thickness
- Mixed Average
- Concentric Fold
- Plunging Concentric Fold
- Top-normal
- Equal-angle (T₈)

Each tab has:
- Input section
- Output section
- Stdout/Stderr section at the bottom

Currently implemented:
- One-dip model with formula:
  `T₁ = M(cosδ - sinδ(cos(φd₁ - φᵦ))tanβ₁)cosβ₁`
- Average-vector model (Berg, 2011) with:
  - `Uav = (Ud₁ + Ud₂) / ||Ud₁ + Ud₂||`
  - `T₂ = M × (Uav • Uᵦ)`
- Average-thickness model with:
  - `T₃ = (M × Ud₁ • Uᵦ + M × Ud₂ • Uᵦ) / 2`
  - `T₃ = M × (Ud₁ + Ud₂) • Uᵦ / 2`
- Mixed Average model with:
  - `T₄ = (T₂ + T₃) / 2`
- Concentric Fold model (Xu et al., 2007, 2010; bed azimuth fixed along strike; Berg, 2011 for M’):
  - `β'₂ = arctan(tanβ₂ |cos(φd₁ - φd₂)|)`
  - Smallest `|φd₁ - φd₂|` ≤ 90°: `U'd₂` from `φd₁`; else from `φd₁ + 180°`; `U_d1` as before with `β₁`
  - `N_dc = (U_d1 × U'd₂) / ||U_d1 × U'd₂||`; `M' = ||M_b - N_dc(N_dc · M_b)||` with `M_b = M U_b`
  - `U_c = (U_d1 - U'd₂) / ||U_d1 - U'd₂||`; `γ = arccos(U_c · U'_b)`, `η = arccos(U_d1 · U'd₂)`, `α = 90° - η/2` where `U'_b = M'_b / ||M'_b||`
  - `T₅ = M' sinγ / cos(η/2)` (equiv. `M' sinγ / sinα` with `sinα = cos(η/2)`)
- Plunging Concentric Fold model (bed azimuths may differ; no base azimuth correction):
  - `N_dp = (Ud₁ × Ud₂) / ||Ud₁ × Ud₂||`; `M' = ||M_b - N_dp(N_dp · M_b)||` with `M_b = M U_b`
  - `U_c = (U_d1 - U_d2) / ||U_d1 - U_d2||`; `γ = arccos(U_c · U'_b)`, `α = arccos(U_d1 · U_c)` with `U'_b = M'_b / ||M'_b||`
  - `T₆ = M' (sinγ / sinα)`
- Top-normal model (`M` measured normal to the top bed; Berg, 2011):
  - Same `N_dp`, `M'`, `U'_b` as Berg (2011) projection; `α = arccos(U_d1 · U'_b)`, `η = arccos(U_d1 · U_d2)`
  - **Top-normal** (paper `T₇`): `S = N_dp · U'_b`; if `S < 0`: `M' cos(α − η) / cos(η)`; if `S ≥ 0`: `M' cos(α + η) / cos(η)` (also `M' (sinγ / sinμ)`)
- Equal-angle (`T₈`) tab: same inputs as Top-normal; `T₈ =` Top-normal `× cos(η/2)` (equal-angle method)
- Computed vectors:
  - `U_d1` (written as `U<sub>d1</sub>` in the app): downward dip-pole unit vector at top contact (`beta1`, `phi_d1`)
  - `U_d2` (written as `U<sub>d2</sub>` in the app): downward dip-pole unit vector at lower contact (`beta2`, `phi_d2`)
  - `U_av` (written as `U<sub>av</sub>` in the app): normalized average dip-pole vector
  - `Uᵦ` (written as `U<sub>b</sub>` in the app): borehole direction unit vector

## Run Locally (Conda: `geo_stc`)

This project assumes your default Conda environment is `geo_stc`.

```powershell
conda activate geo_stc
pip install -r requirements.txt
python -m source.main
```

## Build Portable Executables

Scripts:
- Windows (PowerShell): `build_executable.ps1`
- Linux/macOS (shell): `build_executable.sh`

This script:
- Uses Conda env `geo_stc`
- Installs `requirements.txt`
- Runs PyInstaller with `--onefile --windowed --icon logo.png`
- Detects OS and uses the correct executable name
- Copies the built executable from `dist/` to the project root

Build on each target OS (cross-compiling is generally not supported by PyInstaller).

### Windows (PowerShell)

Run in PowerShell from project root:

```powershell
.\build_executable.ps1
```

Built artifact:
- `StratigraphicThicknessCalculator.exe` (project root)

### Linux

```bash
bash build_executable.sh
```

Built artifact:
- `stratigraphic-thickness-calculator` (project root)

### macOS

```bash
bash build_executable.sh
```

Built artifact:
- `StratigraphicThicknessCalculator` (project root)

## Mobile App (PWA)

`mobile/index.html` is now fully static and runs computations in-browser with Pyodide.

### Test mobile app on PC

```powershell
conda activate geo_stc
pip install -r requirements.txt
python -m http.server 8787
```

Then open `http://localhost:8787/mobile/index.html` in your browser.
Mobile Monte Carlo uses 2,500 samples for faster response on phone-class devices.

### Test on Android / iOS (same network, no app store deploy)

1. Start server on PC:

```powershell
python -m http.server 8787
```

2. Find your PC LAN IP (for example `192.168.1.25`).
3. On phone connected to the same Wi-Fi, open:
   - `http://<PC-LAN-IP>:8787/mobile/index.html`
4. Optional: use browser "Add to Home Screen" to install as PWA.

## Software Guidelines

### About This Software Package

This software package provides a full set of stratigraphic-thickness workflows for dipping and folded beds, including one-dip, average-vector, average-thickness, mixed-average, concentric-fold, plunging-fold, top-normal, and equal-angle methods. It includes:

- A full-featured desktop app (PySide6) with exports (Excel, MC plot PNG/SVG) and detailed outputs.
- A static mobile/web app (PWA) that runs calculations in-browser using the same model logic from `source/models.py` via Pyodide.

The software is designed for practical geology and petroleum/mining workflows where true stratigraphic thickness is needed for mapping, planning, and volumetric interpretation.

### Why These Calculations Matter

Accurate thickness correction is central to:

- Resource and reserve estimation
- Structural interpretation and correlation
- Well planning and risk reduction
- Better consistency between field measurements and subsurface models

Apparent-thickness-only workflows can overstate or understate true layer thickness, especially in moderate-to-steep dip settings and folded geometries.

### How To Use It Correctly

1. Choose the model that matches your geometry assumptions.
2. Enter measured values and angles using the documented conventions in this README.
3. Optional: for uncertainty analysis, enter non-zero `σ` values to enable Monte Carlo outputs (leave `σ = 0` for deterministic runs). Click the `?` icon for a quick cheatsheet of what to do with `σ`.
4. Review geometry warnings in fold models before final interpretation.
5. Export results/plots when needed for reporting and auditability.

For best results, use high-quality field or interpreted inputs (e.g., calibrated dip/azimuth measurements and validated structural picks).

### Model Scope, Assumptions, and Limits

- Models assume idealized geometric conditions documented in each formula section.
- Folded-bed methods are sensitive to angle quality and model selection.
- The mobile app is intended for accessible field/quick use; desktop remains the full-featured workflow.
- Results are computational aids and should be validated against full geologic context (cross-sections, maps, cores/logs, seismic interpretation, and engineering constraints).

### Monte Carlo and Uncertainty Guidance

- Use `σ = 0` for deterministic runs.
- Use non-zero `σ` for uncertainty propagation.
- Desktop Monte Carlo uses higher sample counts; mobile uses 2,500 samples for responsiveness.
- Treat Monte Carlo distributions as input-quality dependent; poor inputs produce misleading confidence.

### Recommended Best Practices

- Keep units consistent through your workflow.
- Verify dip/azimuth domains and direction conventions before calculation.
- Cross-check multiple models when geometry is ambiguous.
- Preserve exported outputs as part of interpretation records.

### Intended Users and Purpose

This package is intended for students, geoscientists, engineers, and technical teams who need transparent, repeatable stratigraphic-thickness calculations across desktop and browser environments.

The purpose is to bridge field/interpretation measurements and quantitative thickness correction with scientifically grounded, reproducible computations.
