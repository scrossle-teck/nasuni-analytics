<#
.SYNOPSIS
  Orchestrate analytics scripts for a run folder.

.PARAMETER RunPath
  Path to the run folder.

.PARAMETER OutDir
  Directory where per-check outputs will be written.

.PARAMETER Checks
  Comma-separated list of checks to run: BroadPerms, AccessibleBy, Summarize

.PARAMETER Identity
  When running AccessibleBy, the identity to query for.
#>
param(
    [Parameter(Mandatory = $true)][string]$RunPath,
    [string]$OutDir = "results",
    [string[]]$Checks = @('BroadPerms', 'Summarize'),
    [string]$Identity
)

if (-not (Test-Path $RunPath)) { Throw "RunPath not found: $RunPath" }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

foreach ($c in $Checks) {
    switch ($c.ToLower()) {
        'broadperms' {
            $out = Join-Path $OutDir 'broad-perms.csv'
            & "$PSScriptRoot\find-broad-perms.ps1" -RunPath $RunPath -OutPath $out
        }
        'accessibleby' {
            if (-not $Identity) { Write-Warning 'AccessibleBy requires -Identity; skipping'; break }
            $out = Join-Path $OutDir 'accessible-by.csv'
            & "$PSScriptRoot\find-accessible-by.ps1" -RunPath $RunPath -Identity $Identity -OutPath $out
        }
        'summarize' {
            $out = Join-Path $OutDir 'run-summary.csv'
            & "$PSScriptRoot\summarize-run.ps1" -RunPath $RunPath -OutPath $out
        }
        default { Write-Warning "Unknown check: $c" }
    }
}

Write-Output "Run analytics complete. Outputs in: $OutDir"
