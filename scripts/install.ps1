<#
.SYNOPSIS
  Install the skills in this repository into an agent's skills directory.
.DESCRIPTION
  Each skill is the same SKILL.md folder for every tool; only the destination
  differs. The -Tool shortcuts point at each agent's personal skills directory
  as documented at the time of writing. Use -Target for project scope or any
  tool not listed, and confirm paths against docs/compatibility.md.

  Creating symbolic links (-Link) on Windows requires Developer Mode or an
  elevated session; copying (the default) does not.
.EXAMPLE
  scripts/install.ps1 -Tool claude
.EXAMPLE
  scripts/install.ps1 -Target C:\path\to\skills -Link
#>
[CmdletBinding()]
param(
  [ValidateSet('claude', 'codex', 'gemini', 'grok')]
  [string]$Tool,
  [string]$Target,
  [switch]$Link
)

$ErrorActionPreference = 'Stop'

$repoDir = Split-Path -Parent $PSScriptRoot
$src = Join-Path $repoDir 'skills'

if (-not $Target) {
  if (-not $Tool) { throw 'Specify -Tool <name> or -Target <dir>.' }
  $userHome = $env:USERPROFILE
  $Target = switch ($Tool) {
    'claude' { Join-Path $userHome '.claude\skills' }
    'codex'  { Join-Path $userHome '.codex\skills' }
    'gemini' { Join-Path $userHome '.gemini\skills' }
    'grok'   { Join-Path $userHome '.grok\skills' }
  }
}

if (-not (Test-Path $src)) { throw "No skills directory found at $src" }

New-Item -ItemType Directory -Force -Path $Target | Out-Null

$count = 0
Get-ChildItem -Path $src -Directory | ForEach-Object {
  $dest = Join-Path $Target $_.Name
  if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
  if ($Link) {
    New-Item -ItemType SymbolicLink -Path $dest -Target $_.FullName | Out-Null
  } else {
    Copy-Item -Recurse -Path $_.FullName -Destination $dest
  }
  Write-Output "installed $($_.Name) -> $dest"
  $count++
}

Write-Output "done: $count skill(s) into $Target"
