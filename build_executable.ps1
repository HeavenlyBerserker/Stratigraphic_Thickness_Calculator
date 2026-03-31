$ErrorActionPreference = "Stop"

$appMain = "source/main.py"
$logoFile = "logo.png"
$appName = "StratigraphicThicknessCalculator"

if (-not (Test-Path $appMain)) {
    throw "Error: $appMain not found. Run this script from project root."
}

if (-not (Test-Path $logoFile)) {
    throw "Error: $logoFile not found. Put logo.png in project root."
}

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "Error: conda command not found. Install Miniconda/Anaconda and ensure conda is on PATH."
}

Write-Host "Using conda environment: geo_stc"
Write-Host "Executable name: $appName"
Write-Host "Bundling asset: $logoFile"

conda run -n geo_stc python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed."
}

conda run -n geo_stc python -m PyInstaller `
    --noconfirm `
    --onefile `
    --windowed `
    --icon "$logoFile" `
    --add-data "$logoFile;." `
    --name "$appName" `
    "$appMain"

if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

$distExe = "dist/$appName.exe"
$rootExe = "./$appName.exe"
if (-not (Test-Path $distExe)) {
    throw "Expected built executable not found at $distExe."
}
Copy-Item -Path $distExe -Destination $rootExe -Force

Write-Host ""
Write-Host "Build complete."
Write-Host "Output copied to: $rootExe"
Write-Host "Original remains in: $distExe"
