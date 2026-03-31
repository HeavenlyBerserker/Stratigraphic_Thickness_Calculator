# Stratigraphic_Thickness_Calculator
Calculates true stratigraphic thickness using 3D borehole data.

## Windows Desktop App (PySide6)

Code lives in `source/` and provides tabs for:
- One-dip
- Average-vector
- Average-thickness
- Mixed Average
- Concentric Fold
- Plunging Concentric Fold

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
  - `T₄ = T₂ + T₃`
- Concentric Fold model with:
  - `β'₂ = arctan(tanβ₂ cos(φd₁ - φd₂))`
  - `T₅ = M' (sinγ / sinα)`
- Plunging Concentric Fold model (no dip-azimuth correction; use `Ud₁`, `Ud₂` directly):
  - `N_dp = (Ud₁ × Ud₂) / ||Ud₁ × Ud₂||`
  - `T₅ = M' (sinγ / sinα)` with `γ`, `α` from `Ud₁`, `Ud₂`, and projected `M'b`
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
