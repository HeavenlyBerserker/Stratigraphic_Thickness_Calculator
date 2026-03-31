# Stratigraphic_Thickness_Calculator
Calculates true stratigraphic thickness using 3D borehole data.

## Windows Desktop App (PySide6)

Code lives in `source/` and provides tabs for:
- One-dip
- Two-dip
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
- Computed vectors:
  - `U_d1` (written as `U<sub>d1</sub>` in the app): downward dip-pole unit vector
  - `Uᵦ` (written as `U<sub>b</sub>` in the app): borehole direction unit vector

## Run Locally (Conda: `geo_stc`)

This project assumes your default Conda environment is `geo_stc`.

```powershell
conda activate geo_stc
pip install -r requirements.txt
python -m source.main
```

## Build Portable Executables (Single Script)

Use the same script on all platforms:
- `build_executable.sh`

This script:
- Uses Conda env `geo_stc`
- Installs `requirements.txt`
- Runs PyInstaller with `--onefile --windowed`
- Detects OS and uses the correct executable name

Build on each target OS (cross-compiling is generally not supported by PyInstaller).

### Windows

Run from **Git Bash** or **WSL**:

```bash
bash build_executable.sh
```

Built artifact:
- `dist/StratigraphicThicknessCalculator.exe`

### Linux

```bash
bash build_executable.sh
```

Built artifact:
- `dist/stratigraphic-thickness-calculator`

### macOS

```bash
bash build_executable.sh
```

Built artifact:
- `dist/StratigraphicThicknessCalculator`
