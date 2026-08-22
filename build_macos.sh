#!/usr/bin/env bash

set -euo pipefail

SPEC_FILE="source/pysidedeploy.spec"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "Error: build_macos.sh must be run on macOS."
  exit 1
fi

if [[ ! -f "$SPEC_FILE" ]]; then
  echo "Error: $SPEC_FILE not found. Run this script from the project root."
  exit 1
fi

if ! command -v pyside6-deploy >/dev/null 2>&1; then
  echo "Error: pyside6-deploy not found. Install PySide6 in the active Python environment:"
  echo "  pip install -r requirements.txt"
  exit 1
fi

if command -v conda >/dev/null 2>&1; then
  ACTIVE_ENV="${CONDA_DEFAULT_ENV:-}"
  if [[ -n "$ACTIVE_ENV" && "$ACTIVE_ENV" != "geo_stc" ]]; then
    echo "Warning: active conda environment is '$ACTIVE_ENV' (not geo_stc). Proceeding anyway."
  elif [[ -z "$ACTIVE_ENV" ]]; then
    echo "Warning: no active conda environment detected. Proceeding with current Python environment."
  else
    echo "Using conda environment: geo_stc"
  fi
else
  echo "Warning: conda command not found. Proceeding with current Python environment."
fi

echo "Installing/updating Python dependencies..."
python -m pip install -r requirements.txt

echo "Building macOS .app bundle with pyside6-deploy..."
(
  cd source
  pyside6-deploy -c pysidedeploy.spec
)

APP_BUNDLE="source/Stratigraphic_Thickness_Calculator_MacOS.app"
if [[ ! -d "$APP_BUNDLE" ]]; then
  echo "Error: expected app bundle not found at $APP_BUNDLE"
  exit 1
fi

echo
echo "Build complete."
echo "App bundle: $APP_BUNDLE"
echo "Open with: open \"$APP_BUNDLE\""
