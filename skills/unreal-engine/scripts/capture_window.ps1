<#
.SYNOPSIS
  Capture a window (Unreal Editor, PIE, or a packaged game) to PNG and print the file path.

.DESCRIPTION
  Uses PrintWindow with full-content rendering, so the window is captured even when other
  windows cover it. Falls back to a screen copy of the window rectangle. The window must not
  be minimized, and the desktop must be unlocked.

.EXAMPLE
  .\capture_window.ps1                              # first Unreal Editor window
  .\capture_window.ps1 -Process MyGame-Win64-Shipping
  .\capture_window.ps1 -Title "Lvl_Main" -Out C:\tmp\shot.png
#>
[CmdletBinding()]
param(
  [string]$Process = "UnrealEditor",
  [string]$Title = "",
  [string]$Out = "",
  [switch]$Screen
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Drawing
if (-not ("AgentCaptureWin32" -as [type])) {
  Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class AgentCaptureWin32 {
  [StructLayout(LayoutKind.Sequential)]
  public struct RECT { public int Left; public int Top; public int Right; public int Bottom; }
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdc, uint flags);
  [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
}
"@
}
[void][AgentCaptureWin32]::SetProcessDPIAware()

$candidates = @(Get-Process -Name $Process -ErrorAction SilentlyContinue |
  Where-Object { $_.MainWindowHandle -ne [IntPtr]::Zero })
if ($Title) {
  $candidates = @($candidates | Where-Object { $_.MainWindowTitle -like "*$Title*" })
}
if ($candidates.Count -eq 0) {
  Write-Error "No window found for process '$Process' (title filter: '$Title')."
  exit 2
}
$target = $candidates[0]
$hwnd = $target.MainWindowHandle
if ([AgentCaptureWin32]::IsIconic($hwnd)) {
  Write-Error "The window '$($target.MainWindowTitle)' is minimized. Restore it and retry."
  exit 3
}

$rect = New-Object AgentCaptureWin32+RECT
[void][AgentCaptureWin32]::GetWindowRect($hwnd, [ref]$rect)
$width = $rect.Right - $rect.Left
$height = $rect.Bottom - $rect.Top
if ($width -le 0 -or $height -le 0) {
  Write-Error "The window has no size ($width x $height)."
  exit 4
}

$bitmap = New-Object System.Drawing.Bitmap $width, $height
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$printed = $false
if (-not $Screen) {
  $hdc = $graphics.GetHdc()
  try {
    $printed = [AgentCaptureWin32]::PrintWindow($hwnd, $hdc, 2)  # PW_RENDERFULLCONTENT
  } finally {
    $graphics.ReleaseHdc($hdc)
  }
}
if (-not $printed) {
  $graphics.CopyFromScreen($rect.Left, $rect.Top, 0, 0, $bitmap.Size)
}
$graphics.Dispose()

if (-not $Out) {
  $dir = Join-Path (Get-Location) "Saved\AgentCaptures"
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $Out = Join-Path $dir ("capture_{0:yyyyMMdd_HHmmss}.png" -f (Get-Date))
} else {
  $parent = Split-Path -Parent $Out
  if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
}
$bitmap.Save($Out, [System.Drawing.Imaging.ImageFormat]::Png)
$bitmap.Dispose()

$mode = if ($printed) { "PrintWindow" } else { "screen copy" }
Write-Host "Captured '$($target.MainWindowTitle)' ($width x $height, $mode)"
Write-Output (Resolve-Path $Out).Path
