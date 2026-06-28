# Cross-compile a raylib-go desktop binary.
param(
    [ValidateSet("windows", "darwin", "linux")]
    [string]$Target = "windows",
    [string]$Output = "dist/game",
    [string]$Main = "."
)

$ErrorActionPreference = "Stop"

switch ($Target) {
    "windows" {
        $env:CGO_ENABLED = "1"
        $env:CC = "x86_64-w64-mingw32-gcc"
        $env:GOOS = "windows"
        $env:GOARCH = "amd64"
        go build -ldflags "-s -w -H=windowsgui" -o "$Output.exe" $Main
    }
    "darwin" {
        $env:CGO_ENABLED = "1"
        $env:CC = "x86_64-apple-darwin21.1-clang"
        $env:GOOS = "darwin"
        $env:GOARCH = "amd64"
        go build -ldflags "-linkmode external -s -w '-extldflags=-mmacosx-version-min=10.15'" -o $Output $Main
    }
    "linux" {
        $env:CGO_ENABLED = "1"
        $env:GOOS = "linux"
        $env:GOARCH = "amd64"
        go build -ldflags "-s -w" -o $Output $Main
    }
}

if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
Write-Host "Built $Target binary: $Output"
