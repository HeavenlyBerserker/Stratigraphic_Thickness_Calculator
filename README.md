# Stratigraphic_Thickness_Calculator
Calculates true stratigraphic thickness using 3D borehole data. Two versions are available:

**The Web App:** Use [Web App Link](https://heavenlyberserker.github.io/Stratigraphic_Thickness_Calculator/mobile/index.html) to access and run the app directly in computer or phone browsers. *On mobile, you can use your browser's "Add to Home Screen" option to install it like an app for faster access and offline/cached use.*

**The Desktop App:** Use the [latest GitHub release](https://github.com/HeavenlyBerserker/Stratigraphic_Thickness_Calculator/releases/latest) to download portable desktop binaries for Windows, macOS, and Linux. The desktop app can be used anywhere after download, without requiring active internet access. Linux note: the Ubuntu build is generally intended for modern glibc-based Linux distributions (including Ubuntu/Debian families and many others), but it is not guaranteed on every Linux variant (for example Alpine/musl or much older glibc systems).

This software is based on and intended as a companion to a coming-soon paper ([paper link coming soon](#)). Most users should use either the hosted web app via **Web App Link** or downloadable binaries from the **latest GitHub release**. The **Build Desktop App from Source** and **Developing on Mobile App (PWA)** sections are intended for code-savvy users who want to inspect/modify code, run from source, or build release artifacts themselves.

**Note for editors.** The repo holds **individual source files** (not a zip-only submission). The README covers purpose, how to run the apps, an [example run](#example-run-and-test), the [MIT license](LICENSE), and optional [`examples/quick_test_models.py`](examples/quick_test_models.py) for developers.

**Note for reviewers.** (1) [Download and open](#download-and-open-the-software) the **web** and **desktop** apps. (2) Follow [Example run and test](#example-run-and-test). That is enough to check results against the paper; see the [Index](#index) for license and other sections if needed.

## Index

- [README (Top)](#stratigraphic_thickness_calculator)
- [Download and open the software](#download-and-open-the-software)
- [Example run and test](#example-run-and-test)
- [License](#license)
- [Software Guidelines](#software-guidelines)
  - [Instructions](#instructions)
  - [About This Software Package](#about-this-software-package)
  - [Why These Calculations Matter](#why-these-calculations-matter)
  - [Model Scope, Assumptions, and Limits](#model-scope-assumptions-and-limits)
  - [Monte Carlo and Uncertainty Guidance](#monte-carlo-and-uncertainty-guidance)
  - [Recommended Best Practices](#recommended-best-practices)
  - [Intended Users and Purpose](#intended-users-and-purpose)
- [Developing on Mobile App (PWA)](#developing-on-mobile-app-pwa)
- [Build Desktop App from Source](#build-desktop-app-from-source)
  - [Windows Desktop App (PySide6)](#windows-desktop-app-pyside6)
  - [Run Locally (Conda: `geo_stc`)](#run-locally-conda-geo_stc)
  - [Build Portable Executables](#build-portable-executables)
    - [Windows (PowerShell)](#windows-powershell)
    - [Linux](#linux)
    - [macOS](#macos)

## Download and open the software

**Web app (browser, no install)**

1. Open the [Web App Link](https://heavenlyberserker.github.io/Stratigraphic_Thickness_Calculator/mobile/index.html) in a desktop or mobile browser.
2. Wait for the page to finish loading (the **Calculate** button becomes active when the in-browser Python runtime is ready).
3. On a phone or tablet, you can use the browser’s **Add to Home Screen** option for quicker access and cached offline use after the first visit.

**Desktop app (offline executable)**

1. Download the build for your operating system from the [latest GitHub release](https://github.com/HeavenlyBerserker/Stratigraphic_Thickness_Calculator/releases/latest).
2. Run the executable (`StratigraphicThicknessCalculator.exe` on Windows, `stratigraphic-thickness-calculator` on Linux, `StratigraphicThicknessCalculator` on macOS). No installer is required for the portable builds.
3. Linux note: the Ubuntu build targets modern glibc-based distributions; it may not run on Alpine/musl or very old glibc systems.

**From source (developers)**

- Desktop: see [Run Locally (Conda: `geo_stc`)](#run-locally-conda-geo_stc) → `python -m source.main`.
- Web/PWA locally: see [Developing on Mobile App (PWA)](#developing-on-mobile-app-pwa) → serve `mobile/index.html` over HTTP.

## Example run and test

These steps support **manual checks** that the calculators match the companion paper and give **coherent** results. **Please try both the web app and the desktop app** when you can; they share the same model logic (`source/models.py`), and running both checks the hosted PWA and the release build.

### A. Deterministic run with default inputs

Perform this on **web** and **desktop** (see [Download and open the software](#download-and-open-the-software)).

1. Open the app and select **One-dip (T₁)** (or any model you are comparing with the paper).
2. Leave the pre-filled default values unchanged (for T₁: **M = 100**, **δ = 20°**, **φᵦ = 120°**, **β = 15°**, **φd = 140°**; all **σ = 0**).
3. Click **Calculate**.
4. Record **T** and the displayed unit vectors (**U**d, **U**b, etc.).

**Expected check for T₁ defaults:** **T₁ ≈ 82.449** on both platforms. Compare with the paper’s worked example or formula for the same inputs, if provided.

Repeat on other tabs (T₂–T₈) with their defaults when verifying those methods against the manuscript.

### B. Uncertainty (Monte Carlo) with non-zero σ

Again, try this on **both web and desktop** when possible.

1. Set a small non-zero **σ** on one or more inputs (e.g. **σ = 1** on **M**; angle **σ** often **0.1°** on desktop; on the web app, **M** uses σ step **1**, other fields **0.1**).
2. Click **Calculate** again.
3. Confirm that a **Monte Carlo** section appears (mean, percentiles, histogram where supported).

**Monte Carlo note:** Each run uses random sampling, so **percentiles and plots will not be identical from run to run**, even with the same inputs. Means and spreads should still be **close** between runs and **similar in order of magnitude** between web and desktop for the same σ (the web app uses fewer samples than desktop for speed). If means diverge strongly between platforms with identical inputs, report the model tab and σ settings.

4. Change **σ** or a dip angle and recalculate; the distribution should shift in a direction consistent with the input change (e.g. larger thickness uncertainty if **σ(M)** increases).

### C. What to verify

We invite reviewers and readers to confirm:

1. **Agreement with the paper** — deterministic **T** values and intermediate quantities (where shown) match the equations and any worked examples in the manuscript for the same inputs.
2. **Coherence** — results stay physically plausible (e.g. **T** positive for benign geometries, fold models respect stated angle domains, Monte Carlo spreads reflect input **σ**, geometry warnings appear when fold assumptions are strained).

If you find a discrepancy, note the **model tab**, **exact inputs**, **σ** settings, and **web vs desktop** so it can be reproduced from this repository.

### D. Automated computation check (optional, advanced)

Not required for a paper review. Optional for developers or anyone who wants a command-line sanity check without opening the apps: [`examples/quick_test_models.py`](examples/quick_test_models.py) runs **T₁–T₈** at web defaults and Monte Carlo on **T₁** and **T₂** with **σ(M) = 1** (fixed random seed; mean and percentiles checked within tolerance). From the repository root, after `pip install -r requirements.txt`:

```bash
python examples/quick_test_models.py
```

Exit code **0** means the check passed. It is included mainly to satisfy common “example script in the repository” expectations; the interactive steps in A–C are the meaningful verification.

## License

This project is released under the **[MIT License](LICENSE)**.

The MIT License is a **permissive open-source** license: you may use, copy, modify, merge, publish, distribute, sublicense, and sell copies of the software, subject only to including the **copyright notice and license text** in copies or substantial portions. There is no copyleft requirement to open-source your own derivative works.

**If you redistribute this software or embed it in another product**, please **explicitly reference the MIT License** and retain the copyright notice (see the full text in [`LICENSE`](LICENSE)). Third-party use is otherwise governed by that file alone; this README is not a substitute for the legal text.

## Software Guidelines

### Instructions

1. Choose the model that matches your geometry assumptions.
2. Enter measured values and angles using the documented conventions in this README.
3. Optional: for uncertainty analysis, enter non-zero `σ` values to enable Monte Carlo outputs (leave `σ = 0` for deterministic runs). Click the `?` icon in the web app or hover over a `σ`value box for a quick cheatsheet of what to do with `σ`.
4. Review geometry warnings in fold models before final interpretation.
5. Export results/plots when needed for reporting and auditability.

For best results, use high-quality field or interpreted inputs (e.g., calibrated dip/azimuth measurements and validated structural picks).

### About This Software Package

This software package provides a full set of stratigraphic-thickness workflows for dipping and folded beds, including one-dip, average-vector, average-thickness, mixed-average, concentric-fold, plunging-fold, top-normal, and equal-angle methods. It includes:

- A full-featured desktop app (PySide6).
- A static mobile/web app (PWA) that runs calculations in-browser using the same model logic from `source/models.py` via Pyodide.

The software is designed for practical geology and petroleum/mining workflows where true stratigraphic thickness is needed for mapping, planning, and volumetric interpretation.

### Why These Calculations Matter

Accurate thickness correction is central to:

- Resource and reserve estimation
- Structural interpretation and correlation
- Well planning and risk reduction
- Better consistency between field measurements and subsurface models

Apparent-thickness-only workflows can overstate or understate true layer thickness, especially in moderate-to-steep dip settings and folded geometries.

### Model Scope, Assumptions, and Limits

- Models assume idealized geometric conditions documented in each formula section.
- Folded-bed methods are sensitive to angle quality and model selection.
- The mobile app is intended for accessible field/quick use; desktop remains the full-featured workflow.
- Results are computational aids and should be validated against full geologic context (cross-sections, maps, cores/logs, seismic interpretation, and engineering constraints).

### Monte Carlo and Uncertainty Guidance

- Use `σ = 0` for deterministic runs.
- Use non-zero `σ` for uncertainty propagation.
- Desktop Monte Carlo uses 10K samples; mobile uses 2,500 samples for responsiveness.
- Treat Monte Carlo distributions as input-quality dependent; poor inputs produce misleading confidence.

### Recommended Best Practices

- Keep units consistent through your workflow.
- Verify dip/azimuth domains and direction conventions before calculation.
- Cross-check multiple models when geometry is ambiguous.
- Preserve exported outputs as part of interpretation records.

### Intended Users and Purpose

This package is intended for students, geoscientists, engineers, and technical teams who need transparent, repeatable stratigraphic-thickness calculations across desktop and browser environments.

The purpose is to bridge field/interpretation measurements and quantitative thickness correction with scientifically grounded, reproducible computations.

## Developing on Mobile App (PWA)

A **PWA** (**P**rogressive **W**eb **A**pp) is a website that behaves like a lightweight installable app: you run it in the browser, and on phones or tablets you can often use **Add to Home Screen** (or similar) to pin it with an icon and open it full screen, without going through an app store. It is still served as ordinary web pages and assets.

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

## Build Desktop App from Source

This section is for developers and technical users who want to run the app from source code, inspect implementation details, or produce release binaries.

If you only want to use the calculator, prefer:
- Mobile web app (no install): [Web App Link](https://heavenlyberserker.github.io/Stratigraphic_Thickness_Calculator/mobile/index.html)
- Desktop binaries from GitHub Releases [latest GitHub release](https://github.com/HeavenlyBerserker/Stratigraphic_Thickness_Calculator/releases/latest)

### Windows Desktop App (PySide6)

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

### Run Locally (Conda: `geo_stc`)

Conda is a package and environment manager for Python that helps install compatible dependencies in isolated environments.

If Conda is not installed, install one of:
- Miniconda: [https://docs.conda.io/en/latest/miniconda.html](https://docs.conda.io/en/latest/miniconda.html)
- Anaconda Distribution: [https://www.anaconda.com/download](https://www.anaconda.com/download)

Then create and use a dedicated Conda environment named `geo_stc`:

```powershell
conda create -n geo_stc python=3.12 -y
conda activate geo_stc
pip install -r requirements.txt
python -m source.main
```

If you already maintain other Conda environments, you can install `requirements.txt` into one of those instead (if you are comfortable mixing project dependencies in that environment).

If you prefer not to use Conda, you can run with a standard Python virtual environment (`venv`) instead.

Windows (PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m source.main
```

Linux/macOS (bash):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m source.main
```

### Build Portable Executables

Scripts:
- Windows (PowerShell): `build_executable.ps1`
- Linux/macOS (shell): `build_executable.sh`

This script:
- Uses the currently active Python environment (Conda or `venv`)
- Warns if a non-`geo_stc` Conda environment is active, but does not block builds
- Installs `requirements.txt`
- Runs PyInstaller with `--onefile --windowed --icon logo.png`
- Detects OS and uses the correct executable name
- Copies the built executable from `dist/` to the project root

Build on each target OS (cross-compiling is generally not supported by PyInstaller).

#### Windows (PowerShell)

Run in PowerShell from project root:

```powershell
.\build_executable.ps1
```

Built artifact:
- `StratigraphicThicknessCalculator.exe` (project root)

#### Linux

```bash
bash build_executable.sh
```

Built artifact:
- `stratigraphic-thickness-calculator` (project root)

#### macOS

```bash
bash build_executable.sh
```

Built artifact:
- `StratigraphicThicknessCalculator` (project root)
