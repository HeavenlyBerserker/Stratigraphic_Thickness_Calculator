#!/usr/bin/env bash

set -euo pipefail

APP_MAIN="source/main.py"
LOGO_FILE="logo.png"

if [[ ! -f "$APP_MAIN" ]]; then
  echo "Error: $APP_MAIN not found. Run this script from project root."
  exit 1
fi

if [[ ! -f "$LOGO_FILE" ]]; then
  echo "Error: $LOGO_FILE not found. Put logo.png in project root."
  exit 1
fi

if ! command -v conda >/dev/null 2>&1; then
  echo "Error: conda command not found."
  echo "Install Miniconda/Anaconda and ensure conda is on PATH."
  exit 1
fi

OS_NAME="$(uname -s)"
APP_NAME="StratigraphicThicknessCalculator"
ADD_DATA_SEP=":"

case "$OS_NAME" in
  Linux*)
    APP_NAME="stratigraphic-thickness-calculator"
    ADD_DATA_SEP=":"
    ;;
  Darwin*)
    APP_NAME="StratigraphicThicknessCalculator"
    ADD_DATA_SEP=":"
    ;;
  MINGW*|MSYS*|CYGWIN*)
    APP_NAME="StratigraphicThicknessCalculator"
    ADD_DATA_SEP=";"
    ;;
  *)
    echo "Warning: unrecognized OS '$OS_NAME'. Using default app name."
    ;;
esac

echo "Using conda environment: geo_stc"
echo "Detected OS: $OS_NAME"
echo "Executable name: $APP_NAME"
echo "Bundling asset: $LOGO_FILE"

conda run -n geo_stc python -m pip install -r requirements.txt
conda run -n geo_stc pyinstaller \
  --noconfirm \
  --onefile \
  --windowed \
  --add-data "${LOGO_FILE}${ADD_DATA_SEP}." \
  --name "$APP_NAME" \
  "$APP_MAIN"

echo
echo "Build complete."
echo "Output is in dist/"
