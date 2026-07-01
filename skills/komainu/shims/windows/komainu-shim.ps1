# Komainu PATH shim for Windows (PowerShell).
# Dot-source from your $PROFILE to intercept raw clone/install:
#     . "$HOME\.komainu\komainu-shim.ps1"
# It defines wrapper functions that shadow git/gh/npm/... on the command path.
# Pattern SoT: core/gate.py. Audited bypass: $env:KOMAINU_BYPASS = '1'.

$KomainuBlock = @(
  'git\s+clone', 'gh\s+repo\s+clone', 'git\s+submodule\s+(add|update\s+--init)',
  'npx\s+degit', '\bdegit\b', 'pip[0-9]?\s+install\s+.*(git\+|https?://)',
  'cargo\s+install\s+--git', 'go\s+install\s+\S+@',
  '(curl|wget)\s+[^|]*\|\s*(sudo\s+)?(sh|bash|zsh|python|node|ruby|pwsh)',
  'claude\s+plugin\s+(install|marketplace\s+add)',
  'npm\s+install\s+.*(github:|git\+|https?://)'
) -join '|'

function Invoke-KomainuGuard {
  param([string]$Tool, [string[]]$Args)
  $full = "$Tool $($Args -join ' ')"
  if ($env:KOMAINU_BYPASS -ne '1' -and $full -notmatch 'komainu' -and $full -match $KomainuBlock) {
    Write-Error "[komainu] blocked raw acquisition: $full`nRoute via: komainu import <https-url>  (bypass: `$env:KOMAINU_BYPASS='1')"
    $log = if ($env:KOMAINU_AUDIT) { $env:KOMAINU_AUDIT } else { "$HOME\.komainu\audit.log" }
    New-Item -ItemType Directory -Force -Path (Split-Path $log) | Out-Null
    "$(Get-Date -Format s)`tBLOCK`t$full" | Add-Content $log
    return $false
  }
  return $true
}

function git  { if (Invoke-KomainuGuard 'git'  $args) { & (Get-Command git.exe  -CommandType Application | Select-Object -First 1) @args } }
function gh   { if (Invoke-KomainuGuard 'gh'   $args) { & (Get-Command gh.exe   -CommandType Application | Select-Object -First 1) @args } }
function npm  { if (Invoke-KomainuGuard 'npm'  $args) { & (Get-Command npm.cmd  -CommandType Application | Select-Object -First 1) @args } }
function pip  { if (Invoke-KomainuGuard 'pip'  $args) { & (Get-Command pip.exe  -CommandType Application | Select-Object -First 1) @args } }
function npx  { if (Invoke-KomainuGuard 'npx'  $args) { & (Get-Command npx.cmd  -CommandType Application | Select-Object -First 1) @args } }
