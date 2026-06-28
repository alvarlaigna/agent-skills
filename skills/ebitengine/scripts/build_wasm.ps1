# Build an Ebitengine WebAssembly bundle with a Go-version-aware wasm_exec.js copy.
param(
    [string]$ProjectDir = ".",
    [string]$DistDir = "dist",
    [string]$Package = "./cmd/game",
    [string]$OutputName = "game.wasm"
)

$ErrorActionPreference = "Stop"
Push-Location $ProjectDir
try {
    New-Item -ItemType Directory -Force -Path $DistDir | Out-Null

    $env:GOOS = "js"
    $env:GOARCH = "wasm"
    go build -trimpath -ldflags="-s -w" -o (Join-Path $DistDir $OutputName) $Package
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

    $goroot = go env GOROOT
    $goversion = (go env GOVERSION).TrimStart("go")
    $parts = $goversion.Split(".")
    $major = [int]$parts[0]
    $minor = [int]$parts[1]

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
    Pop-Location
}
