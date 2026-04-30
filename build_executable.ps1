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

if (Get-Command conda -ErrorAction SilentlyContinue) {
    $activeEnv = $env:CONDA_DEFAULT_ENV
    if ($activeEnv -and $activeEnv -ne "geo_stc") {
        Write-Warning "Active conda environment is '$activeEnv' (not geo_stc). Proceeding anyway."
    } elseif (-not $activeEnv) {
        Write-Warning "No active conda environment detected. Proceeding with current Python environment."
    } else {
        Write-Host "Using conda environment: geo_stc"
    }
} else {
    Write-Warning "conda command not found. Proceeding with current Python environment."
}

Write-Host "Executable name: $appName"
Write-Host "Bundling asset: $logoFile"

python -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    throw "Dependency installation failed."
}

python -m PyInstaller `
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
