# Build an Ebitengine WebAssembly bundle with a Go-version-aware wasm_exec.js copy.
param(
    [string]$ProjectDir = ".",
    [string]$DistDir = "dist",
    [string]$Package = "./cmd/game",
    [string]$OutputName = "game.wasm"
)

$ErrorActionPreference = "Stop"
$prevGOOS = $env:GOOS
$prevGOARCH = $env:GOARCH
Push-Location $ProjectDir
try {
    New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

    $env:GOOS = "js"
    $env:GOARCH = "wasm"
    go build -trimpath -ldflags="-s -w" -o (Join-Path $DistDir $OutputName) $Package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $goroot = go env GOROOT
    $goversion = go env GOVERSION
    # Extract major and minor digits, ignoring suffixes like rc1 or beta1.
    $major = 0
    $minor = 0
    if ($goversion -match 'go(\d+)\.(\d+)') {
        $major = [int]$Matches[1]
        $minor = [int]$Matches[2]
    }

    if ($major -gt 1 -or ($major -eq 1 -and $minor -ge 24)) {
        $wasmDir = Join-Path $goroot "lib\wasm"
    } else {
        $wasmDir = Join-Path $goroot "misc\wasm"
    }

    Copy-Item (Join-Path $wasmDir "wasm_exec.js") (Join-Path $DistDir "wasm_exec.js")

    if (Test-Path "web\index.html") {
        Copy-Item "web\index.html" (Join-Path $DistDir "index.html")
    } elseif (Test-Path "templates\web\index.html") {
        Copy-Item "templates\web\index.html" (Join-Path $DistDir "index.html")
    }

    Write-Host "WASM build complete in $DistDir"
}
finally {
    # Restore GOOS/GOARCH to their prior values. A null value clears a variable that was unset.
    [Environment]::SetEnvironmentVariable("GOOS", $prevGOOS, "Process")
    [Environment]::SetEnvironmentVariable("GOARCH", $prevGOARCH, "Process")
    Pop-Location
}
