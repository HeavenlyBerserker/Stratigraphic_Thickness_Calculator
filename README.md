# Stratigraphic_Thickness_Calculator
Calculates true stratigraphic thickness using 3D borehole data.

## Windows Desktop App (PySide6)

**Input angle conventions:** dip azimuths φ and wellbore azimuth φ_b are clockwise from north with **0° ≤ φ ≤ 360°**; bed dips β with **0° ≤ β ≤ 90°**; borehole inclination δ is the angle from vertical down with **0° ≤ δ ≤ 180°**. Intermediate angles in the fold models satisfy **0° ≤ β′ ≤ 90°**, **0° < α < 90°**, **0° < γ < 90°**, and **0° < η < 180°** where those quantities appear.

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
  - `U_d1` (written as `U<sub>d1</sub>` in the app): downward dip-pole unit vector
  - `U_d2` (written as `U<sub>d2</sub>` in the app): downward dip-pole unit vector at lower contact
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
