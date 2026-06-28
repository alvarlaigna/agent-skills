# Build desktop release binaries for common targets.
param(
    [string]$ProjectDir = ".",
    [string]$DistDir = "dist",
    [string]$Package = "./cmd/game",
    [string]$Name = "game"
)

$ErrorActionPreference = "Stop"
$prevGOOS = $env:GOOS
$prevGOARCH = $env:GOARCH
Push-Location $ProjectDir
try {
    New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

    $env:GOOS = "windows"; $env:GOARCH = "amd64"
    go build -trimpath -ldflags="-s -w -H=windowsgui" -o (Join-Path $DistDir "$Name.exe") $Package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $env:GOOS = "linux"; $env:GOARCH = "amd64"
    go build -trimpath -ldflags="-s -w" -o (Join-Path $DistDir $Name) $Package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $env:GOOS = "darwin"; $env:GOARCH = "arm64"
    go build -trimpath -ldflags="-s -w" -o (Join-Path $DistDir "${Name}_darwin_arm64") $Package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    Write-Host "Release builds written to $DistDir"
}
finally {
    # Restore GOOS/GOARCH to their prior values. A null value clears a variable that was unset.
    [Environment]::SetEnvironmentVariable("GOOS", $prevGOOS, "Process")
    [Environment]::SetEnvironmentVariable("GOARCH", $prevGOARCH, "Process")
    Pop-Location
}
