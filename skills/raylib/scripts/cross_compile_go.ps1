# Cross-compile a raylib-go desktop binary.
param(
    [ValidateSet("windows", "darwin", "linux")]
    [string]$Target = "windows",
    [string]$Output = "dist/game",
    [string]$Main = "."
)

$ErrorActionPreference = "Stop"

# Save the caller's build environment so these settings do not leak into the
# parent shell. SetEnvironmentVariable with a null value removes the variable,
# which correctly restores variables that were unset to begin with.
$saved = @{
    CGO_ENABLED = $env:CGO_ENABLED
    CC          = $env:CC
    GOOS        = $env:GOOS
    GOARCH      = $env:GOARCH
}

try {
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
}
finally {
    foreach ($name in $saved.Keys) {
        [Environment]::SetEnvironmentVariable($name, $saved[$name], "Process")
    }
}
