# Build a raylib game for web with emcc and verified linker flags.
param(
    [string]$ProjectDir = ".",
    [string]$Output = "game.html",
    [string]$Main = "",
    [string]$RaylibPath = $env:RAYLIB_PATH,
    [string]$ShellFile = "web/minshell.html",
    [string]$Resources = "resources"
)

$ErrorActionPreference = "Stop"
Push-Location $ProjectDir
try {
    # Pick the entry file: honor an explicit -Main, else prefer main.c, then main.cpp.
    if (-not $Main) {
        if (Test-Path "main.c") { $Main = "main.c" }
        elseif (Test-Path "main.cpp") { $Main = "main.cpp" }
        else { Write-Error "No main.c or main.cpp found in $ProjectDir (pass -Main to override)" }
    }
    if (-not $RaylibPath) {
        Write-Error "Set RAYLIB_PATH to a raylib install with libraylib.web.a"
    }
    $lib = Join-Path $RaylibPath "src\libraylib.web.a"
    if (-not (Test-Path $lib)) {
        Write-Error "libraylib.web.a not found at $lib"
    }

    $args = @(
        "-o", $Output,
        $Main,
        "-Os", "-Wall",
        $lib,
        "-I$(Join-Path $RaylibPath 'src')",
        "-sUSE_GLFW=3",
        "-sASYNCIFY",
        "-sGL_ENABLE_GET_PROC_ADDRESS=1",
        "-sFORCE_FILESYSTEM=1",
        "-sTOTAL_MEMORY=67108864",
        "--shell-file", $ShellFile
    )
    if (Test-Path $Resources) {
        $args += "--preload-file", $Resources
    }

    & emcc @args
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    Write-Host "Web build complete: $Output"
}
finally {
    Pop-Location
}
