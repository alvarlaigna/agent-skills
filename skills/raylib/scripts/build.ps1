# Build a raylib desktop project with CMake.
param(
    [string]$ProjectDir = ".",
    [string]$BuildDir = "build",
    [string]$BuildType = "Release"
)

$ErrorActionPreference = "Stop"
Push-Location $ProjectDir
try {
    cmake -S . -B $BuildDir -DCMAKE_BUILD_TYPE=$BuildType
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    cmake --build $BuildDir
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Build complete in $BuildDir"
    Write-Host "Run from the directory that contains resources/ if your game loads relative assets."
}
finally {
    Pop-Location
}
